# superdomain 도메인 집중 재편 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** superarchitect에서 아키텍처(스타일·레이어·모듈 구성)를 전부 들어내고 도메인(DDD·컨텍스트 경계·컨텍스트 간 의존)에 집중하는 superdomain으로 재편한다.

**Architecture:** SSOT를 `ARCHITECTURE.md`에서 `DOMAIN.md`로 재편하고, 파서 3층(parse_architecture→parse_style→resolve_rules)을 단층 `parse_domain.py`로 축소하며, 기계 검증은 컨텍스트 격리(`derived.context-isolation`) 하나만 남긴다. 스킬 10→8, 스크립트 8→6, 지식 18→12, 거버넌스 6→5. 개명(superarchitect→superdomain)은 모든 수술이 끝난 마지막 Phase에서 일괄 수행한다.

**Tech Stack:** Python 표준 라이브러리만(unittest, PyYAML·pytest 금지), Claude Code 플러그인 스펙(SKILL.md·agents·hooks), 한국어 문서.

**Spec:** `docs/superpowers/specs/2026-08-17-superdomain-refocus-design.md` — 이 계획의 유일한 요구사항 소스. 태스크가 스펙과 어긋나면 스펙이 이긴다.

## Global Constraints

- Python 표준 라이브러리만 쓴다. 테스트는 `python3 -m unittest discover -s tests`로 돈다. pytest 금지.
- SKILL.md는 500줄 이하, 절차 중심, 상세 지식은 references/로 (progressive disclosure).
- exit 규약: 파서류 1=해석 실패 / 검사기류 1=정상 판정 결과(위반 발견) / collect_signals 1=산출 불가 / 전 스크립트 2=사용법 오류.
- **유지 스크립트(check_invariants·collect_signals·build_index·session_summary)의 기존 테스트는 한 줄도 잃지 않는다** — import 재배선·픽스처 교체로만 조정한다.
- Phase 1~4에서는 기존 이름(`superarchitect` 마커·프리픽스)을 그대로 쓴다. 치환은 Phase 5 한 번뿐이다(D5).
- 하위 호환 계층 금지(YAGNI): 구 `ARCHITECTURE.md`·구 마커를 읽는 코드를 만들지 않는다.
- `docs/superpowers/`(스펙·계획·과거 기록)는 어떤 태스크에서도 수정·치환하지 않는다 — 역사 기록이다.
- 각 Phase 종료 시 검증 게이트: 전체 테스트 + 죽은 참조 grep(각 Phase 마지막 태스크에 명시).
- 커밋 메시지는 한국어, 기존 관례(`feat:`/`docs:`/`refactor:`/`test:` 접두)를 따른다.

## 실측 기준선 (2026-08-17)

- 테스트 386개: build_index 14 · check_imports 85 · check_invariants 82 · collect_signals 51 · parse_architecture 51 · parse_style 45 · resolve_rules 53 · session_summary 5.
- import 그래프: check_imports ← resolve_rules ← (parse_architecture, parse_style). check_invariants ← (check_imports, parse_architecture, resolve_rules). collect_signals ← resolve_rules(`resolve_document`, `KIND_CONTEXT_ISOLATION`).
- **스펙 §8과의 순서 차이 1건**: `test_parse_architecture.py`가 `profiles/`를 참조하므로(프로파일 라벨 검증), profiles/ 삭제를 Phase 1이 아니라 구 파서를 제거하는 Task 8로 옮긴다. 근거: 모든 태스크는 초록 상태로 끝나야 한다.

---

## Phase 1 — 의존받지 않는 것 삭제

### Task 1: fitness·scaffold 스킬 삭제

**Files:**
- Delete: `skills/fitness/` 전체, `skills/scaffold/` 전체

**Interfaces:**
- Consumes: 없음
- Produces: 이후 태스크는 두 스킬이 없다고 전제한다. 다른 파일에 남은 참조(README·스킬·지식 read_when)는 각자의 수술 태스크에서 제거한다.

- [ ] **Step 1: 삭제**

```bash
git rm -r skills/fitness skills/scaffold
```

- [ ] **Step 2: 테스트가 스킬을 참조하지 않음을 확인하고 전체 테스트 실행**

```bash
grep -rn "skills/fitness\|skills/scaffold" tests/ scripts/ ; python3 -m unittest discover -s tests
```

Expected: grep 0건, 386 tests OK.

- [ ] **Step 3: 커밋**

```bash
git commit -m "refactor: fitness·scaffold 스킬 삭제 — 아키텍처 전용 스킬 (superdomain 재편 Phase 1)"
```

### Task 2: 폐기 — Task 17로 병합됨

**실행하지 않는다.** Phase 1 실행 중 두 의존이 실측으로 드러났다:

1. `scripts/resolve_rules.py:41`의 `PRESET_STYLE_DIR`이 `references/knowledge/styles/`를 **런타임에 읽는다**(`:196`에서 프리셋 스타일 문서를 로드). `tests/test_parse_style.py:9`도 이 실디렉터리를 읽어 "정확히 4개"를 단언한다. 구 파서 층이 살아 있는 동안은 지울 수 없다 — 삭제 시 36 failures + 1 error.
2. `scripts/build_index.py:219-222`는 끊어진 위키링크를 하드 에러로 보고 **INDEX를 쓰지 않은 채 exit 1** 한다. 생존 DDD 12종이 삭제 대상을 가리키는 위키링크를 다수 갖고 있어(`[[hexagonal]]` 36건, `[[layered-simple]]` 25건, `[[layered-domain]]` 23건, `[[package-conventions]]` 17건 등) 삭제와 링크 정리를 갈라 놓으면 **초록으로 끝나는 경로가 없다**.

따라서 삭제·링크 정리·INDEX 재생성을 Task 17 한 묶음으로 옮긴다(구 파서가 사라진 Phase 4에서 실행). Phase 1은 Task 1로 끝난다.

---

## Phase 2 — 파서·검사기 재편

전략: **새 것을 옆에 세우고(Task 3~4), 소비자를 하나씩 갈아타게 한 뒤(Task 5~7), 구 층을 마지막에 제거한다(Task 8)**. 모든 태스크가 초록으로 끝난다.

### Task 3: `parse_domain.py` 신설 — 새 템플릿 파서

**Files:**
- Create: `scripts/parse_domain.py` (parse_architecture.py를 복사한 뒤 축소 수술 — 라벨 파싱·괄호 주석 제거·표 파싱·정규화·생성 구역 무시 로직을 재사용한다)
- Create: `tests/fixtures/domain/minimal.md`, `tests/fixtures/domain/full.md`
- Test: `tests/test_parse_domain.py` (신규)

**Interfaces:**
- Consumes: 없음 (독립 신설 — 구 모듈은 아직 건드리지 않는다)
- Produces (이후 모든 태스크가 소비하는 계약):

