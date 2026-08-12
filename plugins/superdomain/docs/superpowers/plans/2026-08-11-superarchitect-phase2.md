# superarchitect Phase 2 (강제) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 선언된 아키텍처를 결정적으로 강제한다 — 스타일 선언 파서, 유효 규칙 해석기, check_imports, fitness(Konsist 생성), review + arch-reviewer, 그리고 review가 인용할 tactical 5종·patterns 3종의 성숙화.

**Architecture:** 해석 파이프라인을 3계층으로 나눈다: `parse_architecture.py`(SSOT, Phase 1) → `parse_style.py`(스타일 선언 + 파라미터 셀 문법) → `resolve_rules.py`(유효 규칙 집합 = 스타일 규칙 − 예외 + 파생 3종, 교차 파일 검증, 정규화 조인). 소비자는 둘: `check_imports.py`(정적 검사)와 fitness 스킬(rule-mappings 템플릿으로 Konsist 코드 생성). review는 결정적 검사 → arch-reviewer(의미론) 순서로 조합한다.

**Tech Stack:** bash + python3 stdlib만(외부 패키지 금지, PyYAML 금지). 생성 대상은 Konsist 0.17.3(`com.lemonappdev:konsist`). 테스트는 `python3 -m unittest discover -s tests`.

**요구사항 소스:** `docs/superpowers/specs/2026-08-08-superarchitect-plugin-design.md` §6.3, §6.4, §9, §10, §12 Phase 2. 정본: `references/governance/rule-vocabulary.md`(어휘·§2 문법), `references/governance/architecture-template.md`(파싱 계약·§5.3·파생 규칙).

## Global Constraints

- 스크립트는 bash + python3 stdlib만. Konsist/ArchUnit은 **대상 프로젝트의** 의존성이다.
- SKILL.md 본문 500줄 이하, description 1,536자 이하(한국어/영어 트리거 포함, 언제 쓰지 않는지 포함).
- knowledge 문서 100~300줄, 300줄 초과 시 목차 필수, 500줄 초과 금지(분할).
- 모든 knowledge 문서는 판정 도구다: `## 적용 기준`·`## 규칙`(정확히 이 레벨-2 문자열이어야 `build_index.py`가 성숙으로 판정) + Kotlin 사례. 백과사전식 서술 금지.
- 미구현 기능을 현재형으로 서술 금지 — 존재하지 않는 것을 참조하면 `> **구현 상태**` 블록으로 명시하고, 구현 시점에 그 블록을 제거한다.
- INDEX.md는 태스크가 직접 커밋하지 않는다 — 컨트롤러가 마지막에 `python3 scripts/build_index.py --write`로 재생성한다.
- 커밋은 `git commit --only <자기 경로들>`만. 다른 태스크 영역의 실패는 고치지 말고 보고만 한다.
- 오류 메시지는 한국어 + `경로:라인: 메시지` 형식(기존 parse_architecture.py 관례).
- 임시 파일·샘플은 `.superpowers/`(git-ignored) 아래에만.
- 각 태스크 종료 전: `python3 -m unittest discover -s tests` 전체 통과 확인(기존 63 + 신규).

## 컨트롤러 확정 결정 (이 계획의 정본 — 태스크는 여기서 벗어나지 않는다)

**D1. 파생 규칙 3종의 id와 예외 불가.** id는 `derived.context-isolation`, `derived.app-confinement`, `derived.shared-module-direction`. 파생 규칙은 `규칙 예외`의 대상이 아니다 — 예외 라벨이 `derived.`로 시작하는 id를 지목하면 오류이며, 오류 메시지는 조절 수단을 안내한다(관계 표 / `포함 컨텍스트` / 공용 모듈 역할). 스타일 예외 id가 그 스타일이 선언한 규칙 id 집합에 없으면 역시 오류다(어휘 §4의 "id 변경 시 예외가 조용히 되살아나는" 사고를 결정적으로 차단).

**D2. 공용 모듈·앱의 패키지는 선언이 아니라 관측이다.** 공용 모듈과 앱 모듈의 패키지 패턴은 결정 템플릿에 선언되지 않는다. 소비자(check_imports·fitness)가 해당 모듈 경로 아래 소스의 `package` 선언을 읽어 유도한다. 소스가 0건이면 해당 인스턴스를 **생략하되 반드시 출력에 고지한다**(침묵 금지). resolve_rules는 관측을 하지 않는다 — 파생 규칙에 모듈 경로를 담아 전달만 한다.

**D3. domain-pure 판별자.** 컨텍스트의 스타일 선언에 `primitive=confine-type` 인스턴스가 하나라도 있으면 그 컨텍스트는 domain-pure다. 공용 모듈 방향 규칙의 "shared-kernel 외 역할은 domain 레이어에서 import 금지" 세부는 그 스타일에 `domain`이라는 레이어가 선언돼 있을 때만 생성하고, 없으면 생략+고지한다.

**D4. check_imports의 커버리지 정직성.** import 스캔이 원리적으로 못 보는 것(같은 패키지 내 참조, import 없는 FQN 사용)은 한계로 **매 실행 리포트 푸터에 명시**한다. 규칙이 from-측 매칭 0건이면 통과가 아니라 `[0건 경고]`를 출력한다 — "지켜지고 있음"과 "아무것도 검사 안 함"을 출력에서 구분한다.

**D5. context-mapping 파킹 6건의 해소 방향.** 번역 경계 확인을 결정 절차의 **0단계(최우선)**로 승격한다 — "이 쌍의 어느 쪽에라도 상대 모델을 번역해 들이는 경계가 있는가? 있으면 `acl`, 이하 단계 진행 안 함"(이미 배포된 R1 문면 "있으면 값은 acl이다"와 정합). 번역 계층을 두는 쌍은 partnership의 정의(서로 맞춰 바꿈)와 양립하지 않음을 한 문장으로 적는다. 절차·표의 술어는 "우리가"가 아니라 쌍 단위("어느 쪽이든")로 통일한다.

**D6. 게이트 상향.** ARCHITECTURE.md 또는 스타일 선언을 만진 뒤의 검증 게이트는 `parse_architecture.py`가 아니라 `resolve_rules.py` CLI다(내부에서 전자를 포함). init의 게이트 지시도 이번 Phase에서 상향한다.

## 파일 구조

