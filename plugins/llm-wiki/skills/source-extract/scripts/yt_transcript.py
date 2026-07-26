#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["yt-dlp>=2025.1.1"]
# ///
"""유튜브 자막 추출 — llm-wiki 플러그인.

usage: uv run yt_transcript.py URL [--langs ko,en]

수동 자막 우선(없으면 자동 자막)으로 VTT를 받아 롤링 캡션 중복을 정리하고
frontmatter + [mm:ss] 문단 트랜스크립트를 stdout으로 출력한다.
영상 다운로드 금지. wiki/ 파일 직접 쓰기 금지.

exit: 0 성공 / 1 일반 오류 / 2 자막 없음
"""
from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from dataclasses import dataclass

PARAGRAPH_GAP_SECONDS = 4.0
PARAGRAPH_MAX_CHARS = 600
NO_SUBTITLE_MSG = "자막이 없는 영상 — 지원 범위 외. 영상 설명란·발표 자료·관련 글 등 수동 대안을 사용하세요."

TIMESTAMP_RE = re.compile(r"(?P<h>\d{1,2}):(?P<m>\d{2}):(?P<s>\d{2})[.,](?P<ms>\d{3})")
TAG_RE = re.compile(r"<[^>]+>")


class NoSubtitlesError(Exception):
    pass


@dataclass
class Cue:
    start: float
    text: str


def _ts_to_seconds(ts: str) -> float:
    m = TIMESTAMP_RE.search(ts)
    if not m:
        raise ValueError(f"타임스탬프 형식 오류: {ts!r}")
    return int(m["h"]) * 3600 + int(m["m"]) * 60 + int(m["s"]) + int(m["ms"]) / 1000


def parse_vtt(text: str) -> list[Cue]:
    cues: list[Cue] = []
    for block in re.split(r"\n\s*\n", text):
        lines = [ln for ln in block.strip().splitlines() if ln.strip()]
        idx = next((i for i, ln in enumerate(lines) if "-->" in ln), None)
        if idx is None:
            continue  # WEBVTT 헤더·NOTE·STYLE 블록
        start = _ts_to_seconds(lines[idx].split("-->")[0])
        payload = TAG_RE.sub("", " ".join(lines[idx + 1:]))
        payload = re.sub(r"\s+", " ", payload).strip()
        if payload:
            cues.append(Cue(start=start, text=payload))
    return cues


MIN_OVERLAP_CHARS = 4


def _longest_overlap(prev: str, cur: str) -> int:
    """prev의 접미부 == cur의 접두부인 최대 문자 수.

    롤링 캡션은 직전 라인 전체를 반복하므로, 우발적 짧은 겹침을 잘라내지 않도록
    단어 경계에서 끝나는 MIN_OVERLAP_CHARS 이상의 겹침만 인정한다.
    """
    for n in range(min(len(prev), len(cur)), MIN_OVERLAP_CHARS - 1, -1):
        if prev[-n:] != cur[:n]:
            continue
        cur_boundary = n == len(cur) or cur[n] == " "
        prev_boundary = n == len(prev) or prev[-n - 1] == " "
        if cur_boundary and prev_boundary:
            return n
    return 0


def dedupe_cues(cues: list[Cue]) -> list[Cue]:
    """자동 자막 롤링 캡션 정리: 직전 큐와의 완전 중복·겹치는 접두부 제거."""
    result: list[Cue] = []
    prev = ""
    for cue in cues:
        if cue.text == prev:
            continue
        text = cue.text
        if prev:
            text = text[_longest_overlap(prev, text):].strip()
        if text:
            result.append(Cue(start=cue.start, text=text))
        prev = cue.text
    return result