```python
# 마커 상수 — Phase 5 치환으로 superdomain이 된다
MARKER_TEMPLATE = "superarchitect:template"
TEMPLATE_VERSION = "v1"
CLASSIFICATIONS = ("core", "supporting", "generic")

@dataclass
class Relation:      # ### 관계 표 한 행
    partner: str; kind: str; contract: str; line: int

@dataclass
class Project:       # ## 프로젝트: <이름>
    name: str; line: int
    path: str | None = None          # - 경로:
    base_package: str | None = None  # - 기본 패키지:

@dataclass
class Context:       # ## 컨텍스트: <이름>
    name: str; line: int
    project: str | None = None       # - 프로젝트: (유일 프로젝트면 생략 가능)
    classification: str | None = None  # - 분류: core|supporting|generic
    patterns: list[str] = field(default_factory=list)   # - 패턴: 쉼표 목록
    packages: list[str] = field(default_factory=list)   # - 패키지: 쉼표 목록 (명시 시)
    relations: list[Relation] = field(default_factory=list)

@dataclass
class ParseError:    # 기존 parse_architecture의 것을 그대로 이관
    line: int; message: str

@dataclass
class Domain:
    projects: list[Project]; contexts: list[Context]
    errors: list[ParseError]

class LocatedError(Exception): ...          # resolve_rules에서 이관 (동일 시그니처)
def format_error(err) -> str: ...           # resolve_rules에서 이관

def parse_domain(path: Path) -> Domain      # 파싱 + validate까지 수행해 errors에 담는다
def context_packages(domain: Domain, context: Context) -> list[str]
    # 명시 `- 패키지:`가 있으면 그것, 없으면 [f"{base_package}.{context.name}.."]
    # 모든 패키지는 `..` 접미로 정규화된 접두 패턴이다
def isolation_allowlist(domain: Domain) -> dict[str, frozenset[str]]
    # 컨텍스트명 → 관계 표에 열린 상대 컨텍스트명 집합
```

- [ ] **Step 1: 새 픽스처 작성**

`tests/fixtures/domain/minimal.md`:

```markdown
# 샘플 — Domain
<!-- superarchitect:template v1 -->

## 프로젝트: backend
- 경로: .
- 기본 패키지: com.acme

## 컨텍스트: claim
- 분류: core
```

`tests/fixtures/domain/full.md` — 프로젝트 2개(경로 backend·batch), 컨텍스트 3개(claim: 패턴 cqrs·outbox + 명시 `- 패키지: com.acme.claiming..` + admin으로의 관계 1행 / admin: 분류 generic, 패키지 생략 / billing: `- 프로젝트: batch`, `- 패키지: com.acme.web.billing.., com.acme.batch.billing..` 복수 위치), 컨텍스트 맵 생성 구역 마커 포함. 구 템플릿의 스타일·모듈 표·규칙 예외·이행은 **넣지 않는다**.

- [ ] **Step 2: 실패하는 테스트 작성**

`tests/test_parse_domain.py` — 다음 골격으로 시작한다(대표 케이스. 이후 스텝에서 목록의 나머지를 채운다):

```python
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from parse_domain import parse_domain, context_packages, isolation_allowlist

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "domain"

class TestParseDomainMinimal(unittest.TestCase):
    def test_minimal_parses_without_errors(self):
        d = parse_domain(FIXTURES / "minimal.md")
        self.assertEqual(d.errors, [])
        self.assertEqual([c.name for c in d.contexts], ["claim"])

    def test_default_package_convention(self):
        d = parse_domain(FIXTURES / "minimal.md")
        self.assertEqual(context_packages(d, d.contexts[0]), ["com.acme.claim.."])

class TestParseDomainFull(unittest.TestCase):
    def test_explicit_and_multi_packages(self):
        d = parse_domain(FIXTURES / "full.md")
        by_name = {c.name: c for c in d.contexts}
        self.assertEqual(context_packages(d, by_name["claim"]), ["com.acme.claiming.."])
        self.assertEqual(len(context_packages(d, by_name["billing"])), 2)

    def test_isolation_allowlist_from_relations(self):
        d = parse_domain(FIXTURES / "full.md")
        self.assertIn("admin", isolation_allowlist(d)["claim"])

class TestParseDomainValidation(unittest.TestCase):
    def _parse_text(self, text):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(text)
        return parse_domain(Path(f.name))

    def test_unknown_relation_partner_is_error(self):
        text = (FIXTURES / "minimal.md").read_text() + \
            "\n### 관계\n| 상대 | 유형 | 계약 |\n|---|---|---|\n| ghost | conformist | - |\n"
        d = self._parse_text(text)
        self.assertTrue(any("ghost" in e.message for e in d.errors))

    def test_style_label_is_rejected(self):
        text = (FIXTURES / "minimal.md").read_text() + "- 스타일: hexagonal\n"
        d = self._parse_text(text)
        self.assertTrue(any("스타일" in e.message for e in d.errors))
```

- [ ] **Step 3: 실패 확인**

```bash
python3 -m unittest tests.test_parse_domain -v
```

Expected: FAIL — `No module named 'parse_domain'`.

- [ ] **Step 4: parse_domain.py 구현**

`cp scripts/parse_architecture.py scripts/parse_domain.py` 후 수술한다.

**제거하는 것(식별자 기준 — 남으면 게이트 grep에 걸린다):** `스타일`·`모듈 구성`·`프로파일`·`아키텍처 테스트 위치`·`규칙 예외`·`이행` 라벨 파싱과 검증, 모듈 표·애플리케이션 표·공용 모듈 표·패키지 규약 표 파싱(`Module`·`Application`·`SharedModule`·`RuleException` 데이터클래스와 그 필수 검증), `PRESET_STYLES`, app-embedded 전용 검증(`## 3` 관련), 구조 다이어그램 생성 구역 상수.

**유지하는 것:** 섹션·라벨·표 공통 파싱 루프, 괄호 주석 제거, `NormalizedPattern`·`normalize`, 생성 구역 마커 무시, 프로젝트·컨텍스트 필수 라벨 검증(필수 = 프로젝트: `경로`·`기본 패키지` / 컨텍스트: `분류`), `분류` 정규 값 검증, 관계 표 파싱, 이름 중복 검증, 템플릿 버전 마커 검증(버전 초과 시 거부 — 침묵하지 않는다).

**추가하는 것:**

```python
def _parse_packages(raw: str, line: int, errors) -> list[str]:
    """`- 패키지:` 값을 쉼표로 갈라 `..` 접미 접두 패턴으로 정규화한다.
    `..`가 없으면 붙이고, 빈 항목·중복 항목은 ParseError."""

def context_packages(domain, context) -> list[str]:
    """명시 packages가 있으면 그대로, 없으면 귀속 프로젝트의
    base_package로 [f"{base}.{context.name}.."]. base_package가 없으면 LocatedError."""

def isolation_allowlist(domain) -> dict[str, frozenset[str]]:
    """관계 표에서 컨텍스트별 열린 상대 집합. **허용 단위는 쌍이고 방향을 구분하지 않는다** —
    한 줄을 쓰면 그 쌍의 참조가 양방향으로 열리고, 유형은 허용 방향을 바꾸지 않는다.
    정본은 context-mapping.md 37·114행과 구 resolve_rules._relation_partners(양방향 등록)."""
```