```
생성:
  scripts/parse_style.py            # T1 — 스타일 선언 파서 (§2 문법 + §2.1 판별)
  scripts/resolve_rules.py          # T2 — 유효 규칙 해석기 + 교차 파일 검증 + CLI
  scripts/check_imports.py          # T4 — 정적 import·배치 검사기 + CLI
  tests/test_parse_style.py         # T1
  tests/test_resolve_rules.py       # T2
  tests/test_check_imports.py       # T4
  tests/fixtures/styles/…           # T1·T2 픽스처
  profiles/README.md                # T5 — 프로파일 계약
  profiles/kotlin-spring/rule-mappings.md   # T5
  agents/arch-reviewer.md           # T9
  skills/fitness/SKILL.md           # T10
  skills/review/SKILL.md            # T11
수정(성숙화 — 스텁 → 완성):
  references/knowledge/tactical/{aggregates,value-objects,domain-events,repositories-domain-services,persistence}.md   # T6
  references/knowledge/patterns/{cqrs,event-sourcing,outbox}.md   # T7
수정(정본·상태):
  references/knowledge/strategic/context-mapping.md   # T8 (파킹 적용)
  scripts/parse_architecture.py     # T2에 병합 (KNOWN_PROFILES 동적화)
  references/governance/architecture-template.md      # T12 (§5.3 행 제거, 파생 규칙 정본)
  references/governance/rule-vocabulary.md            # T12 (§2·§7 상태 블록)
  references/governance/evolution-signals.md          # T12 (상태 블록 축소)
  skills/init/SKILL.md              # T12 (게이트 상향·스킬 목록)
  README.md                         # T12 (Phase 2 경계)
  references/INDEX.md               # 컨트롤러 재생성
```

의존과 실행 웨이브(파일 겹침 없음 = 병렬 가능):

| 웨이브 | 태스크 |
|---|---|
| A (병렬) | T1, T5, T6, T7, T8, T9 |
| B | T2 (T1 뒤) |
| C (병렬) | T4 (T2 뒤), T10 (T2·T5 뒤) |
| D | T11 (T4·T9 뒤, T6·T7 인용) |
| E | T12 (전체 뒤 정본 스위프) |
| F | T13 (Phase 2 검증 ①~④) |

---

### Task 1: parse_style.py — 스타일 선언 파서

**Files:**
- Create: `scripts/parse_style.py`
- Test: `tests/test_parse_style.py`
- Create: `tests/fixtures/styles/valid-hexagonal.md`, `tests/fixtures/styles/broken-*.md` (오류 케이스별)

**필독:** `references/governance/rule-vocabulary.md` §2(문법 전체)·§2.1(가/나 판별)·§3(primitive별 키 표), `references/governance/architecture-template.md` §7(선언 형식). 이 두 문서가 요구하는 **모든** 오류 조건을 구현한다 — §2의 상태 블록이 "지금 시행되지 않는다"고 적은 조항 전부가 이 태스크의 요구사항이다.

**Interfaces (Produces):**

```python
# scripts/parse_style.py — parse_architecture의 ParseError를 import해 재사용
from parse_architecture import ParseError

PRIMITIVES = {
    #  primitive: {키: (필수?, 목록?)}  — 목록?=False면 항목 2개 이상 오류(§2)
    "layer-order": {"layers": (True, True), "strict": (False, False)},
    "forbid-import": {"from": (True, True), "to": (True, True)},
    "confine-type": {"type": (True, False), "allowed_layer": (False, True), "allowed_package": (False, True)},
    "naming-suffix": {"scope": (True, False), "suffixes": (True, True)},
    "forbid-sibling-dependency": {"layer": (True, False), "suffix": (True, False)},
}
SELECTORS = {"jpa-entity"}          # confine-type의 type 정규 값
GA_PARAMS = {("forbid-import", "from"), ("forbid-import", "to"), ("naming-suffix", "scope")}   # §2.1(가)
NA_PARAMS = {("layer-order", "layers"), ("confine-type", "allowed_layer"), ("forbid-sibling-dependency", "layer")}  # §2.1(나)

@dataclass(frozen=True)
class RuleInstance:
    rule_id: str
    primitive: str
    params: dict      # 키 -> 항목 목록(list[str]). 모든 값은 목록(길이 1 포함)
    line: int         # 표 행의 1-기준 라인

@dataclass
class StyleDeclaration:
    name: str         # 파일명에서 유도한 스타일 이름
    layers: list      # ["domain", "application", "adapter"] — 선언 순서 그대로
    rules: list       # [RuleInstance]

def parse_style(text: str, style_name: str, path: str = "<style>") -> tuple:
    """(StyleDeclaration | None, [ParseError]) — 오류가 있어도 파싱 가능한 부분은 채운다."""
```

**파싱 규칙(정본 §7):** `## 선언` **줄 전체 정확 일치**로 섹션을 찾는다(`### 선언`은 매칭하지 않음 — 없으면 오류 "'## 선언' 섹션이 없습니다"). 섹션 안에서 `- 레이어:` 라벨(쉼표 목록, 후행 괄호 주석 1덩어리 제거 — parse_architecture의 `_strip_comment` 재사용)과 첫 표(열 순서 고정: 규칙 id, primitive, 파라미터)를 읽는다. 섹션은 다음 `##` 헤딩에서 끝난다.

**검증(전부 ParseError, 라인 번호 포함):** ① primitive가 5종 밖 ② 규칙 id 중복 ③ §2 문법 — `=` 0개/2개+, 키 중복, 알 수 없는 키, 빈 키/값/항목(후행 `;` 포함), trim 후 내부 공백, 목록 아닌 키에 항목 2+ ④ `strict` 값이 true/false 외 ⑤ confine-type의 allowed_layer XOR allowed_package 위반(둘 다/둘 다 없음) ⑥ type 값이 SELECTORS 밖 ⑦ §2.1(나) 항목이 선언된 레이어 밖 ⑧ §2.1(가) 항목이 `.`을 포함하지 않으면서 레이어 목록에도 없음(어휘 §2.1의 조용한 실패 차단 조항) ⑨ 레이어 라벨 누락/빈 목록/레이어 이름 중복.

- [ ] **Step 1: 실패 테스트 작성** — 아래를 포함한 테스트를 쓴다(각각 독립 케이스). 정상 케이스는 hexagonal 정본 선언(architecture-template.md §7의 블록 그대로)을 픽스처로 쓰고 4개 규칙·3레이어·파라미터 파싱 결과를 정확히 단언한다.