def to_paragraphs(
    cues: list[Cue],
    gap: float = PARAGRAPH_GAP_SECONDS,
    max_chars: int = PARAGRAPH_MAX_CHARS,
) -> list[tuple[float, str]]:
    """시간 간격 또는 누적 길이 기준으로 큐를 문단으로 병합한다."""
    paragraphs: list[tuple[float, str]] = []
    buf: list[str] = []
    buf_start = 0.0
    prev_start: float | None = None
    for cue in cues:
        too_far = prev_start is not None and cue.start - prev_start > gap
        too_long = sum(len(t) + 1 for t in buf) >= max_chars
        if buf and (too_far or too_long):
            paragraphs.append((buf_start, " ".join(buf)))
            buf = []
        if not buf:
            buf_start = cue.start
        buf.append(cue.text)
        prev_start = cue.start
    if buf:
        paragraphs.append((buf_start, " ".join(buf)))
    return paragraphs


def format_timestamp(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def render_markdown(meta: dict, paragraphs: list[tuple[float, str]]) -> str:
    def q(v: object) -> str:
        return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'

    lines = [
        "---",
        f"title: {q(meta.get('title', ''))}",
        f"channel: {q(meta.get('channel', ''))}",
        f"url: {q(meta.get('url', ''))}",
        f"upload_date: {meta.get('upload_date', '')}",
        f"duration: {meta.get('duration', '')}",
        f"lang: {meta.get('lang', '')}",
        f"kind: {meta.get('kind', '')}",
        f"retrieved: {meta.get('retrieved', '')}",
        "---",
        "",
    ]
    for start, text in paragraphs:
        lines.append(f"[{format_timestamp(start)}] {text}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def fetch(url: str, langs: list[str]) -> tuple[dict, str]:
    """메타데이터와 VTT 원문을 가져온다(네트워크). 자막 없으면 NoSubtitlesError."""
    import urllib.request

    from yt_dlp import YoutubeDL

    with YoutubeDL({"skip_download": True, "quiet": True, "no_warnings": True}) as ydl:
        info = ydl.extract_info(url, download=False)

    def pick(track_map: dict | None) -> tuple[str, str] | None:
        for lang in langs:
            for key, formats in (track_map or {}).items():
                if key == lang or key.startswith(lang + "-"):
                    for f in formats:
                        if f.get("ext") == "vtt" and f.get("url"):
                            return key, f["url"]
        return None

    picked, kind = pick(info.get("subtitles")), "manual"
    if picked is None:
        picked, kind = pick(info.get("automatic_captions")), "auto"
    if picked is None:
        raise NoSubtitlesError()
    lang, vtt_url = picked
    with urllib.request.urlopen(vtt_url) as resp:
        vtt = resp.read().decode("utf-8", errors="replace")

    upload = str(info.get("upload_date") or "")
    if len(upload) == 8:
        upload = f"{upload[:4]}-{upload[4:6]}-{upload[6:8]}"
    meta = {
        "title": info.get("title", ""),
        "channel": info.get("channel") or info.get("uploader", ""),
        "url": info.get("webpage_url", url),
        "upload_date": upload,
        "duration": format_timestamp(info.get("duration") or 0),
        "lang": lang,
        "kind": kind,
        "retrieved": _dt.date.today().isoformat(),
    }
    return meta, vtt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="유튜브 자막 → 정리된 마크다운(stdout)")
    parser.add_argument("url")
    parser.add_argument("--langs", default="ko,en", help="자막 언어 우선순위(쉼표 구분, 기본 ko,en)")
    args = parser.parse_args(argv)
    langs = [x.strip() for x in args.langs.split(",") if x.strip()]
    try:
        meta, vtt = fetch(args.url, langs)
    except NoSubtitlesError:
        print(NO_SUBTITLE_MSG, file=sys.stderr)
        return 2
    except Exception as e:  # noqa: BLE001
        print(f"오류: {e}", file=sys.stderr)
        return 1
    cues = dedupe_cues(parse_vtt(vtt))
    if not cues:
        print(NO_SUBTITLE_MSG, file=sys.stderr)
        return 2
    sys.stdout.write(render_markdown(meta, to_paragraphs(cues)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
