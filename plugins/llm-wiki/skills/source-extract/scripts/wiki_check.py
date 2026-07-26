#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml>=6.0"]
# ///
"""위키 결정적 lint — llm-wiki 플러그인. 읽기 전용(어떤 파일도 쓰지 않는다).

usage: uv run wiki_check.py [--format md|json] [--stats]

검사: broken-link / link-style / orphan / index-missing / index-ghost /
frontmatter / source-missing / collision / log-format
--stats: 타입별 페이지 수·소스 수·log 항목 수·마지막 lint 날짜만 출력(검사 생략).

exit: 0 clean / 1 findings 또는 오류
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
import urllib.parse
from pathlib import Path

import yaml

TYPE_DIRS = ("entities", "concepts", "sources", "synthesis")
DIR_TO_TYPE = {"entities": "entity", "concepts": "concept", "sources": "source", "synthesis": "synthesis"}
VALID_TYPES = {"entity", "concept", "source", "synthesis"}
REQUIRED_FIELDS = ("type", "title", "sources", "created", "updated")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n?", re.S)
MD_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
LOG_HEADING_RE = re.compile(r"^## \[\d{4}-\d{2}-\d{2}\] (init|ingest|query|lint|retire) \| .+$")
LOG_ENTRY_RE = re.compile(r"^## \[", re.M)
LINT_REPORT_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-lint\.md$")
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "#")


def find_wiki_root(start: Path) -> Path | None:
    for p in [start, *start.parents]:
        if (p / ".llm-wiki" / "config.yaml").is_file():
            return p
    return None


def load_config(root: Path) -> dict:
    try:
        data = yaml.safe_load((root / ".llm-wiki" / "config.yaml").read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def parse_frontmatter(text: str) -> tuple[dict | None, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, text
    try:
        data = yaml.safe_load(m.group(1))
    except Exception:  # noqa: BLE001
        return None, text[m.end():]
    return (data if isinstance(data, dict) else None), text[m.end():]


def strip_code_fences(text: str) -> str:
    out: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    return "\n".join(out)


def extract_links(body: str) -> tuple[list[str], list[str]]:
    """본문에서 (마크다운 링크 타깃, 위키링크 stem) 목록을 뽑는다."""
    text = strip_code_fences(body)
    md_targets = [
        t for _, t in MD_LINK_RE.findall(text) if not t.startswith(EXTERNAL_PREFIXES)
    ]
    wiki_stems = [s.strip() for s in WIKILINK_RE.findall(text) if s.strip()]
    return md_targets, wiki_stems


def resolve_md_target(page: Path, target: str, root: Path) -> Path:
    target = urllib.parse.unquote(target.split("#", 1)[0])
    if target.startswith("/"):
        return (root / target.lstrip("/")).resolve()
    return (page.parent / target).resolve()


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


class Checker:
    def __init__(self, root: Path):
        self.root = root
        self.wiki_dir = root / "wiki"
        self.config = load_config(root)
        self.link_style = str(self.config.get("link_style") or "markdown")
        self.findings: list[dict] = []
        # 타입 디렉토리의 페이지들
        self.pages: list[Path] = []
        for d in TYPE_DIRS:
            dir_path = self.wiki_dir / d
            if dir_path.is_dir():
                self.pages.extend(sorted(dir_path.glob("*.md")))
        # wiki/ 전체 md (인바운드·stem 계산용)
        self.all_wiki_md: list[Path] = sorted(self.wiki_dir.rglob("*.md")) if self.wiki_dir.is_dir() else []
        self.stems: dict[str, list[Path]] = {}
        for p in self.all_wiki_md:
            self.stems.setdefault(p.stem, []).append(p)
        # 페이지별 frontmatter·본문 캐시
        self.parsed: dict[Path, tuple[dict | None, str]] = {}
        for p in self.all_wiki_md:
            self.parsed[p] = parse_frontmatter(p.read_text(encoding="utf-8"))

    def add(self, check: str, severity: str, file: Path, message: str) -> None:
        self.findings.append(
            {"check": check, "severity": severity, "file": _rel(file, self.root), "message": message}
        )

    def run(self) -> list[dict]:
        self.check_links_and_style()
        self.check_orphans()
        self.check_index()
        self.check_frontmatter()
        self.check_sources_exist()
        self.check_collisions()
        self.check_log()
        return self.findings

    # ① 깨진 링크 + config.link_style 불일치
    def check_links_and_style(self) -> None:
        index_path = self.wiki_dir / "index.md"
        for p in self.all_wiki_md:
            _, body = self.parsed[p]
            md_targets, wiki_stems = extract_links(body)
            if p != index_path:  # index의 md 링크는 index-ghost가 담당
                for t in md_targets:
                    resolved = resolve_md_target(p, t, self.root)
                    if not resolved.exists():
                        self.add("broken-link", "error", p, f"깨진 마크다운 링크: {t}")
            for s in wiki_stems:
                if s not in self.stems:
                    self.add("broken-link", "error", p, f"깨진 위키링크: [[{s}]]")
            if self.link_style == "markdown" and wiki_stems:
                self.add("link-style", "warning", p, "config.link_style=markdown인데 위키링크 사용")
            elif self.link_style == "wikilink" and md_targets:
                internal = [t for t in md_targets if t.endswith(".md")]
                if internal:
                    self.add("link-style", "warning", p, "config.link_style=wikilink인데 마크다운 내부 링크 사용")

    # ② 고아 페이지 (index 제외 인바운드 0)
    def check_orphans(self) -> None:
        index_path = self.wiki_dir / "index.md"
        inbound: set[Path] = set()
        for p in self.all_wiki_md:
            if p == index_path:
                continue
            _, body = self.parsed[p]
            md_targets, wiki_stems = extract_links(body)
            for t in md_targets:
                inbound.add(resolve_md_target(p, t, self.root))
            for s in wiki_stems:
                for target in self.stems.get(s, []):
                    if target != p:
                        inbound.add(target.resolve())
        for page in self.pages:
            if page.resolve() not in inbound:
                self.add("orphan", "warning", page, "다른 페이지로부터의 인바운드 링크 없음(index 제외 기준)")

    # ③ index ↔ 실제 파일 정합
    def check_index(self) -> None:
        index_path = self.wiki_dir / "index.md"
        if not index_path.is_file():
            self.add("index-missing", "error", index_path, "wiki/index.md가 없음")
            return
        _, body = self.parsed[index_path]
        md_targets, wiki_stems = extract_links(body)
        listed: set[Path] = set()
        for t in md_targets:
            resolved = resolve_md_target(index_path, t, self.root)
            listed.add(resolved)
            if not resolved.exists():
                self.add("index-ghost", "error", index_path, f"index가 없는 파일을 가리킴: {t}")
        for s in wiki_stems:
            targets = self.stems.get(s, [])
            if targets:
                listed.update(t.resolve() for t in targets)
            else:
                self.add("index-ghost", "error", index_path, f"index가 없는 파일을 가리킴: [[{s}]]")
        for page in self.pages:
            if page.resolve() not in listed:
                self.add("index-missing", "warning", index_path, f"index에 누락된 페이지: {_rel(page, self.root)}")

    # ④ frontmatter 필수 필드·type enum·날짜 형식
    def check_frontmatter(self) -> None:
        for page in self.pages:
            fm, _ = self.parsed[page]
            if fm is None:
                self.add("frontmatter", "error", page, f"frontmatter 없음 — 필수: {', '.join(REQUIRED_FIELDS)}")
                continue
            for field in REQUIRED_FIELDS:
                if field not in fm or fm[field] is None:
                    self.add("frontmatter", "error", page, f"필수 필드 누락: {field}")
            t = fm.get("type")
            if t is not None and t not in VALID_TYPES:
                self.add("frontmatter", "error", page, f"type 값이 유효하지 않음: {t} (entity|concept|source|synthesis)")
            expected = DIR_TO_TYPE.get(page.parent.name)
            if t in VALID_TYPES and expected and t != expected:
                self.add("frontmatter", "warning", page, f"type={t}인데 {page.parent.name}/ 디렉토리에 위치")
            for field in ("created", "updated"):
                v = fm.get(field)
                if v is None:
                    continue
                if isinstance(v, _dt.date):
                    continue
                if not (isinstance(v, str) and DATE_RE.match(v)):
                    self.add("frontmatter", "error", page, f"{field} 날짜 형식 오류: {v} (YYYY-MM-DD)")
            srcs = fm.get("sources")
            if srcs is not None and (not isinstance(srcs, list) or not srcs):
                self.add("frontmatter", "error", page, "sources는 비어 있지 않은 배열이어야 함")

    # ⑤ sources[] 경로 실존
    def check_sources_exist(self) -> None:
        for page in self.pages:
            fm, _ = self.parsed[page]
            if not fm or not isinstance(fm.get("sources"), list):
                continue
            for src in fm["sources"]:
                if not isinstance(src, str):
                    continue
                if not (self.root / src).exists():
                    self.add("source-missing", "error", page, f"sources 경로가 존재하지 않음: {src}")

    # ⑥ 제목·별칭·파일명 stem 충돌
    def check_collisions(self) -> None:
        names: dict[str, set[Path]] = {}

        def record(name: object, page: Path) -> None:
            key = str(name).strip().lower()
            if key:
                names.setdefault(key, set()).add(page)

        for page in self.pages:
            fm, _ = self.parsed[page]
            record(page.stem, page)
            if fm:
                if fm.get("title") is not None:
                    record(fm["title"], page)
                aliases = fm.get("aliases")
                if isinstance(aliases, list):
                    for a in aliases:
                        record(a, page)
        for key, pages in sorted(names.items()):
            if len(pages) > 1:
                files = ", ".join(sorted(_rel(p, self.root) for p in pages))
                self.add("collision", "error", sorted(pages)[0], f"제목/별칭/파일명 충돌: '{key}' — {files}")

    # ⑦ log 규약
    def check_log(self) -> None:
        log_path = self.wiki_dir / "log.md"
        if not log_path.is_file():
            self.add("log-format", "error", log_path, "wiki/log.md가 없음")
            return
        for lineno, line in enumerate(log_path.read_text(encoding="utf-8").splitlines(), start=1):
            if line.startswith("## ") and not LOG_HEADING_RE.match(line):
                self.add(
                    "log-format", "error", log_path,
                    f"{lineno}행이 log 규약 위반: {line!r} — '## [YYYY-MM-DD] <op> | <제목>' (op ∈ init·ingest·query·lint·retire)",
                )


def run_checks(root: Path) -> list[dict]:
    return Checker(root).run()


def collect_stats(root: Path) -> dict:
    wiki_dir = root / "wiki"
    pages: dict[str, int] = {}
    for d in TYPE_DIRS:
        dir_path = wiki_dir / d
        pages[DIR_TO_TYPE[d]] = len(list(dir_path.glob("*.md"))) if dir_path.is_dir() else 0

    def count_files(p: Path) -> int:
        if not p.is_dir():
            return 0
        return len([f for f in p.iterdir() if f.is_file() and f.name != ".gitkeep" and not f.name.startswith(".")])

    log_path = wiki_dir / "log.md"
    log_entries = (
        len(LOG_ENTRY_RE.findall(log_path.read_text(encoding="utf-8"))) if log_path.is_file() else 0
    )
    last_lint: str | None = None
    reports_dir = wiki_dir / "reports"
    if reports_dir.is_dir():
        dates = [m.group(1) for f in reports_dir.iterdir() if (m := LINT_REPORT_RE.match(f.name))]
        last_lint = max(dates) if dates else None
    return {
        "pages": pages,
        "total_pages": sum(pages.values()),
        "raw_sources": count_files(root / "raw" / "sources"),
        "raw_archive": count_files(root / "raw" / "archive"),
        "log_entries": log_entries,
        "last_lint": last_lint,
    }


def format_findings_md(findings: list[dict]) -> str:
    if not findings:
        return "✅ clean — 발견된 문제 없음\n"
    lines = [f"발견 {len(findings)}건\n"]
    by_check: dict[str, list[dict]] = {}
    for f in findings:
        by_check.setdefault(f["check"], []).append(f)
    for check, items in sorted(by_check.items()):
        lines.append(f"## {check} ({len(items)}건)")
        for f in items:
            lines.append(f"- [{f['severity']}] {f['file']} — {f['message']}")
        lines.append("")
    return "\n".join(lines)


def format_stats_md(stats: dict) -> str:
    p = stats["pages"]
    return (
        f"페이지: entity {p['entity']} / concept {p['concept']} / source {p['source']} / synthesis {p['synthesis']}"
        f" (총 {stats['total_pages']})\n"
        f"원본: raw/sources {stats['raw_sources']} / raw/archive {stats['raw_archive']}\n"
        f"log 항목: {stats['log_entries']}\n"
        f"마지막 lint: {stats['last_lint'] or '없음'}\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="llm-wiki 결정적 lint (읽기 전용)")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    parser.add_argument("--stats", action="store_true", help="검사 없이 통계만 출력")
    args = parser.parse_args(argv)

    root = find_wiki_root(Path.cwd())
    if root is None:
        print(
            "llm-wiki 위키가 아닙니다(.llm-wiki/config.yaml을 찾지 못함). /llm-wiki:wiki-init 으로 생성하세요.",
            file=sys.stderr,
        )
        return 1

    if args.stats:
        stats = collect_stats(root)
        if args.format == "json":
            print(json.dumps(stats, ensure_ascii=False, indent=2))
        else:
            print(format_stats_md(stats), end="")
        return 0

    findings = run_checks(root)
    if args.format == "json":
        summary: dict[str, int] = {}
        for f in findings:
            summary[f["check"]] = summary.get(f["check"], 0) + 1
        print(json.dumps({"clean": not findings, "summary": summary, "findings": findings}, ensure_ascii=False, indent=2))
    else:
        print(format_findings_md(findings), end="")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
