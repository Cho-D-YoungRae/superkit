# superarchitect

문서 기반 아키텍처·도메인 거버넌스 Claude Code 플러그인.

LLM은 세션마다 프로젝트의 구조를 처음부터 다시 추측한다. 어제 합의한 경계도, 왜 이 컨텍스트가
`core`인지도 다음 세션에는 남아 있지 않아 매번 그럴듯하지만 조금씩 다른 답이 나온다.
superarchitect는 그 추측을 없애기 위해 **결정을 문서에 고정하고, 기계로 확인할 수 있는 것은 기계가
확인하게 하고, 의미론적 판단만 LLM에 남긴다.** 구조의 진실은 대상 프로젝트 루트의
`ARCHITECTURE.md` 한 파일(SSOT)이고, 파서가 그 문서의 유일한 해석기다.

이 저장소가 곧 플러그인이다(루트에 `.claude-plugin/plugin.json`).

## 설치 (로컬 개발)

```bash
claude --plugin-dir /path/to/superarchitect
```

스킬은 `/superarchitect:<스킬명>`으로 노출된다. `SKILL.md` 본문은 핫리로드되지만
`plugin.json`·훅·에이전트를 고쳤다면 `/reload-plugins`가 필요하다.

## 현재 상태 (Phase 2까지)

이 플러그인은 Phase 2(강제)까지 구현되어 있다. **없는 것을 있는 것처럼 쓰지 않는 것이 이
플러그인의 제1 원칙이므로, 아래 경계를 그대로 지킨다.**

### 지금 있는 것

| 산출물 | 위치 | 하는 일 |
|---|---|---|
| `/superarchitect:init` | `skills/init/` | 질문으로 컨텍스트 경계·분류·스타일·모듈 구성·관계를 확정하고 `ARCHITECTURE.md`와 파생물(`docs/architecture/summary.md`, ADR)을 만든다 |
| `/superarchitect:fitness` | `skills/fitness/` | 유효 규칙을 프로파일의 `rule-mappings.md`로 번역해 Konsist 아키텍처 테스트를 생성·갱신한다. 생성까지가 몫이고 실행은 대상 프로젝트의 빌드가 한다 |
| `/superarchitect:review` | `skills/review/` | 변경을 결정적 검사로 먼저 거른 뒤 의미론 판단만 `arch-reviewer`에 위임하고, 결과를 `review-log.jsonl`에 append한다 |
| `arch-reviewer` 에이전트 | `agents/arch-reviewer.md` | 읽기 전용. 전달받은 지식 문서의 규칙 절과 자유 관측 5범주로만 판정한다 |
| SessionStart 훅 | `hooks/hooks.json` → `scripts/session_summary.sh` | cwd에서 git 루트까지 올라가며 `docs/architecture/summary.md`를 찾아 세션 컨텍스트로 주입한다. 없으면 조용히 종료한다 |
| 결정 템플릿 파서 | `scripts/parse_architecture.py` | `ARCHITECTURE.md`의 필수 결정 누락·비정규 값·깨진 참조를 라인 번호와 함께 보고한다 |
| 스타일 선언 파서 | `scripts/parse_style.py` | 스타일 문서의 `## 선언` 절을 읽어 레이어 목록과 규칙 인스턴스를 만든다. 규칙 어휘 §2·§2.1의 시행자다 |
| 유효 규칙 해석기 | `scripts/resolve_rules.py` | 두 파서를 조인해 `스타일 선언 − 규칙 예외 + 파생 규칙 3종`을 낸다. **`ARCHITECTURE.md`를 검증하는 가장 넓은 게이트** |
| 정적 import 검사기 | `scripts/check_imports.py` | 유효 규칙으로 `.kt`/`.java` 소스를 걸어 위반을 찾는다. fitness 테스트의 앞단에서 빠르게 도는 근사다 |
| 인덱스 생성기 | `scripts/build_index.py` | `references/knowledge/`를 스캔해 `references/INDEX.md`를 다시 만든다 |
| 거버넌스 문서 5종 | `references/governance/` | 결정 템플릿·규칙 어휘·ADR·진화 신호·지식 문서 표준의 정본 |
| `kotlin-spring` 프로파일 | `profiles/kotlin-spring/rule-mappings.md` | primitive 5종 + 파생 3종 → Konsist 코드 번역의 정본 |
| 지식 문서 18종 | `references/knowledge/` | 성숙 17 / draft 1. INDEX를 거쳐 필요한 것만 선별해 읽는다 |
| `study` 스킬 | `.claude/skills/study/` | 이 저장소 전용. 지식 베이스를 키운다(아래 참조) |

검증 실행 — `resolve_rules.py`가 가장 넓게 본다(`parse_architecture.py`의 검사를 포함하면서 스타일
문서까지 읽는다).

```bash
python3 scripts/resolve_rules.py ARCHITECTURE.md   # 0=OK, 1=해석 오류, 2=사용법 오류
python3 scripts/check_imports.py ARCHITECTURE.md   # 0=위반 없음, 1=위반, 2=해석 불가
```

