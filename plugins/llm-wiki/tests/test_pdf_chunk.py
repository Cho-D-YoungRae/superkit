import json
import os
import shutil
from pathlib import Path

import pytest


def make_pdf(path, pages=45, toc=None, with_text=True):
    import pymupdf

    doc = pymupdf.open()
    for i in range(pages):
        page = doc.new_page()
        if with_text:
            page.insert_text((72, 72), f"Page {i + 1} body text for testing.")
    if toc:
        doc.set_toc(toc)
    doc.save(str(path))
    doc.close()
    return path


def run(pdf_chunk, argv):
    import contextlib
    import io

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = pdf_chunk.main(argv)
    return code, buf.getvalue()


def test_plan_chunks_fixed_without_toc(pdf_chunk):
    chunks = pdf_chunk.plan_chunks(45, [], 20)
    assert [(c.start, c.end) for c in chunks] == [(1, 20), (21, 40), (41, 45)]


def test_plan_chunks_prefers_toc_chapters(pdf_chunk):
    toc = [(1, "Ch 1", 1), (2, "Sec 1.1", 3), (1, "Ch 2", 10), (1, "Ch 3", 30)]
    chunks = pdf_chunk.plan_chunks(45, toc, 20)
    assert [(c.start, c.end, c.title) for c in chunks] == [
        (1, 9, "Ch 1"),
        (10, 29, "Ch 2"),
        (30, 45, "Ch 3"),
    ]


def test_plan_chunks_resplits_huge_chapter(pdf_chunk):
    toc = [(1, "Ch 1", 1), (1, "Ch 2", 5)]
    chunks = pdf_chunk.plan_chunks(60, toc, 20)  # Ch 2 = 56쪽 > 20*1.5
    assert (chunks[0].start, chunks[0].end) == (1, 4)
    assert [(c.start, c.end) for c in chunks[1:]] == [(5, 24), (25, 44), (45, 60)]


def test_plan_chunks_adds_front_matter_when_toc_starts_late(pdf_chunk):
    # 목차 앞쪽(front matter)도 빠짐없이 청크에 들어간다. 2쪽 + Ch 1 18쪽 = 20쪽이라 한 청크로 병합될 수 있다.
    chunks = pdf_chunk.plan_chunks(20, [(1, "Ch 1", 3)], 20)
    assert chunks[0].start == 1 and chunks[-1].end == 20
    assert all(b.start == a.end + 1 for a, b in zip(chunks, chunks[1:]))


def test_plan_chunks_keeps_front_matter_separate_before_split_chapter(pdf_chunk):
    chunks = pdf_chunk.plan_chunks(40, [(1, "Ch 1", 3)], 20)  # Ch 1 = 38쪽 > 30 → 고정 분할(병합 대상 아님)
    assert [(c.start, c.end, c.title) for c in chunks] == [
        (1, 2, "(front matter)"),
        (3, 22, "Ch 1 (1)"),
        (23, 40, "Ch 1 (2)"),
    ]


def test_plan_chunks_merges_small_consecutive_chapters(pdf_chunk):
    toc = [(1, f"Ch {i + 1}", 2 * i + 1) for i in range(30)]  # 2쪽짜리 챕터 30개
    chunks = pdf_chunk.plan_chunks(60, toc, 20)
    assert [(c.start, c.end, c.title) for c in chunks] == [
        (1, 20, "Ch 1 ~ Ch 10"),
        (21, 40, "Ch 11 ~ Ch 20"),
        (41, 60, "Ch 21 ~ Ch 30"),
    ]


def test_plan_chunks_uses_shallowest_level_with_inner_boundary(pdf_chunk):
    # 레벨 1은 1쪽의 책 제목뿐(구간 안 경계 없음) → 레벨 2 챕터 경계로 자른다
    toc = [(1, "Book Title", 1), (2, "Ch 1", 3), (2, "Ch 2", 20), (2, "Ch 3", 40)]
    chunks = pdf_chunk.plan_chunks(60, toc, 20)
    assert [(c.start, c.end) for c in chunks] == [(1, 19), (20, 39), (40, 60)]  # front matter는 Ch 1과 병합
    assert chunks[0].title.endswith("Ch 1")
    assert [c.title for c in chunks[1:]] == ["Ch 2", "Ch 3"]


def test_plan_chunks_resplits_oversized_part_at_deeper_level(pdf_chunk):
    toc = [
        (1, "Part I", 1),
        (2, "Ch 1", 1),
        (2, "Ch 2", 16),
        (2, "Ch 3", 31),
        (1, "Part II", 46),
    ]
    chunks = pdf_chunk.plan_chunks(60, toc, 20)  # Part I = 45쪽 > 30 → 고정 쪽수 대신 레벨 2 경계로 재분할
    assert [(c.start, c.end, c.title) for c in chunks] == [
        (1, 15, "Ch 1"),
        (16, 30, "Ch 2"),
        (31, 45, "Ch 3"),
        (46, 60, "Part II"),
    ]
    assert not any(c.split for c in chunks)


