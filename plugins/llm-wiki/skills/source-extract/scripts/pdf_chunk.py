#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pymupdf>=1.24"]
# ///
"""장문 PDF 분할 — llm-wiki 플러그인.

usage: uv run pdf_chunk.py PATH [--chunk-pages 20] [--cache-dir raw/.cache] [--force] [--info]

PDF를 sha256 기반 캐시 디렉토리(<cache-dir>/<sha12>/)에 part-NN.md로 분할한다.
manifest의 chunk_pages·plan_version이 이번 실행과 같으면 캐시를 재사용(idempotent)하고,
다르거나 --force면 이전 part 파일을 지우고 재생성한다.

분할 계획(N = --chunk-pages, 재분할 한도 = N × 1.5):
1. 문서 전체를, 구간 안(시작 쪽 초과)에 경계가 하나라도 있는 가장 얕은 목차 레벨에서 자른다.
   첫 조각의 제목은 그 레벨의 시작 쪽 항목, 없으면 상위 제목(최상위는 "(front matter)").
2. 한도를 넘는 조각은 같은 규칙으로 더 깊은 레벨에서만 다시 자르고(재귀), 더 깊은 경계가
   없으면 N쪽 고정 조각("<제목> (n)")으로 나눈다.
3. 연속된 온전한 조각(고정 조각 제외)은 합계 N쪽 이하인 동안 병합한다("<첫 제목> ~ <끝 제목>").
1..쪽수 밖을 가리키는 목차 항목은 무시하고, 유효한 목차가 없으면 N쪽 고정 분할.
--info는 쪽수·목차 유무만 JSON으로 출력하고 아무 파일도 만들지 않는다.
stdout에는 JSON만 출력한다. wiki/ 파일 직접 쓰기 금지.

exit: 0 성공 / 1 일반 오류·사용법 오류 / 2 텍스트 추출 불가(암호화·스캔본)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

RESPLIT_FACTOR = 1.5
MIN_TEXT_CHARS = 50
PLAN_VERSION = 2  # 분할 알고리즘이 바뀌면 올린다 — manifest 값과 다르면 캐시를 재생성
FRONT_MATTER = "(front matter)"


class ExtractError(Exception):
    pass


@dataclass
class Chunk:
    start: int  # 1-기반 시작 쪽 (포함)
    end: int    # 1-기반 끝 쪽 (포함)
    title: str | None = None
    split: bool = False  # 고정 쪽수 조각 — 병합하지 않는다


def _fixed_chunks(start: int, end: int, chunk_pages: int, title: str | None) -> list[Chunk]:
    out: list[Chunk] = []
    s = start
    n = 0
    while s <= end:
        e = min(s + chunk_pages - 1, end)
        n += 1
        out.append(Chunk(start=s, end=e, title=f"{title} ({n})" if title else None, split=True))
        s = e + 1
    return out


def _toc_entries(toc: list, page_count: int) -> list[tuple[int, str, int]]:
    """유효한 목차 항목 (level, title, 1-기반 쪽). 1..page_count 밖을 가리키는 항목은 버린다."""
    entries: list[tuple[int, str, int]] = []
    for entry in toc:
        level, title, page = entry[:3]
        if 1 <= int(page) <= page_count:
            entries.append((int(level), str(title), int(page)))
    return entries


def _split_span(
    entries: list[tuple[int, str, int]], start: int, end: int, parent_level: int, title: str, chunk_pages: int
) -> list[Chunk]:
    """[start, end] 구간(제목 title)을 parent_level보다 깊은 목차 경계로 나눈다(재귀)."""
    inner = [(lv, t, p) for lv, t, p in entries if lv > parent_level and start < p <= end]
    if not inner:  # 더 나눌 경계가 없다 — 한도를 넘으면 고정 조각
        if end - start + 1 > chunk_pages * RESPLIT_FACTOR:
            return _fixed_chunks(start, end, chunk_pages, title)
        return [Chunk(start=start, end=end, title=title)]
    level = min(lv for lv, _, _ in inner)  # 구간 안에 경계가 있는 가장 얕은 레벨
    bounds: dict[int, str] = {}
    for lv, t, p in inner:
        if lv == level:
            bounds.setdefault(p, t)
    first = next((t for lv, t, p in entries if lv == level and p == start), title)
    starts = [start, *sorted(bounds)]
    out: list[Chunk] = []
    for i, s in enumerate(starts):
        e = starts[i + 1] - 1 if i + 1 < len(starts) else end
        seg_title = bounds[s] if i else first
        if e - s + 1 > chunk_pages * RESPLIT_FACTOR:
            out.extend(_split_span(entries, s, e, level, seg_title, chunk_pages))  # 더 깊은 레벨로만
        else:
            out.append(Chunk(start=s, end=e, title=seg_title))
    return out


def _merge_segments(segments: list[Chunk], chunk_pages: int) -> list[Chunk]:
    """연속된 온전한 조각을 합계 chunk_pages 이하인 동안 탐욕적으로 병합한다. 고정 조각은 그대로 둔다."""
    groups: list[list[Chunk]] = []
    for seg in segments:
        last = groups[-1] if groups else None
        if last and not seg.split and not last[-1].split and seg.end - last[0].start + 1 <= chunk_pages:
            last.append(seg)
        else:
            groups.append([seg])
    return [
        g[0] if len(g) == 1 else Chunk(start=g[0].start, end=g[-1].end, title=f"{g[0].title} ~ {g[-1].title}")
        for g in groups
    ]


def plan_chunks(page_count: int, toc: list, chunk_pages: int) -> list[Chunk]:
    """분할 계획(순수 로직). toc 항목: (level, title, 1-기반 시작쪽). 규칙은 모듈 docstring 참조."""
    if chunk_pages < 1:
        raise ValueError(f"chunk_pages는 1 이상이어야 합니다: {chunk_pages}")  # 0 이하는 고정 분할이 끝나지 않는다
    if page_count <= 0:
        return []
    entries = _toc_entries(toc, page_count)
    if not entries:
        return _fixed_chunks(1, page_count, chunk_pages, None)
    if any(p > 1 for _, _, p in entries):
        title = FRONT_MATTER  # 첫 경계 앞에 그 레벨 항목이 없을 때의 제목
    else:
        title = min(entries, key=lambda e: e[0])[1]  # 모든 항목이 1쪽 — 가장 얕은 항목이 문서 전체 제목
    top_level = min(lv for lv, _, _ in entries) - 1
    return _merge_segments(_split_span(entries, 1, page_count, top_level, title, chunk_pages), chunk_pages)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _q(v: str) -> str:
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def info_mode(pdf_path: Path) -> dict:
    import pymupdf  # 지연 임포트

    with pymupdf.open(pdf_path) as doc:
        if doc.needs_pass:
            raise ExtractError("암호화된 PDF — 암호를 해제한 사본으로 다시 시도하세요.")
        toc = doc.get_toc() or []
        return {
            "pages": doc.page_count,
            "toc": bool(toc),
            "toc_top_entries": sum(1 for entry in toc if entry[0] == 1),
        }


def _reusable_manifest(manifest_path: Path, chunk_pages: int) -> dict | None:
    """분할 설정(chunk_pages·plan_version)이 이번 실행과 같은 캐시 manifest. 없거나 다르거나 깨졌으면 None."""
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):  # 없음 또는 쓰기 중단으로 깨짐
        return None
    if (
        not isinstance(manifest, dict)
        or manifest.get("chunk_pages") != chunk_pages
        or manifest.get("plan_version") != PLAN_VERSION
    ):
        return None
    for part in manifest.get("parts", []):
        part["file"] = str(manifest_path.parent / Path(part["file"]).name)  # 현재 --cache-dir 기준 경로
    return manifest


def build_cache(pdf_path: Path, cache_dir: Path, chunk_pages: int, force: bool) -> dict:
    import pymupdf  # 지연 임포트

    sha = file_sha256(pdf_path)
    sha12 = sha[:12]
    out_dir = cache_dir / sha12
    manifest_path = out_dir / "manifest.json"
    if not force:
        cached = _reusable_manifest(manifest_path, chunk_pages)
        if cached is not None:
            return cached

    with pymupdf.open(pdf_path) as doc:
        if doc.needs_pass:
            raise ExtractError("암호화된 PDF — 암호를 해제한 사본으로 다시 시도하세요.")
        toc = doc.get_toc() or []
        page_texts = [doc[i].get_text("text").strip() for i in range(doc.page_count)]
        if sum(len(t) for t in page_texts) < MIN_TEXT_CHARS:
            raise ExtractError("텍스트를 추출할 수 없는 PDF(스캔본 추정) — OCR된 사본으로 다시 시도하세요.")
        chunks = plan_chunks(doc.page_count, toc, chunk_pages)
        page_count = doc.page_count

    out_dir.mkdir(parents=True, exist_ok=True)
    # 이전 분할 결과 정리 — manifest부터 지워 중간에 멈춰도 불완전한 캐시가 재사용되지 않게 한다
    manifest_path.unlink(missing_ok=True)
    for stale in out_dir.glob("part-*.md"):
        stale.unlink()
    total = len(chunks)
    parts: list[dict] = []
    for i, ch in enumerate(chunks, start=1):
        fname = f"part-{i:02d}.md"
        front = [
            "---",
            f"source: {_q(str(pdf_path))}",
            f"part: {i}/{total}",
            f"pages: {ch.start}-{ch.end}",
        ]
        if ch.title:
            front.append(f"toc_title: {_q(ch.title)}")
        front += ["---", ""]
        body: list[str] = []
        for pno in range(ch.start, ch.end + 1):
            body.append(f"[p.{pno}]")
            body.append(page_texts[pno - 1])
            body.append("")
        (out_dir / fname).write_text("\n".join(front + body).rstrip() + "\n", encoding="utf-8")
        parts.append({"file": str(out_dir / fname), "pages": f"{ch.start}-{ch.end}", "title": ch.title})

    manifest = {
        "source": str(pdf_path),
        "sha256": sha,
        "sha12": sha12,
        "pages": page_count,
        "chunk_pages": chunk_pages,
        "plan_version": PLAN_VERSION,
        "toc_used": bool(_toc_entries(toc, page_count)),
        "parts": parts,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


class _Parser(argparse.ArgumentParser):
    """사용법 오류는 exit 1 — argparse 기본값(2)은 플러그인 스크립트의 exit 2(도메인 특수상황) 규약과 충돌한다."""

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(1, f"{self.prog}: 오류: {message}\n")


def main(argv: list[str] | None = None) -> int:
    parser = _Parser(description="장문 PDF 분할 → 캐시 + manifest JSON(stdout)")
    parser.add_argument("path")
    parser.add_argument(
        "--chunk-pages", type=int, default=20, help="청크 목표 쪽수 — 고정 분할 단위이자 목차 구간 병합 상한(기본 20)"
    )
    parser.add_argument("--cache-dir", default="raw/.cache", help="캐시 디렉토리(기본 raw/.cache)")
    parser.add_argument("--force", action="store_true", help="캐시 무시하고 재생성")
    parser.add_argument("--info", action="store_true", help="쪽수·목차 정보만 출력(캐시 미생성)")
    args = parser.parse_args(argv)
    if args.chunk_pages < 1:
        parser.error("--chunk-pages는 1 이상이어야 합니다.")  # 0 이하는 고정 분할이 끝나지 않는다

    pdf_path = Path(args.path)
    try:
        if not pdf_path.is_file():
            raise FileNotFoundError(f"파일이 없습니다: {pdf_path}")
        if args.info:
            result = info_mode(pdf_path)
        else:
            result = build_cache(pdf_path, Path(args.cache_dir), args.chunk_pages, args.force)
    except ExtractError as e:
        print(str(e), file=sys.stderr)
        return 2
    except Exception as e:  # noqa: BLE001
        print(f"오류: {e}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