```python
class TestParamGrammar(unittest.TestCase):
    def test_list_value_split(self):        # to=a..,b.. -> ["a..","b.."]
    def test_key_order_irrelevant(self):
    def test_duplicate_key_error(self):
    def test_unknown_key_error(self):       # 'suffix=' on forbid-import
    def test_trailing_semicolon_error(self):
    def test_internal_space_error(self):    # suffixes=Use Case
    def test_nonlist_key_multiple_items_error(self):  # suffix=Service,Component
    def test_equals_count_error(self):      # 0개와 2개 각각
class TestLayerResolution(unittest.TestCase):
    def test_na_param_unknown_layer_error(self):      # layers=domain,typo
    def test_ga_param_bare_word_not_layer_error(self):  # from=kotlinx (점 없음+레이어 아님)
    def test_ga_param_layer_name_accepted(self):
    def test_ga_param_package_pattern_accepted(self):  # to=org.springframework..
class TestConfineType(unittest.TestCase):
    def test_xor_both_error(self); def test_xor_neither_error(self)
    def test_unknown_selector_error(self)
class TestSection(unittest.TestCase):
    def test_missing_declaration_section_error(self)
    def test_level3_heading_not_matched(self)          # "### 선언"만 있는 문서 → 오류
    def test_duplicate_rule_id_error(self)
```

- [ ] **Step 2: 실행해 실패 확인** — `python3 -m unittest tests.test_parse_style -v` → import 오류/FAIL.
- [ ] **Step 3: 구현** — 위 인터페이스 그대로. 파라미터 셀 파싱은 §2의 절차(`;` 분할 → `=` 분리 → trim → `,` 분할 → trim) 순서를 코드로 옮긴다.
- [ ] **Step 4: 통과 확인 + 전체 스위트** — `python3 -m unittest discover -s tests`.
- [ ] **Step 5: Commit** — `git commit --only scripts/parse_style.py tests/test_parse_style.py tests/fixtures/styles -m "feat: parse_style — 스타일 선언 파서 (어휘 §2 문법 시행)"`

---

### Task 2: resolve_rules.py — 유효 규칙 해석기 + 교차 파일 검증 (+ KNOWN_PROFILES 동적화)

**Files:**
- Create: `scripts/resolve_rules.py`
- Modify: `scripts/parse_architecture.py` (KNOWN_PROFILES → `profiles/` 하위 디렉터리 동적 조회, 빈/부재 시 기존 상수 폴백)
- Test: `tests/test_resolve_rules.py` (+ test_parse_architecture.py에 프로파일 동적화 케이스 추가)

**Interfaces (Consumes):** `parse_architecture.parse_architecture(text) -> (Architecture, [ParseError])`, `normalize(arch) -> [NormalizedPattern(project, context, layer, pattern)]`, `parse_style.parse_style(...)`.

**Interfaces (Produces):**

```python
@dataclass(frozen=True)
class EffectiveRule:            # 스타일 유래 규칙 (예외 적용 후)
    project: str; context: str
    rule_id: str; primitive: str
    params: dict                # 원문 파라미터 (키→목록)
    resolved: dict              # §2.1(가) 파라미터의 레이어 항목을 패턴 목록으로 치환한 결과.
                                # (나) 파라미터(layers/allowed_layer/layer)는 레이어 이름 유지 —
                                # 프로파일 매핑이 레이어→패턴 표를 함께 받아 쓴다
    layer_patterns: dict        # 레이어명 → [패턴] (이 컨텍스트의 정규화 결과; "all" 포함)

@dataclass(frozen=True)
class DerivedRule:
    project: str
    kind: str                   # "context-isolation" | "app-confinement" | "shared-module-direction"
    subject: str                # 컨텍스트명 | 앱명 | 공용 모듈명
    detail: dict                # 아래 kind별 스키마

def resolve(arch_path) -> tuple:   # (list[EffectiveRule], list[DerivedRule], list[ParseError])
```

**kind별 detail 스키마(고정):**

| kind | subject | detail |
|---|---|---|
| context-isolation | 컨텍스트 | `{"from": [자기 패턴], "to": [타 컨텍스트 패턴 − 관계 쌍 상대 패턴]}` — to가 비면 인스턴스 생략 |
| app-confinement | 앱 | `{"module_path": 절대 아님·프로젝트 경로 기준, "forbidden": [미포함 컨텍스트 패턴], "reverse_from": [모든 컨텍스트 패턴]}` — 포함이 `all`이면 forbidden은 빈 목록(정방향 생략), reverse는 유지 |
| shared-module-direction | 공용 모듈 | `{"path": 모듈 경로, "role": 역할, "forbidden": [프로젝트의 모든 컨텍스트 패턴], "domain_restricted_contexts": [D3에 따른 domain-pure 컨텍스트 중 domain 레이어 보유분]}` — role이 shared-kernel이면 domain_restricted_contexts는 빈 목록 |

컨텍스트 `"*"` 패턴(컨텍스트 비분할 레이어)은 context-isolation의 from/to 어느 쪽에도 넣지 않는다(모든 컨텍스트 공용이므로 격리 대상이 아니다).

**스타일 로딩:** 프리셋 → `<플러그인 루트>/references/knowledge/styles/<이름>.md` (플러그인 루트 = `Path(__file__).resolve().parent.parent`). `custom/<이름>` → `<ARCHITECTURE.md의 디렉터리>/docs/architecture/styles/<이름>.md`.

**교차 파일 검증(전부 ParseError, ARCHITECTURE.md의 해당 라벨/표 라인 지목):** ① custom 스타일 문서 부재 ② 패키지 규약 표의 레이어 ∉ 스타일 선언 레이어 ③ 모듈 표의 레이어 ∉ 스타일 레이어 ∪ {all} ④ 기본 관례 경로(규약 표 없음)에서 레이어 이름이 유효한 패키지 세그먼트가 아님(`[A-Za-z_][A-Za-z0-9_]*`) ⑤ `패턴` 값 ∉ `references/knowledge/patterns/*.md` 파일명 집합 ⑥ 규칙 예외 id ∉ 그 스타일의 선언 규칙 id 집합 ⑦ 규칙 예외 id가 `derived.` 접두 (D1 — 메시지에 조절 수단 안내 포함) ⑧ 스타일 선언 자체의 파싱 오류는 스타일 파일 경로:라인으로 그대로 전파.

**CLI:**

```
python3 scripts/resolve_rules.py <ARCHITECTURE.md 경로> [--json]
성공(exit 0): "OK: 컨텍스트 N, 유효 규칙 M (스타일 S, 파생 D, 예외 제외 E)"
실패(exit 1): "<경로>:<라인>: <메시지>" 줄들
--json: {"effective": [...], "derived": [...]} — fitness 스킬이 소비하는 기계 출력
```