**이관하는 것:** `resolve_rules.py`의 `LocatedError`·`format_error`를 parse_domain.py로 복사한다(resolve_rules는 아직 살아 있으므로 원본은 건드리지 않는다 — Task 8에서 삭제).

**validate에 추가:** 관계 표의 상대가 선언된 컨텍스트가 아니면 오류. 컨텍스트 `패키지` 패턴이 다른 컨텍스트와 겹치면(한쪽이 다른 쪽의 접두) 오류 — 귀속이 모호해진다. **퇴역 라벨 명시 거부** — 구 파서는 알 수 없는 라벨을 침묵으로 무시했지만, parse_domain은 퇴역 라벨 6종(`스타일`·`모듈 구성`·`규칙 예외`·`이행`·`프로파일`·`아키텍처 테스트 위치`)을 만나면 "구 템플릿의 라벨입니다 — domain-template.md 참조" 오류를 낸다(구 문서 오용을 침묵으로 놓치지 않는다). 그 외 알 수 없는 라벨은 기존대로 무시한다.

- [ ] **Step 5: Step 2 골격의 `...` 케이스를 포함해 테스트를 채우고 통과 확인**

케이스 목록(각각 테스트 1개 이상): minimal·full 파싱, 기본값 규약, 명시·복수 패키지, allowlist, 상대 미존재 오류, 구 라벨(스타일·모듈 구성·규칙 예외·이행) 거부, 분류 비정규 값 오류, 필수 라벨 누락 오류, 패키지 접두 겹침 오류, 버전 초과 거부, 괄호 주석 제거, 이름 중복 오류, CLI exit 규약(0=OK·1=해석 오류·2=사용법).

```bash
python3 -m unittest tests.test_parse_domain -v && python3 -m unittest discover -s tests
```

Expected: 신규 전부 PASS + 기존 386 OK (구 모듈 무수정).

- [ ] **Step 6: 커밋**

```bash
git add scripts/parse_domain.py tests/test_parse_domain.py tests/fixtures/domain/
git commit -m "feat: parse_domain.py — DOMAIN.md 템플릿 파서 신설 (패키지 라벨·격리 allow-list)"
```

### Task 4: `check_imports.py` 축소 — 컨텍스트 격리 전용

**Files:**
- Modify: `scripts/check_imports.py`
- Test: `tests/test_check_imports.py` (레이어 테스트 삭제, 격리·baseline 테스트는 새 픽스처로 재작성)

**Interfaces:**
- Consumes: `parse_domain.parse_domain`, `context_packages`, `isolation_allowlist`, `LocatedError`, `format_error`
- Produces: `SKIP_DIRS`, `SOURCE_SUFFIXES`, `SRC_DIR` (check_invariants가 계속 import — 이름·값 불변), CLI `python3 scripts/check_imports.py <DOMAIN.md>` (0=위반 없음, 1=위반, 2=해석 불가), baseline.jsonl 소비 계약 불변

- [ ] **Step 1: 실패하는 테스트 먼저 — 새 동작의 대표 케이스를 작성**

기존 `tests/test_check_imports.py`에서 **레이어 규칙 테스트(85개 중 스타일·레이어·앱·공용 모듈·@Entity 격리 관련)를 삭제**하고, 다음 계열로 재구성한다(각 계열에 실제 테스트를 작성 — 임시 디렉터리에 DOMAIN.md와 .kt/.java 소스를 만들어 검사):

```python
class TestContextIsolation(unittest.TestCase):
    def test_cross_context_import_without_relation_is_violation(self):
        # com.acme.claim의 소스가 com.acme.admin.X를 import, 관계 없음 → 위반 1건
    def test_cross_context_import_with_relation_passes(self):
        # 관계 표에 claim→admin 열림 → 위반 0건
    def test_same_context_import_passes(self): ...
    def test_import_outside_any_context_ignored(self):
        # java.util 등 어느 컨텍스트 패키지도 아닌 대상 → 무시
    def test_wildcard_import_matches_prefix(self): ...
    def test_explicit_multi_package_context(self):
        # 복수 위치 컨텍스트의 두 패키지 모두 귀속

class TestSilenceGuards(unittest.TestCase):
    def test_context_with_zero_sources_warns(self):
        # 소스 0건 컨텍스트 → "[0건 경고]" — 위반 아님, exit 0 유지

class TestBaseline(unittest.TestCase):
    def test_baselined_violation_not_reported(self): ...
    def test_new_violation_reported_despite_baseline(self): ...
```

- [ ] **Step 2: 실패 확인**

```bash
python3 -m unittest tests.test_check_imports -v
```

Expected: 새 케이스 FAIL (아직 resolve_rules 기반), 삭제한 케이스는 러너에서 사라짐.

- [ ] **Step 3: check_imports.py 수술**

**제거:** `from resolve_rules import ...` 일체, 레이어 규칙 핸들러 전부(`_context_isolation`을 제외한 규칙 디스패치, DOMAIN_LAYER·KIND_APP_CONFINEMENT 소비, @Entity 수집·confine 검사, 최상위 public 타입 네이밍 검사), 레이어 패턴 기반 컨텍스트 범위 계산.

**대체:** 파일 귀속을 `context_packages`의 접두 패턴으로 한다 — 소스의 `package` 선언이 어느 컨텍스트 패턴에 매칭되는지(최장 일치). import 대상도 같은 방식으로 귀속. 서로 다른 컨텍스트이고 `isolation_allowlist`에 그 쌍이 없으면 위반. 보고 형식·JSON 출력·baseline.jsonl 소비(위반 지문 대조)·`[0건 경고]`는 기존 코드를 유지한다.

```python
from parse_domain import (LocatedError, context_packages, format_error,
                          isolation_allowlist, parse_domain)

def _owning_context(package: str, scopes: list[tuple[str, list[str]]]) -> str | None:
    """package가 매칭되는 컨텍스트명. 접두 최장 일치, 없으면 None."""
```

- [ ] **Step 4: 통과 확인 + 전체 테스트**

```bash
python3 -m unittest tests.test_check_imports -v && python3 -m unittest discover -s tests
```

Expected: check_imports 신규 전부 PASS. **check_invariants 82개도 OK** — `SKIP_DIRS`·`SOURCE_SUFFIXES`·`SRC_DIR` 계약을 지켰다면 깨지지 않는다(check_invariants의 parse_architecture 의존은 Task 5에서 처리하므로 이 시점에는 아직 구 픽스처로 돈다).

- [ ] **Step 5: 커밋**

