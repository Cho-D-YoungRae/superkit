# superarchitect Phase 5 (유지·이행) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 시간이 지나도 선언과 현실이 어긋나지 않게 한다 — sync(드리프트 대조), evolve(신호 수집·해석→제안+ADR 초안), migrate(baseline 클러스터 단위 점진 이행), collect_signals.py, 그리고 §4.3 규칙 8의 baseline 래칫 실배선(동결=init, 소비=check_imports·생성 테스트, 축소=migrate).

**Architecture:** baseline.jsonl은 "기존 부채는 warn, 신규 위반은 blocker"를 만드는 래칫이다 — 동결은 이행 선언 시 한 번, 축소는 migrate로만. collect_signals는 git log·review-log·baseline 이력을 신호 5종으로 관측만 하고, 해석 규칙의 정본은 evolution-signals.md다. 세 스킬 모두 제안-확정 분리(불변 1): sync는 드리프트 방향을 임의 판단하지 않고, evolve는 자동 적용하지 않으며, migrate는 한 클러스터씩 승인받는다.

**Tech Stack:** bash + python3 stdlib(git CLI 호출 포함). 테스트 `python3 -m unittest discover -s tests`(현재 310).

**요구사항 소스:** 스펙 §6.6·§6.7·§6.8·§4.3 규칙 8·§12 Phase 5. 정본: evolution-signals.md(신호·임계값·해석), architecture-template.md §5.3 잔존 행 9(baseline — 이번에 제거), rule-mappings.md baseline 블록(이번에 실계약화).

## Global Constraints

- 스크립트 stdlib만(git은 subprocess로 호출 — git 부재·비저장소는 산출 불가 고지). SKILL ≤500줄, description ≤1,536자.
- **review SKILL은 500/500 — 만지기 전에 압축으로 여유를 먼저 확보한다(P5-D4).** rule-mappings 500/500 — 추가는 등량 교환.
- 자동 적용 금지(evolve·sync·migrate 공통 — 스펙 §13). 제거는 착지 확인 후에만. INDEX는 스위프 태스크만.
- 커밋 `git commit --only <자기 경로>`. 오류 한국어 `경로:라인:`.

## 컨트롤러 확정 결정

**P5-D1. baseline.jsonl 스키마·매칭 키.** 한 줄 JSON per 위반: `{"rule": "<id>", "path": "<git 루트 상대>", "note": "<선택>"}`. **매칭 키 = (rule, path)** — line은 리팩터링에 취약해 키에서 제외한다. 대가(같은 파일·같은 규칙의 **추가** 위반이 baseline에 흡수됨)는 한계로 문서·리포트에 명시한다(침묵 금지). 파일은 `docs/architecture/baseline.jsonl`, 정렬(rule, path)·append 아님(동결·축소 시 전체 재작성 — migrate만).

**P5-D2. 래칫의 주체 분담.** 동결 = init(이행 라벨 선언 시 check_imports 전량 실행 결과로 생성 — init SKILL에 실배선) + scaffold/adr은 무관. 소비 = check_imports(baseline.jsonl 존재 시 자동 감지: 매칭 위반을 `[기존 부채]` warn 채널로 분리, 신규만 위반(exit 1 기준) — 플래그 불요)와 생성 Konsist 테스트(rule-mappings baseline 블록을 실계약으로: 생성 테스트가 파일을 읽어 매칭 위반을 실패 대신 리포트로 강등하는 코드 템플릿). 축소 = migrate만(비면 파일 삭제 + 이행 라벨 제거 + 이행 완료 ADR).

**P5-D3. collect_signals CLI.** `python3 scripts/collect_signals.py <ARCHITECTURE.md> [--since <rev|날짜>] [--json]`. 신호 5종: ① 컨텍스트별 변경 빈도(커밋 수·파일 수 — 파일→정규화 패턴 귀속, 미귀속은 "귀속 불가" 버킷으로 고지) ② 핫스팟 파일 상위 N ③ 컨텍스트 쌍 동시 변경(같은 커밋에 두 컨텍스트 파일) ④ review-log.jsonl 반복 위반(rule별 건수) ⑤ baseline 추이(git log -p baseline.jsonl의 줄 수 변화). exit 0=산출 / 1=산출 불가(비 git·빈 이력 — 사유 고지) / 2=사용법. 임계값·해석은 넣지 않는다 — evolution-signals.md가 정본, evolve가 적용.

