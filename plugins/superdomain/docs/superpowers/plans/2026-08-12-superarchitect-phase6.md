# superarchitect Phase 6 (프로파일 확장 — java-spring) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `profiles/java-spring/`을 프로파일 계약(profiles/README.md ①~④)의 완전한 구현으로 채워, Java 프로젝트에서 fitness 생성·실행과 scaffold 전개가 kotlin-spring과 대칭으로 동작하게 한다.

**Architecture:** 프로파일은 어휘의 어댑터다 — primitive 5종+파생 3종을 ArchUnit 1.4.1로 번역하고, 번역 사전(rule-mappings)과 검증 대장(api-verification)을 짝으로 둔다. baseline 소비는 kotlin-spring §7과 동형(생성 테스트가 `baseline.jsonl`을 직접 읽어 강등)으로 코어 계약(P5-D1·D2)의 단일 정본을 지킨다. 템플릿 4종+_shared는 전개 결과가 check_imports 클린+fitness 통과여야 한다는 수용 기준(P4-D2 계보)을 그대로 따른다.

**Tech Stack:** ArchUnit 1.4.1(`com.tngtech.archunit:archunit`), Java 17, Gradle 9.7.0(Kotlin DSL 조각), JUnit 5. 테스트 `python3 -m unittest discover -s tests`(현재 375).

**요구사항 소스:** 스펙 §10(java-spring 절·baseline 연동)·§12 Phase 6·§14 형태 커버리지("java-spring 샘플에서는 fitness 생성·실행과 scaffold까지 확인"). 계약 정본: `profiles/README.md`(① 필수 2파일 ② templates·MANIFEST ③ examples ④ 추가 절차), `references/governance/rule-vocabulary.md`(어휘 의미), P5-D1·D2(baseline 코어 계약).

## Global Constraints

- rule-mappings.md ≤500줄 — **처음부터 api-verification.md 분리 구조로 시작한다**(kotlin-spring이 갈라진 전철). 전 스킬 ≤500 유지.
- **새 API는 api-verification.md에 행을 추가한 뒤에만 템플릿에 쓴다**(①-6). import 정본은 실컴파일로 확인(①-2). 미검증은 `⚠️ (미검증 — 첫 실행 시 확인)` 표기 — 검증된 것처럼 쓰는 것이 이 저장소가 가장 경계하는 실패다.
- 템플릿 수용 기준: 전개 골격이 그 스타일 유효 규칙(파생 포함)에 `check_imports` 클린 + fitness 생성 테스트 통과(②). 통과 못 하면 미완성이 아니라 틀린 것.
- 플레이스홀더 규약은 `profiles/README.md`가 정본 — 프로파일이 이름을 지어내지 않는다.
- 어휘 5종 전부 커버 — 하나라도 ArchUnit으로 표현 불가면 프로파일 추가 대신 그 사실을 보고(④-2).
- 커밋 `git commit --only <자기 경로>`. 오류 한국어. `.superpowers/`는 커밋 금지.

## 컨트롤러 확정 결정

**P6-D1. baseline 소비 = kotlin-spring §7 동형. FreezingArchRule 불채택.** 스펙 §10은 "FreezingArchRule로 동결(ViolationStore 경로는 archunit.properties)"이라 적었으나, 그 문장은 P5-D1·D2가 baseline.jsonl을 코어 계약(매칭 키 (rule,path), 축소는 migrate만)으로 확정하기 전에 쓰였다. FreezingArchRule을 그대로 쓰면 ① ViolationStore는 위반 **메시지 문자열** 저장소라 (rule,path) 키와 사상되지 않고(메시지 유사도 매칭 — 경로 키를 재구성할 수 없다) ② baseline.jsonl과 store의 **이중 장부**가 생겨 migrate 축소가 store에 반영되지 않는 드리프트가 남는다. 따라서 java-spring 생성 테스트도 baseline.jsonl을 직접 읽어 매칭 위반을 리포트로 강등한다(§7 동형 — ArchUnit에서는 `rule.evaluate(classes)` 후 위반의 소스 위치로 (rule,path) 매칭, 미매칭만 실패로. 정확한 API 형태는 T1이 api-verification 대장과 실측으로 확정). **T1은 스펙 §10 baseline 연동 문장에 정정 블록을 남긴다**(관례: 발견 사실+정본 포인터 — kotlin-spring dependsOn 정정과 같은 형식, 스펙 :439 부근). FreezingArchRule 불채택 근거는 rule-mappings.md에도 한 절로 문서화한다(다음 사람이 다시 시도하지 않게).

