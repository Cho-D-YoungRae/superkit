#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["yt-dlp>=2025.1.1"]
# ///
"""유튜브 자막 추출 — llm-wiki 플러그인.

usage: uv run yt_transcript.py URL [--langs ko,en]

VTT 자막을 받아 롤링 캡션 중복을 정리하고
frontmatter + [mm:ss] 문단 트랜스크립트를 stdout으로 출력한다.
영상 다운로드 금지. wiki/ 파일 직접 쓰기 금지.
재생목록 안의 영상 URL(watch?v=…&list=…)은 그 영상 하나만 처리한다. 재생목록 URL 자체
(/playlist?list=…)는 지원 범위 외다(exit 1 — 영상 URL을 하나씩 넘긴다).

자막 선택은 충실도 우선이다 — raw 원본은 위키의 불변 원본 계층이므로
선호 언어의 기계 번역보다 원어 그대로가 낫다. 선택 결과는 frontmatter kind로 밝힌다:
  1. 수동 자막 — --langs 순서, 없으면 영상 원어의 수동 자막 (kind: manual)
  2. 원어 자동 자막(ASR) — 영상 원어(info.language) 트랙 우선, 다음 --langs에 맞는 원어, 없으면 아무 원어
     (kind: auto). 자동 더빙 영상은 더빙 오디오마다 `-orig` ASR이 붙으므로 영상 원어를 먼저 본다
  3. 최후 수단: --langs에 맞는 기계 번역 자동 자막(tlang=) (kind: auto-translated)

exit: 0 성공 / 1 일반 오류·사용법 오류 / 2 자막 없음
"""
from __future__ import annotations

import argparse
import datetime as _dt
import html
import re
import sys
from dataclasses import dataclass
from typing import NoReturn
from urllib.parse import parse_qs, urlparse

PARAGRAPH_GAP_SECONDS = 4.0
PARAGRAPH_MAX_CHARS = 600
NO_SUBTITLE_MSG = "자막이 없는 영상 — 지원 범위 외. 영상 설명란·발표 자료·관련 글 등 수동 대안을 사용하세요."
ORIG_SUFFIX = "-orig"  # yt-dlp가 원어 자동 자막(ASR)에 붙이는 표지 — 번역 트랙과 구분한다

