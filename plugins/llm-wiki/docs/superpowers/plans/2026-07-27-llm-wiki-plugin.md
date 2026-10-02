# llm-wiki 플러그인 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Karpathy llm-wiki 패턴을 구현한 Claude Code 플러그인(부트스트래퍼 + 소스 추출 툴벨트)을 이 저장소에 완성한다.

**Architecture:** 플러그인은 커맨드 4개(워크플로 골격) + 스킬 2개(레시피·운영 보강) + 결정적 Python 스크립트 3개(PEP 723, uv 단독 실행) + 템플릿 7종(위키 스캐폴드 원본)으로 구성된다. 위키의 모든 규칙은 init이 생성하는 위키 내부 `AGENTS.md`에 있고(자립성), 스크립트는 stdout/캐시만 쓰며 `wiki/`를 직접 쓰지 않는다(판단은 LLM). 지식의 단일 소스 원칙: 운영 규칙=AGENTS.md, 추출 레시피=source-extract 스킬, 커맨드는 순서와 게이트만.

**Tech Stack:** Claude Code plugin (plugin.json/marketplace.json, commands, skills), Python ≥3.12 + uv (PEP 723), yt-dlp(하한만), pymupdf, pyyaml, pytest.

**기준 스펙:** `docs/superpowers/specs/2026-07-27-llm-wiki-plugin-design.md` (결정 D1~D12 포함. 충돌 시 스펙의 부록 A가 최우선).

## Global Constraints

- 문서·커맨드·스킬 지시문은 **한국어**. 코드·경로·frontmatter 키·config 키는 영어.
- 커맨드는 정확히 4개(`wiki-init`, `wiki-ingest`, `wiki-lint`, `wiki-status`). 신규 기능은 스키마/스킬로 흡수.
- 금지: MCP 서버, 상주 프로세스, HTTP API, 벡터 DB/임베딩, 지식그래프 엔진/UI, 브라우저 확장, Whisper, 리뷰 큐.
- 스크립트: PEP 723 인라인 메타데이터, `requires-python = ">=3.12"`, stdout·캐시 디렉토리 출력만(`wiki/` 직접 쓰기 금지), 사람용 에러는 stderr(한국어), exit 0 성공/1 일반 오류/2 도메인 특수 상황. 서드파티는 지연 임포트(D8).
- 의존성: `yt-dlp>=2025.1.1`(상한 핀 금지), `pymupdf>=1.24`, `pyyaml>=6.0`.
- 번들 스크립트 참조: 커맨드에서 `${CLAUDE_PLUGIN_ROOT}/skills/source-extract/scripts/…`, 스킬에서 `${CLAUDE_SKILL_DIR}/scripts/…` (D6).
- 커맨드 호출 표기는 항상 네임스페이스 형식 `/llm-wiki:<command>` (D5).
- 테스트 실행 명령(전 태스크 공통): `uv run --with pytest --with pyyaml --with pymupdf pytest tests/ -q`
- 커밋 메시지: 한국어 + 마지막 줄 `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>` (빈 줄로 구분).
- 위키 스캐폴드의 특수 파일(`wiki/index.md`·`log.md`·`overview.md`·`reports/*`)은 페이지 frontmatter 대상이 아님(D12). 페이지 타입 디렉토리는 `entities/ concepts/ sources/ synthesis/` 4개.
- log 규약: `## [YYYY-MM-DD] <op> | <제목>`, op ∈ init·ingest·query·lint·retire.
- managed 마커: `<!-- llm-wiki:managed:start schema_version=1 -->` / `<!-- llm-wiki:managed:end -->` (D10).

---

### Task 1: 플러그인 골격 (plugin.json, marketplace.json, LICENSE, .gitignore)

**Files:**
- Create: `.claude-plugin/plugin.json`
- Create: `.claude-plugin/marketplace.json`
- Create: `LICENSE`
- Create: `.gitignore`

**Interfaces:**
- Produces: 플러그인 이름 `llm-wiki`(→ 커맨드 네임스페이스 `/llm-wiki:*`), 마켓플레이스 이름 `llm-wiki`(→ 설치 표기 `llm-wiki@llm-wiki`). Task 6~8이 이 표기를 그대로 사용.

- [ ] **Step 1: 파일 4개 작성**

`.claude-plugin/plugin.json`:
```json
{
  "name": "llm-wiki",
  "displayName": "LLM Wiki",
  "version": "0.1.0",
  "description": "LLM이 유지보수하는 개인 위키 — 위키 부트스트래핑과 소스 추출 툴벨트 (Karpathy llm-wiki 패턴의 Claude Code 플러그인 구현)",
  "author": { "name": "Cho-D-YoungRae", "url": "https://github.com/Cho-D-YoungRae" },
  "repository": "https://github.com/Cho-D-YoungRae/llm-wiki",
  "license": "MIT",
  "keywords": ["wiki", "knowledge-base", "pkm", "ingest", "karpathy", "llm-wiki"]
}
```

`.claude-plugin/marketplace.json`:
```json
{
  "name": "llm-wiki",
  "owner": { "name": "Cho-D-YoungRae", "url": "https://github.com/Cho-D-YoungRae" },
  "plugins": [
    {
      "name": "llm-wiki",
      "source": "./",
      "description": "LLM이 유지보수하는 개인 위키 — 위키 부트스트래핑과 소스 추출 툴벨트",
      "category": "productivity",
      "keywords": ["wiki", "knowledge-base", "pkm"]
    }
  ]
}
```

`LICENSE`: MIT 전문, 저작권 줄은 `Copyright (c) 2026 Cho-D-YoungRae`.

`.gitignore`:
```
__pycache__/
*.pyc
.pytest_cache/
.venv/
.DS_Store
```

- [ ] **Step 2: JSON 유효성 검증**