**P6-D2. 빌드 조각은 Gradle Kotlin DSL(.kts) 유지, 소스만 .java.** kotlin-spring 조각과 병합 규칙·버전 불박기 규약을 공유한다(스펙 §10도 "settings.gradle(.kts)"). `_shared/` 3파일은 java-spring 자체로 둔다: `build.gradle.kts.app`(부트 플러그인 — Kotlin 컴파일러 플러그인 없음), `{{App}}Application.java`, `build.gradle.kts.archtest`(ArchUnit+JUnit 5 의존, **baseline.jsonl `inputs.files` 선언은 kotlin-spring 신판과 동형** — T6/T7에서 실측된 형태). kotlin-spring `_shared`를 복사하지 않고 Java에 맞게 새로 쓰되, 기계적 부분의 출처를 밝힌다(② 재사용 규율).

**P6-D3. examples 스타일 = hexagonal.** kotlin-spring과 같은 선택(프리셋 중 규칙 최다 — 대칭 유지). good 2~3파일·bad 1~2파일, 각 20줄 내외, `.java`. **bad의 첫 줄 주석 실패 메시지는 ArchUnit을 실제로 돌려 받아 적는다**(③ — 지어내면 ①-6의 실패를 예제에서 반복).

**P6-D4. rule-mappings.md 절 구조는 kotlin-spring과 대칭.** §0 생성 규약(파일 배치·헤더)·§0.1 import 정본(실컴파일 확인)·§0.2 배치 자리·§0.3 0건 거동(**ArchUnit의 빈 스코프 거동을 실측해 적는다** — Konsist의 빈 레이어 예외와 다를 수 있고, 다르면 "0건 침묵" 위험을 §0.3이 막아야 한다)·§1~§5 primitive 5종·§6 파생 3종·§7 baseline 강등·§8 정규화 소비·§9 대장 포인터. `{{ruleIdSafe}}`: Java 메서드명은 백틱이 없다 — **Java 식별자 규칙에 맞는 변환을 이 파일이 정의한다**(예: `@DisplayName`에 원형 보존 + 메서드명은 안전 변환. 정확 형태는 T1이 정하되 유일성 보장은 유지).

**P6-D5. T3가 Phase 5 이연 백로그를 함께 소화한다.** (a) `tests/test_collect_signals.py` 공백 4종 — 멀티 프로젝트 접두 귀속·git 부재 산출 불가·`HOTSPOT_TOP`/`PATH_SAMPLES` 상한·`--json` `baseline`/`cochanges`/`unattributed` 키 집합 고정(+`_tally` 동률 시 `(미기재)` 표시 순서는 코드 수정 없이 테스트로 현 동작 고정만) (b) `skills/migrate/SKILL.md` 1단계 exit 2 복구 열거에 "값에 역슬래시 금지" 1줄(6-b 재작성 형식 규율의 실작성 지점) (c) `skills/fitness/SKILL.md` 6항에 전개 시점 판별 방법(5단계 4항이 여는 빌드 스크립트에서 `inputs.files`/`architectureBaseline` 확인 부착)과 6-d 인용을 "무조건 부착" 처방과 정합하게.

## 파일 구조