- [ ] **Step 1: 실패 테스트** — 픽스처는 tests/fixtures/full.md(기존 imstargg형)와 신규 최소 문서를 쓴다. 핵심 케이스:

```python
def test_hexagonal_effective_rules(self):       # hexagonal 채택 컨텍스트 → 4개 규칙, resolved의 from/to에 실제 패턴
def test_exception_removed_and_counted(self):   # -hex.ports-owned-inside → 3개 + 제외 1 집계
def test_exception_unknown_id_error(self)
def test_exception_derived_id_error(self):      # 메시지에 "관계 표" 안내 포함 단언
def test_context_isolation_pairs_open(self):    # 관계 쌍은 to에서 빠짐 (양방향 모두)
def test_context_isolation_star_pattern_excluded(self)
def test_app_confinement_all(self)              # all → forbidden 빈 목록, reverse_from 유지
def test_shared_module_roles(self)              # shared-kernel vs infrastructure의 domain_restricted 차이
def test_custom_style_missing_error(self)
def test_convention_layer_not_in_style_error(self)   # §5.3 행 1
def test_module_layer_not_in_style_error(self)       # §5.3 행 2
def test_invalid_segment_layer_error(self)           # §5.3 행 3 — 레이어명 interface-adapter
def test_unknown_pattern_key_error(self)             # §5.3 행 5 — 패턴: nosuch
def test_cli_ok_line_format(self); def test_cli_error_exit_code(self)
def test_dynamic_profiles_accepts_new_dir(self)      # parse_architecture: profiles/에 임시 디렉터리 추가 시 허용 (§5.3 행 10)
```

- [ ] **Step 2: 실행해 실패 확인.**
- [ ] **Step 3: 구현** — parse_architecture.py 수정은 `_known_profiles()` 함수 하나 추가 + validate에서 참조 교체(플러그인 루트의 `profiles/` 하위 디렉터리 목록, 부재·빈 목록 시 `KNOWN_PROFILES` 폴백). 다른 동작 변경 금지.
- [ ] **Step 4: 통과 + 전체 스위트.**
- [ ] **Step 5: Commit** — `git commit --only scripts/resolve_rules.py scripts/parse_architecture.py tests/test_resolve_rules.py tests/test_parse_architecture.py tests/fixtures -m "feat: resolve_rules — 유효 규칙 해석기·교차 검증·파생 3종 (+프로파일 동적화)"`

---

### Task 4: check_imports.py — 정적 검사기

**Files:**
- Create: `scripts/check_imports.py`
- Test: `tests/test_check_imports.py` (임시 소스 트리는 기존 테스트의 임시 디렉터리 관례를 따른다)

**Consumes:** `resolve_rules.resolve(arch_path)`.

**동작:** 선언된 프로젝트 `경로` 아래(경로 `.` 포함) `.kt`/`.java` 파일을 걷는다(빌드 산출물 `build/`, `.git/` 등 제외). 파일마다 `package` 선언과 `import` 목록(와일드카드 포함)을 정규식으로 수집. 각 EffectiveRule/DerivedRule을 검사:

| primitive/kind | 판정 |
|---|---|
| layer-order | 안쪽 레이어 패턴에 속한 파일이 바깥 레이어 패턴을 import → 위반. `strict=true`면 인접 외 안쪽 import도 위반 |
| forbid-import | from 패턴 파일이 to 패턴을 import → 위반 |
| confine-type(jpa-entity) | `@Entity` 텍스트를 가진 파일의 패키지가 허용 범위 밖(선언 위반) / 허용 범위 밖 파일이 @Entity 보유 타입을 import(참조 위반 — @Entity 파일들의 `패키지.타입명` 집합을 먼저 수집) |
| naming-suffix | scope 패턴 파일의 최상위 public 타입 이름이 suffixes로 안 끝남 → 위반. Kotlin: `^(?:@\w+\s*)*(?:public\s+)?(?:(?:data|enum|sealed|abstract|open|value)\s+)*(?:class|interface|object)\s+(\w+)`, Java: public class/interface/enum/record. private/internal 제외 |
| forbid-sibling-dependency | layer 패턴 안 suffix 타입 파일이 같은 layer의 다른 suffix 타입을 import → 위반 |
| context-isolation / app-confinement / shared-module-direction | detail 스키마대로. 앱·공용의 from-측은 **모듈 경로 기준**으로 파일을 귀속, to-측 "앱/공용 패키지"는 그 경로 아래 파일들의 package 선언에서 관측(D2). 관측 0건이면 생략+고지 |

**출력 계약:**

```
위반:   "<파일 경로>:<라인>: [<rule id>] <메시지>"
경고:   "[0건 경고] <rule id>: from-측 매칭 파일 0건 — 레이어·패키지 불일치 가능성" (D4)
푸터:   검사 규칙 n / 생략 규칙 m(각 사유) / 한계 고지(같은 패키지 내 참조·import 없는 FQN은 보지 못함 — Konsist/ArchUnit 테스트가 강제의 정본)
exit: 0 클린 / 1 위반 존재 / 2 해석 불가(resolve 오류 — 오류 줄 그대로 출력)
--json: 위반 목록 기계 출력
```

- [ ] **Step 1: 실패 테스트** — 임시 트리에 최소 Kotlin 파일들을 만들어 각 primitive 위반 1개씩 + 클린 케이스 + 0건 경고 케이스 + exit code 3종 + 와일드카드 import 케이스 + `@Entity` 참조 위반(위반 B) 케이스를 단언한다. 파생 3종은 관계 쌍 열림/앱 미포함 컨텍스트 참조/공용→컨텍스트 역참조 각 1개.
- [ ] **Step 2: 실행해 실패 확인.**
- [ ] **Step 3: 구현.**
- [ ] **Step 4: 통과 + 전체 스위트.**
- [ ] **Step 5: Commit** — `git commit --only scripts/check_imports.py tests/test_check_imports.py -m "feat: check_imports — 5 primitive + 파생 3종 정적 검사 (0건 경고·한계 고지)"`

---

### Task 5: profiles/README.md + kotlin-spring/rule-mappings.md

**Files:**
- Create: `profiles/README.md`
- Create: `profiles/kotlin-spring/rule-mappings.md`

**필독:** 스펙 §10, `rule-vocabulary.md` §3(각 primitive의 의미가 번역의 원본), 부록 B의 Konsist 검증 사실. **불확실한 Konsist API는 context7/공식 문서로 확인하고, 확인 못 한 API는 문서에 `(미검증 — 첫 실행 시 확인)` 표기를 남긴다** — 부록 B가 보증하는 것은 `scopeFromProject`, `assertArchitecture`, `Layer(name, "pkg..")`, `dependsOn(vararg, strict)`, `dependsOnNothing()`, `doesNotDependOn()`뿐이다.

