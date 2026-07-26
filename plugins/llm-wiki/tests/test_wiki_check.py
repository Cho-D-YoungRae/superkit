from pathlib import Path

import pytest

FM = """---
type: {type}
title: {title}
sources:
  - {source}
created: 2026-07-27
updated: 2026-07-27
aliases: [{aliases}]
---

"""


def make_wiki(root: Path) -> Path:
    (root / ".llm-wiki").mkdir(parents=True)
    (root / ".llm-wiki" / "config.yaml").write_text(
        "schema_version: 1\nlanguage: ko\nobsidian: false\nlink_style: markdown\nsearch: none\n",
        encoding="utf-8",
    )
    (root / "raw" / "sources").mkdir(parents=True)
    (root / "raw" / "archive").mkdir(parents=True)
    src = root / "raw" / "sources" / "2026-07-27-note.md"
    src.write_text("# note\n", encoding="utf-8")
    for d in ("entities", "concepts", "sources", "synthesis", "reports"):
        (root / "wiki" / d).mkdir(parents=True)
    w = root / "wiki"
    (w / "entities" / "karpathy.md").write_text(
        FM.format(type="entity", title="Andrej Karpathy", source="raw/sources/2026-07-27-note.md", aliases='"카파시"')
        + "[llm-wiki 패턴](../concepts/llm-wiki-pattern.md) 제안자.\n",
        encoding="utf-8",
    )
    (w / "concepts" / "llm-wiki-pattern.md").write_text(
        FM.format(type="concept", title="llm-wiki 패턴", source="raw/sources/2026-07-27-note.md", aliases="")
        + "[Karpathy](../entities/karpathy.md)가 제안. 요약은 [노트](../sources/note-summary.md).\n",
        encoding="utf-8",
    )
    (w / "sources" / "note-summary.md").write_text(
        FM.format(type="source", title="노트 요약", source="raw/sources/2026-07-27-note.md", aliases="")
        + "[Karpathy](../entities/karpathy.md), [패턴](../concepts/llm-wiki-pattern.md) 참조.\n",
        encoding="utf-8",
    )
    (w / "index.md").write_text(
        "# Index\n\n## Entities\n\n- [Karpathy](entities/karpathy.md)\n\n"
        "## Concepts\n\n- [llm-wiki 패턴](concepts/llm-wiki-pattern.md)\n\n"
        "## Sources\n\n- [노트 요약](sources/note-summary.md)\n\n## Synthesis\n\n(없음)\n",
        encoding="utf-8",
    )
    (w / "log.md").write_text(
        "# Log\n\n## [2026-07-27] init | 위키 생성\n\n설정: markdown\n\n"
        "## [2026-07-27] ingest | 노트\n\nsha: abc123def456\n",
        encoding="utf-8",
    )
    (w / "overview.md").write_text("# Overview\n", encoding="utf-8")
    return root


@pytest.fixture()
def wiki(tmp_path):
    return make_wiki(tmp_path / "w")


def run(wiki_check, root, argv):
    import contextlib
    import io
    import os

    cwd = os.getcwd()
    os.chdir(root)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            code = wiki_check.main(argv)
    finally:
        os.chdir(cwd)
    return code, buf.getvalue()


def findings_of(wiki_check, root):
    import json

    code, out = run(wiki_check, root, ["--format", "json"])
    return code, json.loads(out)["findings"]


def test_clean_wiki_exits_zero(wiki_check, wiki):
    code, findings = findings_of(wiki_check, wiki)
    assert findings == []
    assert code == 0


def test_not_a_wiki_exits_one(wiki_check, tmp_path):
    code, _out = run(wiki_check, tmp_path, ["--format", "json"])
    assert code == 1


def test_broken_markdown_link(wiki_check, wiki):
    p = wiki / "wiki" / "concepts" / "llm-wiki-pattern.md"
    p.write_text(p.read_text(encoding="utf-8") + "\n[없음](../entities/nope.md)\n", encoding="utf-8")
    code, findings = findings_of(wiki_check, wiki)
    assert code == 1
    assert any(f["check"] == "broken-link" and "nope.md" in f["message"] for f in findings)