```
생성: profiles/java-spring/rule-mappings.md          # T1
      profiles/java-spring/api-verification.md       # T1
      profiles/java-spring/templates/{layered-simple,layered-domain,hexagonal,clean}/  # T2
      profiles/java-spring/templates/_shared/{build.gradle.kts.app, {{App}}Application.java, build.gradle.kts.archtest}  # T2
      profiles/java-spring/examples/{good,bad}/*.java # T2
수정: docs/superpowers/specs/...-plugin-design.md    # T1 — §10 정정 블록(P6-D1)
      skills/fitness/SKILL.md — :107 구현 상태 블록 제거·:271 대장 경로 병기, P6-D5(c)  # T3
      skills/scaffold/SKILL.md — :280 구현 상태 블록 제거                                # T3
      skills/adr/SKILL.md — :291 구현 상태 블록 제거(어휘 확장 완주 가능)                # T3
      skills/migrate/SKILL.md — P6-D5(b)                                                # T3
      references/governance/rule-vocabulary.md — :379 머리 블록 제거                     # T3
      profiles/README.md — 현황 표·구현 상태 블록 제거                                   # T3
      README.md — :74「아직 없는 것」절 갱신·:144·수치                                    # T3
      tests/test_collect_signals.py — P6-D5(a)                                          # T3
```

| 웨이브 | 태스크 |
|---|---|
| A | T1(매핑+대장 — 실측 필수) |
| B (병렬) | T2(templates+examples — T1 소비), T3(스위프+이연 백로그 — 파일 무겹침) |
| C | T4(Phase 6 검증) |

---

### Task 1: java-spring rule-mappings.md + api-verification.md

**Files:** Create: `profiles/java-spring/rule-mappings.md`, `profiles/java-spring/api-verification.md`. Modify: 스펙 §10 :439 부근(정정 블록 — P6-D1).

**Interfaces:** Consumes: `resolve_rules.py --json`의 `EffectiveRule`(rule_id·primitive·params·layer_patterns·resolved)·`DerivedRule`(kind·subject·detail) — 플레이스홀더 규약은 profiles/README 정본. Produces: fitness가 읽는 번역 사전 — kotlin-spring과 같은 절 이름(§0~§9, P6-D4)이라 fitness 문면의 "§0.1 import 정본" 참조가 양 프로파일에서 성립.

- [ ] 계약 문서 정독: `profiles/README.md` ①·④, `rule-vocabulary.md` §2·§2.1·§3(primitive 의미)·§5(파생), kotlin-spring `rule-mappings.md`(절 구조 대칭 참조 — 코드는 복사 불가, 도구가 다르다), `architecture-template.md` §5.1 규칙 8(baseline).
- [ ] **실측 환경 먼저**: `.superpowers/verify6/probe/`에 최소 Gradle+ArchUnit 1.4.1+JUnit5 프로젝트(kotlin-spring 검증들의 gradle 캐시 재사용 — `GRADLE_USER_HOME`, SDKMAN gradle 9.7.0·java 17). 여기서 모든 템플릿 후보 코드를 컴파일·실행으로 확인하며 쓴다.
- [ ] primitive 5종 번역 — 각각 입력(어느 필드)→완전한 코드 템플릿→주의·커버리지 한계. 방향: `layer-order`는 `layeredArchitecture().consideringOnlyDependenciesInLayers()` 계열(**strict 의미론과 0건 거동을 실측** — 빈 레이어에서 ArchUnit이 죽는지/침묵하는지 §0.3에 기록), `forbid-import`·`forbid-sibling-dependency`는 `noClasses().that().resideInAPackage()...` 계열, `confine-type`은 kotlin-spring §3의 contextScope 한정(수집·검사 양축)을 ArchUnit으로 동형 구현, `naming-suffix`는 `classes().that()...haveSimpleNameEndingWith()` 계열. **API 하나 쓸 때마다 대장에 행 먼저.**
- [ ] 파생 3종(§6) — context-isolation·app-confinement(+`app_patterns` 파생 목록은 이름 있는 목록으로 풀어 쓰는 kotlin-spring §6.2 방식 승계)·shared-module-direction.
- [ ] §7 baseline 강등(P6-D1) — baseline.jsonl 로드(형식 오류=중단, 값 역슬래시 금지 — kotlin-spring §7 로더와 같은 규율)+위반의 소스 위치→git 루트 상대 path 사상→(rule,path) 매칭 강등→미매칭만 fail. **동결 전 실패→동결 후 통과+`[기존 부채]` 출력을 probe에서 실측.** 한계(흡수 대가·경로 사상의 전제)를 §7에 명시.
- [ ] §0.1 import 정본 — probe에서 **실컴파일로 확인한** 전체 import 블록. §0.3 0건 거동 실측. `{{ruleIdSafe}}` Java 변환 정의(P6-D4)+유일성 논증(§6.2 계보).
- [ ] 스펙 §10 :439 정정 블록 — "FreezingArchRule로 구현" 문장에 발견 사실(P6-D1 근거 요약 2~3줄)+정본 포인터(`profiles/java-spring/rule-mappings.md` §7). 기존 정정 블록(:430)과 같은 형식.
- [ ] api-verification.md — 쓴 API 전 행(✅/✅ 실측/⚠️), kotlin-spring 대장과 같은 표 형식.
- [ ] 캡 확인(각 ≤500), `git commit --only profiles/java-spring/rule-mappings.md --only profiles/java-spring/api-verification.md --only docs/superpowers/specs/2026-08-08-superarchitect-plugin-design.md`.

