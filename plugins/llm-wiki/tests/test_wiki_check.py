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


def _append(path: Path, text: str) -> None:
    path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")


def _broken(findings) -> list[str]:
    return [f["message"] for f in findings if f["check"] == "broken-link"]


# --- log.md·reports/**는 과거 기록: 링크 검사·고아 인바운드 계산에서 제외 ---


def _add_lonely_page(wiki: Path) -> None:
    """index에만 등재되고 다른 페이지의 인바운드가 없는 개념 페이지를 추가한다."""
    (wiki / "wiki" / "concepts" / "lonely.md").write_text(
        FM.format(type="concept", title="외톨이", source="raw/sources/2026-07-27-note.md", aliases="") + "본문.\n",
        encoding="utf-8",
    )
    _append(wiki / "wiki" / "index.md", "- [외톨이](concepts/lonely.md)\n")


def test_log_links_do_not_count_as_inbound(wiki_check, wiki):
    _add_lonely_page(wiki)
    _append(wiki / "wiki" / "log.md", "\n## [2026-07-28] ingest | 외톨이\n\n갱신: [외톨이](concepts/lonely.md)\n")
    code, findings = findings_of(wiki_check, wiki)
    assert code == 1
    assert any(f["check"] == "orphan" and "lonely.md" in f["file"] for f in findings)


def test_log_link_to_retired_page_is_not_checked(wiki_check, wiki):
    # retire로 페이지가 사라져도 append-only log의 과거 링크는 고칠 수 없다 — 위키가 clean일 수 있어야 한다
    _append(
        wiki / "wiki" / "log.md",
        "\n## [2026-07-28] retire | 외톨이\n\n삭제: [외톨이](concepts/lonely.md), [[lonely]]\n",
    )
    code, findings = findings_of(wiki_check, wiki)
    assert findings == []
    assert code == 0


def test_lint_report_links_are_not_checked(wiki_check, wiki):
    reports = wiki / "wiki" / "reports"
    (reports / "2026-07-28-lint.md").write_text(
        "# Lint 2026-07-28\n\n- 깨진 링크: [nope](../concepts/nope.md)\n", encoding="utf-8"
    )
    (reports / "2026").mkdir()
    (reports / "2026" / "2026-07-01-lint.md").write_text("- [[ghost-page]]\n", encoding="utf-8")
    code, findings = findings_of(wiki_check, wiki)
    assert findings == []
    assert code == 0


def test_lint_report_links_do_not_count_as_inbound(wiki_check, wiki):
    _add_lonely_page(wiki)
    (wiki / "wiki" / "reports" / "2026-07-28-lint.md").write_text(
        "# Lint\n\n- 고아: [외톨이](../concepts/lonely.md)\n", encoding="utf-8"
    )
    code, findings = findings_of(wiki_check, wiki)
    assert any(f["check"] == "orphan" and "lonely.md" in f["file"] for f in findings)


def test_overview_counts_as_inbound(wiki_check, wiki):
    _add_lonely_page(wiki)
    _append(wiki / "wiki" / "overview.md", "\n- [외톨이](concepts/lonely.md)\n")
    code, findings = findings_of(wiki_check, wiki)
    assert findings == []
    assert code == 0


# --- 옵시디언(wikilink) 모드: 볼트 전체에서 옵시디언 방식으로 위키링크 해석 ---


