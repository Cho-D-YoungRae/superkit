# 스킬 공통 규약 — 정본

이 문서는 superdomain 스킬 8종(init·model·apply·adr·review·sync·evolve·migrate)이 함께 따르는
절차의 정본이다. 각 스킬은 여기의 절을 한 줄로 지목하고 본문을 되풀이하지 않는다 — 같은 규칙이
여러 스킬에 복사되면 한 곳만 고쳐지는 순간 스킬끼리 다른 말을 한다(0.2.0의 라우팅 모순이 그렇게
생겼다). 스킬 본문과 이 문서가 어긋나면 이 문서가 이긴다.

## 1. 산출물 배치

대상 프로젝트에 superdomain이 만드는 파일은 전부 `docs/superdomain/` 아래에 있다. 경로의 기계적
정본은 `scripts/layout.py`다.

| 경로 | 무엇 | 쓰는 스킬 |
|---|---|---|
| `docs/superdomain/DOMAIN.md` | 도메인 SSOT — 경계·분류·패키지·관계 | init(생성) · sync·evolve(확정받은 편집) · 사용자(adr이 짚은 편집) |
| `docs/superdomain/summary.md` | SessionStart 훅이 주입하는 요약(30줄 이하) | init·sync·evolve(재생성) |
| `docs/superdomain/contexts/<컨텍스트>.md` | 불변식·애그리거트·값 객체·도메인 이벤트·도메인 서비스·열린 질문. 컨텍스트가 하나여도 이 자리다 | model(본문) · apply·review(열린 질문 append) |
| `docs/superdomain/adr/yyyy-MM-dd-slug.md` | MADR 결정 기록 | adr · init · evolve(`proposed` 초안) |
| `docs/superdomain/conventions/<key>.md` | 선언에 자리가 없는 팀 규약 | 사용자(스킬은 승격을 제안만 한다) |
| `docs/superdomain/state/baseline.jsonl` | 동결된 격리 위반 | init(동결) · migrate(축소) |
| `docs/superdomain/state/review-log.jsonl` | 리뷰 판정 이력 | review(append) |

**작업 기준은 git 루트다.** 하위 디렉터리에서 시작했어도 `git rev-parse --show-toplevel`로 올라와서
작업한다. git 저장소가 아니면 그 사실을 알리고 현재 디렉터리를 루트로 삼을지 확인한다.

## 2. 스크립트 호출

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/<스크립트>.py" docs/superdomain/DOMAIN.md [플래그]
```

| 스크립트 | 0 | 1 | 2 | 플래그 |
|---|---|---|---|---|
| `parse_domain.py` | OK | 해석 오류 | 사용법·배치 오류 | 없음 |
| `check_imports.py` | 위반 없음 | 위반 발견 | 해석 불가·사용법·배치 오류 | `--json` |
| `check_invariants.py` | 위반 없음 | 위반 발견 **또는 검사 불능** | 해석 불가·사용법·배치 오류 | `--json`, `--context <이름>` |
| `collect_signals.py` | 산출 | 산출 불가 | 사용법·배치 오류 | `--json`, `--since <rev\|날짜>` |

- **네 스크립트의 1은 뜻이 다르다.** exit만 보고 판정하지 않는다 — 출력을 읽는다. 특히
  `check_invariants.py`의 1은 위반과 `검사 불능`을 겸하므로 exit로 건수를 세지 않는다.
- **배치 오류(exit 2이고 stderr가 "옛 배치" 또는 "이행이 끝나지 않았습니다"로 시작)는 §3-3으로
  간다.** 출력을 그대로 보여 주고 멈춘다.
- 서브에이전트에 지식 문서 경로를 넘길 때는 **셸에서 전개된 절대경로**로 적는다. 문자열
  `${CLAUDE_PLUGIN_ROOT}`를 그대로 넘기지 않는다 — 스킬 본문에서 이미 절대경로로 보이면 그대로
  쓰고, 아니면 `echo "${CLAUDE_PLUGIN_ROOT}"`로 값을 확인해 붙인다.

## 3. 초기화 게이트

init을 뺀 모든 스킬의 0단계다. init에는 3의 중단만 적용되고, 4의 갈래(선언이 없다)는 init이 할 일이다.

1. git 루트로 올라간다(§1).
2. 배치를 확인한다 — 선언 파일이 없어도 돌린다. 옛 배치 판정의 정본은 `scripts/layout.py`이고,
   스킬은 그 판정 규칙을 글로 되풀이하지 않는다.

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/parse_domain.py" docs/superdomain/DOMAIN.md
   ```

   exit가 2가 아니고 `docs/superdomain/DOMAIN.md`가 있으면 **통과**한다. 해석 오류(exit 1)는 각
   스킬이 자기 단계에서 다룬다.