---

### Task 2: java-spring templates 4종 + _shared + examples

**Files:** Create: `profiles/java-spring/templates/{layered-simple,layered-domain,hexagonal,clean}/`(각 MANIFEST.md+settings 조각+build 조각+`.java` 소스 템플릿+test 골격), `templates/_shared/` 3파일(P6-D2), `examples/{good,bad}/*.java`(P6-D3).

**Interfaces:** Consumes: T1의 rule-mappings(수용 기준 검증에 fitness 생성 테스트 필요), kotlin-spring templates의 MANIFEST 6절 구조·병합 규칙 서술 방식(구조만 — 내용은 Java), 플레이스홀더 규약. Produces: scaffold가 읽는 MANIFEST — kotlin-spring과 같은 절 구성이라 scaffold 3단계 위임이 양 프로파일에서 성립.

- [ ] kotlin-spring 각 스타일 MANIFEST를 구조 참조로 정독(6절: 통과 규칙/파일 목록/레이아웃 3형+병합 규칙/ARCHITECTURE.md 등록/치환/수용 기준 — 강제·교육 구분 포함).
- [ ] 4종 각각: `.java` 소스 템플릿(애그리거트 스텁 1·포트 1·유스케이스 1·어댑터 1·테스트 골격 1 최소 구성, 레이어 전부 비지 않게 — strict·빈 레이어 검사), build 조각(버전 불박기, **Java라 no-arg/open 계열 Kotlin 플러그인은 불필요 — 대신 Java+Spring에서 구조 검사가 못 보는 항목이 있으면 근거 주석과 함께**), settings 조각, MANIFEST 6절.
- [ ] `_shared` 3파일(P6-D2) — archtest 조각의 baseline `inputs.files` 선언은 kotlin-spring 신판(0c9fc7a+6e69385의 workingDir 전제 주석 포함)과 동형.
- [ ] **수용 기준 실측(② — 스타일마다)**: `.superpowers/verify6/expand-<style>/`에 전개→`check_imports` 클린→fitness 절차대로 생성한 ArchUnit 테스트 `gradle test` 통과→(hexagonal 1종은 bootJar까지 — kotlin-spring T5 관례). 실패한 템플릿은 고쳐서 재실측.
- [ ] examples: good(hexagonal 규칙 전부 만족하는 최소 발췌)·bad(1~2, **첫 줄 주석에 걸리는 규칙 id 전부+ArchUnit 실측 실패 메시지 첫 줄**).
- [ ] `git commit --only profiles/java-spring/templates --only profiles/java-spring/examples` (논리 단위 분할 허용).

---

### Task 3: Phase 6 스위프 + Phase 5 이연 백로그

