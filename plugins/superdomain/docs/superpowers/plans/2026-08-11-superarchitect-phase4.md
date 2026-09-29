# superarchitect Phase 4 (생성) Implementation Plan

> **보관 문서.** 현행 정본은 `references/governance/`와 최신 스펙(`2026-09-28-superdomain-layout-and-fixes-design.md`)이다. 이 문서의 경로·절차·지시를 실행하지 않는다 — 체크박스가 비어 있어도 완료된 작업이다.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 선언에서 코드 골격을 만든다 — kotlin-spring 프리셋 템플릿(4종 × 레이아웃 변형)과 examples, scaffold 스킬(신규 프로젝트 증분 등록·그린필드 프로젝트 골격·컨텍스트 골격·app-embedded 레이어 패키지), adr 스킬(MADR 생성·supersede 흐름).

**Architecture:** 템플릿의 수용 기준은 하나 — "그대로 전개되면 그 스타일의 fitness 생성 테스트를 통과한다". scaffold는 init 이후 유일하게 ARCHITECTURE.md를 편집하는 스킬군의 일원이므로 매 편집 후 resolve_rules 게이트(D6)와 파생물 재생성 의무를 진다. adr은 결정 기록이 기계 규칙을 함의할 때 스타일 선언·어휘 확장으로 연결하는 다리다.

**Tech Stack:** 템플릿은 Kotlin + Gradle Kotlin DSL 조각(대상 프로젝트 의존성 기준 — Konsist 0.17.3). 스크립트 신규 없음.

**요구사항 소스:** 스펙 §6.2(scaffold)·§6.5(adr)·§10(templates·examples 규약)·§12 Phase 4. 정본: profiles/README.md(계약 — templates 절은 이 Phase에서 확정), rule-mappings.md(§0.1 파일 배치·유일 키), adr-template.md(MADR·supersede·조정됨 마커), architecture-template.md.

## Global Constraints

- SKILL ≤500줄, description ≤1,536자(트리거·비트리거). 스크립트 신규 금지(생성은 스킬+템플릿).
- gradle wrapper는 생성하지 않는다 — 명령 안내만(스펙 §6.2-2).
- 템플릿·examples는 짧게(YAGNI — 샘플 포트/어댑터/유스케이스 각 1개, examples 좋은/나쁜 각 1개 짧게).
- 미착지 참조는 구현 상태 블록(sync·evolve·migrate = Phase 5). INDEX는 스위프 태스크만.
- 커밋 `git commit --only <자기 경로>`. 전체 스위트 300 유지.

## 컨트롤러 확정 결정

**P4-D1. 템플릿 변수 규약(프로파일 계약에 정본화).** `{{context}}`(소문자 그대로), `{{basePackage}}`, `{{Context}}`(PascalCase — **하이픈 제거 + 각 세그먼트 첫 글자 대문자화**: `core-api` → `CoreApi` — Phase 2 이연 미결의 확정), `{{app}}`(하이픈→점은 패키지 위치에서만·모듈 경로는 원형), `{{layer}}`. 파일명·디렉터리명에도 같은 치환. 이 규약은 rule-mappings의 플레이스홀더 규약(§0)과 한 계약으로 합류 — profiles/README가 정본.

**P4-D2. 템플릿 수용 기준 = fitness 통과.** 각 프리셋 템플릿을 그대로 전개한 골격은 그 스타일의 유효 규칙(파생 포함)에 대해 check_imports 클린 + 생성 Konsist 테스트 통과여야 한다. 검증 ①이 실측하고, 템플릿 작성 태스크가 자체 전개·검사로 선확인한다.

**P4-D3. scaffold의 SSOT 편집 권한과 의무.** scaffold는 ARCHITECTURE.md의 프로젝트 섹션·모듈 표·애플리케이션 표를 편집할 수 있다(신규 등록·골격 반영). 의무: 매 편집 후 `resolve_rules.py` 게이트, 종료 전 summary.md·생성 구역 재생성(init과 같은 규율), 편집 전 사용자 확정(불변 1 — 인터뷰 결과를 표로 보여주고 확정 후 기록).

**P4-D4. adr 채번·supersede.** 번호 = `docs/architecture/decisions/` 내 최대+1(4자리 zero-pad). supersede: 신 ADR에 "대체함: NNNN", 구 ADR status → `superseded` + "대체됨: NNNN" — 양방향, 그리고 구 ADR을 참조하는 `규칙 예외`가 있으면 재검토를 안내(예외 근거가 낡는 지점). adr-template.md의 조정됨 마커 규약 준수.

**P4-D5. 커스텀 스타일 골격은 템플릿이 아니라 유도.** 커스텀 스타일 컨텍스트의 scaffold는 스타일 선언(레이어·규칙)에서 골격을 유도(레이어당 패키지 + 규칙이 함의하는 최소 구조)하며, 가장 가까운 프리셋 템플릿을 참고로 제시만 한다.