```bash
git add scripts/check_imports.py tests/test_check_imports.py
git commit -m "refactor: check_imports를 컨텍스트 격리 전용으로 축소 — parse_domain 소비, baseline·0건 경고 유지"
```

### Task 5: `check_invariants.py` 재배선

**Files:**
- Modify: `scripts/check_invariants.py:41-46` (import 3줄), 문서 경로 기본값(`docs/architecture/domain/` → `docs/domain/`)
- Test: `tests/test_check_invariants.py` (픽스처의 ARCHITECTURE.md 문서를 DOMAIN.md 템플릿으로 교체, 테스트 로직 무수정)

**Interfaces:**
- Consumes: `parse_domain.parse_domain`, `parse_domain.LocatedError`, `parse_domain.format_error`, `check_imports.SKIP_DIRS/SOURCE_SUFFIXES/SRC_DIR`
- Produces: CLI 계약 불변 (0=위반 없음, 1=위반·검사 불능, 2=해석 불가), `@Tag("INV-...")` 대조·`검사 불능` 판정 불변

- [ ] **Step 1: import 재배선과 경로 변경**

```python
from check_imports import SKIP_DIRS, SOURCE_SUFFIXES, SRC_DIR   # 불변
from parse_domain import LocatedError, format_error, parse_domain
```

`parse_architecture(...)` 호출부를 `parse_domain(...)`으로, 도메인 문서 탐색 경로를 `docs/domain/`으로 바꾼다. 판정 로직(confirmed 대조·태그 리터럴 수집·검사 불능)은 한 줄도 바꾸지 않는다.

- [ ] **Step 2: 테스트 픽스처 교체**

`tests/test_check_invariants.py`가 임시로 만드는 SSOT 문서 내용을 새 템플릿(Task 3의 minimal.md 형태 + 도메인 문서는 `docs/domain/<컨텍스트>.md`)으로 바꾼다. **테스트 수와 assert는 그대로 82개** — 문서 문법만 갈아탄다.

- [ ] **Step 3: 통과 확인 + 전체 테스트 + 커밋**

```bash
python3 -m unittest tests.test_check_invariants -v && python3 -m unittest discover -s tests
git add scripts/check_invariants.py tests/test_check_invariants.py
git commit -m "refactor: check_invariants를 parse_domain·docs/domain으로 재배선 — 판정 로직 무수정"
```

Expected: 82개 그대로 OK.

### Task 6: `collect_signals.py` 재배선

**Files:**
- Modify: `scripts/collect_signals.py:75` 및 귀속 로직
- Test: `tests/test_collect_signals.py` (픽스처 문서 교체, 테스트 51개 유지)

**Interfaces:**
- Consumes: `parse_domain.parse_domain`, `context_packages`, `format_error`
- Produces: CLI·JSON payload 계약 불변(contexts·unattributed·hotspots·cochanges), "관측만 하고 임계값 없음" 원칙 불변

- [ ] **Step 1: 귀속(attribution) 재구현**

`from resolve_rules import ... resolve_document`를 제거하고, 파일→컨텍스트 귀속을 패키지 경로형 매칭으로 바꾼다:

```python
def _package_as_path(pkg: str) -> str:
    """'com.acme.claim..' → 'com/acme/claim/' (접미 `..` 제거 후 경로형)."""

def _attribute(path: str, scopes: list[tuple[str, list[str]]]) -> str | None:
    """변경 파일 경로에 컨텍스트 패키지의 경로형이 포함되면 그 컨텍스트로 귀속.
    복수 매칭이면 최장 일치. 없으면 미귀속(unattributed) — 기존 의미 유지."""
```

- [ ] **Step 2: 픽스처 교체 후 통과 확인 + 전체 테스트 + 커밋**

테스트가 만드는 SSOT 문서·디렉터리 구조를 새 템플릿·패키지 경로형에 맞춘다. 51개 유지.

```bash
python3 -m unittest tests.test_collect_signals -v && python3 -m unittest discover -s tests
git add scripts/collect_signals.py tests/test_collect_signals.py
git commit -m "refactor: collect_signals 귀속을 패키지 경로형 매칭으로 재배선 — 관측 전용 원칙 유지"
```

### Task 7: `session_summary.sh` 경로 변경

**Files:**
- Modify: `scripts/session_summary.sh` (`docs/architecture/summary.md` → `docs/domain/summary.md`)
- Test: `tests/test_session_summary.py` (경로 문자열만 교체, 5개 유지)

- [ ] **Step 1: 경로 교체 후 테스트 + 커밋**

```bash
python3 -m unittest tests.test_session_summary -v && python3 -m unittest discover -s tests
git add scripts/session_summary.sh tests/test_session_summary.py
git commit -m "refactor: 세션 훅 요약 경로를 docs/domain/summary.md로 변경"
```

### Task 8: 구 파서 3층·profiles·구 픽스처 일괄 삭제 — Phase 2 게이트

**Files:**
- Delete: `scripts/parse_architecture.py`, `scripts/parse_style.py`, `scripts/resolve_rules.py`, `tests/test_parse_architecture.py`, `tests/test_parse_style.py`, `tests/test_resolve_rules.py`, `tests/fixtures/styles/` 전체, `tests/fixtures/minimal.md`, `tests/fixtures/full.md`(구 템플릿 픽스처 — 신 픽스처는 `tests/fixtures/domain/`), `profiles/` 전체

- [ ] **Step 1: 아무도 import하지 않음을 확인**

```bash
grep -rn "parse_architecture\|parse_style\|resolve_rules" scripts/ tests/ --include="*.py" | grep -v "test_parse_architecture\|test_parse_style\|test_resolve_rules"
```

Expected: 0건 (Task 4~6에서 전부 재배선됨).

- [ ] **Step 2: 삭제**

```bash
git rm scripts/parse_architecture.py scripts/parse_style.py scripts/resolve_rules.py
git rm tests/test_parse_architecture.py tests/test_parse_style.py tests/test_resolve_rules.py
git rm -r tests/fixtures/styles profiles
git rm tests/fixtures/minimal.md tests/fixtures/full.md
```

- [ ] **Step 3: Phase 2 검증 게이트**

```bash
python3 -m unittest discover -s tests 2>&1 | tail -3
grep -rn "resolve_rules\|parse_style\|parse_architecture\|profiles/" scripts/ tests/ hooks/
```

Expected: 테스트 전부 OK(대략 289±α — 386 − parse_style 45 − resolve_rules 53 − parse_architecture 51 + parse_domain 신규 − check_imports 감소분. **실측값을 README 갱신 태스크(Task 18)를 위해 기록해 둔다**), grep 0건.

- [ ] **Step 4: 커밋**

```bash
git commit -m "refactor: 구 파서 3층·profiles·구 픽스처 삭제 — 단층 parse_domain으로 전환 완료"
```

---

## Phase 3 — 스킬 8개 수술

공통 규율: 각 스킬의 뼈대(게이트·인터뷰 규율·append 규칙·확정은 사용자만)는 유지한다. 수술 후 각 태스크는 **게이트 grep**을 통과해야 한다:

