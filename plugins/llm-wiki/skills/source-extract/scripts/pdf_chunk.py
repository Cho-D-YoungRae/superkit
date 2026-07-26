#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pymupdf>=1.24"]
# ///
"""장문 PDF 분할 — llm-wiki 플러그인.

usage: uv run pdf_chunk.py PATH [--chunk-pages 20] [--cache-dir raw/.cache] [--force] [--info]

PDF를 sha256 기반 캐시 디렉토리(<cache-dir>/<sha12>/)에 part-NN.md로 분할한다.
캐시가 있으면 재사용(idempotent)하고 --force로 재생성한다.
TOC(목차)가 있으면 최상위 챕터 경계를 우선하고, 챕터가 chunk-pages의 1.5배를
넘으면 고정 쪽수로 재분할한다. TOC가 없으면 고정 쪽수 분할.
--info는 쪽수·목차 유무만 JSON으로 출력하고 아무 파일도 만들지 않는다.
stdout에는 JSON만 출력한다. wiki/ 파일 직접 쓰기 금지.

exit: 0 성공 / 1 일반 오류 / 2 텍스트 추출 불가(암호화·스캔본)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

RESPLIT_FACTOR = 1.5
MIN_TEXT_CHARS = 50


class ExtractError(Exception):
    pass


@dataclass
class Chunk:
    start: int  # 1-기반 시작 쪽 (포함)
    end: int    # 1-기반 끝 쪽 (포함)
    title: str | None = None


def _fixed_chunks(start: int, end: int, chunk_pages: int, title: str | None) -> list[Chunk]:
    out: list[Chunk] = []
    s = start
    n = 0
    while s <= end:
        e = min(s + chunk_pages - 1, end)
        n += 1
        out.append(Chunk(start=s, end=e, title=f"{title} ({n})" if title else None))
        s = e + 1
    return out


def plan_chunks(page_count: int, toc: list, chunk_pages: int) -> list[Chunk]:
    """분할 계획(순수 로직). toc 항목: (level, title, 1-기반 시작쪽)."""
    if page_count <= 0:
        return []
    top = [(str(t), int(p)) for level, t, p in toc if level == 1 and 1 <= int(p) <= page_count]
    if not top:
        return _fixed_chunks(1, page_count, chunk_pages, None)
    titles: dict[int, str] = {}
    for t, p in top:
        titles.setdefault(p, t)
    starts = sorted(titles)
    if starts[0] != 1:
        titles.setdefault(1, "(front matter)")
        starts = [1] + starts
    chunks: list[Chunk] = []
    for i, s in enumerate(starts):
        e = (starts[i + 1] - 1) if i + 1 < len(starts) else page_count
        if e < s:
            continue
        title = titles.get(s)
        if (e - s + 1) > chunk_pages * RESPLIT_FACTOR:
            chunks.extend(_fixed_chunks(s, e, chunk_pages, title))
        else:
            chunks.append(Chunk(start=s, end=e, title=title))
    return chunks


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


def build_cache(pdf_path: Path, cache_dir: Path, chunk_pages: int, force: bool) -> dict:
    import pymupdf  # 지연 임포트

    sha = file_sha256(pdf_path)
    sha12 = sha[:12]
    out_dir = cache_dir / sha12
    manifest_path = out_dir / "manifest.json"
    if manifest_path.is_file() and not force:
        return json.loads(manifest_path.read_text(encoding="utf-8"))

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
        "toc_used": any(entry[0] == 1 for entry in toc),
        "parts": parts,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="장문 PDF 분할 → 캐시 + manifest JSON(stdout)")
    parser.add_argument("path")
    parser.add_argument("--chunk-pages", type=int, default=20, help="목차 없을 때 고정 분할 쪽수(기본 20)")
    parser.add_argument("--cache-dir", default="raw/.cache", help="캐시 디렉토리(기본 raw/.cache)")
    parser.add_argument("--force", action="store_true", help="캐시 무시하고 재생성")
    parser.add_argument("--info", action="store_true", help="쪽수·목차 정보만 출력(캐시 미생성)")
    args = parser.parse_args(argv)

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