Run: `python3 -m json.tool .claude-plugin/plugin.json > /dev/null && python3 -m json.tool .claude-plugin/marketplace.json > /dev/null && echo OK`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin LICENSE .gitignore
git commit -m "feat: 플러그인 골격 — plugin.json·marketplace.json·MIT 라이선스"
```

---

### Task 2: templates/ 7종 (위키 스캐폴드 원본)

**Files:**
- Create: `templates/AGENTS.md.tmpl`, `templates/CLAUDE.md.tmpl`, `templates/purpose.md.tmpl`, `templates/config.yaml.tmpl`, `templates/index.md.tmpl`, `templates/log.md.tmpl`, `templates/overview.md.tmpl`

**Interfaces:**
- Produces: 플레이스홀더 `{{PURPOSE}} {{KEY_QUESTIONS}} {{LANGUAGE}} {{OBSIDIAN}} {{LINK_STYLE}} {{YT_LANGS}}`, 조건 블록 키 `if:markdown` `if:wikilink` `if:obsidian`, managed 마커(schema_version=1). Task 3(wiki_check가 검증하는 frontmatter·log 규약의 원천), Task 6(wiki-init 렌더링 지시)이 의존.

- [ ] **Step 1: AGENTS.md.tmpl 작성** — 아래 전문을 그대로 사용:

````markdown
# AGENTS.md — 이 위키의 운영 규약

<!-- llm-wiki:managed:start schema_version=1 -->

## 1. 개요와 3계층

이 저장소는 LLM이 유지보수하는 개인 위키다. 에이전트(당신)는 이 위키의 사서로서 소스를 소화해 페이지로 압축하고, 질문에 위키 기반으로 답하고, 주기적으로 정합성을 관리한다.

3계층:

- `raw/` — 불변 원본 계층. 여기 파일의 내용은 수정하지 않는다(신규 추가와 `raw/archive/` 이동만 허용).
- `wiki/` — LLM 생성 계층. 상호 링크된 마크다운 페이지. 자유롭게 생성·편집한다.
- 스키마 — 이 파일. 위키의 헌법. 사용자 승인 없이 수정하지 않는다.

핵심 가치는 압축이다. 위키는 여러 소스에 흩어진 사실을 모아 압축할 때만 가치가 있다. 소스를 그대로 옮긴 1:1 미러 페이지는 만들지 않는다.

## 2. 세션 시작 절차

위키 작업을 시작할 때 다음 순서로 읽는다.

1. `.llm-wiki/config.yaml` — 언어·링크 스타일·인제스트 설정
2. `purpose.md` — 목적·핵심 질문·발전 중인 논지
3. `wiki/log.md` 최근 항목 — `grep '^## \[' wiki/log.md | tail -n 10`

## 3. 페이지 타입 4종

| 타입 | 정의 | 위치 | 예시 |
|------|------|------|------|
| entity | 고유 개체 — 인물·조직·제품·시스템·논문 등 | `wiki/entities/` | `wiki/entities/andrej-karpathy.md` |
| concept | 여러 소스를 가로지르는 개념·주제 | `wiki/concepts/` | `wiki/concepts/context-engineering.md` |
| source | 원본 하나당 요약 1페이지 | `wiki/sources/` | `wiki/sources/2026-07-27-llm-wiki-gist.md` |
| synthesis | 질의 답변 회수, 비교·종합 | `wiki/synthesis/` | `wiki/synthesis/rag-vs-wiki.md` |

## 4. 페이지 frontmatter 스펙

`entities/`·`concepts/`·`sources/`·`synthesis/`의 모든 페이지는 다음 frontmatter로 시작한다. `index.md`·`log.md`·`overview.md`·`reports/`는 특수 파일로 예외다.

```yaml
type: entity        # 필수 — entity | concept | source | synthesis
title: 표시 제목     # 필수
sources:            # 필수 — 이 페이지에 기여한 원본 경로 배열 (위키 루트 기준)
  - raw/sources/2026-07-27-example.md
created: 2026-07-27 # 필수 — YYYY-MM-DD
updated: 2026-07-27 # 필수 — 편집할 때마다 갱신
tags: []            # 선택
aliases: []         # 선택 — 검색·링크용 별칭
```

## 5. 링크 규칙

<!-- if:markdown -->
표준 마크다운 상대 링크를 쓴다: `[표시 제목](../concepts/page-name.md)`, 같은 디렉토리는 `[표시 제목](page-name.md)`. 페이지를 만들거나 언급할 때 관련 페이지로 적극 링크한다.
<!-- endif:markdown -->
<!-- if:wikilink -->
옵시디언 위키링크를 쓴다: `[[page-name]]`, 표시 제목이 다르면 `[[page-name|표시 제목]]`. 파일명 stem만으로 링크한다(경로 불필요). 페이지를 만들거나 언급할 때 관련 페이지로 적극 링크한다.
<!-- endif:wikilink -->

## 6. 네이밍

- 페이지 파일명: kebab-case 영어(`context-engineering.md`). 비영어 제목은 frontmatter `title`·`aliases`에 담는다.
- 원본 파일명: `YYYY-MM-DD-slug.ext` — 날짜는 인제스트한 날, slug는 내용 기반 kebab-case 영어.

## 7. Ingest 워크플로 (2단계)

1. **1단계 분석**: 원본을 읽고 분석 노트를 만든다 — 엔티티·개념 후보, 기존 페이지와의 연결(`wiki/index.md` 대조), 기존 내용과 모순되는 지점.
2. **사용자 확인**: 분석 노트를 보여주고 확인받는다(대화형 기본). batch 모드에서는 생략하되 분석 요약을 log 항목에 남긴다.
3. **2단계 생성·갱신**: 한 pass로 — (a) 엔티티/개념 페이지 생성·편집 (b) `wiki/sources/`에 소스 요약 1페이지 (c) `wiki/index.md`·`wiki/log.md` 갱신.

판단 휴리스틱:

- new-page vs edit: 처음 등장하는 고유 개체/개념이면 새 페이지, 기존 대상의 속성 변화·보강이면 기존 페이지 편집.
- 승격: 여러 소스 페이지에서 3회 이상 언급되는 개념은 독립 concept 페이지로 승격한다.
- 압축 원칙: 소스 요약 1페이지 + 횡단 페이지 갱신이 기본. 1:1 미러 페이지 금지.

재인제스트 스킵: 인제스트 전 원본의 sha256 앞 12자리를 구해 `grep <sha12> wiki/log.md`로 중복을 확인한다. 이미 있으면 스킵한다(사용자가 강제할 때만 재수행). 인제스트 후 log 항목에 sha12를 기록한다.

## 8. Query 워크플로

1. `wiki/index.md`를 먼저 읽고 후보 페이지 ~10개를 고른다.
2. 후보 페이지만 정독한다. 관련성을 찾으려고 페이지 본문 전체를 스캔하지 않는다(디렉토리 통째 읽기 금지).
3. 출처(페이지와 원본)를 표기하며 합성해 답한다.
4. 가치 있는 답변은 `wiki/synthesis/`에 회수 저장하고 log에 query 항목을 남긴다 — 탐색이 복리로 쌓이게.

## 9. Lint 워크플로

- 기계 검사: 플러그인 환경이면 `wiki_check.py`를 실행한다(깨진 링크·고아 페이지·index 정합·frontmatter·sources 실존·제목/별칭 충돌·log 규약). 플러그인이 없으면 같은 항목을 표본 수동 점검한다.
- LLM 판단 검사: 페이지 간 모순, 낡은 주장(stale), 언급은 잦은데 존재하지 않는 페이지. 전수 조사 금지 — 최근 변경분 + 표본.
- 리포트: `wiki/reports/YYYY-MM-DD-lint.md` 작성 후 log에 lint 항목 기록.
- 규모: index 항목이 200개를 넘으면 qmd 같은 검색 CLI 도입을 사용자에게 제안한다.
- 스키마 공진화: lint는 이 AGENTS.md 자체의 개정을 제안할 수 있다. 적용은 사용자 승인 후에만 한다.

## 10. Retire 절차 (소스 제거)

1. 원본을 `raw/archive/`로 이동한다(삭제 금지).
2. 관련 페이지들의 frontmatter `sources[]`에서 해당 경로를 제거한다.
3. 그 소스가 유일한 출처였던 페이지만 삭제한다. 다른 출처도 있는 공유 페이지는 유지하되 해당 소스 유래 내용을 정리한다.
4. 죽은 링크와 index 항목을 정리한다.
5. log에 retire 항목을 기록한다.

## 11. log 규약 (`wiki/log.md`)

- append-only. 기존 항목을 수정·삭제하지 않는다.
- 모든 항목은 `## [YYYY-MM-DD] <op> | <제목>`으로 시작한다. op ∈ init·ingest·query·lint·retire.
- `grep '^## \[' wiki/log.md | tail`로 파싱 가능해야 한다.
- 본문에 원본 sha256 12자리(`sha: ` 접두), 생성·갱신된 페이지 목록을 남긴다.