```bash
grep -n "스타일\|레이어\|모듈 구성\|fitness\|scaffold\|프로파일\|resolve_rules\|parse_style\|parse_architecture\|ARCHITECTURE\.md\|규칙 예외\|아키텍처 테스트" skills/<스킬>/SKILL.md
```

Expected: 0건. (문맥상 정당한 잔존 — 예: "이 플러그인은 아키텍처 스타일을 다루지 않는다"는 안내 문장 — 은 허용하되 커밋 메시지에 사유를 남긴다.)

### Task 9: `model` + `apply` 수술 (소)

**Files:**
- Modify: `skills/model/SKILL.md` — `docs/architecture/domain/` → `docs/domain/`, `ARCHITECTURE.md` → `DOMAIN.md` 경로 참조만 교체. 세 모드(인터뷰·이벤트 스토밍·미팅 정리)·proposed/confirmed 승격 규율 무수정.
- Modify: `skills/apply/SKILL.md` — ① 경로 교체(위와 동일) ② 프로파일 참조 절을 다음 원칙으로 대체: "언어·빌드 도구·테스트 관례는 대상 코드베이스에서 감지한다 — 빌드 파일(build.gradle.kts·pom.xml)과 기존 테스트의 import·assert 관례를 먼저 읽고 그에 맞춘다. 감지가 불가능하면(테스트 소스 0건) 사용자에게 묻는다." ③ `@Tag("INV-...")` 규약·inside-out 순서·proposed 불가침·check_invariants 게이트 무수정.

- [ ] **Step 1: 수술** (위 지시대로)
- [ ] **Step 2: 게이트 grep 2종 + 전체 테스트**

```bash
grep -n "스타일\|레이어\|모듈 구성\|fitness\|scaffold\|프로파일\|ARCHITECTURE\.md\|규칙 예외" skills/model/SKILL.md skills/apply/SKILL.md
python3 -m unittest discover -s tests
```

- [ ] **Step 3: 커밋**

```bash
git add skills/model skills/apply && git commit -m "refactor(skills): model·apply — docs/domain 경로 전환, apply 프로파일 참조를 코드베이스 감지로 대체"
```

### Task 10: `adr` + `evolve` 수술 (소)

**Files:**
- Modify: `skills/adr/SKILL.md` — MADR·accepted/superseded 양방향 링크 무수정. "결정이 기계 규칙을 함의하면 규칙 예외·스타일 선언·어휘 확장 중 어디로 가는지" 절을 "결정이 SSOT 변경을 함의하면 관계 표 변경·분류 변경·패키지 라벨 변경 중 어디로 가는지"로 대체. `ARCHITECTURE.md` → `DOMAIN.md`.
- Modify: `skills/evolve/SKILL.md` — collect_signals 소비·evolution-signals.md 임계값 적용·proposed ADR 초안·수락된 제안만 반영 구조 무수정. 제안 유형에서 "스타일 변경·이행 제안"을 제거하고 경계 재획정·분류 변경·관계 추가/삭제만 남긴다. resolve_rules 언급 제거.

- [ ] **Step 1: 수술** → **Step 2: 게이트 grep(공통 패턴, 두 파일) + 전체 테스트** → **Step 3: 커밋**

```bash
git add skills/adr skills/evolve && git commit -m "refactor(skills): adr·evolve — 기계 규칙 연결을 도메인 결정(관계·분류·패키지)으로 재정의"
```

### Task 11: `review` 수술 + `domain-reviewer` 개명 (중)

**Files:**
- Modify: `skills/review/SKILL.md`
- Rename+Modify: `agents/arch-reviewer.md` → `agents/domain-reviewer.md`

**review 수술:** 구조(결정적 검사 먼저 → 의미론만 위임 → review-log.jsonl append) 무수정. 결정적 검사 체인을 `check_imports.py`(컨텍스트 격리)+`check_invariants.py` 둘로 재정의 — fitness 생성 테스트·resolve_rules 언급 제거. 위임 대상을 `domain-reviewer`로. **`inherited` 채널 정리** — `skills/review/SKILL.md:165`의 JSON 키 목록에서 `inherited`를 빼고, `:176`의 `| 승계 경고 | ARCHITECTURE.md:<줄>: … (공허 레이어) | 그대로 승계 |` 행을 삭제한다(레이어 소멸로 영원히 비는 자리다).

**domain-reviewer 재정의:** `git mv agents/arch-reviewer.md agents/domain-reviewer.md`. 읽기 전용·"전달받은 지식 문서의 규칙 절로만 판정" 구조 유지(전달원은 이제 strategic·tactical·patterns 12종). 자유 관측 5범주를 다음으로 교체:

1. **경계 누수** — 다른 컨텍스트의 내부 모델·테이블을 직접 사용 (관계 표의 계약을 우회)
2. **유비쿼터스 언어 불일치** — 코드 명명이 도메인 문서 용어와 어긋남
3. **애그리거트 우회** — 루트를 거치지 않는 비루트 엔티티 직접 조작·조회
4. **불변식 후보** — 코드에 숨은 업무 규칙 중 도메인 문서에 없는 것 (proposed 승격 신호)
5. **관계 유형 위반** — 선언(예: customer-supplier)과 실제 결합 방향의 불일치

- [ ] **Step 1: 수술** → **Step 2: 게이트 grep(두 파일) + `grep -rn "arch-reviewer" skills/ agents/ hooks/` 0건 확인 + 전체 테스트** → **Step 3: 커밋**

```bash
git add -A && git commit -m "refactor(skills): review 결정적 검사 체인 재정의, arch-reviewer→domain-reviewer 개명·도메인 관측 5범주"
```

### Task 12: `sync` 수술 (중)

**Files:**
- Modify: `skills/sync/SKILL.md`

**수술:** ① §1 "선언을 읽는다"의 두 실행을 `parse_domain.py`(게이트)+`check_imports.py`로 교체. ② §2-b "관측 — 빌드 모듈" 삭제(모듈 개념 소멸), §2-c 패키지 인벤토리는 유지. ③ 대조 축 6→5: §3-c "레이어 매핑 불일치" 삭제. §3-a는 "선언된 컨텍스트의 패키지가 디스크에 없다", §3-b는 "선언 밖 패키지가 컨텍스트 후보로 보인다"로 재정의. §3-d에서 스타일 참조 검사 제거(깨진 ADR 참조는 유지). §3-e(파생물 낡음 — summary·컨텍스트 맵)·§3-f(해석 오류) 유지. ④ §4 처분 네 선택지에서 "scaffold로 생성"을 "패키지 직접 생성(빈 패키지·최소 스텁을 이 스킬이 직접 만든다)"으로 대체, §5-b scaffold 위임 절 삭제. ⑤ 확인 없이 확정하지 않음·"대조하지 않음≠0건" 규율 무수정.