PLAN_SHAPES = [
    (45, [], 20),
    (1, [], 20),
    (60, [(1, "Ch 1", 1), (1, "Ch 2", 5)], 20),
    (60, [(1, "Book", 1), (2, "Ch 1", 3), (2, "Ch 2", 20), (2, "Ch 3", 40)], 20),
    (60, [(1, f"Ch {i + 1}", 2 * i + 1) for i in range(30)], 20),
    (120, [(1, "Part I", 1), (2, "Ch 1", 2), (3, "Sec 1.1", 10), (2, "Ch 2", 70), (1, "Part II", 100)], 20),
    (50, [(1, "Only", 1)], 20),  # 경계 없음 → 고정 분할
    (50, [(1, "Late", 49)], 20),  # 거대한 front matter
    (30, [(1, "Out", 0), (1, "Out2", 31), (1, "Bad", -1), (1, "Ch", 10)], 7),  # 범위 밖 항목 무시
    (30, [(1, "Out", 0), (1, "Bad", -1)], 7),  # 유효 항목 0개 → 목차 없음 취급
    (40, [(1, "A", 10), (1, "A dup", 10), (3, "Skip", 12), (1, "B", 5)], 3),  # 중복·비정렬·레벨 건너뜀
    (25, [(1, "C", 2), (1, "D", 3)], 1),
]


@pytest.mark.parametrize(("page_count", "toc", "chunk_pages"), PLAN_SHAPES)
def test_plan_chunks_invariants(pdf_chunk, page_count, toc, chunk_pages):
    chunks = pdf_chunk.plan_chunks(page_count, toc, chunk_pages)
    assert chunks[0].start == 1 and chunks[-1].end == page_count  # 1..page_count 정확히 커버
    assert all(b.start == a.end + 1 for a, b in zip(chunks, chunks[1:]))  # 빈틈·겹침 없음
    for c in chunks:
        size = c.end - c.start + 1
        assert size >= 1
        if c.split:
            assert size <= chunk_pages
        else:
            assert size <= chunk_pages * pdf_chunk.RESPLIT_FACTOR


def test_info_mode(pdf_chunk, tmp_path):
    pdf = make_pdf(tmp_path / "a.pdf", pages=5)
    code, out = run(pdf_chunk, [str(pdf), "--info", "--cache-dir", str(tmp_path / "cache")])
    assert code == 0
    assert json.loads(out) == {"pages": 5, "toc": False, "toc_top_entries": 0}
    assert not (tmp_path / "cache").exists()  # --info는 캐시를 만들지 않는다


def test_chunk_creates_cache_and_is_idempotent(pdf_chunk, tmp_path):
    pdf = make_pdf(tmp_path / "b.pdf", pages=45, toc=[[1, "Ch 1", 1], [1, "Ch 2", 10], [1, "Ch 3", 30]])
    cache = tmp_path / "cache"
    code, out = run(pdf_chunk, [str(pdf), "--cache-dir", str(cache), "--chunk-pages", "20"])
    assert code == 0
    manifest = json.loads(out)
    assert manifest["pages"] == 45 and manifest["toc_used"] is True
    assert len(manifest["parts"]) == 3
    part1 = cache / manifest["sha12"] / "part-01.md"
    text = part1.read_text(encoding="utf-8")
    assert "part: 1/3" in text and "pages: 1-9" in text and "[p.1]" in text
    mtime = part1.stat().st_mtime_ns
    code2, out2 = run(pdf_chunk, [str(pdf), "--cache-dir", str(cache), "--chunk-pages", "20"])
    assert code2 == 0 and json.loads(out2)["sha12"] == manifest["sha12"]
    assert part1.stat().st_mtime_ns == mtime  # 캐시 재사용
    code3, _ = run(pdf_chunk, [str(pdf), "--cache-dir", str(cache), "--chunk-pages", "20", "--force"])
    assert code3 == 0
    assert part1.stat().st_mtime_ns != mtime  # --force 재생성


