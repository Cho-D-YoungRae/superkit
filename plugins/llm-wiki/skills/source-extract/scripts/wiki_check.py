#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml>=6.0"]
# ///
"""위키 결정적 lint — llm-wiki 플러그인. 읽기 전용(어떤 파일도 쓰지 않는다).

usage: uv run wiki_check.py [--root PATH] [--format md|json] [--stats | --pending]

--root: 위키 루트(또는 그 안의 경로). 생략하면 현재 디렉토리에서 위로 찾는다. 스킬은 이 옵션에 절대 경로를
  넘긴다 — `cd <위키> && …` 복합 명령은 사용자 권한 확인을 부르기 쉽다.

검사: broken-link / link-style / orphan / index-missing / index-ghost /
frontmatter / source-missing / collision / log-format / log-sha / raw-unreferenced
--stats: 타입별 페이지 수·소스 수·log 항목 수·마지막 lint 날짜만 출력(검사 생략).
--pending: raw/sources/ 바로 아래 원본 중 sha12(sha256 앞 12자리)가 wiki/log.md 어디에도 없는 것 —
  인제스트 대기 목록만 출력(검사 생략, 항상 exit 0). --stats와 함께 쓸 수 없다.

원본 드리프트:
- log-sha: ingest 항목 본문(다음 '## ' 헤딩 전까지)에 `sha: <12자리 이상 hex>` 줄이 없음. 재인제스트 중복
  확인이 `grep <sha12> wiki/log.md`이므로 기록이 빠지면 같은 원본이 다시 인제스트된다.
- raw-unreferenced: raw/sources/ 바로 아래 원본(점 파일 제외)이 어느 페이지 frontmatter sources[]에도 없음.
  log에 sha12가 없으면 미인제스트, 있으면 인제스트 후 페이지 참조가 끊긴 드리프트다.

링크 판정:
- 코드(``` · ~~~ 펜스 블록, 인라인 코드) 안의 링크와 외부 타깃(URI 스킴 https:·obsidian: 등, //, #앵커)은
  검사하지 않는다.
- 위키링크는 옵시디언처럼 볼트(위키 루트) 전체 파일에서 대소문자 무시로 찾는다 — [[name]]·[[name.md]]·
  [[folder/name]](경로 접미사)·![[file.png]]·./·../ 상대 경로, #헤딩·#^블록·|별칭 허용.
  '.'으로 시작하는 경로(.git·.obsidian·.llm-wiki·raw/.cache 등)는 옵시디언처럼 색인하지 않는다.
- wiki/log.md(append-only)와 wiki/reports/**(lint 리포트)는 과거 시점의 기록이다. 이후 retire 등으로 링크가
  깨져도 고칠 수 없으므로 broken-link·link-style 검사에서 빼고, 고아 판정의 인바운드로도 치지 않는다
  (기록에 언급됐다고 페이지가 탐색 가능해지지는 않는다). index.md도 인바운드에서 빼고, overview.md는 센다.

exit: 0 clean / 1 findings 또는 오류(사용법 오류 포함)
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import posixpath
import re
import sys
import unicodedata
import urllib.parse
from pathlib import Path
from typing import NoReturn

import yaml

TYPE_DIRS = ("entities", "concepts", "sources", "synthesis")
DIR_TO_TYPE = {"entities": "entity", "concepts": "concept", "sources": "source", "synthesis": "synthesis"}
VALID_TYPES = {"entity", "concept", "source", "synthesis"}
REQUIRED_FIELDS = ("type", "title", "sources", "created", "updated")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n?", re.S)
MD_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
# [[...]] 안쪽 전체(![[임베드]] 포함) — 경로만 남기는 건 wikilink_target
WIKILINK_RE = re.compile(r"\[\[([^\[\]\n]+)\]\]")
LOG_HEADING_RE = re.compile(r"^## \[\d{4}-\d{2}-\d{2}\] (init|ingest|query|lint|retire) \| .+$")
LOG_ENTRY_RE = re.compile(r"^## \[", re.M)
# ingest 항목의 sha 기록: `sha: <hex 12+>`(백틱 감싸기 허용). hex는 소문자만 — shasum 출력과 grep이 맞아야 한다
SHA_LINE_RE = re.compile(r"\b(?i:sha):\s*`?[0-9a-f]{12,}")
LINT_REPORT_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-lint\.md$")
# 외부 타깃: URI 스킴(https:·mailto:·obsidian: …)·프로토콜 상대(//host)·같은 페이지 앵커(#…)
EXTERNAL_RE = re.compile(r"^(?:[A-Za-z][A-Za-z0-9+.-]*:|//|#)")
# 펜스 줄: 백틱 또는 물결 3개 이상 + 정보 문자열
FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})(.*)$")
# 인라인 코드 스팬: 여는 백틱 열과 길이가 같은 백틱 열이 닫는다(한 줄 안). \`는 이스케이프라 열지 않는다
INLINE_CODE_RE = re.compile(r"(?<![`\\])(`+)(?!`).*?(?<!`)\1(?!`)")


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
    """펜스 코드 블록(``` · ~~~)을 지운다. 닫는 펜스는 여는 펜스와 같은 문자·같거나 긴 길이이고 뒤에 공백만
    올 수 있다(CommonMark). 닫히지 않은 펜스는 문서 끝까지 코드다. 들여쓰기 칸 수는 제한하지 않는다 —
    리스트 안의 펜스는 문서 기준 4칸 이상 들여써지는데, 리스트 컨테이너를 파싱하지 않기 때문이다."""
    out: list[str] = []
    fence = ""  # 열린 펜스 문자열(예: "````") — 빈 문자열이면 펜스 밖
    for line in text.splitlines():
        m = FENCE_RE.match(line)
        if not fence:
            # 백틱 펜스의 정보 문자열엔 백틱이 올 수 없다 — 한 줄짜리 ```x```는 인라인 코드
            if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
                fence = m.group(1)
            else:
                out.append(line)
        elif m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not m.group(2).strip():
            fence = ""
    return "\n".join(out)


def strip_inline_code(text: str) -> str:
    """인라인 코드 스팬(`x`, ``x`y``)을 지운다 — 코드 안의 링크 예시는 링크가 아니다."""
    return INLINE_CODE_RE.sub(" ", text)


def wikilink_target(inner: str) -> str:
    """[[...]] 안쪽에서 링크 경로만 남긴다 — |별칭·#헤딩·#^블록을 떼고, 표 안의 \\| 이스케이프도 처리한다.
    빈 문자열이면 같은 페이지 링크([[#헤딩]])다."""
    return inner.split("|", 1)[0].split("#", 1)[0].strip().rstrip("\\").strip()


def extract_links(body: str) -> tuple[list[str], list[str]]:
    """본문에서 (내부 마크다운 링크 타깃, 위키링크 경로) 목록을 뽑는다. 코드 안의 링크·외부 타깃은 뺀다."""
    text = strip_inline_code(strip_code_fences(body))
    md_targets = [t for _, t in MD_LINK_RE.findall(text) if not EXTERNAL_RE.match(t)]
    wiki_targets = [t for inner in WIKILINK_RE.findall(text) if (t := wikilink_target(inner))]
    return md_targets, wiki_targets


def resolve_md_target(page: Path, target: str, root: Path) -> Path:
    target = urllib.parse.unquote(target.split("#", 1)[0])
    if target.startswith("/"):
        return (root / target.lstrip("/")).resolve()
    return (page.parent / target).resolve()


def build_vault_index(root: Path) -> dict[str, list[tuple[str, Path]]]:
    """볼트(위키 루트) 파일을 소문자 파일명 → [(소문자 상대 경로, 경로)]로 색인한다.
    옵시디언처럼 '.'으로 시작하는 경로 구성요소(.git·.obsidian·.llm-wiki·raw/.cache 등)는 건너뛴다."""
    vault: dict[str, list[tuple[str, Path]]] = {}
    for dirpath, dirnames, filenames in root.walk():
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in sorted(filenames):
            if not name.startswith("."):
                path = dirpath / name
                vault.setdefault(name.lower(), []).append((path.relative_to(root).as_posix().lower(), path))
    return vault


def resolve_wikilink(page: Path, target: str, root: Path, vault: dict[str, list[tuple[str, Path]]]) -> list[Path]:
    """위키링크 경로(wikilink_target 결과)를 옵시디언처럼 볼트 파일로 해석한다. 대소문자 무시, 못 찾으면 [].
    - [[name]]·[[name.md]]는 파일명, [[folder/name]]·[[wiki/entities/name]]은 '/' 경계의 경로 접미사로 찾는다.
    - 확장자 없이 쓰면 .md 노트도 찾는다. 비-md 파일(![[diagram.png]])은 확장자까지 써야 한다.
    - ./ · ../로 시작하면 링크한 페이지 기준 상대 경로다(옵시디언 '상대 경로' 링크 형식)."""
    t = target.lower()
    relative = t.startswith(("./", "../"))
    if relative:
        t = posixpath.normpath(posixpath.join(page.parent.relative_to(root).as_posix().lower(), t))
    found: list[Path] = []
    for cand in (t, f"{t}.md"):
        for rel, path in vault.get(cand.rsplit("/", 1)[-1], []):
            if rel == cand or (not relative and rel.endswith(f"/{cand}")):
                found.append(path)
    return found


def raw_files(d: Path) -> list[Path]:
    """디렉토리 바로 아래 일반 파일(점 파일·.gitkeep 제외), 이름순."""
    if not d.is_dir():
        return []
    return sorted(f for f in d.iterdir() if f.is_file() and not f.name.startswith("."))


def sha12(path: Path) -> str:
    """sha256 앞 12자리 — `shasum -a 256`·`sha256sum`과 같은 값. 인제스트가 log에 `sha: `로 남기는 키."""
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()[:12]


def norm_source(path: str) -> str:
    """sources[] 경로 비교용 정규화 — ./·중복 /·.. 정리, 유니코드 NFC(macOS의 NFD 파일명 대비)."""
    return unicodedata.normalize("NFC", posixpath.normpath(path.strip()))


def parse_log_entries(text: str) -> list[tuple[int, str, list[str]]]:
    """log.md를 (헤딩 행 번호, op, 본문 줄들) 항목으로 나눈다. 본문 = 다음 '## ' 헤딩 전까지.
    규약 위반 헤딩도 경계로는 쓰되 항목에서는 뺀다(형식 위반은 log-format이 보고)."""
    entries: list[tuple[int, str, list[str]]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if line.startswith("## "):
            m = LOG_HEADING_RE.match(line)
            entries.append((lineno, m.group(1) if m else "", []))
        elif entries:
            entries[-1][2].append(line)
    return [e for e in entries if e[1]]


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
        # wiki/ 전체 md (링크 검사·인바운드 계산용)
        self.all_wiki_md: list[Path] = sorted(self.wiki_dir.rglob("*.md")) if self.wiki_dir.is_dir() else []
        # 볼트 전체 파일 색인 (위키링크 해석용)
        self.vault = build_vault_index(root)
        # 페이지별 frontmatter·본문 캐시
        self.parsed: dict[Path, tuple[dict | None, str]] = {}
        for p in self.all_wiki_md:
            self.parsed[p] = parse_frontmatter(p.read_text(encoding="utf-8"))
        # log.md 원문 (없으면 None — log-format이 보고)
        log_path = self.wiki_dir / "log.md"
        self.log_text: str | None = log_path.read_text(encoding="utf-8") if log_path.is_file() else None

    def add(self, check: str, severity: str, file: Path, message: str) -> None:
        self.findings.append(
            {"check": check, "severity": severity, "file": _rel(file, self.root), "message": message}
        )

    def is_record(self, p: Path) -> bool:
        """log.md·reports/**는 과거 시점의 기록 — 링크 검사와 고아 인바운드 계산에서 뺀다."""
        return p == self.wiki_dir / "log.md" or p.is_relative_to(self.wiki_dir / "reports")

    def run(self) -> list[dict]:
        self.check_links_and_style()
        self.check_orphans()
        self.check_index()
        self.check_frontmatter()
        self.check_sources_exist()
        self.check_collisions()
        self.check_log()
        self.check_log_sha()
        self.check_raw_sources()
        return self.findings

    # ① 깨진 링크 + config.link_style 불일치 (log·reports 기록은 당시 상태 그대로 두므로 제외)
    def check_links_and_style(self) -> None:
        index_path = self.wiki_dir / "index.md"
        for p in self.all_wiki_md:
            if self.is_record(p):
                continue
            _, body = self.parsed[p]
            md_targets, wiki_targets = extract_links(body)
            if p != index_path:  # index의 링크는 index-ghost가 담당(중복 보고 방지)
                for t in md_targets:
                    resolved = resolve_md_target(p, t, self.root)
                    if not resolved.exists():
                        self.add("broken-link", "error", p, f"깨진 마크다운 링크: {t}")
                for t in wiki_targets:
                    if not resolve_wikilink(p, t, self.root, self.vault):
                        self.add("broken-link", "error", p, f"깨진 위키링크: [[{t}]]")
            if self.link_style == "markdown" and wiki_targets:
                self.add("link-style", "warning", p, "config.link_style=markdown인데 위키링크 사용")
            elif self.link_style == "wikilink" and md_targets:
                internal = [t for t in md_targets if t.endswith(".md")]
                if internal:
                    self.add("link-style", "warning", p, "config.link_style=wikilink인데 마크다운 내부 링크 사용")

    # ② 고아 페이지 (index·log·reports 제외 인바운드 0)
    def check_orphans(self) -> None:
        index_path = self.wiki_dir / "index.md"
        inbound: set[Path] = set()
        for p in self.all_wiki_md:
            if p == index_path or self.is_record(p):
                continue
            _, body = self.parsed[p]
            md_targets, wiki_targets = extract_links(body)
            targets = {resolve_md_target(p, t, self.root) for t in md_targets}
            for t in wiki_targets:
                targets.update(x.resolve() for x in resolve_wikilink(p, t, self.root, self.vault))
            targets.discard(p.resolve())  # 자기 링크는 인바운드가 아니다
            inbound |= targets
        for page in self.pages:
            if page.resolve() not in inbound:
                self.add("orphan", "warning", page, "다른 페이지로부터의 인바운드 링크 없음(index·log·reports 제외 기준)")

    # ③ index ↔ 실제 파일 정합
    def check_index(self) -> None:
        index_path = self.wiki_dir / "index.md"
        if not index_path.is_file():
            self.add("index-missing", "error", index_path, "wiki/index.md가 없음")
            return
        _, body = self.parsed[index_path]
        md_targets, wiki_targets = extract_links(body)
        listed: set[Path] = set()
        for t in md_targets:
            resolved = resolve_md_target(index_path, t, self.root)
            listed.add(resolved)
            if not resolved.exists():
                self.add("index-ghost", "error", index_path, f"index가 없는 파일을 가리킴: {t}")
        for t in wiki_targets:
            targets = resolve_wikilink(index_path, t, self.root, self.vault)
            if targets:
                listed.update(x.resolve() for x in targets)
            else:
                self.add("index-ghost", "error", index_path, f"index가 없는 파일을 가리킴: [[{t}]]")
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
        if self.log_text is None:
            self.add("log-format", "error", log_path, "wiki/log.md가 없음")
            return
        for lineno, line in enumerate(self.log_text.splitlines(), start=1):
            if line.startswith("## ") and not LOG_HEADING_RE.match(line):
                self.add(
                    "log-format", "error", log_path,
                    f"{lineno}행이 log 규약 위반: {line!r} — '## [YYYY-MM-DD] <op> | <제목>' (op ∈ init·ingest·query·lint·retire)",
                )

    # ⑧ ingest 항목의 sha 기록 — 재인제스트 중복 확인(grep <sha12> wiki/log.md)의 근거
    def check_log_sha(self) -> None:
        if self.log_text is None:
            return  # log 부재는 log-format이 보고
        for lineno, op, body in parse_log_entries(self.log_text):
            if op == "ingest" and not any(SHA_LINE_RE.search(line) for line in body):
                self.add(
                    "log-sha", "warning", self.wiki_dir / "log.md",
                    f"{lineno}행 ingest 항목에 'sha: <sha12>' 기록 없음 — 재인제스트 중복 확인이 log를 sha12로 "
                    "grep하므로, 기록이 없으면 같은 원본을 중복 인제스트하게 된다",
                )

    # ⑨ raw/sources 원본 ↔ 페이지 sources[] — 미인제스트 원본·인제스트 후 참조가 끊긴 원본
    def check_raw_sources(self) -> None:
        referenced: set[str] = set()
        for page in self.pages:
            fm, _ = self.parsed[page]
            if fm and isinstance(fm.get("sources"), list):
                referenced.update(norm_source(s) for s in fm["sources"] if isinstance(s, str))
        for f in raw_files(self.root / "raw" / "sources"):
            if norm_source(f.relative_to(self.root).as_posix()) in referenced:
                continue
            digest = sha12(f)
            if digest in (self.log_text or ""):
                message = f"인제스트 기록(sha: {digest})은 있으나 어느 페이지 sources[]에도 없음"
            else:
                message = "미인제스트 원본(log에 sha 기록 없음) — /llm-wiki:wiki-ingest 대상"
            self.add("raw-unreferenced", "warning", f, message)


def run_checks(root: Path) -> list[dict]:
    return Checker(root).run()


def collect_stats(root: Path) -> dict:
    wiki_dir = root / "wiki"
    pages: dict[str, int] = {}
    for d in TYPE_DIRS:
        dir_path = wiki_dir / d
        pages[DIR_TO_TYPE[d]] = len(list(dir_path.glob("*.md"))) if dir_path.is_dir() else 0

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
        "raw_sources": len(raw_files(root / "raw" / "sources")),
        "raw_archive": len(raw_files(root / "raw" / "archive")),
        "log_entries": log_entries,
        "last_lint": last_lint,
    }


def collect_pending(root: Path) -> list[dict]:
    """raw/sources/ 바로 아래 원본 중 sha12가 wiki/log.md 어디에도 없는 것(인제스트 대기), 파일 경로순."""
    log_path = root / "wiki" / "log.md"
    log_text = log_path.read_text(encoding="utf-8") if log_path.is_file() else ""
    pending: list[dict] = []
    for f in raw_files(root / "raw" / "sources"):
        digest = sha12(f)
        if digest not in log_text:
            pending.append({"file": f.relative_to(root).as_posix(), "sha12": digest})
    return pending


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


def format_pending_md(pending: list[dict]) -> str:
    if not pending:
        return "미인제스트 원본 없음\n"
    return "".join(f"- {p['file']} (sha: {p['sha12']})\n" for p in pending)


class _Parser(argparse.ArgumentParser):
    """사용법 오류는 exit 1 — argparse 기본값(2)은 플러그인 스크립트의 exit 2(도메인 특수상황) 규약과 충돌한다."""

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(1, f"{self.prog}: 오류: {message}\n")


def main(argv: list[str] | None = None) -> int:
    parser = _Parser(description="llm-wiki 결정적 lint (읽기 전용)")
    parser.add_argument("--root", help="위키 루트 또는 그 안의 경로(기본: 현재 디렉토리에서 위로 탐색)")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--stats", action="store_true", help="검사 없이 통계만 출력")
    mode.add_argument(
        "--pending", action="store_true", help="검사 없이 미인제스트 원본(log에 sha 없는 raw/sources 파일)만 출력"
    )
    args = parser.parse_args(argv)

    root = find_wiki_root(Path(args.root).resolve() if args.root else Path.cwd())
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

    if args.pending:
        pending = collect_pending(root)
        if args.format == "json":
            print(json.dumps({"pending": pending}, ensure_ascii=False, indent=2))
        else:
            print(format_pending_md(pending), end="")
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