**Files:** Modify: `skills/fitness/SKILL.md`, `skills/scaffold/SKILL.md`, `skills/adr/SKILL.md`, `skills/migrate/SKILL.md`, `references/governance/rule-vocabulary.md`, `profiles/README.md`, `README.md`, `tests/test_collect_signals.py`.

- [ ] 구현 상태 블록 제거·문면 갱신(착지 증거와 함께): fitness:107(매핑 부재 중단 → 양 프로파일 정상 경로, :271에 java-spring 대장 경로 병기), scaffold:280(템플릿 kotlin-spring뿐 → 양 프로파일), adr:291-294(어휘 확장 완주 가능 — 7-e 문면 정합), rule-vocabulary:379 머리 블록, profiles/README 현황 표("네 가지 다 있음" ×2)+:22 블록, README:74「아직 없는 것」(java-spring 항목 제거 — 절 자체가 비면 절 처분까지)·:144·테스트 수치.
- [ ] P6-D5(a) collect_signals 테스트 4종+_tally 동작 고정 — TDD(현 동작 고정이므로 red는 "테스트 부재" 확인으로 갈음, 각 케이스가 실동작을 단언하는지 실행 확인). (b) migrate 1줄. (c) fitness 6항 판별 방법+6-d 인용 정합.
- [ ] 재검증 grep: `Phase 6|아직|예정` 잔존이 정당한 용법뿐인지 전수(잔존 목록 보고서에). `java-spring` 언급 전 지점이 새 현실과 정합인지.
- [ ] 전체 스위트(375+신규), 캡 전수 wc -l, 논리 단위 커밋 분할.

---

### Task 4: Phase 6 검증

스펙 §14 형태 커버리지의 java-spring 요구 그대로: **"java-spring 샘플에서는 fitness 생성·실행과 scaffold까지 확인한다."** `.superpowers/verify6/` 아래, 저장소 커밋 금지, 중첩 headless 세션 관례(이전 Phase 동일).

- [ ] ① Java 프로젝트 샘플에서 init 인터뷰(java-spring 프로파일 제안 확인 — "프로파일이 있어서" 기준)→선언 확정(대본).
- [ ] ② scaffold 전개(hexagonal 1종 이상)→`check_imports` 클린 실측.
- [ ] ③ fitness 생성→`gradle test` 실행(ArchUnit)→위반 심고 재실행→검출 실측(규칙별 스팟 — primitive 5종 각 1건 이상+파생 1건).
- [ ] ④ baseline 사이클: init 이행 선언(확인 대본 — H1 봉합 문면 검증 겸)→동결→check_imports warn/blocker 분리→**ArchUnit 생성 테스트의 §7 강등 실측**(동결 전 실패→동결 후 통과+`[기존 부채]`)→migrate 1클러스터(승인 대본)→축소 실측.
- [ ] 보고서 `.superpowers/verify6/report.md` — 판정·환류 분류([환류-높음/중간/낮음]).

## Self-Review 결과
- 스펙 §12 Phase 6 구성요소: ArchUnit rule 매핑(T1)·FreezingArchRule 연동(P6-D1이 불채택으로 확정 — 스펙 정정 블록으로 처분, "연동"의 상위 의도인 baseline 동결은 §7 동형이 이행)·Java 템플릿(T2)·examples(T2). §14 java-spring 행 = T4.
- 계약 단일 정본: 번역=T1(rule-mappings), 골격=T2(MANIFEST), baseline=P5-D1 불변(§7은 소비자).
- 이연 백로그 소화 = P6-D5(T3). §14 잔여(e2e·형태 커버리지 나머지·README 완비·전체 브랜치 리뷰)는 Phase 6 범위 밖 — 별도 최종 태스크(Task #32)로.
- 플레이스홀더 없음 — 코드 템플릿의 정확 형태는 api-verification 실측 규율(①-6)이 계획 문면보다 정확성을 보장하는 구조라, 계획은 방향+실측 게이트를 명세한다(Phase 2에서 확립된 방식).