**두 스크립트의 exit 의미가 다르다.** `check_imports.py`의 1은 정상 판정 결과(위반 발견)이고,
`resolve_rules.py`의 1은 해석 실패다. CI에서 같게 다루지 않는다.

### 아직 없는 것

- **나머지 스킬 일곱 개** — `scaffold`, `adr`, `sync`, `evolve`, `migrate`, `model`, `apply`.
  지금 노출되는 스킬은 `init`·`fitness`·`review` 셋이다.
- **`java-spring` 프로파일**(Phase 6) — `profiles/java-spring/`은 빈 디렉터리다. Java 프로젝트를
  선언할 수는 있지만 fitness는 매핑 부재를 알리고 생성하지 않는다.
- **`baseline.jsonl`과 진화 신호 수집**(Phase 5) — `이행`을 선언해도 baseline은 동결되지 않으므로
  생성된 테스트는 기존 위반도 전부 blocker로 다룬다. `collect_signals.py`·`evolve`도 없다.
- **`templates/`**(Phase 4) — scaffold가 쓸 골격은 어느 프로파일에도 없다.

거버넌스 문서 안에서 "아직 시행되지 않는 조항"은 각 문서의 구현 상태 블록에 모아 두었다
(`references/governance/architecture-template.md` §5.3이 그 형식의 기준이다). 문서가 요구하는데
기계가 확인하지 않는 항목의 공통 실패 모드는 오류가 아니라 **침묵**이므로, 그 목록을 지우는 것은
구현이 도착했을 때뿐이다.

## 테스트

```bash
python3 -m unittest discover -s tests
```

221개 테스트가 돈다. **`pytest`를 쓰지 않는다** — 스크립트도 테스트도 Python 표준 라이브러리에만
의존하므로 설치할 것이 없다(PyYAML도 쓰지 않는다. frontmatter는 제한 문법 자체 파서로 읽는다).

## 지식 추가 절차

지식 베이스는 `references/knowledge/<topic>/<key>.md` **정확히 한 단계**다. 더 깊이 중첩하면
`build_index.py`가 오류로 거부한다.

**`study` 스킬로** — 이 저장소에서 "지식 추가", "이 문서 보완해줘", `/study`라고 요청하면 INDEX와
대조해 신규 작성 또는 기존 문서 보완을 진행하고 INDEX 재생성까지 한다. 이 저장소 로컬 스킬이라
대상 프로젝트에는 배포되지 않는다.

**손으로 할 때** — 세 단계가 전부다.

1. `references/knowledge/<topic>/<새파일>.md`를 만든다. `<topic>`은 기존 디렉터리
   (`strategic`, `tactical`, `patterns`, `structure`, `styles`) 중 하나이거나 새로 만든 하나다.
   파일명이 곧 `key`이고 `knowledge/` 전체에서 유일해야 한다.
2. 맨 위에 frontmatter로 `summary` 한 줄을 넣는다. 유일한 필수 필드다.
   ```markdown
   ---
   summary: 한 줄 요약
   read_when: [init, review]
   ---
   ```
3. `python3 scripts/build_index.py`를 실행해 `references/INDEX.md`를 갱신한다.

문서는 본문에 `## 적용 기준`과 `## 규칙` **레벨 2 헤딩이 둘 다** 생길 때까지 `draft`로 등재된다.
**draft 문서는 배경 설명으로 인용해도 되지만 판정 근거로 삼을 수 없다** — 완벽보다 존재가
우선이므로 얇은 초안을 올리는 것은 정상이고, 대신 그것이 판정에 쓰이지 않도록 막는 장치가 draft
플래그다. 자세한 규칙(frontmatter 제한 문법, 분량, 승격 절차)은
`references/governance/knowledge-doc-template.md`에 있다.

## 저장소 구조

```
.claude-plugin/plugin.json   플러그인 매니페스트
.claude/skills/study/        이 저장소 전용 스킬 (배포되지 않음)
skills/init|fitness|review/  /superarchitect:<스킬명>
agents/arch-reviewer.md      review가 의미론 판단만 위임하는 읽기 전용 에이전트
hooks/hooks.json             SessionStart 훅 등록
scripts/
  parse_architecture.py      ARCHITECTURE.md 파서 — 결정 템플릿의 유일한 해석기
  parse_style.py             스타일 선언 파서 — 규칙 어휘의 시행자
  resolve_rules.py           유효 규칙 해석기 — 두 파서를 조인하는 최상층
  check_imports.py           정적 import 검사기 — 해석 결과의 첫 소비자
  build_index.py             references/INDEX.md 생성기
  session_summary.sh         SessionStart 훅 본체
profiles/                    kotlin-spring (있음), java-spring (Phase 6)
references/
  INDEX.md                   생성물 — 직접 고치지 말고 build_index.py를 다시 돌린다
  governance/                결정 템플릿·규칙 어휘·ADR·진화 신호·문서 표준의 정본
  knowledge/<topic>/         아키텍처 지식 문서 (INDEX 경유 선별 로드)
tests/                       python3 -m unittest
docs/superpowers/            설계 스펙과 구현 계획
```