def test_broken_wikilink_and_style_mismatch(wiki_check, wiki):
    p = wiki / "wiki" / "entities" / "karpathy.md"
    p.write_text(p.read_text(encoding="utf-8") + "\n[[nonexistent-page]]\n", encoding="utf-8")
    code, findings = findings_of(wiki_check, wiki)
    assert any(f["check"] == "broken-link" and "nonexistent-page" in f["message"] for f in findings)
    assert any(f["check"] == "link-style" for f in findings)  # markdown 설정인데 wikilink 사용


def test_orphan_page(wiki_check, wiki):
    (wiki / "wiki" / "concepts" / "lonely.md").write_text(
        FM.format(type="concept", title="외톨이", source="raw/sources/2026-07-27-note.md", aliases="") + "본문.\n",
        encoding="utf-8",
    )
    idx = wiki / "wiki" / "index.md"
    idx.write_text(idx.read_text(encoding="utf-8") + "- [외톨이](concepts/lonely.md)\n", encoding="utf-8")
    code, findings = findings_of(wiki_check, wiki)
    assert any(f["check"] == "orphan" and "lonely.md" in f["file"] for f in findings)


def test_index_missing_and_ghost(wiki_check, wiki):
    (wiki / "wiki" / "synthesis" / "unlisted.md").write_text(
        FM.format(type="synthesis", title="미등록", source="raw/sources/2026-07-27-note.md", aliases="")
        + "[패턴](../concepts/llm-wiki-pattern.md)\n",
        encoding="utf-8",
    )
    idx = wiki / "wiki" / "index.md"
    idx.write_text(idx.read_text(encoding="utf-8") + "- [유령](concepts/ghost.md)\n", encoding="utf-8")
    code, findings = findings_of(wiki_check, wiki)
    assert any(f["check"] == "index-missing" and "unlisted.md" in f["message"] for f in findings)
    assert any(f["check"] == "index-ghost" and "ghost.md" in f["message"] for f in findings)


def test_frontmatter_violations(wiki_check, wiki):
    (wiki / "wiki" / "concepts" / "bad.md").write_text(
        "---\ntype: banana\ntitle: 나쁜 페이지\ncreated: 2026/07/27\nupdated: 2026-07-27\n---\n\n본문\n",
        encoding="utf-8",
    )
    code, findings = findings_of(wiki_check, wiki)
    msgs = [f for f in findings if f["check"] == "frontmatter" and "bad.md" in f["file"]]
    assert any("type" in f["message"] for f in msgs)      # enum 위반
    assert any("sources" in f["message"] for f in msgs)   # 필수 필드 누락
    assert any("created" in f["message"] for f in msgs)   # 날짜 형식


def test_source_path_not_exists(wiki_check, wiki):
    p = wiki / "wiki" / "entities" / "karpathy.md"
    p.write_text(
        p.read_text(encoding="utf-8").replace("2026-07-27-note.md", "2026-01-01-ghost.md"),
        encoding="utf-8",
    )
    code, findings = findings_of(wiki_check, wiki)
    assert any(f["check"] == "source-missing" for f in findings)


def test_title_alias_collision(wiki_check, wiki):
    (wiki / "wiki" / "synthesis" / "dup.md").write_text(
        FM.format(type="synthesis", title="Andrej Karpathy", source="raw/sources/2026-07-27-note.md", aliases="")
        + "[패턴](../concepts/llm-wiki-pattern.md)\n",
        encoding="utf-8",
    )
    idx = wiki / "wiki" / "index.md"
    idx.write_text(idx.read_text(encoding="utf-8") + "- [dup](synthesis/dup.md)\n", encoding="utf-8")
    code, findings = findings_of(wiki_check, wiki)
    assert any(f["check"] == "collision" for f in findings)


def test_log_violation(wiki_check, wiki):
    log = wiki / "wiki" / "log.md"
    log.write_text(log.read_text(encoding="utf-8") + "\n## [2026-7-1] deploy | 이상한 항목\n", encoding="utf-8")
    code, findings = findings_of(wiki_check, wiki)
    assert any(f["check"] == "log-format" for f in findings)


def test_stats(wiki_check, wiki):
    import json

    code, out = run(wiki_check, wiki, ["--stats", "--format", "json"])
    stats = json.loads(out)
    assert code == 0
    assert stats["pages"] == {"entity": 1, "concept": 1, "source": 1, "synthesis": 0}
    assert stats["raw_sources"] == 1
    assert stats["log_entries"] == 2
    assert stats["last_lint"] is None