def make_wikilink_wiki(root: Path) -> Path:
    """link_style: wikilink 위키. 옵시디언이 해석하는 위키링크 형태를 두루 쓰며 clean이어야 한다."""
    make_wiki(root)
    (root / ".llm-wiki" / "config.yaml").write_text(
        "schema_version: 1\nlanguage: ko\nobsidian: true\nlink_style: wikilink\nsearch: none\n",
        encoding="utf-8",
    )
    (root / "raw" / "assets").mkdir()
    (root / "raw" / "assets" / "diagram.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    src = "raw/sources/2026-07-27-note.md"
    w = root / "wiki"
    (w / "entities" / "karpathy.md").write_text(
        FM.format(type="entity", title="Andrej Karpathy", source=src, aliases='"카파시"')
        + "[[llm-wiki-pattern|llm-wiki 패턴]] 제안자. 원본: [[2026-07-27-note]]\n",
        encoding="utf-8",
    )
    (w / "concepts" / "llm-wiki-pattern.md").write_text(
        FM.format(type="concept", title="llm-wiki 패턴", source=src, aliases="")
        + "[[Karpathy]]가 제안. 요약은 [[note-summary.md]].\n\n![[diagram.png]]\n",
        encoding="utf-8",
    )
    (w / "sources" / "note-summary.md").write_text(
        FM.format(type="source", title="노트 요약", source=src, aliases="")
        + "[[entities/karpathy]], [[wiki/concepts/llm-wiki-pattern.md#개요|패턴]], [[#요약]] 참조.\n"
        + "상대 경로: [[../entities/karpathy]] · 블록: [[llm-wiki-pattern#^abc123]] · ![[raw/assets/diagram.png|300]]\n",
        encoding="utf-8",
    )
    (w / "index.md").write_text(
        "# Index\n\n## Entities\n\n- [[entities/karpathy|Karpathy]]\n\n"
        "## Concepts\n\n- [[llm-wiki-pattern]]\n\n## Sources\n\n- [[Note-Summary.md]]\n\n## Synthesis\n\n(없음)\n",
        encoding="utf-8",
    )
    (w / "overview.md").write_text(
        "# Overview\n\n| 페이지 | 설명 |\n|---|---|\n| [[karpathy\\|카파시]] | 인물 |\n", encoding="utf-8"
    )
    return root


@pytest.fixture()
def wl_wiki(tmp_path):
    return make_wikilink_wiki(tmp_path / "wl")


def test_wikilink_wiki_clean(wiki_check, wl_wiki):
    code, findings = findings_of(wiki_check, wl_wiki)
    assert findings == []
    assert code == 0


def test_wikilink_genuinely_broken_still_reported(wiki_check, wl_wiki):
    _append(wl_wiki / "wiki" / "entities" / "karpathy.md", "\n[[nope]] ![[missing.png]]\n")
    code, findings = findings_of(wiki_check, wl_wiki)
    assert code == 1
    assert _broken(findings) == ["깨진 위키링크: [[nope]]", "깨진 위키링크: [[missing.png]]"]


def test_wikilink_into_dot_folder_is_broken(wiki_check, wl_wiki):
    # 옵시디언은 '.'으로 시작하는 폴더(.git·.obsidian·.llm-wiki·raw/.cache …)를 색인하지 않는다
    cache = wl_wiki / "raw" / ".cache" / "abc"
    cache.mkdir(parents=True)
    (cache / "part-01.md").write_text("# part 1\n", encoding="utf-8")
    _append(wl_wiki / "wiki" / "entities" / "karpathy.md", "\n[[part-01]]\n")
    code, findings = findings_of(wiki_check, wl_wiki)
    assert code == 1
    assert _broken(findings) == ["깨진 위키링크: [[part-01]]"]


# --- 오탐·중복 보고 ---


def test_index_broken_wikilink_reported_once(wiki_check, wiki):
    _append(wiki / "wiki" / "index.md", "- [[nope]]\n")
    code, findings = findings_of(wiki_check, wiki)
    assert [f["check"] for f in findings if "nope" in f["message"]] == ["index-ghost"]


def test_inline_code_links_are_ignored(wiki_check, wiki):
    _append(
        wiki / "wiki" / "concepts" / "llm-wiki-pattern.md",
        "\n문법 예: `[예시](example.md)`, ``[b](x`y.md)``, `[[위키링크]]` — 실제 링크 [사라진](../entities/gone.md)\n",
    )
    code, findings = findings_of(wiki_check, wiki)
    assert code == 1
    assert _broken(findings) == ["깨진 마크다운 링크: ../entities/gone.md"]
    assert not any(f["check"] == "link-style" for f in findings)


def test_tilde_and_nested_fences_hide_links(wiki_check, wiki):
    _append(
        wiki / "wiki" / "concepts" / "llm-wiki-pattern.md",
        "\n~~~markdown\n[a](nope-a.md)\n```\n[b](nope-b.md)\n~~~\n\n"  # ~~~ 펜스는 ```로 닫히지 않는다
        "````md\n```\n[c](nope-c.md)\n```\n````\n\n"  # 여는 길이 이상이어야 닫힌다
        "   ```\n[d](nope-d.md)\n   ```\n\n"  # 들여쓴 펜스
        "```\n[g](nope-g.md)\n```python\n[h](nope-h.md)\n```\n\n"  # 정보 문자열이 붙은 줄은 닫는 펜스가 아니다
        "```인라인``` 뒤의 [e](nope-e.md)\n\n"  # 한 줄짜리 ```x```는 펜스가 아니라 인라인 코드
        "[f](nope-f.md)\n",
    )
    code, findings = findings_of(wiki_check, wiki)
    assert _broken(findings) == ["깨진 마크다운 링크: nope-e.md", "깨진 마크다운 링크: nope-f.md"]


def test_uri_scheme_targets_are_external(wiki_check, wiki):
    _append(
        wiki / "wiki" / "concepts" / "llm-wiki-pattern.md",
        "\n[열기](obsidian://open?vault=w) [전화](tel:+82-2-000) [ftp](ftp://example.com/f.md) "
        "[프로토콜 상대](//example.com/a.md) [앵커](#개요) [메일](mailto:a@example.com)\n",
    )
    code, findings = findings_of(wiki_check, wiki)
    assert findings == []
    assert code == 0


# --- 사용법 오류 exit 코드 ---


def test_usage_error_exits_one(wiki_check):
    # argparse 기본값(2)은 플러그인 스크립트의 exit 2(도메인 특수상황) 규약과 충돌한다
    with pytest.raises(SystemExit) as exc:
        wiki_check.main(["--bogus"])
    assert exc.value.code == 1
