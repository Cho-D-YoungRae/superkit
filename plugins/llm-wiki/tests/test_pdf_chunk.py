import json


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
    chunks = pdf_chunk.plan_chunks(20, [(1, "Ch 1", 3)], 20)
    assert (chunks[0].start, chunks[0].end) == (1, 2)


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


def test_scanned_pdf_exits_two(pdf_chunk, tmp_path):
    pdf = make_pdf(tmp_path / "c.pdf", pages=3, with_text=False)
    code, _ = run(pdf_chunk, [str(pdf), "--cache-dir", str(tmp_path / "cache")])
    assert code == 2


def test_missing_file_exits_one(pdf_chunk, tmp_path):
    code, _ = run(pdf_chunk, [str(tmp_path / "nope.pdf"), "--cache-dir", str(tmp_path / "cache")])
    assert code == 1