- [ ] **Step 1: 수술** → **Step 2: 게이트 grep + 전체 테스트** → **Step 3: 커밋**

```bash
git add skills/sync && git commit -m "refactor(skills): sync 대조 축 6→5 — 레이어 축 제거, scaffold 처분을 직접 생성으로 대체"
```

### Task 13: `migrate` 수술 (중)

**Files:**
- Modify: `skills/migrate/SKILL.md`

**수술:** ① 부채 종류가 컨텍스트 격리 위반 하나 — 클러스터 정의를 "컨텍스트 쌍(A↔B) 단위"로 재정의(**허용 단위는 쌍이고 방향 구분이 없다**). ② `이행` 라벨 연동 제거 — 활성 조건은 **`docs/domain/baseline.jsonl` 존재**(경로 이관 확정 — Task 4에서 `check_imports.BASELINE_RELATIVE`가 이미 이 값이다. init·migrate·check_imports 세 지점이 같은 경로를 봐야 한다). ⑥ **`inherited[]`·「승계 경고」 행 삭제** — `skills/migrate/SKILL.md:108`의 `inherited[]`(공허 레이어 승계 경고) 언급을 지운다. 그 채널은 레이어 소멸로 영원히 빈 목록이며, 남겨두면 리포트에 채워지지 않는 자리가 생긴다. ③ 상환 검증에서 fitness 테스트 재생성 단계를 `check_imports.py` 재실행으로 대체. ④ "한 번에 한 클러스터·삭제 근거는 실측된 해소뿐" 규율 무수정. ⑤ 완료 처리: "빈 파일·`이행` 라벨·완료 ADR 한 묶음"에서 라벨을 빼고 "baseline.jsonl 삭제 + 완료 ADR"로.

- [ ] **Step 1: 수술** → **Step 2: 게이트 grep + 전체 테스트** → **Step 3: 커밋**

```bash
git add skills/migrate && git commit -m "refactor(skills): migrate — 격리 위반 부채 전용, 이행 라벨 연동을 baseline 존재 기반으로"
```

### Task 14: `init` 수술 (대) — Phase 3 게이트

**Files:**
- Modify: `skills/init/SKILL.md`

**수술:** ① §2 거버넌스 후보 감지의 기준을 "프로파일 매칭"에서 "kt/java 소스 존재"로. ② §4 기존 코드 스캔에서 "실현 형태(모듈 구성) 추정"·"세 표 도출" 삭제, 대신 "패키지 구조에서 컨텍스트 후보 추정 — `{기본 패키지}` 바로 아래 패키지들을 후보로 제시하고 사용자가 확정"으로 대체. ③ §5 인터뷰: 5-a 경계·5-b 분류·5-e 관계 유지, **5-c 스타일·5-d 모듈 구성 삭제**, 새 5-c "패키지 — 규약 기본값과 다른 컨텍스트만 명시"를 추가. "모델이 혼자 정했다면 되돌아간다" 규율 유지. ④ §6 산출을 `DOMAIN.md`로, 파서 게이트를 `python3 scripts/parse_domain.py DOMAIN.md`로. "이행 선언" 절 삭제. ⑤ "baseline 동결" 절 재정의: 브라운필드에서 `check_imports.py` 실측 → 위반 > 0이면 동결 여부를 **사용자에게 질문** → 동결 시 **`docs/domain/baseline.jsonl`** 생성(경로 이관 확정 — `check_imports.BASELINE_RELATIVE`와 migrate가 같은 값을 본다). ⑥ §7 파생물: **`docs/domain-summary.md`**(요약 — `docs/domain/` **밖**이다. 안에 두면 `check_invariants._discover`가 컨텍스트 문서로 오인해 매 실행 거짓 경고를 낸다) + 컨텍스트 맵 생성 구역. 구조 다이어그램 생성 절 삭제. ⑦ 지식 참조 프로토콜의 대상을 strategic 문서들(bounded-contexts·domain-classification·context-mapping·event-storming)로 갱신.

- [ ] **Step 1: 수술** → **Step 2: 게이트 grep + 전체 테스트**
- [ ] **Step 3: Phase 3 검증 게이트 — 스킬·에이전트 전체 죽은 참조 스캔**

```bash
grep -rn "fitness\|scaffold\|스타일\|레이어\|모듈 구성\|프로파일\|resolve_rules\|parse_style\|parse_architecture\|ARCHITECTURE\.md\|arch-reviewer\|규칙 예외\|docs/architecture" skills/ agents/ hooks/
```

Expected: 0건 (정당한 잔존은 사유 기록).

- [ ] **Step 4: 커밋**

```bash
git add skills/init && git commit -m "refactor(skills): init — 인터뷰에서 스타일·모듈 구성 제거, DOMAIN.md 산출·실측 기반 baseline 동결"
```

---

## Phase 4 — 거버넌스·지식·README

### Task 15: `domain-template.md` 재작성 + `rule-vocabulary.md` 흡수·삭제

**Files:**
- Create: `references/governance/domain-template.md`
- Delete: `references/governance/architecture-template.md`, `references/governance/rule-vocabulary.md`

**새 문서 구성(정본 — Task 3에서 구현한 파서가 이 문서의 유일한 해석기다):**

1. **§1 개요** — DOMAIN.md의 성격: 도메인 결정의 SSOT, 파서가 유일한 해석기, 자유 서술은 파서가 무시.
2. **§2 템플릿 스켈레톤** — 그대로 복사해 `parse_domain.py`를 통과하는 완본(Task 3의 full.md와 동형: 프로젝트 2·컨텍스트 3·명시/복수 패키지·관계 표·생성 구역). **작성 후 실제로 파서에 통과시켜 검증한다(Step 2).**
3. **§3 라벨·표 사전** — 프로젝트(경로·기본 패키지), 컨텍스트(프로젝트·분류·패턴·패키지), 관계 표 3열(상대·유형·계약)과 6종 유형, 괄호 주석 규칙, 생성 구역 마커 2종(template 버전·context-map).
4. **§4 파싱 계약** — 필수 라벨, 정규 값, 오류 목록(상대 미존재·패키지 접두 겹침·구 라벨 거부·버전 초과 거부), exit 규약.
5. **§5 컨텍스트 격리 규칙과 baseline** (rule-vocabulary에서 흡수) — `derived.context-isolation` 정의(관계 표 = allow-list, **허용 단위는 쌍이고 방향 구분 없음** — 유형이 방향 해석을 바꾸지 않는다. context-mapping.md 37·114행과 정합), **컨텍스트 이름은 유효한 패키지 세그먼트여야 한다**(규약 기본값을 쓰는 컨텍스트에 한함 — 아니면 매칭 0건 패턴이 조용히 통과한다), 패키지 규약 기본값 `{기본 패키지}.{컨텍스트}..`, baseline.jsonl 문법(위반 지문 필드 — 기존 rule-vocabulary §의 해당 정의를 그대로 이관)·동결(init)/소비(check_imports)/축소(migrate) 경로.
6. **§6 버전 관리** — 마커 버전 규칙(초과 버전 거부, 침묵하지 않음).
7. **§7 관련 문서** — domain-doc-template·adr-template·evolution-signals·knowledge-doc-template.