## 파일 구조

```
생성:
  profiles/kotlin-spring/templates/layered-simple/…    # T1 (4종 각각: MODULE.md 매니페스트 + 파일 템플릿)
  profiles/kotlin-spring/templates/layered-domain/…
  profiles/kotlin-spring/templates/hexagonal/…
  profiles/kotlin-spring/templates/clean/…
  profiles/kotlin-spring/examples/good/… + bad/…       # T1 (짧게)
  skills/scaffold/SKILL.md                             # T2
  skills/adr/SKILL.md                                  # T3
수정:
  profiles/README.md                                   # T1 (templates·examples 계약 확정, P4-D1 정본화)
  (스위프) skills/init·model·apply·review·fitness의 scaffold/adr 언급, README, INDEX   # T4
```

| 웨이브 | 태스크 |
|---|---|
| A (병렬) | T1(templates+examples+계약), T3(adr) |
| B | T2(scaffold — T1 계약 소비) |
| C | T4(스위프·INDEX) |
| D | T5(Phase 4 검증 ①~④) |

---

### Task 1: kotlin-spring templates 4종 + examples + 계약 확정

**Files:** Create: `profiles/kotlin-spring/templates/<style>/…`(4종), `profiles/kotlin-spring/examples/{good,bad}/…` / Modify: `profiles/README.md`

**필독:** 스펙 §10(templates 요구 항목: settings 조각·모듈 빌드 스크립트·패키지 골격·샘플 포트/어댑터/유스케이스·테스트 골격 + single-module 변형 + app-embedded 변형), styles 프리셋 4종의 `## 선언`(레이어·규칙 — 골격이 이 규칙을 통과해야 함), rule-mappings §0.1(아키텍처 테스트 배치), P4-D1·D2.

**설계(고정):** 각 스타일 디렉터리는 ① `MANIFEST.md` — 이 스타일 골격의 파일 목록·배치 규칙(레이아웃 3형별: multi-module = 레이어별 모듈, single-module = 단일 모듈 + 레이어 패키지, app-embedded = 규약 패턴 위치에 레이어 패키지만) + 변수 치환 규약 참조 ② 파일 템플릿들 — `settings.gradle.kts.fragment`, `build.gradle.kts.<layer>`, 소스 템플릿(`{{Context}}.kt` 애그리거트 스텁, 포트/유스케이스/어댑터 각 1, 테스트 골격 `{{Context}}Test.kt` — @Tag 예시 주석 포함). 템플릿 파일 안 변수는 P4-D1. examples: good = hexagonal 최소 준수 발췌 1(파일 2~3개), bad = 위반 발췌 1~2(각 위반이 어느 rule id에 걸리는지 주석) — 각 20줄 내외.
**계약 확정:** profiles/README의 templates 구현 상태 블록 제거 → ② 절을 실계약으로(MANIFEST 규약·변수 표·수용 기준 D2 명문화). examples 규약(③)도 확정.

- [ ] **Step 1: 작성.**
- [ ] **Step 2: 자체 검증(D2)** — hexagonal 템플릿을 `.superpowers/scratch-t1/`에 손으로 전개(치환)해 `check_imports` 클린 + fitness 절차로 생성한 테스트가 구조적으로 통과 가능한지 확인(gradle 실행 가능하면 실행). 다른 3종은 전개+check_imports 클린까지. 증거를 보고서에.
- [ ] **Step 3: Commit** — `git commit --only profiles -m "feat: kotlin-spring 템플릿 4종·examples — 전개=fitness 통과 수용 기준"`

---

### Task 2: skills/scaffold/SKILL.md

**Files:** Create: `skills/scaffold/SKILL.md` (~420줄 이내)

**필독:** 스펙 §6.2 전체(4단계), T1의 MANIFEST 규약·변수 표, P4-D3(SSOT 편집 의무)·D5(커스텀 유도), architecture-template §4·§6(표 편집 시 형식), init SKILL(인터뷰·게이트·파생물 재생성 관례 — 재서술 말고 관례 참조).

**절차(고정):** ① 게이트 + 트리거 분기(신규 프로젝트 / 그린필드 프로젝트 골격 / 신규·기존 컨텍스트 / app-embedded 레이어 패키지 / sync 위임 — Phase 5 구현 상태) ② 신규 프로젝트 증분 등록: 인터뷰(경로·프로파일·기본 패키지·테스트 위치·필요시 앱·공용·규약) → 표로 확정 후 ARCHITECTURE.md 프로젝트 섹션 추가 → 게이트 ③ 프로젝트 골격: 선언됐는데 디스크에 없으면 settings·빌드 스크립트·선언된 모듈 골격 생성(wrapper는 명령 안내) ④ 컨텍스트 골격: 신규면 분류 인터뷰(domain-classification 체크리스트 — init과 동일 경로) 후 등록, 프리셋이면 T1 템플릿 전개(MANIFEST대로, 변수 치환), 커스텀이면 D5 유도, app-embedded면 각 소속 앱에 규약 패턴 위치의 레이어 패키지 생성 ⑤ `패턴` 선언 반영(cqrs → command/query 패키지 등 — 해당 knowledge 문서를 읽고) ⑥ 모듈 표/애플리케이션 표 갱신 → 게이트 → summary·생성 구역 재생성 → fitness 실행 권유. 스킬이 만든 골격이 스타일 규칙을 위반하지 않는지 check_imports로 자가 확인.