3. **exit 2면 이행 문제다.** stderr를 그대로 보여 준다 — "옛 배치(superdomain 0.2.x)입니다"로
   시작하면 옮길 명령(`mkdir -p`·`git mv`) 목록이고, "이행이 끝나지 않았습니다"로 시작하면 새
   선언은 있는데 옛 자리에 남은 산출물 목록이다. 아래를 알린 뒤 **중단**한다. 이행은 사용자가
   한다 — 스킬이 대신 옮기지 않는다. 남은 산출물을 두고 진행하지 않는 이유는 옛 자리의 문서를
   어떤 검사도 읽지 않아 그 안의 불변식·부채가 검사에서 빠지기 때문이다.

   > superdomain 0.3.0부터 산출물 위치가 `docs/superdomain/`으로 바뀌었습니다. 위 출력과
   > `${CLAUDE_PLUGIN_ROOT}/CHANGELOG.md`의 0.3.0 이행 절차를 따른 뒤 다시 실행하세요.

4. exit가 2가 아니고 `docs/superdomain/DOMAIN.md`가 없으면 아래를 알리고 **중단**한다.

   > superdomain이 초기화되지 않았습니다. `/superdomain:init`으로 도메인 경계 선언을 먼저 세우세요.

## 4. 확정은 사용자의 것이다

스킬은 관측과 지식 문서를 근거로 **판단을 적극적으로 제안한다.** 금지되는 것은 사용자 확인 없는
**확정**(선언 편집·상태 승격·파일 생성과 삭제·착수) 하나뿐이다. 판단을 아끼라는 뜻이 아니다 —
"알아서 해 달라"는 요청에도 근거와 함께 하나를 제안하고, 동의를 받은 뒤에 적는다. 무엇이 확정
대상인지는 각 스킬이 정한다. 모델이 조용히 정해 버리면 이 플러그인이 없애려는 문제(세션마다
다른 추측)가 재현된다.

## 5. 지식 참조 프로토콜

1. 지식이 필요하면 **먼저 `${CLAUDE_PLUGIN_ROOT}/references/INDEX.md`를 읽는다.**
2. 필요한 문서만 연다 — 경로는 `${CLAUDE_PLUGIN_ROOT}/references/knowledge/<topic>/<key>.md`.
   `references/knowledge/`를 통째로 또는 디렉터리 단위로 읽지 않는다.
3. 고르는 기준은 셋이다: INDEX의 `read_when`에 이 스킬 이름이 있고 **이번 작업에 실제로
   해당하는** 문서, 대상 컨텍스트가 `- 패턴:`으로 선언한 key의 문서, 대상 프로젝트의
   `docs/superdomain/conventions/` 문서(같은 주제면 **로컬이 이긴다**). 각 스킬은 여기에 더해 어느
   단계에서 어느 문서를 여는지를 정할 수 있다.
4. INDEX의 `draft` 칸이 찬 문서는 배경으로 인용할 수 있지만 **판정·구현 규칙의 근거로 쓰지 않는다.**
5. 스킬은 정본의 라벨 목록·정규 값·체크리스트를 복제하지 않는다 — 단계가 지시하는 시점에 정본을
   읽는다. 정본이 바뀌면 스킬은 고치지 않아도 맞는다.

## 6. check_imports 결과 해석

"위반 없음"과 "검사한 것이 0개"는 다른 상태다. 아래 채널은 **어느 exit에서든** 그대로 보고한다 —
침묵을 통과로 읽지 않는다. 각 채널을 **어떻게 처리할지**는 각 스킬이 정한다.

| 채널 | `--json` 키 | 텍스트 모양 | 뜻 |
|---|---|---|---|
| 위반 | `violations[]` (`from_context`·`to_context` 포함) | `경로:라인: [derived.context-isolation] 메시지` | 관계 표에 없는 쌍의 참조. exit 1 |
| 기존 부채 | `baseline.demoted[]` | `[기존 부채] 경로:라인: …` | baseline에 동결된 위반. exit에 반영되지 않는다 |
| 0건 경고 | `zero_match[]` | `[0건 경고] <rule id>: …` | 컨텍스트 패키지에 귀속된 소스가 0건 — 패키지 선언과 실제의 어긋남 가능성 |
| 생략 | `skipped[]` | 푸터의 `생략: …` | 검사가 서지 않았다 — 경로 부재·경로가 디렉터리 아님·소스 0건·있는 소스를 전부 읽지 못함·선언된 컨텍스트 0건(다섯 갈래를 뭉뚱그리지 않는다) |
| 귀속 불신 | `ambiguous_package[]` | 푸터의 `package 선언이 여러 건인 소스 …` | 그 파일의 귀속과 판정을 믿을 수 없다 |
| 읽지 못함 | `unreadable[]` | 푸터의 `읽지 못한 소스 …` | 검사에서 빠진 사각지대 |
| 한계(검사 범위) | 없음 — 텍스트 전용 | 푸터의 `한계: 같은 패키지 안의 참조와 …` | import 없는 참조(같은 패키지·FQN)는 보지 못한다. 언제나 나온다 — 위반 0건이 누수 0건을 뜻하지 않는다 |
| 한계(부채 매칭) | `baseline.note`(baseline이 있을 때) | 푸터의 `한계: 부채 매칭 키는 …` | 부채 매칭 키가 (규칙 id, 경로)뿐이라 같은 파일의 추가 위반도 기존 부채로 흡수된다 |

