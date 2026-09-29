# superarchitect 최종 완료 기준(§14) Implementation Plan

> **보관 문서.** 현행 정본은 `references/governance/`와 최신 스펙(`2026-09-28-superdomain-layout-and-fixes-design.md`)이다. 이 문서의 경로·절차·지시를 실행하지 않는다 — 체크박스가 비어 있어도 완료된 작업이다.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 스펙 §14의 네 기준(설치·노출 / e2e 시나리오 / 형태 커버리지 / README 완비)을 실측·문서로 닫고, 전체 브랜치 최종 리뷰로 v1을 마감한다.

**Architecture:** 각 단계는 Phase 1~6 검증에서 개별 실측이 끝났다 — 남은 것은 **연속성**(한 샘플에서 스킬 체인이 끊기지 않고 도는가)과 **형태 공백 2건**(kotlin clean·layered-domain multi-module 실측 기록, app-embedded scaffold 갈래), 그리고 README의 §14 요구 요소다. e2e 샘플의 형태를 공백에 맞춰 골라 한 번에 닫는다.

**Tech Stack:** 기존 검증 관례 그대로(중첩 headless·SDKMAN gradle 9.7.0·java 17·Konsist 0.17.3). 테스트 383.

**요구사항 소스:** 스펙 §14. 형태 커버리지의 기존 근거: 모노레포=verify4/mono+Phase 1 V②, 그린필드=verify4/green+verify6/svc, app-embedded(검사 축)=verify2/appemb, java-spring=verify6 전체.

## Global Constraints

- 검증 산출물은 `.superpowers/verify-final/` — 저장소 커밋 금지, 오염 시 git checkout 원복 후 보고.
- 불변 1(무단 확정 0)·침묵 실패 금지 판정 기준 유지. 승인 대본 관례.
- README·profiles 문서 수정은 실재와 실측만 서술(제1 원칙). 전 스킬 ≤500 캡 불변.
- 커밋 `git commit --only <자기 경로>`.

## 컨트롤러 확정 결정

**F-D1. e2e 샘플 형태 = 루트 SSOT 모노레포(backend + frontend 더미)**, 컨텍스트 2개: 기존 컨텍스트는 **clean**(multi-module — 실측 기록 공백 ①을 닫음), e2e 도중 scaffold로 추가하는 신규 컨텍스트는 **layered-domain**(multi-module — 공백 ②를 닫음). 이로써 §14 모노레포 형태 확인과 미실측 스타일 2종이 한 시나리오에서 닫힌다.

**F-D2. app-embedded scaffold 갈래는 e2e에 얹지 않고 소검증으로 분리** — e2e 서사를 흐리지 않기 위해. `### 패키지 규약`에 `{앱}` 행이 있는 최소 샘플에서 scaffold의 app-embedded 배치(모듈·빌드 조각 없이 규약 패턴 위치에 레이어 패키지만)를 1회 전개·check_imports 클린 확인.

**F-D3. README의 §14 요구 4요소 처분** — 설치(이미 있음·유지), **워크플로 mermaid**(신규 — 스킬 10종의 흐름: init→scaffold→fitness→review 루프, sync·evolve·migrate 유지 루프, model→apply→check_invariants 도메인 루프. 검증은 테스트가 담당하므로 다이어그램은 이해용이라는 §5 원칙 문면 동반), **스킬별 사용법**(현 표를 유지하되 "언제 부르는가" 관점의 짧은 절 신설 — 표 중복 서술 금지, 트리거 상황 중심), **ARCHITECTURE.md·domain 문서 예시**(README 안에 긴 예시를 넣지 않는다 — 정본 템플릿·실전개 예시 위치를 가리키는 포인터 절. references/governance 템플릿 2종과 profiles examples가 실재 예시다).

**F-D4. Phase 6 이연 문면 3건을 T-B가 소화** — ① profiles/README ④에 "프로파일 중립 문서(스킬·거버넌스)는 §7 커버리지 한계를 번호가 아니라 **행 이름**으로 인용한다" 규약 한 줄(재발 방지 — fitness·migrate가 이미 그 형태) ② profiles/README ② 파일 구성 표의 `<레이어>/*.kt`·`test/*.kt`를 언어 중립 표기로(각 프로파일 소스 확장자는 그 프로파일 몫) ③ java-spring `templates/clean/MANIFEST.md:104` 부근 `api > implementation` 병합 규칙이 그 스타일 조각에 api가 없어 죽은 문면 — 조각 실재에 맞게 정리(kotlin 3종은 무언급이 실재와 정합이라 무수정).