**금지:** 사용자 확정 없는 SSOT 편집, 템플릿 밖 임의 구조, wrapper 생성, 기존 코드 이동(그건 migrate — Phase 5 구현 상태).

- [ ] **Step 1: 작성. Step 2: §6.2 문장별 커버 대조표. Step 3: Commit** — `git commit --only skills/scaffold`

---

### Task 3: skills/adr/SKILL.md

**Files:** Create: `skills/adr/SKILL.md` (~250줄 이내)

**필독:** 스펙 §6.5, adr-template.md 전체(MADR 형식·조정됨 마커·양방향 supersede), P4-D4, rule-vocabulary §7(어휘 확장 ADR 요구 — 연결 지점).

**절차(고정):** ① 게이트 ② 신규: 인터뷰(제목·맥락·검토한 대안 — **실제 논의된 것만, 날조 금지**·결정·결과) → 채번(D4) → adr-template 형식 생성(status: proposed) ③ 승인 전환: proposed → accepted(사용자 확정) ④ supersede: D4 양방향 + 구 ADR 참조하는 `규칙 예외` 재검토 안내 ⑤ 결정이 기계 검증 가능 규칙을 함의하면: 기존 어휘로 표현 가능한지 rule-vocabulary §6 체크리스트로 먼저 확인 → 스타일 선언 수정 또는 어휘 확장(§7 — java-spring 매핑 부재로 완주 불가면 그 사실 고지) 제안 + fitness 갱신 권유.

**금지:** 검토한 대안 날조(없으면 "검토한 대안 없음" — Phase 1 검증에서 관측된 실패 유형의 방어), 무단 accepted 전환, ADR 소급 수정(정정은 새 ADR).

- [ ] **Step 1: 작성. Step 2: §6.5 문장별 대조 + adr-template 형식 준수 확인. Step 3: Commit** — `git commit --only skills/adr`

---

### Task 4: Phase 4 스위프

**Files:** Modify: `skills/init/SKILL.md`, `skills/model/SKILL.md`, `skills/apply/SKILL.md`, `skills/review/SKILL.md`, `skills/fitness/SKILL.md`, `README.md`, `references/INDEX.md`(재생성 — 변화 없어도 확인)

sweep-before-edit. 고정 처분: ① scaffold·adr 실재 반영 — init의 scaffold 안내(그린필드 흐름·9단계 pre-commit 제안 부근), apply의 "골격은 scaffold(Phase 4)" 구현 상태, model·review의 adr 언급, 없는 스킬 목록(sync·evolve·migrate 3종으로 축소) ② description들의 비트리거 문구 중 scaffold/adr 관련 갱신 ③ README(있는 것 7 스킬·없는 것 3·수치) ④ 재검증 grep(`Phase 4|아직|예정` — 잔존은 Phase 5+만).

- [ ] **Step 1: 처분 표 → 적용 → 재검증 + 스위트. Step 2: Commit**

---

### Task 5: Phase 4 검증 ①~④

**Files:** `.superpowers/verify4/` 샘플(커밋 금지), 리포트 `.superpowers/verify4/report.md`

스펙 §12 Phase 4 그대로: ① 새 컨텍스트 scaffold(중첩 세션 실측 — 인터뷰 대본) → fitness 생성·실행 통과(gradle 가용 확인됨) ② 그린필드 샘플(Phase 1 검증 ③ 형태 재현)에서 scaffold가 프로젝트 골격 자체를 생성 ③ 기존 모노레포에 신규 프로젝트 증분 등록(인터뷰 대본 — 무단 확정 0 판정) ④ ADR 생성·supersede 흐름(양방향 링크·규칙 예외 재검토 안내·**대안 날조 0 판정**). PASS/FAIL+증거, 트리 클린, 환류 분류.

## Self-Review 결과
- 스펙 §12 Phase 4 구성요소: scaffold(T2)·adr(T3) + §10 templates·examples(T1). 검증 4건 = T5. §6.2의 4단계·§6.5 전 문장이 태스크에 배정됨.
- 타입 일관성: 변수 규약은 P4-D1 단일 정본(profiles/README), T1 정의·T2 소비. adr 채번·supersede는 P4-D4 단일 정본.
- 플레이스홀더 없음.