**P5-D4. review 압축 선행.** T2가 review 5-c의 baseline 구현 상태 블록(3줄)을 실동작 서술로 교체하기 전, 같은 커밋에서 압축으로 순증 0 이하 유지.

**P5-D5. evolve 산출 = 제안 리포트 + proposed ADR 초안만.** 문서 반영은 사용자가 수락한 제안만, 반영 후 파생물·fitness 갱신 안내. 도메인 리팩터링 제안(모델 재편)도 같은 경로.

## 파일 구조

```
생성: scripts/collect_signals.py, tests/test_collect_signals.py        # T1
      skills/sync/SKILL.md                                             # T3
      skills/evolve/SKILL.md                                           # T4
      skills/migrate/SKILL.md                                          # T5
수정: scripts/check_imports.py(+tests) — baseline 소비                  # T2
      profiles/kotlin-spring/rule-mappings.md — baseline 블록 실계약    # T2
      profiles/kotlin-spring/api-verification.md — 신규 API 행(필요시)  # T2
      skills/init/SKILL.md — 동결 실배선(6단계)                          # T2
      skills/review/SKILL.md — 5-c 블록 교체(압축 선행)                  # T2
      references/governance/architecture-template.md — §5.3 행 9 제거   # T2
      (스위프) evolution-signals 머리 블록·README·INDEX·description들    # T6
```

| 웨이브 | 태스크 |
|---|---|
| A (병렬) | T1(collect_signals), T2(baseline 래칫 — 파일 무겹침) |
| B (병렬) | T3(sync), T4(evolve — T1 소비), T5(migrate — T2 소비) |
| C | T6(스위프·INDEX) |
| D | T7(Phase 5 검증) |

---

### Task 1: collect_signals.py

**Files:** Create: `scripts/collect_signals.py`, `tests/test_collect_signals.py`

P5-D3 그대로. 파일→컨텍스트 귀속은 resolve_rules의 정규화 패턴(effective layer_patterns + derived detail)으로 — 패키지 경로를 파일 경로에 사상(src 경로에서 패키지 추출은 check_imports 관례 참조). git 호출은 `git -C <root> log --numstat --format=...`; 테스트는 임시 git 저장소를 만들어 실이력으로(기존 임시 트리 관례 + `git init`·커밋 — 환경 git 필수는 스위트 전제에 이미 있음). review-log 파싱은 한 줄 JSON(깨진 줄은 고지하고 건너뜀 — 침묵 금지). --json 계약 명세는 docstring에.

- [ ] TDD: 신호 5종 각 1+ 케이스 / 비 git 산출 불가 / 귀속 불가 버킷 / 깨진 review-log 줄 고지 / --json 구조. 전체 스위트 통과 후 `git commit --only scripts/collect_signals.py tests/test_collect_signals.py`.

---

### Task 2: baseline 래칫 실배선

**Files:** Modify: `scripts/check_imports.py`, `tests/test_check_imports.py`, `profiles/kotlin-spring/rule-mappings.md`(+api-verification.md 필요시), `skills/init/SKILL.md`, `skills/review/SKILL.md`, `references/governance/architecture-template.md`

P5-D1·D2·D4 그대로. ① check_imports: baseline.jsonl 자동 감지 → 매칭 위반 `[기존 부채]` 채널(warn — exit에 미반영), 신규만 exit 1. 푸터에 부채 건수·한계(같은 파일·규칙 추가 위반 흡수) 고지. 깨진 baseline 줄은 오류(exit 2 아님 — 해당 줄 지목 exit 1? **판정: 깨진 줄은 전체 신뢰 불가이므로 exit 2 계열 오류** — 래칫이 침묵으로 새는 것 방지). --json에 baseline 필드. ② rule-mappings baseline 블록 → 실코드 템플릿(생성 테스트가 `docs/architecture/baseline.jsonl` 읽어 매칭 실패를 soft-assert로 강등 — Konsist에서의 구현 형태는 위반 수집 후 필터·리포트 출력, 미매칭만 assert 실패. 사용 API는 api-verification 행 추가 후에만). 500 캡 — 등량 교환. ③ init 6단계: 이행 라벨 시 check_imports 실행→baseline 생성 실배선(현 문면의 선언-only 상태 교체). ④ review 5-c 블록 교체(압축 선행 — P5-D4). ⑤ §5.3 행 9 제거(착지 증거) — 남는 행 1(마커 분기)로 머리 개서.

- [ ] TDD(check_imports 쪽): 매칭 warn·신규 blocker·깨진 줄 오류·부채 푸터·자동 감지. 전개 샘플로 rule-mappings 템플릿 정합 확인(.superpowers/scratch). 커밋 분할 허용(--only).