def test_chunk_pages_change_regenerates_cache(pdf_chunk, tmp_path):
    pdf = make_pdf(tmp_path / "d.pdf", pages=45)
    cache = tmp_path / "cache"
    code, out = run(pdf_chunk, [str(pdf), "--cache-dir", str(cache), "--chunk-pages", "20"])
    assert code == 0 and len(json.loads(out)["parts"]) == 3
    code2, out2 = run(pdf_chunk, [str(pdf), "--cache-dir", str(cache), "--chunk-pages", "10"])
    assert code2 == 0
    manifest = json.loads(out2)
    assert manifest["chunk_pages"] == 10
    assert [p["pages"] for p in manifest["parts"]] == ["1-10", "11-20", "21-30", "31-40", "41-45"]
    sha_dir = cache / manifest["sha12"]
    assert sorted(p.name for p in sha_dir.glob("part-*.md")) == [Path(p["file"]).name for p in manifest["parts"]]
    # 5 → 3개로 줄어도 이전 part 파일이 남지 않는다
    code3, out3 = run(pdf_chunk, [str(pdf), "--cache-dir", str(cache), "--chunk-pages", "20"])
    assert code3 == 0
    manifest3 = json.loads(out3)
    assert manifest3["chunk_pages"] == 20 and len(manifest3["parts"]) == 3
    assert sorted(p.name for p in sha_dir.glob("part-*.md")) == ["part-01.md", "part-02.md", "part-03.md"]


@pytest.mark.parametrize("stale", ["no_plan_version", "corrupt"])
def test_stale_manifest_is_regenerated(pdf_chunk, tmp_path, stale):
    pdf = make_pdf(tmp_path / "e.pdf", pages=45)
    cache = tmp_path / "cache"
    code, out = run(pdf_chunk, [str(pdf), "--cache-dir", str(cache)])
    assert code == 0
    manifest = json.loads(out)
    assert manifest["plan_version"] == pdf_chunk.PLAN_VERSION
    manifest_path = cache / manifest["sha12"] / "manifest.json"
    if stale == "no_plan_version":  # 구버전 분할 알고리즘이 만든 캐시
        old = {k: v for k, v in manifest.items() if k != "plan_version"}
        manifest_path.write_text(json.dumps(old), encoding="utf-8")
    else:  # 쓰기 도중 중단된 manifest
        manifest_path.write_text("{", encoding="utf-8")
    part1 = cache / manifest["sha12"] / "part-01.md"
    os.utime(part1, ns=(0, 0))
    code2, out2 = run(pdf_chunk, [str(pdf), "--cache-dir", str(cache)])
    assert code2 == 0
    assert json.loads(out2)["plan_version"] == pdf_chunk.PLAN_VERSION
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["plan_version"] == pdf_chunk.PLAN_VERSION
    assert part1.stat().st_mtime_ns != 0  # 재생성됨


def test_cached_manifest_paths_follow_current_cache_dir(pdf_chunk, tmp_path):
    pdf = make_pdf(tmp_path / "f.pdf", pages=45)
    cache_a = tmp_path / "cache-a"
    code, out = run(pdf_chunk, [str(pdf), "--cache-dir", str(cache_a)])
    assert code == 0
    sha12 = json.loads(out)["sha12"]
    cache_b = tmp_path / "cache-b"
    shutil.copytree(cache_a, cache_b)  # 캐시 디렉토리 이동·경로 표기 변경 흉내
    part1 = cache_b / sha12 / "part-01.md"
    mtime = part1.stat().st_mtime_ns
    code2, out2 = run(pdf_chunk, [str(pdf), "--cache-dir", str(cache_b)])
    assert code2 == 0
    parts = json.loads(out2)["parts"]
    assert [p["file"] for p in parts] == [str(cache_b / sha12 / f"part-{i:02d}.md") for i in (1, 2, 3)]
    assert all(Path(p["file"]).is_file() for p in parts)
    assert part1.stat().st_mtime_ns == mtime  # 재사용(재생성 아님)


@pytest.mark.parametrize(
    "argv",
    [
        ["x.pdf", "--pages", "10"],  # 알 수 없는 플래그
        ["x.pdf", "--chunk-pages", "abc"],  # 타입 오류
        ["x.pdf", "--chunk-pages", "0"],  # 0 이하 → 무한 루프 방지
    ],
)
def test_usage_error_exits_one(pdf_chunk, argv):
    # argparse 기본값(2)은 exit 2(텍스트 추출 불가) 규약과 충돌한다
    with pytest.raises(SystemExit) as exc:
        pdf_chunk.main(argv)
    assert exc.value.code == 1


def test_scanned_pdf_exits_two(pdf_chunk, tmp_path):
    pdf = make_pdf(tmp_path / "c.pdf", pages=3, with_text=False)
    code, _ = run(pdf_chunk, [str(pdf), "--cache-dir", str(tmp_path / "cache")])
    assert code == 2


def test_missing_file_exits_one(pdf_chunk, tmp_path):
    code, _ = run(pdf_chunk, [str(tmp_path / "nope.pdf"), "--cache-dir", str(tmp_path / "cache")])
    assert code == 1