YDL_OPTS = {
    "skip_download": True,  # 영상 다운로드 금지 — 메타데이터·자막 목록만
    "quiet": True,  # stdout은 트랜스크립트 전용
    "no_warnings": True,
    "noplaylist": True,  # watch?v=ID&list=PL… 가 재생목록 전체로 풀리지 않게
    "extract_flat": "in_playlist",  # 재생목록 URL이면 항목을 하나하나 조회하지 않는다(바로 거절)
    "socket_timeout": 30,  # 초 — 자막 다운로드(ydl.urlopen)에도 적용
    "ignore_no_formats_error": True,  # 자막만 쓴다 — 영상 포맷이 없다고 추출 전체를 실패시키지 않는다
}
PLAYLIST_MSG = "재생목록 URL — 지원 범위 외. 재생목록 안의 영상 URL을 하나씩 인제스트하세요."

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
        payload = html.unescape(payload)  # 태그 제거 뒤에 — &lt;x&gt;가 만든 <x>는 태그가 아니라 본문
        payload = re.sub(r"\s+", " ", payload).strip()  # &nbsp;(U+00A0)도 공백으로 정규화
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

    # YAML 1.1(PyYAML 등)은 따옴표 없는 10:00을 60진수 정수 600으로, no(노르웨이어)를 false로 읽는다
    lines = [
        "---",
        f"title: {q(meta.get('title', ''))}",
        f"channel: {q(meta.get('channel', ''))}",
        f"url: {q(meta.get('url', ''))}",
        f"upload_date: {meta.get('upload_date', '')}",
        f"duration: {q(meta.get('duration', ''))}",
        f"lang: {q(meta.get('lang', ''))}",
        f"kind: {meta.get('kind', '')}",
        f"retrieved: {meta.get('retrieved', '')}",
        "---",
        "",
    ]
    for start, text in paragraphs:
        lines.append(f"[{format_timestamp(start)}] {text}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _vtt_url(formats: list[dict] | None) -> str | None:
    return next((f["url"] for f in formats or [] if f.get("ext") == "vtt" and f.get("url")), None)


def _first_vtt(tracks: dict[str, list[dict]], langs: list[str] | None) -> tuple[str, str] | None:
    """langs 순서로 언어가 맞는(None이면 언어 무관) 첫 vtt 트랙의 (키, URL)."""
    for lang in [None] if langs is None else langs:
        for key, formats in tracks.items():
            matches = lang is None or key == lang or key.startswith(lang + "-")
            if matches and (url := _vtt_url(formats)):
                return key, url
    return None


def _is_machine_translated(formats: list[dict] | None) -> bool:
    """자막 URL에 tlang=이 붙은 트랙은 YouTube 기계 번역이다."""
    return "tlang" in parse_qs(urlparse(_vtt_url(formats) or "").query)


def pick_track(info: dict, langs: list[str]) -> tuple[str, str, str] | None:
    """yt-dlp info에서 (lang, vtt_url, kind)를 고른다 — 우선순위는 모듈 docstring. 없으면 None.

    yt-dlp automatic_captions에는 번역 언어마다 기계 번역 트랙(tlang=)이 들어 있고,
    원어 ASR 트랙은 `<lang>-orig`(+호환용 `<lang>`)로 표시된다. 번역 언어 목록을 주지 않는
    클라이언트의 응답이면 `-orig` 키 없이 원어 트랙만 오고, 원어가 번역 언어 목록 밖이면(예: 광둥어)
    `-orig` 없이 원어와 번역이 섞여 온다 — 그때는 URL의 tlang=으로 가른다.
    """
    manual = info.get("subtitles") or {}
    auto = info.get("automatic_captions") or {}
    # 원어 URL은 `-orig` 키에서 가져온다 — 호환용 `<lang>` 키에는 (다중 오디오 영상에서)
    # 다른 원어의 번역 트랙이 앞서 섞일 수 있다.
    originals = {k.removesuffix(ORIG_SUFFIX): v for k, v in auto.items() if k.endswith(ORIG_SUFFIX)} or {
        k: v for k, v in auto.items() if not _is_machine_translated(v)
    }
    video_lang = info.get("language") or ""
    video_langs = [x for x in dict.fromkeys((video_lang, video_lang.split("-")[0])) if x]

    # 수동 자막은 langs 순서로, 없으면 영상 원어의 수동 자막(langs 밖이어도 원어 ASR보다 정확하다)
    if hit := (_first_vtt(manual, langs) or _first_vtt(manual, video_langs or list(originals))):
        return (*hit, "manual")

    # 원어 ASR — 영상 원어 먼저: 자동 더빙 영상은 더빙 오디오(사실상 기계 번역)마다 `-orig` ASR이 붙는다
    if hit := (_first_vtt(originals, video_langs) or _first_vtt(originals, langs) or _first_vtt(originals, None)):
        return (*hit, "auto")

    translated = {k: v for k, v in auto.items() if not k.endswith(ORIG_SUFFIX) and k not in originals}
    if hit := _first_vtt(translated, langs):
        return (*hit, "auto-translated")
    return None


def fetch(url: str, langs: list[str]) -> tuple[dict, str]:
    """메타데이터와 VTT 원문을 가져온다(네트워크). 자막 없으면 NoSubtitlesError."""
    from yt_dlp import YoutubeDL

    with YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(url, download=False)
        if info.get("_type") == "playlist":
            raise ValueError(PLAYLIST_MSG)
        picked = pick_track(info, langs)
        if picked is None:
            raise NoSubtitlesError()
        lang, vtt_url, kind = picked
        # yt-dlp 네트워크 계층 재사용 — 헤더·프록시·쿠키 설정과 socket_timeout이 그대로 적용된다
        with ydl.urlopen(vtt_url) as resp:
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


class _Parser(argparse.ArgumentParser):
    """사용법 오류는 exit 1 — argparse 기본값(2)은 플러그인 스크립트의 exit 2(도메인 특수상황) 규약과 충돌한다."""

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(1, f"{self.prog}: 오류: {message}\n")


def main(argv: list[str] | None = None) -> int:
    parser = _Parser(description="유튜브 자막 → 정리된 마크다운(stdout)")
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
