# superarchitect Phase 3 (도메인) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 질문 주도 도메인 모델링을 플러그인에 넣는다 — domain 문서 표준(domain-doc-template), model 스킬(인터뷰·이벤트 스토밍·미팅 정리), apply 스킬(문서→코드 inside-out), check_invariants.py(불변식 ID ↔ 테스트 태그 결정적 대조), event-storming 성숙화, 그리고 Phase 2가 열어 둔 도메인 훅(arch-reviewer C3 완화·review의 구현 상태 블록·aggregates R4)의 마감.

**Architecture:** domain 문서는 SSOT(파생물 아님)이고 결정 템플릿과 같은 파싱 철학(헤딩·표·라벨, 알려진 것만 읽기)을 따른다. 결정적 게이트는 check_invariants.py 하나 — confirmed 불변식마다 대응 테스트 태그의 존재를 대조하고, 문서 구조 오류(중복 ID·비정규 상태·형식 위반)도 같은 CLI가 잡는다. model은 제안-확정 분리(불변 1)를 지키는 인터뷰 절차, apply는 confirmed만 구현하는 실행 절차다.

**Tech Stack:** bash + python3 stdlib만. 테스트 `python3 -m unittest discover -s tests`(현재 221). 대상 테스트 태그는 JUnit5 `@Tag("INV-...")`.

**요구사항 소스:** 스펙 §5(산출물 규격), §6.3-4·6.9·6.10, §12 Phase 3. Phase 2 원장의 이월: arch-reviewer C3 완화 제거(T9 우려), review SKILL check_invariants 상태 블록 제거(T11), aggregates R4 상태 블록(T6), INDEX draft 마지막 1건(event-storming).

## Global Constraints

- 스크립트 stdlib만. SKILL ≤500줄, description ≤1,536자(트리거·비트리거). knowledge 문서 150~300줄, `## 적용 기준`·`## 규칙` 레벨-2 정확 일치.
- 미구현 참조는 구현 상태 블록 — 제거는 착지 확인 후에만. INDEX는 마지막 정리 태스크에서만 재생성.
- 커밋 `git commit --only <자기 경로>`. 오류 메시지 한국어 `경로:라인: 메시지`. 임시 파일은 `.superpowers/`.
- **불변 1(정본: skills/init/SKILL.md·메모리)**: 판단 제안은 적극, 사용자 확인 없는 **확정**만 금지. model의 confirmed 승격·apply의 구현 대상 선정 모두 이 원칙 아래.
- exit 계약 통일: 검사 스크립트는 check_imports와 동일(0 클린 / 1 위반 / 2 해석 불가) — docstring 머리에 명기.

## 컨트롤러 확정 결정

**P3-D1. 불변식 ID 형식.** `INV-<컨텍스트 대문자>-<3자리>` — 컨텍스트명은 선언명을 대문자화(하이픈 유지, 예: `core-api` → `INV-CORE-API-001`). 파싱은 접두 `INV-` 제거 후 **선언된 컨텍스트 집합 기반 최장 일치**(하이픈 중의성 제거). 대조 실패(어느 컨텍스트에도 못 붙는 ID)는 오류.

**P3-D2. domain 문서 위치·파싱 계약.** 위치는 `docs/architecture/domain/<context>.md`, 컨텍스트가 1개뿐인 프로젝트는 `docs/architecture/DOMAIN.md` 허용(스펙 §5) — check_invariants는 두 위치를 모두 찾고, 같은 컨텍스트가 양쪽에 있으면 오류. 불변식은 `## 불변식` 아래 표(열 순서 고정: ID, 서술, 상태)로 선언한다 — 표가 곧 기계 계약이고 그 밖 섹션(애그리거트·VO·이벤트·도메인 서비스·열린 질문)은 자유 서술+권장 구조(파서는 읽지 않음, 스킬이 관리). 상태 정규 값 `proposed | confirmed` 만.

**P3-D3. check_invariants의 정직성(=D4 연장).** confirmed인데 태그 없음 → 위반. 태그는 있는데 문서에 없는 ID → 경고(드리프트 — sync 도착 전까지 이 채널이 유일). proposed인데 태그 있음 → 경고(확정 전 구현). 테스트 소스 0건(테스트 디렉터리 부재 포함) → "검사 불능" 고지와 함께 confirmed 위반으로 처리하지 않고 **exit 1 + 사유**(침묵 통과 금지 — 태그가 있을 수 없는 환경에서 클린 판정을 내리지 않는다).