- [ ] **Step 1: 작성** (rule-vocabulary.md의 context-isolation·baseline 정의를 먼저 읽고 이관한다)
- [ ] **Step 2: 스켈레톤 실측 검증**

```bash
sed -n '/```markdown/,/```/p' references/governance/domain-template.md | sed '1d;$d' > /tmp/skeleton-check.md
python3 scripts/parse_domain.py /tmp/skeleton-check.md; echo "exit=$?"
```

Expected: exit=0. (§2 완본 블록이 실제로 파서를 통과한다 — "그대로 복사해 쓸 수 있다"의 실측.)

- [ ] **Step 3: 구 문서 삭제 + 전체 테스트 + 커밋**

```bash
git rm references/governance/architecture-template.md references/governance/rule-vocabulary.md
python3 -m unittest discover -s tests
git add references/governance/domain-template.md
git commit -m "docs(governance): domain-template.md 정본 신설 — 결정 템플릿 재편, rule-vocabulary 흡수·삭제"
```

### Task 16: 잔여 거버넌스 3종 손질

**Files:**
- Modify: `references/governance/domain-doc-template.md` — 위치 절(§2)의 경로 **세 개를 전부** 새 값으로: 기본 `docs/architecture/domain/<컨텍스트>.md` → **`docs/domain/<컨텍스트>.md`**, 통합 배치 `docs/architecture/DOMAIN.md` → **`docs/domain.md`**(루트 SSOT `DOMAIN.md`와 이름이 겹치지 않게 — "나누면 디렉터리, 합치면 파일 하나"), 그리고 세션 요약이 **`docs/domain-summary.md`**로 `docs/domain/` 밖에 있음을 명시(그 디렉터리의 `*.md`는 전부 컨텍스트 문서로 읽힌다). ARCHITECTURE.md 참조 → DOMAIN.md. 파싱 계약·절별 규칙 무수정. **이 셋은 `check_invariants.py`의 `DOMAIN_SUBDIR`·`CONSOLIDATED_DOC`·`session_summary.sh`와 정확히 일치해야 한다.**
- Modify: `references/governance/evolution-signals.md` — 스타일 이행 관련 임계값·해석 절 삭제. 경계 재획정·공변경·핫스팟 해석 유지. 참조하는 스킬 목록에서 fitness·scaffold 제거.
- Modify: `references/governance/adr-template.md` — 후속 연결 예시에서 "규칙 예외·스타일 선언" → "관계 표·분류·패키지 라벨" (Task 10의 adr 수술과 정합).

- [ ] **Step 1: 수술** → **Step 2: 게이트 grep + 전체 테스트** → **Step 3: 커밋**

```bash
grep -rn "스타일\|레이어\|fitness\|scaffold\|ARCHITECTURE\.md\|docs/architecture\|규칙 예외\|rule-vocabulary" references/governance/
git add references/governance && git commit -m "docs(governance): 잔여 3종 손질 — 경로 전환·스타일 이행 해석 절제"
```

### Task 17: styles·structure 6종 삭제 + DDD 12종 손질 + INDEX 재생성

**Task 2가 여기로 병합됐다** — 삭제·위키링크 정리·INDEX 재생성이 한 커밋에서 끝나야 초록이다(Task 2의 폐기 사유 참조). 이 태스크는 **한 커밋**으로 낸다.

**Files:**
- Delete: `references/knowledge/styles/` 전체(clean·hexagonal·layered-domain·layered-simple), `references/knowledge/structure/` 전체(module-composition·package-conventions)
- Modify: `references/knowledge/strategic/*.md`(4), `references/knowledge/tactical/*.md`(5), `references/knowledge/patterns/*.md`(3), `references/INDEX.md`(재생성)

**선행 조건 확인:** Task 8에서 `resolve_rules.py`·`parse_style.py`·`test_parse_style.py`가 삭제됐어야 한다. 남아 있으면 이 태스크는 실행하지 않는다.

```bash
ls scripts/resolve_rules.py scripts/parse_style.py tests/test_parse_style.py 2>&1   # 전부 No such file 이어야 한다
```

**수술 3종:**

1. **삭제** — `git rm -r references/knowledge/styles references/knowledge/structure`.
2. **끊어진 위키링크 정리** — 생존 12종 본문에서 삭제된 6개 key를 가리키는 `[[...]]`를 없앤다. 대상 key: `hexagonal`·`clean`·`layered-domain`·`layered-simple`·`module-composition`·`package-conventions`. **대괄호만 벗기지 말고 문장을 도메인 언어로 고친다** — 예: "[[hexagonal]]에서는 포트를 도메인이 소유한다" → "도메인이 자신이 필요로 하는 인터페이스를 소유한다". 문장 전체가 스타일 선택에만 의미가 있으면 그 문장·절을 지운다. 생존 key끼리의 링크(`[[aggregates]]` 등)는 그대로 둔다.
3. **frontmatter `read_when`** — 죽은 스킬 `fitness`·`scaffold`만 제거(migrate는 살아 있으므로 유지). 실측 대상 7파일: bounded-contexts, domain-classification, context-mapping, persistence, event-sourcing, cqrs, outbox.
4. **본문 표현 완화** — 레이어 전제 표현을 도메인 언어로. 집중 대상은 실측된 두 파일: `persistence.md`("어댑터 봉쇄"→"영속 코드 격리", "domain 레이어"→"도메인 모델" 계열) · `repositories-domain-services.md`. **`## 적용 기준`·`## 규칙` 절 구조와 판정 내용은 유지한다 — 표현 수술이지 재작성이 아니다.**

- [ ] **Step 1: 선행 조건 확인 후 삭제·수술**

- [ ] **Step 2: INDEX 재생성 + 게이트 + 전체 테스트**

```bash
python3 scripts/build_index.py            # exit 0이어야 한다 — 끊어진 링크가 하나라도 남으면 exit 1
grep -c "^| " references/INDEX.md          # 헤더 1행 + 데이터 12행 = 13
grep -rn "styles/\|structure/\|fitness\|scaffold\|hexagonal\|layered\|레이어" references/knowledge/
python3 -m unittest discover -s tests
```

Expected: build_index exit 0 · INDEX 13행 · grep 0건(도메인 문맥상 정당한 "레이어" 잔존은 사유 기록) · 테스트 전부 OK.

- [ ] **Step 3: 커밋**

```bash
git add -A && git commit -m "docs(knowledge): styles·structure 6종 삭제, DDD 12종 손질 — 위키링크·read_when·레이어 표현 정리, INDEX 재생성"
```

### Task 18: README 재작성 — Phase 4 게이트

**Files:**
- Modify: `README.md` (전면 재작성)