## 12. 이미지

- 이미지는 `raw/assets/`에 로컬 저장하고 페이지에서 상대 경로로 참조한다.
- 소스를 읽을 때 텍스트를 먼저 읽고, 본문이 참조하는 이미지는 필요한 것만 별도로 열람한다.
<!-- if:obsidian -->
- 옵시디언 설정(Files & Links)에서 첨부 저장 위치를 `raw/assets`로 지정해두면 붙여넣은 이미지가 규약대로 저장된다.
<!-- endif:obsidian -->

## 13. overview.md

주요 인제스트 pass 후 `wiki/overview.md`의 전역 요약(주제 클러스터·커버리지·공백)을 갱신한다. 사용자 요청에 대한 답변 형식은 자유다(표·페이지·슬라이드 개요 등) — 별도 툴링 없이 마크다운으로 쓴다.

<!-- llm-wiki:managed:end -->

## 사용자 확장 영역

이 마커 아래는 사용자의 자유 영역이다. 플러그인 업그레이드가 건드리지 않는다.
````

- [ ] **Step 2: 나머지 템플릿 6종 작성**

`templates/CLAUDE.md.tmpl`:
```markdown
@AGENTS.md

> 위 `@AGENTS.md` 임포트가 동작하지 않는 환경이라면, 이 위키의 규약 파일 `AGENTS.md`를 직접 읽고 따르세요.
```

`templates/purpose.md.tmpl`:
```markdown
# 이 위키의 목적

{{PURPOSE}}

## 핵심 질문

{{KEY_QUESTIONS}}

## 발전 중인 논지

(아직 없음 — 인제스트와 질의가 쌓이면 이 위키가 지지하는 주장을 근거 페이지 링크와 함께 여기에 정리한다.)
```

`templates/config.yaml.tmpl`:
```yaml
schema_version: 1
language: {{LANGUAGE}}
obsidian: {{OBSIDIAN}}
link_style: {{LINK_STYLE}}    # markdown | wikilink
search: none                  # none | qmd
ingest:
  pdf_direct_max_pages: 30    # 이하면 PDF 직접 참조, 초과면 청킹
  pdf_chunk_pages: 20         # 목차 없을 때 고정 분할 단위
  youtube_sub_langs: [{{YT_LANGS}}]
```

`templates/index.md.tmpl`:
```markdown
# Index — 전체 페이지 카탈로그

인제스트·정리 때마다 갱신한다. 항목 형식: 링크 + 한 줄 설명.

## Entities

(없음)

## Concepts

(없음)

## Sources

(없음)

## Synthesis

(없음)
```

`templates/log.md.tmpl`:
```markdown
# Log — append-only 연대기

모든 항목은 `## [YYYY-MM-DD] <op> | <제목>`으로 시작한다(op ∈ init·ingest·query·lint·retire). 본문에 소스 sha 12자리와 갱신된 페이지 목록을 남긴다. 기존 항목은 수정하지 않는다.
```

`templates/overview.md.tmpl`:
```markdown
# Overview — 전역 요약

(아직 비어 있음 — 주요 인제스트 pass 후 위키 전체의 지형을 요약한다: 주요 주제 클러스터, 커버리지, 공백.)
```

- [ ] **Step 3: 구조 검증**

Run: `grep -c '^## ' templates/AGENTS.md.tmpl; grep -c 'llm-wiki:managed' templates/AGENTS.md.tmpl; grep -c '<!-- if:' templates/AGENTS.md.tmpl; grep -c '<!-- endif:' templates/AGENTS.md.tmpl`
Expected: `14`(managed 13 + 사용자 확장 영역 1) / `2` / `3` / `3`

- [ ] **Step 4: Commit**

```bash
git add templates/
git commit -m "feat: 위키 스캐폴드 템플릿 7종 — AGENTS.md 13섹션·managed 마커·조건 블록"
```

---

### Task 3: wiki_check.py (결정적 lint) — TDD

**Files:**
- Create: `skills/source-extract/scripts/wiki_check.py`
- Create: `tests/conftest.py`
- Test: `tests/test_wiki_check.py`

**Interfaces:**
- Consumes: Task 2의 frontmatter 스펙·log 규약·특수 파일 목록.
- Produces: CLI `uv run wiki_check.py [--format md|json] [--stats]`, exit 0 clean/1 findings. 함수: `find_wiki_root(start: Path) -> Path | None`, `parse_frontmatter(text: str) -> tuple[dict | None, str]`, `run_checks(root: Path) -> list[dict]`(각 finding: `{"check","severity","file","message"}`), `collect_stats(root: Path) -> dict`, `main(argv: list[str] | None) -> int`. JSON 출력: `{"clean": bool, "summary": {check: count}, "findings": [...]}` / `--stats`: `{"pages": {...}, "total_pages", "raw_sources", "raw_archive", "log_entries", "last_lint"}`. Task 6·7의 커맨드/스킬이 이 CLI를 호출.

- [ ] **Step 1: conftest.py 작성** (스크립트 모듈 로더 — Task 4·5도 공용)

```python
import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "skills" / "source-extract" / "scripts"


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def wiki_check():
    return load_script("wiki_check")


@pytest.fixture(scope="session")
def yt_transcript():
    return load_script("yt_transcript")


@pytest.fixture(scope="session")
def pdf_chunk():
    return load_script("pdf_chunk")
```

- [ ] **Step 2: 실패하는 테스트 작성** — `tests/test_wiki_check.py`. 미니 위키 빌더 + 검사 7종 각각의 양성/음성 + stats:

```python
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
    import contextlib, io, os

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
```

- [ ] **Step 3: 실패 확인**

Run: `uv run --with pytest --with pyyaml --with pymupdf pytest tests/test_wiki_check.py -q`
Expected: FAIL (`wiki_check.py` 파일 없음 → conftest 로드 에러)

- [ ] **Step 4: wiki_check.py 구현** — 계약:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml>=6.0"]
# ///
"""위키 결정적 lint — llm-wiki. 읽기 전용(어떤 파일도 쓰지 않는다).

검사: broken-link / link-style / orphan / index-missing / index-ghost /
frontmatter / source-missing / collision / log-format
exit: 0 clean / 1 findings 또는 오류
"""
```