**P3-D4. 태그 스캔 범위.** 선언된 프로젝트 경로 아래 테스트 소스(`src/test/`·`test/` 및 `아키텍처 테스트 위치`)의 `.kt`/`.java`에서 `@Tag("INV-...")` 리터럴(정규식, 여러 개/줄 허용). FQN·상수 간접 참조는 보지 못함 — 한계 푸터에 명시.

**P3-D5. review의 discussion 루프 마감.** T11이 이미 append 절차를 갖고 있으므로 Phase 3의 일은 (a) domain 문서가 실재하는 표준이 되고 (b) review SKILL의 check_invariants 구현 상태 블록을 실행 지시로 교체하는 것. arch-reviewer C3의 "Phase 3 예정" 완화 문장도 제거(그 자리에는 §3 원칙 — 결정적 검사가 잡는 것 보고 금지 — 만 남는다).

## 파일 구조

```
생성:
  references/governance/domain-doc-template.md     # T1
  scripts/check_invariants.py                      # T3
  tests/test_check_invariants.py                   # T3
  skills/model/SKILL.md                            # T4
  skills/apply/SKILL.md                            # T5
수정:
  references/knowledge/strategic/event-storming.md # T2 (스텁 → 성숙; 마지막 draft 해소)
  skills/review/SKILL.md                           # T6 (상태 블록 → 실행 지시)
  agents/arch-reviewer.md                          # T6 (C3 완화 제거)
  references/knowledge/tactical/aggregates.md      # T6 (R4 상태 블록 제거)
  skills/init/SKILL.md                             # T6 (model·apply 실재 반영 — 스킬 목록)
  README.md                                        # T6 (경계 갱신)
  references/INDEX.md                              # T6 재생성 (draft 0 도달)
```

| 웨이브 | 태스크 |
|---|---|
| A (병렬) | T1(domain-doc-template), T2(event-storming) |
| B | T3(check_invariants — T1의 표 계약 소비) |
| C (병렬) | T4(model — T1·T2 소비), T5(apply — T1·T3 소비) |
| D | T6(스위프·INDEX), T7(Phase 3 검증) |

---

### Task 1: governance/domain-doc-template.md

**Files:** Create: `references/governance/domain-doc-template.md` (~180줄)

**필독:** 스펙 §5(:238 문단 — 문서 구성 요구 전부), P3-D1·D2. 하우스 참고: knowledge-doc-template.md(문서 표준의 서술 방식), architecture-template.md(표-계약 서술 방식 — "파서는 아는 것만 읽는다").

**고정 요구:** ① 문서 스켈레톤(그대로 복사해 쓰는 블록 — `# <컨텍스트> — Domain`, `## 불변식` 표(ID/서술/상태), `## 애그리거트`(경계 표: 애그리거트/루트/포함/불변식 ID), `## 값 객체`, `## 도메인 이벤트`(이벤트/발행 시점/스키마), `## 도메인 서비스`, `## 열린 질문`(체크박스 목록 — model·review가 append), mermaid 병기 위치) ② 파싱 계약 — 기계가 읽는 것은 `## 불변식` 표뿐(열 순서 고정), 상태 정규 값 2종, ID 형식(P3-D1)과 최장 일치 규칙, 컨텍스트 1개 프로젝트의 DOMAIN.md 통합 규칙과 중복 배치 오류 ③ 용어 정의를 쓰지 않는다(superglossery 위임 — 참조만) ④ domain-pure 스타일 컨텍스트에 필수·layered-simple에 선택(스펙 §5) ⑤ 소유권 — 이 문서는 SSOT(파생물 헤더 없음), model·apply·review가 관리하고 사람이 직접 편집해도 된다 ⑥ 구현 상태: check_invariants는 이 Phase에서 함께 착지하므로 현재형 서술 허용하되 T3 완료 전 커밋되므로 "이 Phase에서 도착"의 한 줄 표기(T6 스위프가 제거).