**profiles/README.md (~120줄):** 프로파일 계약 — ① `rule-mappings.md` 필수: primitive 5종 각각에 대해 "파라미터 → 코드 템플릿" 표기(플레이스홀더 `{{...}}` 규약 포함) ② `templates/<style>/` 규약(Phase 4에서 kotlin-spring 최초 구현 — 구현 상태 블록) ③ `examples/` 규약(좋은/나쁜 각 1, 짧게) ④ 제3 프로파일 추가 절차 = 이 계약 구현 + `profiles/<이름>/` 생성(파서가 디렉터리를 자동 인식함 — T2의 동적화) ⑤ java-spring은 Phase 6(구현 상태 블록).

**rule-mappings.md (~250줄):** 각 primitive마다: 입력(파라미터·resolve_rules의 resolved/layer_patterns 어느 쪽을 쓰는지) → Konsist 코드 템플릿(컴파일 가능한 완전한 형태, `{{context}}`, `{{layerName}}`, `{{pattern}}`, `{{items}}` 플레이스홀더) → 생성 파일 배치 규약. 고정 사항:
- layer-order → `assertArchitecture { Layer(...) + dependsOn/dependsOnNothing }`, `strict=true`면 인접 의존만 나열.
- forbid-import → to가 패턴이면 `Layer("금지대상", "<패턴>")` + `doesNotDependOn` 조합을 우선 사용(부록 B 검증 범위 내). 파일 단위 imports API를 쓰는 대안 템플릿은 미검증 표기와 함께 부기.
- confine-type(jpa-entity) → 선언 위반·참조 위반 두 어서션. 참조 위반은 도구 특성상 어려우면 문서에 커버리지 한계를 명시(침묵 금지).
- naming-suffix, forbid-sibling-dependency → declarations API 템플릿 + 미검증 표기 규율 적용.
- 파생 3종 → detail 스키마별 템플릿(앱·공용의 from-측은 관측 패키지 목록을 리터럴로 굽고, 출처 주석 `// 관측: <경로>` 병기 — D2).
- 생성 파일 헤더(고정 문자열): `// GENERATED by superarchitect from ARCHITECTURE.md` + `// 수정 금지 — 규칙 변경은 스타일 선언에서. 재생성: /superarchitect:fitness`.
- baseline 연동(kotlin은 Freezing 부재 → 생성 테스트가 baseline.jsonl을 읽어 warn 강등): **Phase 5 구현 — 구현 상태 블록**.
- Spring Modulith: single-module 보조 검증 수단으로 문서화만(생성 안 함).

- [ ] **Step 1: 두 문서 작성** (테스트 없음 — 문서 태스크).
- [ ] **Step 2: 검증** — 템플릿의 플레이스홀더 목록이 resolve_rules의 detail/resolved 스키마와 1:1 대응하는지 self-check 표를 문서 끝이 아닌 리포트에 포함.
- [ ] **Step 3: Commit** — `git commit --only profiles -m "feat: 프로파일 계약 + kotlin-spring rule-mappings (Konsist 번역)"`

---

### Task 6: tactical 5종 성숙화

**Files:** Modify: `references/knowledge/tactical/{aggregates,value-objects,domain-events,repositories-domain-services,persistence}.md`

**필독:** `references/governance/knowledge-doc-template.md`, 각 스텁의 "담을 내용" 목록(요구사항이다 — 전부 커버), 스펙 §11.3의 tactical 항목별 괄호 내용. 각 문서 150~300줄, `## 적용 기준`(레벨-2 정확 문자열)·`## 규칙`(리뷰 체크리스트 — review가 인용하는 판정 도구)·`## 사례`(Kotlin 올바른 1 + 안티패턴 1~2) 필수. frontmatter `read_when`은 스텁 값 유지, `rules:` 필드는 쓰지 않는다(기계 규칙 id는 스타일 선언 소유 — 관련 규칙은 본문에서 `hex.domain-pure` 등 기존 id를 언급).

문서별 고정 요구:
- **aggregates**: 경계 설정 기준(불변식 단위·트랜잭션 1개=애그리거트 1개·ID 참조), 크기 판단 체크리스트, `INV-` 불변식과의 연결(Phase 3 check_invariants는 구현 상태 블록으로 언급).
- **value-objects**: 불변성·동등성·원시 타입 강박, Kotlin `data class`/`value class` 사용 기준.
- **domain-events**: 발행 위치(애그리거트)·시점(커밋 경계), 과거형 명명, 관계 표 `계약` 칸과의 연결([[context-mapping]]), [[outbox]] 연결.
- **repositories-domain-services**: 리포지토리 인터페이스는 도메인 소유·구현은 어댑터, 도메인 서비스 vs 애플리케이션 서비스 구분 체크리스트, "서비스끼리 참조 금지"가 필요할 때 `forbid-sibling-dependency` 채택 안내.
- **persistence**: 순수 도메인 ↔ 영속 엔티티 분리·매핑은 어댑터(out), 노출 위반은 `*.domain-pure`(confine-type)가 잡는 것과 리뷰가 볼 것의 구분, lazy loading 누수·양방향 연관 남용 안티패턴, JPA 직접 사용이 정당한 조건 → layered-simple 연결.

- [ ] **Step 1: 5개 문서 작성** — 스텁의 frontmatter summary는 유지·필요시 정밀화.
- [ ] **Step 2: 검증** — `python3 scripts/build_index.py`(쓰기 없이)로 5개 전부 draft 해제 확인 + 각 문서 500줄 미만 + `[[...]]` 링크가 실재 key인지.
- [ ] **Step 3: Commit** — `git commit --only references/knowledge/tactical -m "docs: tactical 5종 성숙화 — 판정 도구(체크리스트·사례) 완비"`

---

### Task 7: patterns 3종 성숙화

**Files:** Modify: `references/knowledge/patterns/{cqrs,event-sourcing,outbox}.md`