**F-D5. L2(러너 권한)는 T-A 러너 구성에서 흡수** — `--allowedTools` 조합을 verify6 러너에서 손봐 migrate 6-c 기본 형식 게이트가 돌게 함. 실패해도 --json 동등 성립 관례 유지(비차단).

## 파일 구조

```
수정(T-B): README.md — mermaid·사용법 절·예시 포인터 절
          profiles/README.md — F-D4 ①②
          profiles/java-spring/templates/clean/MANIFEST.md — F-D4 ③
산출(T-A): .superpowers/verify-final/{e2e, appemb}/ + report.md (커밋 금지)
```

| 웨이브 | 태스크 |
|---|---|
| A (병렬) | T-A(e2e+형태 공백 실측), T-B(README·문면 — 파일 무겹침) |
| B | T-C(전체 브랜치 최종 리뷰 fable → 픽스 → 마감) |

---

### Task A: e2e 시나리오 + 형태 공백 실측

**Files:** 산출만 — `.superpowers/verify-final/`. 저장소 커밋 금지.

- [ ] **e2e (F-D1 형태)**: 루트 SSOT 모노레포 샘플 구축(backend/ + frontend/ 더미 package.json) → 중첩 세션 체인:
  1. init(컨텍스트 1개 clean multi-module로 확정, frontend는 "대응 프로파일 없음" 확인, 승인 대본)
  2. scaffold(신규 컨텍스트 layered-domain 추가 — 인터뷰→SSOT 등록→전개→check_imports 클린·gradle 컴파일)
  3. 위반 코드 삽입 → review 검출(결정적 검사 축) → fitness 생성 테스트 gradle 실패
  4. 수정 → fitness 통과 → sync 클린(드리프트 0 보고)
  5. evolve 리포트 생성(git 이력 얕아도 산출 불가가 아니라 신호 빈약 고지로 — collect_signals exit 판정 포함)
  6. 도메인 루프: model(인터뷰 대본→불변식 proposed→항목별 확정 1건) → apply(confirmed 구현+@Tag) → check_invariants 클린 → review가 열린 질문 반영
- [ ] 각 단계 사이 판정: 무단 확정 0, 침묵 실패 0, 이전 단계 산출을 다음 단계가 실제 소비(연속성 — 이 검증의 존재 이유).
- [ ] **app-embedded 소검증(F-D2)**: `{앱}` 규약 샘플에서 scaffold 갈래 1회 → check_imports 클린.
- [ ] clean·layered-domain 실측 기록을 MANIFEST 갱신용으로 정리(수정은 T-C 전 마감 픽스 몫 — 검증자는 기록만).
- [ ] report.md — 단계별 PASS/FAIL·연속성 판정·환류 분류.

### Task B: README 완비 + 이연 문면 3건

**Files:** Modify: `README.md`, `profiles/README.md`, `profiles/java-spring/templates/clean/MANIFEST.md`

- [ ] F-D3 4요소(mermaid는 flowchart — 스킬 10종+스크립트 소비 관계, 루프 3개 구분). F-D4 3건.
- [ ] mermaid 문법 검증(렌더 확인 가능한 선에서 — 구조 오류 없게), README 전체 통독으로 신설 절과 기존 절의 중복·모순 제거.
- [ ] 스위트 383 유지 확인, 커밋 분할.

### Task C: 전체 브랜치 최종 리뷰 → 마감

- [ ] T-A·T-B 착지 후: MANIFEST 실측 기록 갱신(clean·layered-domain "기록 없음"→실측 — T-A 결과 반영) 등 마감 픽스가 있으면 처리.
- [ ] **전체 브랜치 리뷰(fable)**: main..HEAD 전 범위 — 커밋 수가 많으므로 diff 통독이 아니라 (1) 각 Phase 최종 리뷰 판정의 소급 유효성 (2) Phase 간 교차(마지막으로 남은 스테일·모순) (3) §14 네 기준 충족 판정 (4) 파킹 전수 최종 triage. 조건 발견 시 픽스 웨이브 1회.
- [ ] 완료 보고(사용자에게): Phase별 요약·커밋 범위·§14 충족 근거·PR은 요청 시.

## Self-Review 결과
- §14 4기준: 설치·노출=e2e가 자연 확인(+기존 전 검증), e2e=T-A, 형태=기존 근거+T-A(공백 3건 봉합), README=T-B. 전체 리뷰=T-C.
- 이연 전수: Phase 6의 5건 — 문면 3건(T-B), 실측 2건(T-A), L2(F-D5). 플레이스홀더 없음.