- [ ] **Step 1: 작성.** 스켈레톤 블록은 T3의 테스트 픽스처가 그대로 복사해 파싱 성공해야 한다(Interfaces: T3가 이 블록을 정본 픽스처로 사용).
- [ ] **Step 2: 검증** — 스켈레톤의 표를 눈으로 재확인(열 순서·정규 값), 줄 수.
- [ ] **Step 3: Commit** — `git commit --only references/governance/domain-doc-template.md -m "feat: domain 문서 표준 — 불변식 표 계약과 스켈레톤"`

---

### Task 2: strategic/event-storming.md 성숙화

**Files:** Modify: `references/knowledge/strategic/event-storming.md` (스텁 → 150~300줄)

**필독:** 스텁의 "담을 내용", 스펙 §6.9(스토밍 모드 문면 — "도메인 이벤트를 과거형으로 나열 → 커맨드·액터 연결 → 애그리거트 후보로 묶기 → 컨텍스트 경계·핫스팟 표시"), 기존 성숙 문서 하우스 스타일.

**고정 요구:** ① 텍스트 채팅 기반 진행 규약 — 단계별(이벤트 수집→타임라인 정렬→커맨드·액터→애그리거트 후보→경계·핫스팟) 진행 문형과 촉진 질문, 각 단계의 산출 형식(모델이 세션 중 유지하는 목록 형식) ② `## 적용 기준` — 언제 스토밍이 인터뷰보다 나은가/언제 과하다 ③ `## 규칙` — 진행 규율 체크리스트(한 번에 한 단계, 과거형 강제, 이벤트에 주어 금지 등) + 결과 반영 규칙(domain 문서의 어느 절로, 컨텍스트 맵에 무엇을) ④ 사례 — 짧은 세션 발췌 1개(모델·사용자 대화 형식) ⑤ [[bounded-contexts]]·[[domain-events]]·[[aggregates]] 링크.

- [ ] **Step 1: 작성** (frontmatter summary 유지·정밀화, read_when 유지).
- [ ] **Step 2: 검증** — build_index 드라이런 draft 해제(단, INDEX 커밋은 T6).
- [ ] **Step 3: Commit** — `git commit --only references/knowledge/strategic/event-storming.md -m "docs: event-storming 성숙화 — 텍스트 진행 규약"`

---

### Task 3: check_invariants.py

**Files:** Create: `scripts/check_invariants.py`, `tests/test_check_invariants.py`

**Interfaces (Consumes):** `parse_architecture.parse_architecture/normalize`(컨텍스트·프로젝트 경로), T1 스켈레톤(픽스처 정본). **Produces:** CLI `python3 scripts/check_invariants.py <ARCHITECTURE.md> [--context <이름>] [--json]`.

**동작(P3-D1~D4 그대로):** ① ARCHITECTURE.md 파싱(오류 시 exit 2) → 선언 컨텍스트 집합 ② domain 문서 발견(domain/<context>.md + DOMAIN.md, 중복 배치 오류) ③ `## 불변식` 표 파싱 — 열 3(ID/서술/상태), 상태 정규 값 검증, ID 형식·최장 일치 검증, 중복 ID 오류. 표 없는 domain 문서 = "불변식 0건" 고지(오류 아님) ④ 테스트 소스 스캔(P3-D4) → 태그 집합 ⑤ 판정: confirmed−태그 = 위반(`문서경로:행: [INV-...] confirmed 불변식에 대응 테스트 태그가 없습니다`), 태그−문서 = 경고(고아 태그), proposed∩태그 = 경고 ⑥ 테스트 소스 0건 = exit 1 + "검사 불능: 테스트 소스가 없습니다 — confirmed N건을 대조할 수 없습니다"(P3-D3) ⑦ 푸터: 대조 N건/위반/경고/한계(FQN·상수 태그 불가시) ⑧ --json.

- [ ] **Step 1: 실패 테스트** — 케이스: 정본 스켈레톤 파싱 성공 / confirmed 미태그 위반(행 번호) / 고아 태그 경고 / proposed 태그 경고 / 중복 ID·비정규 상태·형식 위반 오류 / 하이픈 컨텍스트 최장 일치(`core-api`) / DOMAIN.md 통합·중복 배치 오류 / 테스트 소스 0건 exit 1 / 클린 케이스 exit 0 / --json 구조. 임시 트리는 기존 관례.
- [ ] **Step 2: RED 확인. Step 3: 구현. Step 4: 전체 스위트(221+신규).**
- [ ] **Step 5: Commit** — `git commit --only scripts/check_invariants.py tests/test_check_invariants.py -m "feat: check_invariants — confirmed 불변식 ↔ 테스트 태그 결정적 대조"`