T6과 같은 표준. 추가 고정 요구(스펙 §11.3 마지막 문단 — "언제 쓰지 않는가"를 강하게):
- **cqrs**: 적용 스펙트럼(같은 모델 호출 분리 → 모델 분리 → 저장소 분리)과 단계별 채택 기준. `## 규칙`에 **커맨드/쿼리 체크리스트**: 커맨드 핸들러에 조회 반환·조회용 조인 금지, 쿼리 핸들러에 상태 변경 금지, command/query 패키지 분리 시 교차 import 금지 — Phase 2 검증 ②가 이 체크리스트로 "커맨드 핸들러 안의 조회 로직"을 검출한다. 리뷰어가 그대로 판정할 수 있는 문형으로 쓴다.
- **event-sourcing**: 첫 문장이 "대부분의 컨텍스트에는 불필요하다"로 시작. 적용 판단 기준(감사 요구·시간 여행·이벤트가 곧 도메인), 스냅샷·리플레이·스키마 진화 비용, 대안(감사 테이블·outbox) 먼저 검토.
- **outbox**: 트랜잭션적 발행 문제와 해법, 릴레이 방식 비교(폴링/CDC), at-least-once와 멱등 소비, [[domain-events]] 연결.

- [ ] **Step 1: 3개 문서 작성.**
- [ ] **Step 2: 검증** — build_index 드라이런으로 draft 해제 확인.
- [ ] **Step 3: Commit** — `git commit --only references/knowledge/patterns -m "docs: patterns 3종 성숙화 — 과잉 적용 방어선 포함"`

---

### Task 8: context-mapping 파킹 6건 적용

**Files:** Modify: `references/knowledge/strategic/context-mapping.md`

**요구(전부 D5의 전순서 아래에서, 원장 판정문 그대로):**
1. **0단계 신설**: 결정 절차 맨 앞에 "0. **이 쌍의 어느 쪽에라도 상대 모델을 번역해 들이는 경계가 있는가?** 있으면 `acl` — 이하 단계로 가지 않는다. 번역 계층을 두는 쌍은 partnership의 정의(서로 맞춰 바꿈)와 양립하지 않는다." 기존 2단계의 acl 갈래는 0단계로 흡수하고 2단계는 "번역하지 않는 쌍"만 다루도록 재서술.
2. **술어 통일(파킹 1)**: 절차 1·2단계와 3단계 조건, 표기 규칙 문단, acl·open-host 행의 술어를 쌍 단위로 통일("우리가" → "어느 쪽이든/이 쌍에"). 3단계의 "번역이 호스팅을 이긴다" 괄호는 0단계 참조로 교체.
3. **파킹 4**: partnership 행에 번역 단서("번역 계층이 보이면 이 유형이 아니다 — 0단계"), customer-supplier 행에 번역 단서 + 소비자 수 판별자(3 이상이고 우리가 공급자면 open-host 검토) 추가.
4. **파킹 5**: "규칙은 하나다"를 "open-host와 published-language가 동시에 성립할 때의 규칙은 하나다"로 범위 한정.
5. **파킹 6**: R3 체크리스트의 customer-supplier 정정 항목을 "번역 계층이 실재하면 `acl`로, 없으면 `conformist`로 정정한다"로 확장.
6. **R1의 :115-117 확인 지시**를 0단계와 중복되지 않게 정리(0단계를 가리키는 한 문장으로 축약 — 문면 "있으면 값은 acl이다" 유지).
7. 머리의 **구현 상태 블록(:18-20)은 유지하되 이번 Phase에서 fitness·check_imports가 생기므로 T12가 최종 문면을 정리한다** — 이 태스크는 내용 충돌만 안 나게 둔다.
8. 기존 사례(claim–policy customer-supplier)가 새 절차로도 같은 값에 도달하는지 절차를 손으로 밟아 리포트에 기록한다(번역 없음 → 0단계 통과 → 1단계 customer-supplier).

- [ ] **Step 1: 수정 적용** — sweep-before-edit: 수정 전에 "우리가/우리 " 전 출현을 grep으로 나열하고 각각 유지/교체 판정 표를 만든 뒤 일괄 적용한다(Phase 1 T8의 재발 유형 — 재진술 잔존 — 방지).
- [ ] **Step 2: 검증** — grep 재실행으로 잔존 0건(의도적 유지분은 판정 표에 근거) + build_index 드라이런.
- [ ] **Step 3: Commit** — `git commit --only references/knowledge/strategic/context-mapping.md -m "docs: context-mapping — 번역 경계 0단계 승격, 술어 쌍 단위 통일 (파킹 6건 해소)"`

---

### Task 9: agents/arch-reviewer.md

**Files:** Create: `agents/arch-reviewer.md`

**필독:** 스펙 §9 (전체 요구가 이 한 절이다), 부록 B 에이전트 형식.

**frontmatter:** `name: arch-reviewer`, `description`(위임 시점 명시 — review 스킬이 의미론 검토를 위임할 때), `tools: Read, Grep, Glob` (읽기 전용).

**본문 고정 요구:** ① 입력 계약 — summary.md 내용, 검토 대상 파일/diff 목록, 선별된 지식 문서 **경로 목록**, 해당 컨텍스트 domain 문서(있으면) ② 판정 기준은 전달받은 문서의 `## 규칙`·리뷰 체크리스트 섹션만 — 그 외 knowledge 임의 탐색 금지 ③ 결정적 검사(check_imports·fitness)로 잡히는 항목 보고 금지(중복 방지 — 의심되면 보고하지 않는다) ④ 의미론 5범주만: 도메인 로직 누출 / 애그리거트 경계 / 불변식 행위 정합성(태그만 달린 빈 테스트, 불변식 의미와 다른 검증) / 과잉·과소 설계 / 제2의 방식 도입 ⑤ 불확실하면 severity=info ⑥ **날조 금지 — 인용하는 파일·라인·문서 섹션은 실제로 읽은 것만. 근거 문서에 없는 기준을 만들어 내지 않으며, 확신 없는 근거는 근거 없이 info로 보고한다**(Phase 1 검증에서 관측된 ADR 대안 날조 유형의 방어) ⑦ 출력은 JSON 배열만: `[{"type": "violation|missing|drift|discussion", "path": "...", "line": 0, "severity": "blocker|warn|info", "rationale": "...", "related_rule": "...", "related_invariant": "...", "related_adr": "..."}]` — line·related_*는 선택 필드.

- [ ] **Step 1: 작성** (frontmatter + 본문 ~120줄).
- [ ] **Step 2: 검증** — description 1,536자 이내, 스펙 §9의 문장별 커버 대조표를 리포트에.
- [ ] **Step 3: Commit** — `git commit --only agents/arch-reviewer.md -m "feat: arch-reviewer 에이전트 — 의미론 5범주 읽기 전용 리뷰"`

---

### Task 10: skills/fitness/SKILL.md

**Files:** Create: `skills/fitness/SKILL.md`

**필독:** 스펙 §6.4, `profiles/kotlin-spring/rule-mappings.md`(T5 산출), resolve_rules CLI 계약(T2).