컨텍스트 쌍은 `violations[].from_context`·`to_context`(부채는 `baseline.demoted[]`의 같은 키)에서
읽는다. **메시지 문자열을 파싱하지 않는다.**

## 7. 관계 표 — 쌍이고 방향이 없다

`### 관계` 표의 한 줄이 여는 것은 **쌍**이고 방향을 구분하지 않는다 — 어느 컨텍스트 섹션에 적든
같은 선언이고, 유형(`customer-supplier`·`acl` 등)은 설계 의도의 기록이지 허용 방향을 바꾸는
입력이 아니다(정본: `references/knowledge/strategic/context-mapping.md` R1). **한 줄을 열면 그 두
컨텍스트 사이의 격리 검사가 영구히 꺼진다** — 그래서 쌍을 여는 결정에는 근거 ADR이 있어야 하고,
그 기록은 `/superdomain:adr`이 남긴다.

## 8. 열린 질문 append

형식과 규율의 정본은 `${CLAUDE_PLUGIN_ROOT}/references/governance/domain-doc-template.md` §5다.
요지만 적는다.

- 대상은 `docs/superdomain/contexts/<컨텍스트>.md`의 `## 열린 질문` 절 **끝**이다. append만 한다 —
  다른 절을 고치거나 재생성하지 않는다. 절이 없으면 문서 끝에 헤딩을 만들고 그 아래에 쓴다.
- 한 줄 체크박스 불릿: `- [ ] [<YYYY-MM-DD> <스킬>] <질문>`. review가 붙이는 항목만
  뒤에 `(관측: <경로:라인>)`을 단다. **`- [ ]`를 빠뜨리지 않는다** — model이 다음
  세션의 안건을 고르는 기준이 빈 체크박스다.
- 같은 질문이 이미 있으면 넣지 않는다. 추가한 줄은 리포트에 그대로 보여 준다.
- 문서가 없으면 만들지 않는다 — 리포트에 남기고 `/superdomain:model`을 안내한다.
- 쓰는 스킬은 model·apply·review 셋뿐이다.

## 9. 라우팅 — 어떤 상황에 어느 스킬인가

이 표가 라우팅의 유일한 정본이다. README는 이 표를 요약하고, 각 스킬의 description은 이 표와 같은
문장을 쓴다(§10).

| 상황 | 스킬 |
|---|---|
| `docs/superdomain/DOMAIN.md`가 없다(옛 배치가 아님) · 컨텍스트를 신설·병합·분리한다 · `- 패키지:`를 바꾼다 · 기존 격리 위반을 동결한다 | `init` |
| 옛 배치(0.2.x)다 · 이행이 덜 끝났다(§3-3) | 스킬이 아니다 — `CHANGELOG.md` 0.3.0 이행 절차 |
| 업무 규칙을 불변식으로 정리한다 · 열린 질문이 쌓였다 | `model` |
| `confirmed` 불변식에 대응 테스트 태그가 없다 | `apply` |
| `- 분류:`·`- 패턴:`·`### 관계` 쌍을 바꾸는 결정 · 되돌리기 비싼 결정을 기록한다 | `adr` — 편집 자리를 짚고, 편집은 사용자가 한다 |
| PR·커밋 전에 변경이 경계를 넘었는지 본다 | `review` |
| 선언과 디스크가 어긋났는지 본다 · 선언된 컨텍스트의 패키지 디렉터리를 만든다 · 파생물이 낡았다 | `sync` |
| 회고 자리 · 같은 지적이 반복된다 · 분류나 경계가 아직 맞는지 묻는다 | `evolve` — 수락된 분류·관계 제안은 선언까지 반영하고, 경계 재획정은 `init`으로 넘긴다 |
| `docs/superdomain/state/baseline.jsonl`의 부채를 줄인다 | `migrate` |

**선언 변경의 경로를 한 문장으로:** 선언을 바꾸는 결정은 `adr`이 편집 자리를 짚고, 경계
재획정과 `- 패키지:` 변경만 `init`이 받는다. `sync`는 드리프트 처분으로 확정받은 편집을,
`evolve`는 수락된 제안을 반영한다. 나머지 스킬(model·apply·review·migrate)은 `DOMAIN.md`를 읽기만 한다.

## 10. description 작성 규칙

description은 매 세션 컨텍스트에 상주하고, 모델이 스킬을 고르는 근거다.

- 무엇을 하는지 → 트리거 문구 → **가장 헷갈리는 이웃 1~2개만** "쓰지 않는 경우"로 적는다. 이웃을
  전부 나열하지 않는다.
- 선언 변경을 언급할 때는 §9의 한 문장과 같은 뜻으로 쓴다. "분류·관계 변경은 init" 같은 문장을
  쓰지 않는다.