**새 구성(기존 README의 골격을 유지하되 내용 교체):** ① 정체성 한 단락 — "문서 기반 **도메인 거버넌스**(DDD) 플러그인. 구조의 진실은 `DOMAIN.md`, 파서가 유일한 해석기." ② 설치(기존 명령 유지 — 개명은 Task 20에서). ③ 워크플로 — 루프 2개로 재편한 mermaid: **도메인 루프**(model→apply, dom SSOT·check_invariants 게이트)와 **유지 루프**(sync / evolve→migrate), 그리고 루프 밖 init(SSOT 생성)·review(경계 검사)·adr. ④ "언제 어느 스킬을"(8항목 — fitness·scaffold 행 삭제, scaffold 행이 하던 "새 컨텍스트 올리기"는 sync의 직접 생성으로 안내). ⑤ 산출물 표 — 스킬 8·에이전트 domain-reviewer·훅·스크립트 6·거버넌스 5·지식 12·study. ⑥ 직접 실행 명령 4종(`parse_domain.py`·`check_imports.py`·`check_invariants.py`·`collect_signals.py`)과 exit 규약 차이 설명(기존 문단 재사용). ⑦ 테스트 절 — **Task 8에서 기록한 실측 테스트 수**로 갱신. ⑧ 문서 예시 표 — domain-template §2·domain-doc-template §3·(profiles 행 삭제). ⑨ 지식 추가 절차(무수정에 가까움 — topic 예시에서 styles·structure 제거). ⑩ 저장소 구조 트리 갱신.

- [ ] **Step 1: 재작성** → **Step 2: Phase 4 검증 게이트**

```bash
grep -rn "fitness\|scaffold\|profiles\|스타일\|레이어\|ARCHITECTURE\.md\|rule-vocabulary\|architecture-template\|arch-reviewer\|resolve_rules\|parse_style\|parse_architecture" README.md references/ skills/ agents/
python3 -m unittest discover -s tests
```

Expected: 0건 + 전체 OK.

- [ ] **Step 3: 커밋**

```bash
git add README.md && git commit -m "docs: README 재작성 — 도메인 집중 정체성, 루프 2개 워크플로, 산출물 갱신"
```

---

## Phase 5 — 일괄 개명

### Task 19: 저장소 내 문자열 치환 superarchitect → superdomain

**Files:**
- Modify: `superarchitect` 문자열이 남은 전 파일(실측 42개 언저리 — Step 1에서 재실측). 주요: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `scripts/parse_domain.py`(MARKER_TEMPLATE), 스킬 8종(`/superarchitect:` 프리픽스·마커), `agents/domain-reviewer.md`, `README.md`, `.claude/skills/study/SKILL.md`, `references/governance/*`, `tests/*`(마커가 든 픽스처).
- **제외:** `docs/superpowers/**` (역사 기록 — Global Constraints).

- [ ] **Step 1: 대상 재실측 후 치환**

```bash
grep -rl "superarchitect" . --exclude-dir=.git --exclude-dir=docs --exclude-dir=__pycache__ --exclude-dir=.pytest_cache | xargs sed -i '' 's/superarchitect/superdomain/g'
```

- [ ] **Step 2: 매니페스트 정리** — 치환으로 끝나지 않는 것을 손으로:

`.claude-plugin/plugin.json`: `description`을 "문서 기반 도메인 거버넌스(DDD) — 질문으로 도메인을 구체화하고, 사람과 Claude가 함께 읽는 문서로 고정하고, 컨텍스트 간 의존을 결정적으로 강제한다"로. `keywords`에서 `architecture`·`fitness-function` 제거, `ddd`·`context-mapping` 추가. `homepage`·`repository`는 새 URL(`https://github.com/Cho-D-YoungRae/superdomain`). `marketplace.json`의 description·keywords도 동형으로.

- [ ] **Step 3: 검증 — 치환 무결성 + 전체 테스트**

```bash
grep -rn "superarchitect" . --exclude-dir=.git --exclude-dir=docs --exclude-dir=__pycache__ --exclude-dir=.pytest_cache
python3 -m unittest discover -s tests
python3 -c "import json; [json.load(open(p)) for p in ('.claude-plugin/plugin.json', '.claude-plugin/marketplace.json')]"
```

Expected: grep 0건, 테스트 전부 OK(마커 상수와 픽스처가 함께 치환되므로), JSON 파싱 OK.

- [ ] **Step 4: 커밋**

```bash
git add -A && git commit -m "refactor!: superarchitect → superdomain 일괄 개명 — 마커·프리픽스·매니페스트"
```

### Task 20: 리포지토리·디렉터리 개명 + 설치 검증 — 최종 게이트

**⚠️ 이 태스크는 외부(GitHub)에 닿는다 — 각 스텝을 실행 전에 사용자에게 확인받는다.**

- [ ] **Step 1: 원격 push + GitHub 리포지토리 개명 (사용자 확인 후)**

```bash
git push origin main
gh repo rename superdomain --repo Cho-D-YoungRae/superarchitect --yes
git remote set-url origin https://github.com/Cho-D-YoungRae/superdomain.git
```

(구 URL은 GitHub이 리다이렉트한다.)

- [ ] **Step 2: 로컬 디렉터리 개명 — 사용자 안내**

세션의 cwd가 사라지므로 **사용자가 직접 실행**하도록 안내만 한다:

```bash
mv ~/Projects/superarchitect ~/Projects/superdomain
```

- [ ] **Step 3: 설치 실측 (새 세션에서 사용자와 함께)**

```bash
claude plugin marketplace add Cho-D-YoungRae/superdomain
claude plugin install superdomain@superdomain
claude plugin details superdomain
```

Expected: 스킬 8종(`/superdomain:*`)·에이전트 `domain-reviewer`·SessionStart 훅 1개가 잡힌다. 이것이 스펙 §10-5의 최종 성공 기준 실측이다.

---

## Self-Review 기록

- **스펙 커버리지:** §3(SSOT)→Task 3·15 / §4.1(제거)→Task 1·8 / §4.2(스킬 8)→Task 9~14 / §4.3(에이전트·훅)→Task 11·7 / §5(스크립트)→Task 3~8 / §6.1(지식)→Task 2·17 / §6.2(거버넌스)→Task 15·16 / §6.3(테스트)→각 태스크 내장+게이트 / §7·§8(이름·순서)→Task 19·20 / §9(YAGNI)→Global Constraints / §10(성공 기준)→Phase 게이트+Task 20. 갭 없음.
- **순서 조정 1건:** profiles/ 삭제를 Phase 1→Task 8로 이동(test_parse_architecture 의존 실측). 스펙 §8의 의도(개명 전 완료)는 유지된다.
- **타입 정합:** `context_packages`·`isolation_allowlist`·`LocatedError`·`format_error`·`SKIP_DIRS/SOURCE_SUFFIXES/SRC_DIR` 시그니처가 Task 3(생산)과 Task 4~6(소비)에서 일치함을 확인.