**절차(고정):**
1. ARCHITECTURE.md 부재 → "superarchitect가 초기화되지 않았습니다" + `/superarchitect:init` 안내 후 중단(공통 규칙).
2. `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/resolve_rules.py <ARCHITECTURE.md> --json` 실행 — 오류면 그대로 보여주고 중단(게이트 = D6). 0건 경고성 상황(컨텍스트 0, 유효 규칙 0)도 중단 사유.
3. 프로젝트의 `프로파일` 확인 → `profiles/<프로파일>/rule-mappings.md`를 읽는다. java-spring인데 매핑 부재(Phase 6 전) → 정직하게 "이 프로파일의 매핑은 아직 없다" 안내 중단.
4. 컨텍스트별 생성: `<아키텍처 테스트 위치>/<PascalCase 컨텍스트>ArchitectureTest.kt` — effective rule마다 매핑 템플릿 치환. 파생 규칙은 프로젝트당 `DerivedRulesTest.kt`. 앱·공용 관측 패키지(D2)는 이 시점에 소스를 읽어 리터럴로 굽고 `// 관측:` 주석 병기, 관측 0건은 생략+출력 고지.
5. 기존 파일 존재 시: 생성 헤더 온전 → diff 표시 후 갱신. 헤더 훼손(수동 수정) → 경고 + 덮어쓸지 사용자 확인(확인 없이 덮지 않는다).
6. 종료: 생성/갱신 파일 목록, 규칙 수 집계(스타일/파생/제외), 실행 안내(`./gradlew :<테스트 모듈>:test` — 테스트 위치에서 모듈 경로 유도, Konsist 의존성 미설정 시 추가할 좌표 `com.lemonappdev:konsist:0.17.3` 안내), `/superarchitect:review` 연계 언급.

**금지:** ARCHITECTURE.md·스타일 선언 수정(이 스킬은 SSOT를 읽기만 한다), 어휘 밖 규칙 임시 생성, 매핑에 없는 primitive 발견 시 임의 번역(오류 보고).

**description(초안 — 구현자가 다듬되 요소 유지):** 무엇(선언된 스타일·파생 규칙에서 Konsist/ArchUnit 아키텍처 테스트 생성/갱신) + 트리거("아키텍처 테스트 생성", "피트니스", "fitness", "/superarchitect:fitness", 스타일·규칙 예외 변경 후) + 비트리거(위반 검토는 review, 선언 변경은 init/adr).

- [ ] **Step 1: 작성** (~300줄 이내).
- [ ] **Step 2: 검증** — 스펙 §6.4 문장별 커버 대조표, description 길이, 500줄 제한.
- [ ] **Step 3: Commit** — `git commit --only skills/fitness -m "feat: fitness 스킬 — 유효 규칙 → Konsist 테스트 생성"`

---

### Task 11: skills/review/SKILL.md

**Files:** Create: `skills/review/SKILL.md`

**필독:** 스펙 §6.3, arch-reviewer 입력 계약(T9), check_imports CLI(T4), 공통 규칙(스펙 §6 서두).

**절차(고정):**
1. 초기화 게이트(공통 규칙) → 대상 결정: 기본 = `git diff`(작업 트리+staged, HEAD 대비), 인자로 경로·브랜치·커밋 범위 지정 가능. 대상이 비면 "변경 없음" 종료.
2. **결정적 검사 먼저**: 선언된 아키텍처 테스트 위치에 생성 테스트가 있고 gradle 실행 가능 → 해당 task 실행. 아니면 `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_imports.py <ARCHITECTURE.md>` (필요시 `--paths`로 diff 파일 한정). check_invariants.py는 Phase 3 — 구현 상태 블록으로 언급만. superglossery 설치 감지 시 용어 검증은 위임 언급(중복 검사 금지).
3. **지식 선별**: INDEX.md를 읽고 (a) 대상 컨텍스트의 `스타일`·`패턴` 선언 해당 문서 (b) read_when에 review 포함 문서 (c) 대상 프로젝트 `docs/architecture/conventions/`·`styles/` 문서를 경로 목록으로 만든다. draft 문서는 판정 근거로 넣지 않는다(INDEX의 draft 표시 확인).
4. **arch-reviewer 위임**: summary.md 내용 + 대상 파일/diff 목록 + 선별 경로 + domain 문서(있으면)를 전달. 결정적 검사 결과와 겹치는 항목은 병합 시 결정적 쪽만 남긴다.
5. **리포트**: 항목별 — rule id(결정적) 또는 semantic 태그(의미론), 분류(위반 | 누락 | 드리프트 | 추가 논의), 심각도(blocker/warn/info), 근거(규칙 id·문서 섹션·ADR 인용), 수정 제안. check_imports의 `[0건 경고]`와 한계 푸터는 리포트에 그대로 승계한다(D4 — 삼키지 않는다).
6. "추가 논의" 항목: `docs/architecture/domain/<context>.md`가 존재하면 그 문서의 `## 열린 질문`에 append(파생물 아님 — SSOT 문서다), 없으면 "domain 문서 없음 — Phase 3의 model 스킬이 생성한다(구현 상태)"를 리포트에 남긴다.
7. `docs/architecture/review-log.jsonl`에 append: `{"date": "YYYY-MM-DD", "rule": "<rule id 또는 semantic 태그>", "path": "...", "severity": "...", "note": "..."}` — 한 항목당 한 줄, 기존 줄 수정 금지.

**금지:** 자동 수정 적용(제안까지만), 결정적으로 판정 가능한 것을 LLM 판단으로 대체, draft 문서 인용, review-log 재작성.

**description 초안 요소:** 무엇(변경분의 아키텍처 검토 — 결정적 검사 + 의미론 리뷰) + 트리거("아키텍처 리뷰", "이 변경 검토", "architecture review", "/superarchitect:review", PR 전 점검) + 비트리거(테스트 생성은 fitness, 문서-코드 대조는 sync).

- [ ] **Step 1: 작성** (~350줄 이내).
- [ ] **Step 2: 검증** — 스펙 §6.3 5단계 커버 대조표 + review-log 스키마 필드 일치.
- [ ] **Step 3: Commit** — `git commit --only skills/review -m "feat: review 스킬 — 결정적 검사 우선 + arch-reviewer 의미론 위임"`

---

### Task 12: 정본 상태 스위프

**Files:** Modify: `references/governance/architecture-template.md`, `references/governance/rule-vocabulary.md`, `references/governance/evolution-signals.md`, `references/knowledge/strategic/context-mapping.md`(상태 블록만), `skills/init/SKILL.md`, `README.md`