---

### Task 4: skills/model/SKILL.md

**Files:** Create: `skills/model/SKILL.md` (~380줄 이내)

**필독:** 스펙 §6.9 전체(3모드·6단계), T1 표준, T2 규약, 불변 1(init SKILL의 문면), skills/review/SKILL.md(열린 질문 append 형식 — 동일 규약 사용).

**절차(고정):** ① 초기화 게이트(공통 규칙) + 대상 컨텍스트 결정(인자 없으면 선언 컨텍스트 제시·선택) ② 세션 유형 3종 제안(인터뷰 기본 / 이벤트 스토밍 — 도메인이 넓거나 처음, event-storming.md 읽고 규약대로 / 미팅 정리 — 붙여넣은 내용 구조화) — 상황 관찰 근거와 함께 하나를 권하되 선택은 사용자 ③ domain 문서 로드(없으면 T1 스켈레톤으로 생성 — 파생물 헤더 없음), 기존 열린 질문부터 안건 ④ **한 번에 하나씩** 질문 — 불변식 유도 질문 문형(스펙 §6.9-2의 4종 + 경계·동시성·시점), 답변 즉시 `INV-<CTX>-NNN` 채번(다음 번호 규칙: 문서 내 최대+1) proposed로 표에 추가 ⑤ 불변식이 모이면 tactical 문서(INDEX 경유 선별 — aggregates·value-objects·domain-events)를 근거로 애그리거트 경계·VO·이벤트 후보 제안 → 사용자 확인 후 해당 절 반영 ⑥ **confirmed 승격은 항목별 사용자 확정으로만**(일괄 승격 금지 — 불변 1의 확정 규율). 합의 안 된 것은 proposed 유지 또는 열린 질문 추가 — 분석 완결 강박 금지(스펙 "문서는 코드와 함께 자란다") ⑦ 새 용어 등장 시 superglossery(`/glossary:add`) 등록 제안 — 정의를 이 문서에 쓰지 않기 ⑧ 종료: 이번 세션 confirmed 요약 + `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_invariants.py` 실행(새 confirmed가 미구현이면 위반이 정상 — "apply로 구현하라"는 다음 행동 안내) + `/superarchitect:apply` 권유.

**금지:** 사용자 확인 없는 confirmed 승격, 스킬이 임의로 불변식 서술 각색(사용자 문장 우선·다듬기는 제안으로), ARCHITECTURE.md 수정(컨텍스트 경계 변화 제안이 나오면 init/adr 안내만).

**description 초안 요소:** 무엇(질문 주도 도메인 모델링 — 불변식·애그리거트·이벤트를 domain 문서로) + 트리거("도메인 모델링", "도메인 정리", "이벤트 스토밍", "미팅 내용 정리", "domain modeling", "/superarchitect:model") + 비트리거(구현은 apply, 구조 선언은 init).

- [ ] **Step 1: 작성. Step 2: 스펙 §6.9 문장별 커버 대조표 + description 자수. Step 3: Commit** — `git commit --only skills/model -m "feat: model 스킬 — 인터뷰·스토밍·미팅 정리 3모드"`

---

### Task 5: skills/apply/SKILL.md

**Files:** Create: `skills/apply/SKILL.md` (~300줄 이내)

**필독:** 스펙 §6.10 전체, T1 표준, check_invariants CLI(T3), 스타일 선언(레이어 배치 — 구현 위치 결정), persistence.md·aggregates.md(inside-out 구현의 판정 근거).

**절차(고정):** ① 게이트 + 대상 컨텍스트/domain 문서 로드(없으면 model 안내 중단) ② **confirmed 미구현 추출** — check_invariants 실행 결과의 위반 목록이 곧 작업 목록(직접 재스캔 금지 — 결정적 결과 재사용), 애그리거트·VO 타입 존재는 선언된 레이어 패턴 아래 타입 검색으로 확인 ③ 구현 순서 inside-out 고정: 도메인 코어(불변식 강제 로직 — 스타일의 domain 레이어 패턴 위치에) → 불변식당 `@Tag("INV-...")` 테스트(태그는 confirmed ID 그대로) → 최소 퍼사드·포트 ④ **proposed는 구현하지 않는다** — 목록에 있으면 "model로 확정 먼저" 안내 ⑤ 구현 중 모호·모순 발견 시 임의 해석 금지 — 열린 질문 append(재작성 금지, review와 같은 형식) ⑥ 완료 후 결정적 게이트: check_invariants(위반 0 확인) + check_imports(새 코드가 아키텍처 규칙 위반하지 않는지) — 실패 시 보고하고 수정, 통과까지가 완료 ⑦ 커밋 제안(자동 커밋 금지).