구현 요점(함수 시그니처는 Interfaces와 동일):
- `find_wiki_root`: cwd에서 상위로 `.llm-wiki/config.yaml` 탐색. 실패 시 main이 stderr 안내 + exit 1.
- `parse_frontmatter`: `^---\n ... \n---\n` 블록을 `yaml.safe_load`. 없으면 `(None, 원문)`.
- 링크 추출 정규식: md `\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)`, wikilink `\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]`. `http(s)://`·`mailto:`·`#`으로 시작하는 md 타깃은 제외. 코드 펜스(````` ``` `````) 내부는 제외.
- broken-link: md는 파일 기준 상대 해석(anchor 제거) 후 실존 확인. wikilink는 `wiki/**/*.md` stem 집합에서 확인. index.md의 md 링크는 여기서 제외(index-ghost가 담당).
- link-style: config `link_style=markdown`인데 wikilink 발견(또는 반대) → warning 1건/파일.
- orphan: 타입 4디렉토리 페이지 중, index.md를 제외한 `wiki/**/*.md`로부터 인바운드 0 → warning.
- index-missing / index-ghost: index.md의 링크 집합 vs 실제 타입 디렉토리 파일 집합.
- frontmatter: 필수 `type,title,sources,created,updated`, `type` enum, 날짜 `^\d{4}-\d{2}-\d{2}$`, `sources`는 비어 있지 않은 list.
- source-missing: `sources[]` 각 경로가 위키 루트 기준 실존.
- collision: title·aliases(소문자 정규화)·파일 stem이 서로 다른 파일에서 중복.
- log-format: `## `로 시작하는데 `^## \[\d{4}-\d{2}-\d{2}\] (init|ingest|query|lint|retire) \| .+$` 불일치.
- `collect_stats`: 타입별 페이지 수(frontmatter type 아닌 **디렉토리 기준**), raw_sources/raw_archive 파일 수(`.gitkeep` 제외), log_entries(`^## \[` 라인 수), last_lint(`wiki/reports/*-lint.md` 파일명 날짜 최대값, 없으면 None).
- 출력: `--format md`(기본, 사람용 한국어 요약) / `json`. exit: findings 있으면 1(‑-stats 단독은 항상 0).

- [ ] **Step 5: 통과 확인**

Run: `uv run --with pytest --with pyyaml --with pymupdf pytest tests/test_wiki_check.py -q`
Expected: PASS (전건)

- [ ] **Step 6: Commit**

```bash
git add skills/source-extract/scripts/wiki_check.py tests/conftest.py tests/test_wiki_check.py
git commit -m "feat: wiki_check.py — 결정적 lint 검사 7종 + --stats (pytest 포함)"
```

---

### Task 4: yt_transcript.py (유튜브 자막) — TDD

**Files:**
- Create: `skills/source-extract/scripts/yt_transcript.py`
- Create: `tests/fixtures/sample-captions.vtt`
- Test: `tests/test_yt_transcript.py`

**Interfaces:**
- Produces: CLI `uv run yt_transcript.py URL [--langs ko,en]`, exit 0/1/2(자막 없음). 순수 함수: `parse_vtt(text) -> list[Cue]`(`Cue(start: float, text: str)`), `dedupe_cues(cues) -> list[Cue]`, `to_paragraphs(cues, gap=4.0, max_chars=600) -> list[tuple[float, str]]`, `format_timestamp(seconds) -> str`, `render_markdown(meta: dict, paragraphs) -> str`. 네트워크 함수 `fetch(url, langs)`만 yt_dlp 지연 임포트.

- [ ] **Step 1: 픽스처 작성** — `tests/fixtures/sample-captions.vtt` (롤링 캡션 중복·태그 포함):

```
WEBVTT
Kind: captions
Language: ko

00:00:00.000 --> 00:00:02.000
안녕하세요 오늘은

00:00:02.000 --> 00:00:04.000
안녕하세요 오늘은
위키 패턴을 다룹니다

00:00:04.000 --> 00:00:06.000
위키 패턴을 다룹니다
<c>핵심은</c> 압축입니다

00:00:12.000 --> 00:00:14.000
다음 주제로 넘어갑니다
```

- [ ] **Step 2: 실패하는 테스트 작성** — `tests/test_yt_transcript.py`:

```python
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "sample-captions.vtt"


def test_parse_vtt_extracts_cues(yt_transcript):
    cues = yt_transcript.parse_vtt(FIXTURE.read_text(encoding="utf-8"))
    assert [c.start for c in cues] == [0.0, 2.0, 4.0, 12.0]
    assert cues[2].text == "위키 패턴을 다룹니다 핵심은 압축입니다"  # 태그 제거·라인 병합


def test_dedupe_rolling_captions(yt_transcript):
    cues = yt_transcript.dedupe_cues(yt_transcript.parse_vtt(FIXTURE.read_text(encoding="utf-8")))
    assert [c.text for c in cues] == [
        "안녕하세요 오늘은",
        "위키 패턴을 다룹니다",
        "핵심은 압축입니다",
        "다음 주제로 넘어갑니다",
    ]


def test_paragraphs_split_on_gap(yt_transcript):
    cues = yt_transcript.dedupe_cues(yt_transcript.parse_vtt(FIXTURE.read_text(encoding="utf-8")))
    paras = yt_transcript.to_paragraphs(cues, gap=4.0, max_chars=600)
    assert len(paras) == 2
    assert paras[0][0] == 0.0
    assert paras[1] == (12.0, "다음 주제로 넘어갑니다")


def test_paragraphs_split_on_length(yt_transcript):
    Cue = yt_transcript.Cue
    cues = [Cue(start=float(i), text="가" * 250) for i in range(4)]
    paras = yt_transcript.to_paragraphs(cues, gap=100.0, max_chars=600)
    assert len(paras) > 1


def test_format_timestamp(yt_transcript):
    assert yt_transcript.format_timestamp(0) == "00:00"
    assert yt_transcript.format_timestamp(75) == "01:15"
    assert yt_transcript.format_timestamp(3671) == "1:01:11"


def test_render_markdown_frontmatter_and_markers(yt_transcript):
    meta = {
        "title": 'He said "hi"',
        "channel": "ch",
        "url": "https://youtu.be/x",
        "upload_date": "2026-07-01",
        "duration": "10:00",
        "lang": "ko",
        "kind": "auto",
        "retrieved": "2026-07-27",
    }
    out = yt_transcript.render_markdown(meta, [(0.0, "본문 첫 문단"), (75.0, "둘째 문단")])
    assert out.startswith("---\n")
    assert 'title: "He said \\"hi\\""' in out
    assert "[00:00] 본문 첫 문단" in out
    assert "[01:15] 둘째 문단" in out
```

- [ ] **Step 3: 실패 확인**

Run: `uv run --with pytest --with pyyaml --with pymupdf pytest tests/test_yt_transcript.py -q`
Expected: FAIL (모듈 파일 없음)

- [ ] **Step 4: yt_transcript.py 구현**

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["yt-dlp>=2025.1.1"]
# ///
"""유튜브 자막 추출 — llm-wiki.

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


def _longest_overlap(prev: str, cur: str) -> int:
    """prev의 접미부 == cur의 접두부인 최대 문자 수."""
    for n in range(min(len(prev), len(cur)), 0, -1):
        if prev[-n:] == cur[:n]:
            return n
    return 0


def dedupe_cues(cues: list[Cue]) -> list[Cue]:
    """자동 자막 롤링 캡션 정리: 직전 큐 텍스트와 겹치는 접두부·완전 중복 제거."""
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

    def pick(track_map: dict) -> tuple[str, str] | None:
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
```

- [ ] **Step 5: 통과 확인**

Run: `uv run --with pytest --with pyyaml --with pymupdf pytest tests/test_yt_transcript.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add skills/source-extract/scripts/yt_transcript.py tests/fixtures/sample-captions.vtt tests/test_yt_transcript.py
git commit -m "feat: yt_transcript.py — 자막 추출·롤링 캡션 정리·문단화 (pytest 포함)"
```

---

### Task 5: pdf_chunk.py (장문 PDF 분할) — TDD

**Files:**
- Create: `skills/source-extract/scripts/pdf_chunk.py`
- Test: `tests/test_pdf_chunk.py`

**Interfaces:**
- Produces: CLI `uv run pdf_chunk.py PATH [--chunk-pages 20] [--cache-dir raw/.cache] [--force] [--info]`, exit 0/1/2(텍스트 추출 불가). 순수 함수 `plan_chunks(page_count: int, toc: list[tuple[int, str, int]], chunk_pages: int) -> list[Chunk]`(`Chunk(start: int, end: int, title: str | None)`, 쪽 번호 1-기반 포함 범위, `RESPLIT_FACTOR = 1.5`). `--info` stdout: `{"pages", "toc", "toc_top_entries"}`. 분할 stdout: manifest JSON `{"source","sha256","sha12","pages","chunk_pages","toc_used","parts":[{"file","pages","title"}]}`. 캐시: `<cache-dir>/<sha12>/manifest.json` + `part-NN.md`(frontmatter: source/part n\/m/pages a-b/toc_title, 본문 쪽마다 `[p.N]` 마커). Task 6·7이 `--info`→직접/청킹 분기, manifest→pass 계획에 사용.

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/test_pdf_chunk.py`:

```python
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
    import contextlib, io

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


def test_scanned_pdf_exits_two(pdf_chunk, tmp_path, capsys):
    pdf = make_pdf(tmp_path / "c.pdf", pages=3, with_text=False)
    code, _ = run(pdf_chunk, [str(pdf), "--cache-dir", str(tmp_path / "cache")])
    assert code == 2


def test_missing_file_exits_one(pdf_chunk, tmp_path):
    code, _ = run(pdf_chunk, [str(tmp_path / "nope.pdf"), "--cache-dir", str(tmp_path / "cache")])
    assert code == 1
```

- [ ] **Step 2: 실패 확인**

Run: `uv run --with pytest --with pyyaml --with pymupdf pytest tests/test_pdf_chunk.py -q`
Expected: FAIL (모듈 파일 없음)

- [ ] **Step 3: pdf_chunk.py 구현** — 요점:

- PEP 723 헤더(`pymupdf>=1.24`), docstring에 사용법·exit 계약(한국어).
- `plan_chunks`: level 1 TOC 항목만 사용, 같은 시작 쪽 중복 제거, 시작이 1이 아니면 `(front matter)` 청크 선행, 챕터 길이 > `chunk_pages * RESPLIT_FACTOR`면 `_fixed_chunks(start, end, chunk_pages, title)`로 재분할(제목에 ` (n)` 접미). TOC 없으면 전체 고정 분할.
- `ExtractError(Exception)`: 암호화(`doc.needs_pass`) 또는 전체 추출 텍스트 50자 미만(스캔본) → main에서 stderr 안내 + exit 2.
- `file_sha256(path)`: 1MB 블록 스트리밍.
- `build_cache(pdf_path, cache_dir, chunk_pages, force) -> dict`: `pymupdf` 지연 임포트. `<cache-dir>/<sha12>/manifest.json` 존재 && not force → 그대로 반환. 아니면 part 파일 생성(frontmatter의 문자열 값은 큰따옴표 이스케이프, `toc_title`은 있을 때만) 후 manifest 기록·반환.
- `info_mode(pdf_path) -> dict`: `{"pages", "toc": bool, "toc_top_entries": level1 개수}` — 파일 생성 없음.
- `main(argv) -> int`: argparse(PATH, `--chunk-pages` 기본 20, `--cache-dir` 기본 `raw/.cache`, `--force`, `--info`). 결과 JSON은 `json.dumps(..., ensure_ascii=False, indent=2)` stdout. `FileNotFoundError` 등 일반 오류 → stderr + 1.

- [ ] **Step 4: 통과 확인**

Run: `uv run --with pytest --with pyyaml --with pymupdf pytest tests/ -q`
Expected: PASS (전체 스위트 — 회귀 포함)

- [ ] **Step 5: Commit**

```bash
git add skills/source-extract/scripts/pdf_chunk.py tests/test_pdf_chunk.py
git commit -m "feat: pdf_chunk.py — sha 캐시·TOC 우선 분할·--info (pytest 포함)"
```

---

### Task 6: 커맨드 4종

**Files:**
- Create: `commands/wiki-init.md`, `commands/wiki-ingest.md`, `commands/wiki-lint.md`, `commands/wiki-status.md`

**Interfaces:**
- Consumes: Task 2 템플릿(경로·플레이스홀더·조건 키·마커), Task 3~5 CLI 계약, Task 7의 스킬 이름(`llm-wiki:source-extract`).
- Produces: 사용자 표기 `/llm-wiki:wiki-init` `…:wiki-ingest` `…:wiki-lint` `…:wiki-status` — Task 8 문서가 참조.

공통 원칙(D4): 커맨드에는 순서·게이트·출력만. 레시피는 source-extract 스킬, 운영 규칙은 위키 AGENTS.md로 위임. 위키 루트 탐색 문구(“cwd에서 상위로 `.llm-wiki/config.yaml` 탐색, 없으면 `/llm-wiki:wiki-init` 안내 후 종료”)는 wiki-init 제외 3개 커맨드에 공통.

- [ ] **Step 1: wiki-init.md 작성** — frontmatter `description: 새 LLM 위키 스캐폴드 생성 또는 기존 위키 업그레이드 (인터뷰 → 렌더링 → 사전요건 체크)`, `argument-hint: "[대상 디렉토리]"`. 본문(한국어) 필수 내용:
  1. 대상 디렉토리: `$ARGUMENTS` 경로 또는 cwd.
  2. `.llm-wiki/config.yaml` 존재 → **업그레이드 모드**: 위키 AGENTS.md 마커의 `schema_version` vs `${CLAUDE_PLUGIN_ROOT}/templates/AGENTS.md.tmpl`의 값 비교 → 같으면 “이미 최신” 종료 / 다르면 현재 config(link_style·obsidian)로 새 managed 블록 렌더링 → 기존 블록과 diff 제시 → **승인 후** 마커 사이만 교체(마커 밖 보존), config에 신규 키 기본값 추가(기존 값 유지)·schema_version 갱신, log에 `## [날짜] init | 스키마 업그레이드 vN→vM` append. 거부 시 무변경.
  3. 신규 모드 인터뷰 — **한 번에 하나씩** 4문항: ① 목적+핵심 질문 2~3개 ② 옵시디언 뷰어 사용? (yes→`obsidian: true`, link_style 기본 wikilink·사용자가 원하면 markdown, `.obsidian/` 생성 + `app.json`에 `{}`) ③ 유튜브 소스 사용? ④ git 관리?
  4. 사전요건: `uv --version`. 실패 + 유튜브 yes → 설치 안내(macOS `brew install uv`, 기타 https://docs.astral.sh/uv/) 출력하되 **스캐폴드는 계속**.
  5. 스캐폴드: 디렉토리 `raw/{sources,assets,archive,.cache}`, `wiki/{reports,entities,concepts,sources,synthesis}`, `.llm-wiki/`. 템플릿 렌더링 — config.yaml({{LANGUAGE}}=사용자 대화 언어 기본 ko, {{OBSIDIAN}}, {{LINK_STYLE}}, {{YT_LANGS}}=`ko, en`), AGENTS.md(채택 조건 블록은 마커만 제거, 미채택 블록 통삭제, **managed 마커는 유지**), CLAUDE.md(그대로), purpose.md({{PURPOSE}}, {{KEY_QUESTIONS}} 불릿), index/log/overview(그대로). log 끝에 `## [오늘] init | 위키 생성` + 설정 요약 append.
  6. git yes: `git init` + `.gitignore`에 `raw/.cache/`·`.DS_Store` + 빈 디렉토리 8곳에 `.gitkeep`. 커밋은 하지 않고 첫 커밋 명령만 안내.
  7. 완료 안내: 생성 요약, obsidian yes면 Web Clipper(웹 저장 → `raw/sources/`)·graph view 팁, 다음 단계 `/llm-wiki:wiki-ingest <url|경로>` 예시.
  8. 금지: 기존 위키 콘텐츠(페이지·log 기존 항목·purpose 본문) 수정 금지.

- [ ] **Step 2: wiki-ingest.md 작성** — frontmatter `description: 소스(유튜브·웹·PDF·로컬 파일)를 위키에 인제스트 — 유형 판별 → 추출 → 2단계 인제스트`, `argument-hint: "<url|경로> [--batch] [--force]"`. 본문 필수 내용:
  1. 위키 루트 탐색(공통 문구) → config·AGENTS.md·purpose.md·log 최근 항목 읽기(세션 시작 절차). `$ARGUMENTS`에서 소스와 `--batch`/`--force` 해석, 소스 없으면 사용법 안내 후 종료.
  2. 원본 확보: `llm-wiki:source-extract` 스킬을 로드해 유형별 레시피를 따른다. 원본은 `raw/sources/YYYY-MM-DD-slug.ext`.
  3. 중복 확인: `shasum -a 256`(macOS)/`sha256sum`(Linux) → 앞 12자리 → `grep <sha12> wiki/log.md`. 존재 시 해당 log 항목 인용 + “재수행은 --force” 안내 후 종료(원본 파일은 유지). 장문 PDF는 log의 `part n/m`로 중단 인제스트를 감지해 이어하기 제안.
  4. 2단계 인제스트: **위키 AGENTS.md의 Ingest 워크플로(§7)를 그대로 수행**. 대화형 기본(분석 노트 → 확인 → 생성), `--batch`는 확인 생략 + 분석 요약을 log에. 청킹 PDF는 청크당 1 pass + pass마다 log에 `part n/m` 기록.
  5. 종료 요약: 신규/수정 페이지·소스 요약 페이지·log 항목 제목 표.

- [ ] **Step 3: wiki-lint.md 작성** — frontmatter `description: 위키 정합성 점검 — 기계 검사(wiki_check) + LLM 판단 검사 → 리포트`, `argument-hint: ""`. 본문 필수 내용:
  1. 위키 루트 탐색(공통 문구) → AGENTS.md·purpose.md 읽기.
  2. 기계 검사: 위키 루트에서 `uv run "${CLAUDE_PLUGIN_ROOT}/skills/source-extract/scripts/wiki_check.py" --format json`. exit 0=clean/1=findings. uv 없으면 설치 안내 후 §3만 진행(리포트에 명시).
  3. LLM 판단 검사(전수 금지): 범위 = log 최근 항목의 변경 페이지 + index 무작위 표본 ~10. 항목 = 모순 / stale / 언급 잦은데 없는 페이지.
  4. `wiki/reports/YYYY-MM-DD-lint.md` 작성(기계 결과 표 + 판단 발견 + 권고 조치) → log에 lint 항목. 발견 수정은 목록 제안 후 **승인된 것만** 적용.
  5. `--stats`의 total_pages(또는 index 항목 수) > 200 → qmd 검색 CLI 도입 제안(현재 설치법을 조사해 안내만, 자동 설치 금지).
  6. 반복 패턴 관찰 시 리포트에 “AGENTS.md 개정 제안” 섹션(적용은 사용자 승인 후) — 공진화 조항.

- [ ] **Step 4: wiki-status.md 작성** — frontmatter `description: 위키 현황 — 최근 로그 10건 + 통계 + 핵심 질문 (읽기 전용)`, `argument-hint: ""`, `disallowed-tools: ["Write", "Edit", "NotebookEdit"]`. 본문 필수 내용: **읽기 전용 — 어떤 파일도 만들거나 수정하지 않는다(log 기록도 금지)** 선언, 위키 루트 탐색(공통 문구), `grep '^## \[' wiki/log.md | tail -n 10`, `uv run "${CLAUDE_PLUGIN_ROOT}/skills/source-extract/scripts/wiki_check.py" --stats --format json`(uv 없으면 디렉토리 나열로 대체), purpose.md 핵심 질문 재표시, 한 화면 요약(최근 활동/통계 표/핵심 질문/마지막 lint 7일 초과 시 `/llm-wiki:wiki-lint` 권장 한 줄).

- [ ] **Step 5: frontmatter 검증**

Run: `for f in commands/*.md; do python3 - "$f" <<'EOF'
import sys, re
text = open(sys.argv[1], encoding="utf-8").read()
m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
assert m, sys.argv[1] + ": frontmatter 없음"
assert "description:" in m.group(1), sys.argv[1] + ": description 없음"
print(sys.argv[1], "OK")
EOF
done`
Expected: 4줄 모두 `OK`

- [ ] **Step 6: Commit**

```bash
git add commands/
git commit -m "feat: 커맨드 4종 — wiki-init·wiki-ingest·wiki-lint·wiki-status"
```

---

### Task 7: 스킬 2종

**Files:**
- Create: `skills/wiki-maintainer/SKILL.md`
- Create: `skills/source-extract/SKILL.md`

**Interfaces:**
- Consumes: Task 3~5 스크립트 CLI 계약, Task 6 커맨드 이름.
- Produces: 스킬 이름 `wiki-maintainer`·`source-extract`(호출 표기 `llm-wiki:source-extract`) — Task 6 커맨드와 Task 8 문서가 참조.

skill-creator 규약: 트리거 조건은 전부 frontmatter `description`에 pushy하게(언더트리거 방지), 본문 500줄 이하, 규칙 중복 서술 금지(progressive disclosure).

- [ ] **Step 1: wiki-maintainer/SKILL.md 작성** — frontmatter:
```yaml
---
name: wiki-maintainer
description: llm-wiki로 생성된 위키(.llm-wiki/ 디렉토리 존재)에서 작업할 때 반드시 사용. 페이지 생성·편집·질의·정리·소스 제거(retire), 사용자가 위키 내용을 묻거나 자료를 추가·정리하거나 위키를 인용해 답할 때 모두 해당. 위키 저장소 안에서의 모든 운영 판단에 필요.
---
```
본문 필수 내용(≤80줄): **1원칙 — 위키의 `AGENTS.md`를 읽고 따르라**(규칙 복제 금지 명시) / 세션 시작 절차(config → purpose → log tail) / 플러그인 보강 — 기계 lint `uv run "${CLAUDE_PLUGIN_ROOT}/skills/source-extract/scripts/wiki_check.py" --format md`, 통계 `--stats`, 소스 추출은 `llm-wiki:source-extract` 스킬, 정형 워크플로는 `/llm-wiki:wiki-ingest`·`/llm-wiki:wiki-lint`·`/llm-wiki:wiki-status`·업그레이드는 `/llm-wiki:wiki-init` / 주의 — 스크립트는 stdout·캐시만 쓰고 wiki/ 반영은 항상 에이전트 판단, AGENTS.md 수정은 사용자 승인 후에만.

- [ ] **Step 2: source-extract/SKILL.md 작성** — frontmatter:
```yaml
---
name: source-extract
description: 소스를 LLM 위키의 raw/ 원본으로 변환할 때 반드시 사용 — 유튜브 URL 자막 추출, 장문 PDF 분할, 웹 페이지 본문 저장, 로컬 md·txt 복사. /llm-wiki:wiki-ingest 실행 중이거나 사용자가 위키에 영상·문서·링크·파일을 추가하려 할 때 항상 이 레시피를 따른다.
---
```
본문 필수 내용(≤120줄):
- 공통: 원본은 `raw/sources/YYYY-MM-DD-slug.ext`(오늘 날짜·kebab-case 영어 slug), 스크립트는 stdout/`raw/.cache/`만 출력(저장·반영은 에이전트), 경로는 `${CLAUDE_SKILL_DIR}/scripts/…`(커맨드 문맥에서는 `${CLAUDE_PLUGIN_ROOT}/skills/source-extract/scripts/…`), exit 0/1/2 의미.
- 유튜브: config `ingest.youtube_sub_langs`로 `uv run "${CLAUDE_SKILL_DIR}/scripts/yt_transcript.py" "<URL>" --langs ko,en` → stdout을 원본 md로 저장. exit 2(자막 없음) → stderr 안내를 사용자에게 그대로 전달 + 수동 대안(설명란·발표 자료·관련 글 인제스트) 제안, Whisper는 범위 외. uv 없으면 설치 안내 후 중단.
- 웹 URL: 내장 웹 조회 도구로 본문 위주 마크다운 정리(내비게이션·광고 제거), frontmatter `url`/`title`/`retrieved`(+author·published 있으면) 붙여 저장. 실패 시 폴백 — obsidian 사용자면 “옵시디언 Web Clipper로 저장 후 그 파일을 인제스트”, 아니면 본문 수동 복사 안내.
- 로컬 md/txt: `raw/sources/`로 **복사**(원본 이동 금지, 이미 안이면 생략).
- 로컬 PDF: ① `--info`로 쪽수 확인 ② PDF를 `raw/sources/`로 복사 ③ `pages ≤ config.ingest.pdf_direct_max_pages`면 직접 읽기(Read, 필요 시 pages 지정)로 인제스트 ④ 초과면 `uv run … pdf_chunk.py <복사본> --chunk-pages <config> --cache-dir raw/.cache` → manifest `parts`가 pass 계획, 청크당 1 pass + log `part n/m`(중단 후 재개), `--force`로 캐시 재생성 ⑤ exit 2(암호화·스캔본) → 안내(해제/OCR 사본 재시도, OCR은 범위 외).
- 이미지: `raw/assets/` 저장 후 상대 참조, 필요한 것만 열람(AGENTS.md §12를 따름).

- [ ] **Step 3: frontmatter 검증**

Run: `for f in skills/*/SKILL.md; do python3 - "$f" <<'EOF'
import sys, re
text = open(sys.argv[1], encoding="utf-8").read()
m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
assert m and "name:" in m.group(1) and "description:" in m.group(1), sys.argv[1]
print(sys.argv[1], "OK", len(text.splitlines()), "lines")
EOF
done`
Expected: 2줄 `OK`, 각 500줄 미만

- [ ] **Step 4: Commit**

```bash
git add skills/wiki-maintainer skills/source-extract/SKILL.md
git commit -m "feat: 스킬 2종 — wiki-maintainer(운영 보강)·source-extract(추출 레시피)"
```

---

### Task 8: 문서 3종 + 픽스처

**Files:**
- Modify: `README.md` (기존 1줄 파일 — 먼저 Read 후 전면 교체)
- Create: `ARCHITECTURE.md`
- Create: `CLAUDE.md` (플러그인 저장소 루트 — 개발 가이드. `templates/CLAUDE.md.tmpl`과 다른 파일임에 주의)
- Create: `tests/fixtures/sample-note.md`

**Interfaces:**
- Consumes: Task 1 설치 표기(`/plugin marketplace add Cho-D-YoungRae/llm-wiki`, `/plugin install llm-wiki@llm-wiki`, `claude --plugin-dir .`), Task 6 커맨드 표기, Task 3~5 계약, 전 태스크 공통 테스트 명령.

- [ ] **Step 1: README.md 작성** (한국어) — 필수 섹션·내용:
  1. 첫 화면 크레딧(그대로 포함): “Andrej Karpathy의 [llm-wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)에서 영감을 받아 그 패턴을 Claude Code 플러그인으로 구현했다. [nashsu/llm_wiki](https://github.com/nashsu/llm_wiki)를 참고 구현으로 참조했다(개념 일부 차용, 아키텍처는 독자적).”
  2. 설치: 마켓플레이스 2줄(`/plugin marketplace add Cho-D-YoungRae/llm-wiki` → `/plugin install llm-wiki@llm-wiki`) + 로컬 개발(`claude --plugin-dir .`).
  3. Quickstart(3분): `/llm-wiki:wiki-init` → 유튜브 URL 하나 `/llm-wiki:wiki-ingest` → 위키에 질문 → `/llm-wiki:wiki-status`.
  4. 커맨드 레퍼런스 표: 4개 커맨드 × (용도, 인자·플래그).
  5. 유즈케이스 3개 구체 시나리오: (a) 기술 학습 위키 — 유튜브 강의+블로그를 개념 위키로 (b) 전자책 정독 위키 — 챕터별 인제스트로 인물·주제 페이지 축적 (c) 도메인 리서치 위키 — 규정 PDF+웹 자료를 질의 가능한 synthesis로. 각각 실제 명령 흐름 3~5줄 포함.
  6. 아키텍처 한 단락(3계층·3연산·플러그인/위키 경계) + ARCHITECTURE.md 링크.
  7. 요구사항: Claude Code, uv 필수 / Obsidian·qmd 선택.
  8. FAQ: “왜 MCP가 없나”(상태가 전부 파일시스템 — 프로토콜 서버가 낄 자리가 없음) / “Codex에서 쓰려면”(위키는 AGENTS.md 표준으로 그대로 동작, 스크립트는 `uv run`으로 직접 실행) / “자막 없는 영상은?”(범위 외 — 수동 대안) / “위키가 커지면?”(index 200 초과 시 qmd 안내).
  9. 라이선스: MIT.

- [ ] **Step 2: ARCHITECTURE.md 작성** — 필수 내용:
  1. 3계층(raw/wiki/schema)·3연산(Ingest/Query/Lint) mermaid `flowchart`.
  2. ingest mermaid `sequenceDiagram`: 사용자 → 커맨드(유형 판별) → 스크립트/WebFetch(추출) → raw/sources 저장 → sha 중복 확인 → 1단계 분석 → 사용자 확인 → 2단계 생성 → index·log 갱신.
  3. 플러그인 vs 위키 경계 표(무엇이 어디 사는지: 커맨드·스킬·스크립트·템플릿 ↔ AGENTS.md·config·raw·wiki).
  4. 옵션 매트릭스: core/obsidian/qmd × 영향 범위(링크 문법·.obsidian/·클리퍼 안내 / 콘텐츠 무변경·attach 시점).
  5. ADR-lite 4건(제목·결정·근거): ① MCP를 두지 않은 이유(상태가 전부 파일시스템에 있음) ② AGENTS.md를 canonical로 둔 이유(양 런타임 호환·드리프트 방지 — CLAUDE.md는 `@AGENTS.md` 포인터, 심볼릭링크는 Windows 이식성 문제로 배제) ③ 장문 PDF를 청킹하는 이유(인제스트 단위·런타임 호환·토큰 경제 — 원본 보존과는 무관) ④ 스크립트가 wiki/를 쓰지 않는 이유(판단/기계 경계).

- [ ] **Step 3: CLAUDE.md(루트) 작성** — 필수 내용: ① 저장소 구조 지도(트리+한 줄 책임) ② 불변 원칙 7개 요약 ③ 수정 규칙 — 커맨드는 4개 유지(신규 기능은 스킬/스키마 흡수 우선 검토), 스크립트는 stdout·캐시만(wiki/ 쓰기 금지), `templates/` 변경 시 `AGENTS.md.tmpl`의 `schema_version` 증가 + wiki-init 업그레이드 경로 갱신 ④ 문서 동기화 — 원칙 변경 시 README·ARCHITECTURE 동반 수정 ⑤ 테스트 절차 — `uv run --with pytest --with pyyaml --with pymupdf pytest tests/ -q` + §8 스모크 시나리오 9종 실행법(임시 디렉토리 + `claude --plugin-dir <repo>` 세션에서 순서대로).

- [ ] **Step 4: tests/fixtures/sample-note.md 작성** — 스모크 2번용 픽스처. 조건: 엔티티 2개 이상(예: Andrej Karpathy, Claude Code)·개념 2개 이상(예: llm-wiki 패턴, 컨텍스트 엔지니어링)이 서로 얽힌 500~800자 한국어 학습 노트. frontmatter 없이 평문 마크다운(로컬 노트 시늉).

- [ ] **Step 5: 검증** — README에 크레딧 링크 2개(`gist.github.com/karpathy`·`github.com/nashsu`)와 설치 2경로, ARCHITECTURE에 ` ```mermaid ` 블록 2개·ADR 4건이 있는지 grep으로 확인:

Run: `grep -c 'mermaid' ARCHITECTURE.md; grep -c 'ADR' ARCHITECTURE.md; grep -c 'karpathy' README.md; grep -c 'nashsu' README.md`
Expected: 각각 ≥2 / ≥4 / ≥1 / ≥1

- [ ] **Step 6: Commit**

```bash
git add README.md ARCHITECTURE.md CLAUDE.md tests/fixtures/sample-note.md
git commit -m "docs: README·ARCHITECTURE·CLAUDE.md + 스모크 픽스처"
```

---

### Task 9: §8 스모크 검증 (수용 기준)

**Files:**
- 검증 대상: 저장소 전체. 임시 위키는 스크래치 디렉토리에 생성(저장소 외부). 발견된 결함 수정만 저장소에 커밋.

**Interfaces:**
- Consumes: 전 태스크 산출물 전부.

- [ ] **Step 1: 전체 테스트 재실행** — `uv run --with pytest --with pyyaml --with pymupdf pytest tests/ -q` → PASS 확인.
- [ ] **Step 2: 시나리오 1 (init)** — 스크래치에 새 디렉토리를 만들고 `commands/wiki-init.md`의 지시를 에이전트가 그대로 수행(옵시디언 no·유튜브 yes·git yes 가정). 검증: §3 구조 전부, AGENTS.md `## ` 섹션 13개(managed 내)·마커 2개·`if:` 잔존 0, CLAUDE.md가 `@AGENTS.md` 포함, log에 init 항목, `.gitignore`에 `raw/.cache/`.
- [ ] **Step 3: 시나리오 2·3 (ingest·재-ingest)** — `tests/fixtures/sample-note.md`를 인제스트(분석 노트 표시 확인). 검증: `wiki/sources/` 요약 1페이지 + entity/concept 페이지 ≥2 + index·log 갱신 + 1:1 미러 없음. 같은 파일 재시도 → sha 중복 스킵 문구, `--force` 경로 동작.
- [ ] **Step 4: 시나리오 4 (유튜브)** — 자막 있는 실제 URL 1건 실행 → `raw/sources/`에 frontmatter+`[mm:ss]` 트랜스크립트. 자막 없는 URL 1건 → exit 2·stderr 안내 전달. 네트워크 불가 시: pytest 결과로 대체하고 스모크 기록에 명시.
- [ ] **Step 5: 시나리오 5 (장문 PDF)** — pymupdf로 40쪽 테스트 PDF 생성(`--info` → pages 40 > 30) → 청킹 → part 1 인제스트 후 중단 → log `part 1/2` 확인 → 재개해 `part 2/2` 완료.
- [ ] **Step 6: 시나리오 6 (질의)** — 위키 내용 질문 1건: index 우선 조회로 답변 + `wiki/synthesis/` 회수 + log query 항목.
- [ ] **Step 7: 시나리오 7 (lint)** — `/llm-wiki:wiki-lint` 절차 수행 → clean 리포트 생성. 링크 하나 고의 파손 → `wiki_check.py` exit 1 + broken-link finding 확인 → 복구.
- [ ] **Step 8: 시나리오 8 (status)** — status 절차 수행 → log 10건+통계+핵심 질문 출력. 전후 `find <위키> -newer <기준파일>`로 파일 무변경 확인.
- [ ] **Step 9: 시나리오 9 (문서)** — §7.1(8항목)·§7.2(5항목)·§7.3(5항목) 체크리스트 대조.
- [ ] **Step 10: 결함 수정·커밋** — 스모크에서 발견된 결함을 수정하고 커밋(메시지: `fix: 스모크 검증 반영 — <요약>`). 스모크 결과 요약은 최종 보고에 포함.

---

## Self-Review (작성 후 점검 완료)

- 스펙 커버리지: §2 구조(전 파일 Task 1~8), §3 스캐폴드(Task 2·6), §3.1 config(Task 2), §3.2 13섹션(Task 2), §3.3 렌더링(Task 2·6), §4 커맨드 4종(Task 6), §5 스킬(Task 7), §6 스크립트 3종(Task 3~5), §7 문서(Task 8), §8 수용 기준(Task 9), D1~D12 반영 확인.
- 플레이스홀더 없음(모든 코드·본문 명세 포함), 함수·CLI 시그니처 태스크 간 일치(conftest 픽스처명 = wiki_check/yt_transcript/pdf_chunk).