**방법: sweep-before-edit** — 파일마다 편집 전에 `Phase 2|구현 상태|미구현|아직` grep 목록을 만들고 항목별 처분(제거/개서/유지)을 판정한 뒤 일괄 적용, 편집 후 grep 재실행으로 잔존 검증.

고정 처분:
1. **architecture-template.md §5.3**: 이번 Phase에 구현된 행 제거 — 규약 레이어 검증·모듈 레이어 검증·세그먼트 유효성·custom 실존·패턴 key 실존(이상 T2), 파생 규칙 3종 생성·앱→앱 금지(T2/T4/T10), 프로파일 하드코딩 드리프트(T2). 남는 행: 마커 버전 분기(v2 전제), baseline 동결(Phase 5). 머리 블록 문면을 남은 두 행 기준으로 개서. **§5.1 규칙 5에 파생 규칙 정본 추가(D1·D2·D3 — id 3종, 예외 불가+조절 수단, 관측 패키지 원칙, domain-pure 판별자)**. 문서는 500줄 이하 유지 — 초과가 불가피하면 편집 전에 컨트롤러에게 §5.3 분리 여부를 물어본다(Phase 1 최종 파킹 A의 판정).
2. **rule-vocabulary.md**: §2 머리 상태 블록 제거(파라미터 셀 해석 시행됨 — T1·T2). §2.1의 "아직 시행되지 않는다" 참조 제거. §7 상태 블록 개서 — kotlin-spring 매핑 실재, java-spring은 Phase 6(그때까지 어휘 확장 불가 문면 유지).
3. **evolution-signals.md**: 머리 상태 블록 개서 — review-log.jsonl은 이번 Phase부터 실재(review가 append), collect_signals.py·evolve는 Phase 5(그 부분만 미구현 표기 유지).
4. **context-mapping.md**: 머리 상태 블록(:18-20) 개서 — "fitness가 생성한다"가 이제 사실이므로 블록 제거, 단 관계 쌍 강제의 실검증은 fitness 생성 테스트 실행에 달려 있음을 §5.3 잔여와 혼동 없게 확인.
5. **skills/init/SKILL.md**: ① 파서 게이트 명령을 resolve_rules.py CLI로 상향(D6 — 6단계·7-e 등 모든 게이트 지점) ② 존재 스킬 목록 갱신(fitness·review 실재 — :446 부근 부분 목록과 :344 summary의 review 줄은 이제 참) ③ scaffold 등 여전히 미존재 스킬 언급에 구현 상태 표기 유지 ④ §5.3 인용 지점이 제거된 행을 가리키지 않는지 대조.
6. **README.md**: Phase 1 경계 서술 갱신 — 있는 것에 fitness·review·arch-reviewer·check_imports·resolve_rules·parse_style 추가, 없는 것 목록 축소(7개 스킬), 테스트 수 갱신.

- [ ] **Step 1: 스위프 표 작성 → 일괄 적용.**
- [ ] **Step 2: 검증** — grep 재실행 잔존 0(의도 유지분 근거 표) + `python3 -m unittest discover -s tests` + `wc -l references/governance/architecture-template.md` ≤ 500.
- [ ] **Step 3: Commit** — `git commit --only <위 6파일> -m "docs: Phase 2 구현 반영 — §5.3 축소, 파생 규칙 정본, 게이트 상향"`

---

### Task 13: Phase 2 검증 ①~④

**Files:** `.superpowers/verify2/` 아래 샘플(커밋 안 함), 리포트 `.superpowers/verify2/report.md`

스펙 §12 Phase 2 검증 4건. 샘플은 Phase 1 검증 샘플(.superpowers/verify/{single,mono,green})을 참고하되 새로 만든다.

1. **① 위반 검출**: 최소 kotlin 멀티모듈 샘플(hexagonal 컨텍스트 1개) 생성 → domain 모듈에 `import org.springframework.stereotype.Component` 심기 → `check_imports.py` 실행이 `[hex.domain-no-framework]` 위반을 정확한 파일:라인으로 보고하는지 → fitness 절차로 생성한 Konsist 테스트 파일에 해당 규칙 어서션이 존재하는지 → (java·gradle 사용 가능하면 실제 실행해 실패 확인, 불가하면 환경 부재를 리포트에 기록).
2. **② cqrs 의미론**: 샘플 컨텍스트에 `패턴: cqrs` 선언 + 커맨드 핸들러에 조회 로직 심기 → review 절차대로 arch-reviewer에 cqrs.md 경로를 전달해 검출되는지(중첩 headless 세션 `claude -p --plugin-dir . ...` 또는 Agent 직접 위임 — Phase 1 검증의 중첩 세션 방식 재사용). review-log.jsonl append 확인.
3. **③ 커스텀 스타일**: `docs/architecture/styles/ports-lite.md`(레이어 3 + 규칙 2개 선언) 작성 → `custom/ports-lite` 채택 → resolve_rules OK → fitness 생성물에 같은 파이프라인으로 규칙이 나오는지.
4. **④ app-embedded**: 앱 2개 + 패키지 규약 샘플 → resolve_rules의 파생 3종(앱 봉쇄·공용 방향·컨텍스트 간 금지) 산출 확인 → check_imports가 미포함 컨텍스트 참조를 위반으로 잡는지 → 생성물에 파생 규칙 포함 확인.

각 항목 PASS/FAIL + 증거(명령·출력 발췌)를 리포트에. FAIL은 수정 태스크로 환류한다.

- [ ] **Step 1~4: 검증 수행 + 리포트.**
- [ ] **Step 5: 커밋 없음** (검증 전용 — 트리 클린 확인). 수정이 나오면 해당 파일만 별도 커밋.

## Self-Review 결과

- 스펙 §12 Phase 2 구성요소 대조: fitness(T10)·review(T11)·arch-reviewer(T9)·check_imports(T4)·tactical 5종(T6)·patterns 3종(T7) — 전부 태스크 존재. 검증 ①~④(T13). kotlin-spring rule-mappings는 §10이 요구하고 fitness의 전제라 T5로 포함. 파라미터 셀 파서(어휘 §2 이월)는 T1, §5.3 이월분은 T2·T12.
- 타입 일관성: EffectiveRule/DerivedRule 스키마는 T2가 정의하고 T4·T5·T10이 동일 명세를 인용한다. ParseError는 parse_architecture에서 단일 재사용.
- 플레이스홀더 없음 확인. 각 코드 태스크에 실패 테스트 → 구현 → 통과 사이클 존재.