---

### Task 3: skills/sync/SKILL.md (~380줄)

스펙 §6.6 그대로: 대조 축 — 선언됐는데 없는 프로젝트/모듈(→ [scaffold로 생성]이 1순위 선택지), 존재하는데 미선언(스캔 범위 = 선언된 프로젝트 경로 안만 — frontend 등 미선언 프로젝트는 오검출 대상 아님), 레이어 매핑 불일치(공허 레이어 경고 활용), 깨진 ADR·스타일 참조(규칙 예외의 ADR 파일 실존·custom 문서 실존), 파생물 신선도(summary·생성 구역이 결정 템플릿보다 낡음 — mtime이 아니라 내용 대조), resolve_rules 오류도 드리프트로 보고. 각 드리프트에 [scaffold로 생성 / 코드 수정 / 문서 수정 / 무시] 제시 — **방향 임의 판단 금지**(불변). 선택 반영 후 파생물 재생성. adr 7-c의 "sync가 완결" 약속 이행(옛 ADR 번호 참조 문서 대조 포함).

---

### Task 4: skills/evolve/SKILL.md (~380줄)

스펙 §6.7 그대로: collect_signals 실행(P5-D3 계약) → evolution-signals.md의 신호·임계값·해석 규칙을 **읽고 그대로 적용**(재서술 금지) → 제안 리포트(신호 근거 인용) + 제안별 proposed ADR 초안(adr 스킬 형식 준거 — 날조 금지 규율 승계) → 사용자가 수락한 것만 문서 반영 + 파생물·fitness 갱신 안내(P5-D5). review-log 반복 semantic 지적 → conventions/ 승격 제안 경로. 도메인 모델 리팩터링 제안도 같은 경로. baseline 정체 → migrate 권유 또는 목표 재검토 제안.

---

### Task 5: skills/migrate/SKILL.md (~350줄)

스펙 §6.8 그대로: baseline 부재 시 "이행할 부채가 없습니다" 종료. 로드→클러스터링(모듈·패키지·rule 단위 응집)→우선순위(collect_signals 핫스팟 우선·의존 리프 우선)→**한 클러스터만** 계획 제시→승인 후 수행(scaffold 템플릿 재사용·코드 이동)→fitness·check_imports 재실행으로 해소 확인→baseline에서 해당 항목 제거(P5-D1 재작성 규칙)→비면 파일 삭제+이행 라벨 제거+완료 ADR(adr 스킬 경유). 빅뱅 계획 금지·자동 진행 금지.

---

### Task 6: Phase 5 스위프

evolution-signals.md 머리 블록 제거(collect_signals·evolve 착지 — 증거), review·init description의 sync 언급 정합(이제 실재— 비트리거→정식 라우팅), init 1단계 "일부만 고치기" 안내 정합, 없는 스킬 목록 0(10 스킬 전원 실재 — README·init·model 등 전 지점), rule-vocabulary·architecture-template의 baseline 관련 잔존 문면, README(10 스킬·수치), INDEX 재생성, 재검증 grep(`Phase 5|아직|예정` 잔존 = Phase 6만).

---

### Task 7: Phase 5 검증

스펙 §12 Phase 5 그대로: ① 미선언 모듈 추가 → sync 감지(+선언 프로젝트 밖 디렉터리 무시 확인) ② "선언됐는데 없음"에 [scaffold로 생성] 1순위 확인 ③ 조작된 review-log(반복 위반 심기) → evolve가 제안+ADR 초안(자동 적용 0 판정) ④ **레거시 샘플 풀 사이클**: 프리셋 불일치 코드 → init(이행 선언) → baseline 동결 → check_imports가 기존 warn·신규 blocker 분리 → 생성 테스트의 강등 실행(gradle) → migrate 1클러스터(승인 대본) → baseline 축소 실측. `.superpowers/verify5/`, 커밋 금지, 환류 분류.

## Self-Review 결과
- §12 Phase 5 구성요소: sync(T3)·evolve(T4)·migrate(T5)·collect_signals(T1) + §4.3 규칙 8 래칫(T2). 검증 4문장=T7. §5.3 행 9 제거=T2. Phase 3~4 이월(500 캡 압축 선행·sync 언급 3건)=P5-D4·T6.
- 계약 단일 정본: baseline 스키마·매칭=P5-D1(T2 구현·T5 소비), 신호=P5-D3(T1 구현·T4 소비).
- 플레이스홀더 없음.