**금지:** proposed 구현, 도메인 코어보다 어댑터 먼저, 태그 없는 불변식 테스트, domain 문서의 confirmed 임의 수정.

**description 초안 요소:** 무엇(domain 문서의 confirmed 항목을 코드로 — inside-out) + 트리거("도메인 문서 적용", "불변식 구현", "apply domain", "/superarchitect:apply") + 비트리거(모델 정리는 model, 구조 골격은 scaffold(Phase 4 — 구현 상태)).

- [ ] **Step 1: 작성. Step 2: §6.10 문장별 커버 대조표. Step 3: Commit** — `git commit --only skills/apply -m "feat: apply 스킬 — confirmed 불변식의 inside-out 구현"`

---

### Task 6: Phase 3 스위프

**Files:** Modify: `skills/review/SKILL.md`, `agents/arch-reviewer.md`, `references/knowledge/tactical/aggregates.md`, `skills/init/SKILL.md`, `README.md`, `references/INDEX.md`(재생성)

**방법: sweep-before-edit.** 고정 처분: ① review SKILL — check_invariants 구현 상태 블록을 실행 지시로 교체(2-b에 명령 추가·결과 승계 규약은 check_imports와 동형) ② arch-reviewer — C3의 "check_invariants.py는 Phase 3 예정" 완화 문장 제거, §3 결정적 검사 열거에 check_invariants 추가 ③ aggregates.md R4 상태 블록 제거(착지 확인 후) ④ init — 실재 스킬 목록에 model·apply 추가 ⑤ README — 있는 것/없는 것(5개 스킬로 축소: scaffold·adr·sync·evolve·migrate)·테스트 수 갱신 ⑥ `python3 scripts/build_index.py --write` — draft 0 확인 ⑦ 전 파일 `Phase 3|아직|예정` grep 재검증(잔존 = Phase 4+ 것만).

- [ ] **Step 1: 처분 표 → 적용 → 재검증 grep + 전체 스위트. Step 2: Commit** — `git commit --only <위 파일들> -m "docs: Phase 3 착지 반영 — 상태 블록 해소, INDEX draft 0"`

---

### Task 7: Phase 3 검증

**Files:** `.superpowers/verify3/` 샘플(커밋 금지), 리포트 `.superpowers/verify3/report.md`

스펙 §12 Phase 3 검증 그대로: ① 샘플(Phase 2 검증 샘플 재사용 가능)에서 model 세션을 중첩 headless 세션으로 실측 — 대본 답변으로 불변식 2~3개 proposed→confirmed(항목별 확정 실증 — 무단 승격 0 확인) ② apply 절차 수행 — 도메인 코어+태그 테스트 생성, check_invariants 클린 도달 ③ 태그 테스트 하나 삭제 → check_invariants가 해당 INV를 파일:행으로 위반 보고 ④ review의 discussion 항목이 열린 질문에 append되는지(arch-reviewer 실측 포함) ⑤ 전 과정에서 불변 1 위반(무단 확정) 0건 판정. PASS/FAIL+증거, 트리 클린 확인.

- [ ] **Step 1~5: 수행 + 리포트. 수정 필요 결함은 환류 분류(직접 수정 금지).**

## Self-Review 결과
- 스펙 §12 Phase 3 구성요소: model(T4)·apply(T5)·check_invariants(T3)·domain-doc-template(T1)·event-storming(T2)·review 분류 확장(T6-①·검증 ④) — 전부 태스크 존재. 검증 4문장 = T7.
- 타입 일관성: INV ID 형식·표 계약은 P3-D1·D2가 단일 정본, T1(문서)·T3(파서)·T4(채번)·T5(태그)가 같은 문면 인용.
- 플레이스홀더 없음. Phase 2 이월 훅 3건(T9·T11·T6 기록) 전부 T6에 배정.
