# superdomain — 도메인 집중 재편 설계 스펙

> **보관 문서.** 현행 정본은 `references/governance/`와 최신 스펙(`2026-09-28-superdomain-layout-and-fixes-design.md`)이다. 이 문서의 경로·절차·지시를 실행하지 않는다 — 체크박스가 비어 있어도 완료된 작업이다.

- 날짜: 2026-08-17
- 상태: 승인됨 (브레인스토밍 세션 확정안)
- 역할: **superarchitect → superdomain 재편의 유일한 요구사항 소스다.** 2026-08-08 스펙이 정의한 플러그인(Phase 6 완성, 386 테스트)을 출발점으로 삼아, 무엇을 남기고 무엇을 들어내는지를 확정한다.
- 다음 단계: superpowers:writing-plans로 구현 계획 작성. Phase 단위로 진행하고, 각 Phase가 끝나면 검증 절차를 실행한 뒤 멈춰서 사용자 확인을 받는다.

## 1. 재편의 이유

superarchitect는 도메인(DDD)부터 아키텍처(스타일·레이어·모듈 구성)까지 전부를 다룬다. 그런데
프로젝트 아키텍처는 케이스가 워낙 다양해 프리셋·규칙 어휘로 일반화하기 어렵고, 유지 비용이
플러그인의 절반 이상을 차지한다. 반면 도메인 쪽 — 컨텍스트 경계, 불변식, 컨텍스트 간 의존 —
은 일반화가 잘 되고 기계 검증도 명확하다.

그래서 플러그인을 **도메인에 집중**하도록 재편한다: DDD를 돕고, 도메인을 구체화하며,
도메인(컨텍스트) 간 의존관계를 문서와 기계 검증 양쪽으로 정리한다. 헥사고날·레이어드 등
아키텍처 스타일에 대한 내용은 전부 들어낸다.

## 2. 브레인스토밍에서 확정된 결정

| # | 결정 | 선택지 중 확정안 |
|---|---|---|
| D1 | 컨텍스트 간 의존 검증 강도 | **코드 검증 유지** — 관계 표를 allow-list로 유지하고 `check_imports.py`를 컨텍스트 격리 전용으로 축소. "기계로 확인할 수 있는 것은 기계가 확인한다"는 제1 원칙을 도메인 경계에 존속시킨다 |
| D2 | 지식 베이스 | **DDD 12종 유지** — styles 4종·structure 2종만 삭제. 지식 메커니즘(INDEX·build_index.py·study 스킬)도 유지 |
| D3 | 스킬 재편 범위 | **A안: 스킬 8개** — fitness·scaffold·프로파일 제거, 나머지 8개는 아키텍처 절만 절제. 유지 루프(sync·evolve·migrate)와 baseline 래칫 존속 |
| D4 | 새 이름 | **superdomain** — 검토 결과 채택 (§7) |
| D5 | 개명 시점 | **모든 수술이 끝난 마지막 Phase에서 일괄** — 중간 단계는 기존 이름을 그대로 쓴다 |

## 3. 새 SSOT — `DOMAIN.md`

### 3.1 파일명과 배치

| 문서 | 기존 | 재편 후 |
|---|---|---|
| 구조 SSOT | `ARCHITECTURE.md` (대상 프로젝트 루트) | `DOMAIN.md` (대상 프로젝트 루트) |
| 컨텍스트별 도메인 문서 | `docs/architecture/domain/<컨텍스트>.md` | `docs/domain/<컨텍스트>.md` |
| 세션 훅 요약 | `docs/architecture/summary.md` | `docs/domain/summary.md` |

생성 구역 마커는 새 계보로 시작한다: `<!-- superdomain:template v1 -->`,
`<!-- superdomain:generated:context-map -->`. 기존 `superarchitect:*` 마커와의 호환 계층은
두지 않는다 — v1은 방금 출시됐고 이행 대상 프로젝트가 없다.

### 3.2 프로젝트 절 — 라벨 4개 → 2개

`경로`·`기본 패키지`만 남긴다. `프로파일`(프로파일 소멸)·`아키텍처 테스트 위치`(fitness 소멸)는
제거한다. 애플리케이션 표·공용 모듈 표·패키지 규약 표도 제거한다(구조 소관).

**멀티 프로젝트 지원은 유지한다** — 프로젝트 절은 복수 허용, 컨텍스트의 `- 프로젝트:` 귀속
라벨과 "유일 프로젝트면 생략 가능" 규칙도 기존 그대로다. 아키텍처 제거와 직교하는 기능이다.

### 3.3 컨텍스트 절 — 도메인 결정만

| 결정 | 운명 | 이유 |
|---|---|---|
| `분류` (core·supporting·generic) | 유지 | 도메인 분류 그 자체 (domain-classification 지식) |
| `패턴` (cqrs·outbox·event-sourcing) | 유지 | patterns 지식 3종 유지(D2)에 대응 |
| `### 관계` 표 (6종 유형·계약) | 유지 | 재편의 심장 — 컨텍스트 간 참조 allow-list |
| `### 근거`, 컨텍스트 맵 생성 구역 | 유지 | 자유 서술·mermaid 컨텍스트 맵은 순수 도메인 |
| `스타일` | 제거 | 아키텍처 결정 |
| `모듈 구성`, 모듈 표(레이어 열 포함) | 제거 | 구조 결정 |
| `규칙 예외` | 제거 | 스타일 규칙(hex.* 등) 대상이었다. 관계 표 자체가 allow-list라 예외 개념이 불필요하다 |
| `이행` | 제거 | 스타일 이행 선언이었다. baseline 활성화는 §3.5의 파일 존재로 대체 |
| `### 구조 다이어그램` 생성 구역 | 제거 | 레이어 구조 그림이었다 |

### 3.4 새 라벨 `패키지` — 컨텍스트 → 코드 매핑

코드 검증(D1)에는 "컨텍스트가 코드 어디인가"가 필요하다. 기존에는 레이어 패턴 합집합에서
얻었으므로 대체 선언이 필요하다.

- **규약 기본값**: `{기본 패키지}.{컨텍스트}..` — 선언 0줄로 동작한다.
- **명시 오버라이드**: 규약과 다른 컨텍스트만 `- 패키지: com.acme.billing..`처럼 적는다.
- **복수 위치**: 여러 위치에 걸친 컨텍스트(구 app-embedded 형태)는 쉼표 목록을 허용한다 —
  `- 패키지: com.acme.web.claim.., com.acme.batch.claim..`

### 3.5 파생 규칙 3종 → 1종, baseline 래칫

- `derived.context-isolation`만 존속한다: 컨텍스트 패키지 안의 소스가 다른 컨텍스트 패키지를
  import하면, 그 쌍이 관계 표에 열려 있어야 한다.
- `derived.app-confinement`·`derived.shared-module-direction`은 앱·공용 모듈이라는 구조 개념
  소관이므로 제거한다.
- **baseline 래칫은 존속한다.** `이행` 라벨 대신 `baseline.jsonl` 파일 존재로 활성화한다.
  브라운필드에서 init가 기존 교차 참조 위반을 실측한 뒤 동결 여부를 묻는다. 동결은 init,
  소비는 check_imports, 축소는 migrate — 기존 원칙 그대로다.

## 4. 스킬 10개 → 8개

### 4.1 제거: fitness · scaffold

존재 이유가 아키텍처다(스타일 규칙→테스트 생성, 스타일 템플릿 전개). 통째로 삭제한다.
`profiles/` 전체(kotlin-spring·java-spring의 rule-mappings·api-verification·templates·examples)도
함께 삭제한다 — 전부 스타일 산출물이다.

### 4.2 유지 8개 — 수술 내용

원칙: 각 스킬의 뼈대(게이트·인터뷰 규율·append 규칙·확정은 사용자만)는 건드리지 않고
아키텍처 절만 들어낸다.

| 스킬 | 수술 | 규모 |
|---|---|---|
| `model` | 문서 경로만 변경 (`docs/domain/`) | 최소 |
| `apply` | 프로파일 참조 제거 — 언어·테스트 관례는 대상 코드베이스에서 감지한다. `@Tag("INV-...")` 규약 유지 | 소 |
| `adr` | 결정→기계 규칙 연결에서 "규칙 예외·스타일 선언·어휘 확장" 제거, "관계 표 변경·분류 변경" 연결로 대체 | 소 |
| `evolve` | 신호(컨텍스트별 변경률·미귀속 변경·핫스팟·공변경)는 이미 도메인 경계 신호라 유지. `evolution-signals.md`의 스타일 이행 해석만 절제 | 소 |
| `review` | 결정적 검사(컨텍스트 격리) → 의미론 위임 구조 유지. 위임 관측 범주를 아키텍처 5범주에서 도메인 범주(경계 누수·유비쿼터스 언어 불일치·애그리거트 경유 위반 등)로 재정의 | 중 |
| `sync` | 대조 축 6→5: "레이어 매핑 불일치" 축 제거, "깨진 참조" 축에서 스타일 참조 제거. 처분 선택지의 scaffold 항목은 "패키지 직접 생성" 안내로 대체 | 중 |
| `migrate` | baseline 클러스터 상환 구조 유지. 부채 종류가 컨텍스트 격리 위반 하나로 줄고 `이행` 라벨 연동 제거 | 중 |
| `init` | 인터뷰에서 스타일·모듈 구성 단계 제거, 경계·분류·관계 유지. 기존 코드 스캔은 "모듈 구성 추정" 대신 "패키지 구조에서 컨텍스트 후보 추정". baseline 동결은 브라운필드 실측 후 질문. 산출은 `DOMAIN.md`+파생물 | 대 |

### 4.3 에이전트·훅

- `arch-reviewer` → `domain-reviewer` 개명. 읽기 전용·전달받은 지식 문서의 규칙 절로만 판정하는
  구조는 유지하고, 자유 관측 범주를 도메인 것으로 재정의한다.
- SessionStart 훅(`session_summary.sh`)은 `docs/domain/summary.md`로 경로만 변경한다.

## 5. 스크립트 8개 → 6개

| 스크립트 | 운명 |
|---|---|
| `parse_architecture.py` | → `parse_domain.py` — 새 템플릿(§3) 파서. 스타일·모듈 표·애플리케이션 표·패키지 규약 표 파싱 제거, `패키지` 라벨(+규약 기본값·복수 위치) 추가 |
| `parse_style.py` | **삭제** |
| `resolve_rules.py` | **삭제** — 유효 규칙이 context-isolation 하나뿐이라 해석기 층이 과잉이다. 파서가 관계 allow-list를 직접 산출하고 check_imports가 소비한다 |
| `check_imports.py` | 컨텍스트 격리 전용으로 축소 — 레이어 규칙 핸들러 전부 제거. baseline 소비와 `[0건 경고]`(침묵 방지) 유지 |
| `check_invariants.py` | 유지 — 경로·문서명 참조만 갱신. `검사 불능` 판정 유지 |
| `collect_signals.py` | 유지 — 관측만 하고 임계값을 갖지 않는 원칙 그대로 |
| `build_index.py` | 유지 |
| `session_summary.sh` | 경로만 변경 |

**"가장 넓은 게이트"가 `resolve_rules.py`에서 `parse_domain.py`로 내려온다.** 층이 하나 줄어드는
만큼 파서가 관계 표 정합성(존재하지 않는 상대 컨텍스트 참조, 중복 관계 등)까지 책임진다.
exit 규약은 기존 관례를 따른다: 파서류의 1은 해석 실패, 검사기류의 1은 정상 판정 결과(위반
발견), `collect_signals.py`의 1은 산출 불가.

## 6. 지식·거버넌스·테스트

### 6.1 지식 베이스 18종 → 12종

- 삭제: `styles/` 4종(clean·hexagonal·layered-domain·layered-simple), `structure/`
  2종(module-composition·package-conventions).
- 유지 12종(strategic 4·tactical 5·patterns 3)의 손질은 두 가지뿐이다:
  frontmatter `read_when`에서 죽는 스킬(fitness·scaffold) 참조 제거, 본문에서 스타일 문서
  링크·레이어 전제 표현 완화(예: persistence의 "어댑터 봉쇄" → "영속 코드 격리". 전면 재작성
  아님).
- `build_index.py`로 INDEX 재생성. 지식 추가 메커니즘(정확히 한 단계 디렉터리, draft 승격
  규칙, study 스킬)은 무수술.

### 6.2 거버넌스 문서 6종 → 5종

| 문서 | 운명 |
|---|---|
| `architecture-template.md` | → `domain-template.md` — §3의 `DOMAIN.md` 정본으로 재작성 (최대 작업) |
| `rule-vocabulary.md` | **삭제** — 어휘 체계(primitive 5종+파생 3종)가 사라진다. context-isolation의 정의·baseline 문법은 `domain-template.md`의 한 절로 흡수 |
| `domain-doc-template.md` | 유지 — 경로(`docs/domain/`)만 반영, 내용 무수술 |
| `evolution-signals.md` | 스타일 이행 관련 해석만 절제 |
| `adr-template.md` | 유지 |
| `knowledge-doc-template.md` | 유지 |

### 6.3 테스트

- 삭제 대상: parse_style·resolve_rules 테스트 전체, check_imports의 레이어 규칙 테스트,
  `tests/fixtures/styles/` 픽스처.
- 신규: `parse_domain.py`는 새 픽스처로 새 테스트를 쓴다.
- 원칙: **유지 스크립트의 기존 테스트는 한 줄도 잃지 않는다.** 정확한 삭제/신규 규모는 구현
  계획 단계에서 실측 산정한다.
- 실행 방식 불변: `python3 -m unittest discover -s tests`, 표준 라이브러리만.

## 7. 이름 — superdomain 채택

검토 결론: **적절하다. 채택한다.**

- 장점: superpowers→superarchitect 계보와 일관되고, 재편 후 초점("도메인")을 이름이 정확히
  말하며, `/superdomain:model` 스킬 프리픽스와 SSOT `DOMAIN.md`가 이름과 한 몸이 된다.
- 리스크: "domain"이 도구 생태계에서 DNS 도메인으로 오독될 여지. README 첫 문장("DDD 기반
  도메인 거버넌스 플러그인")이 즉시 보완하므로 수용한다. 모호성 0인 대안 `superddd`는
  발음·가독이 나빠 비채택.
- 개명 범위: GitHub 리포지토리명(구 URL은 GitHub 리다이렉트), 로컬 디렉터리,
  `.claude-plugin/plugin.json`·`marketplace.json`, 스킬 프리픽스 `/superdomain:*`, 생성 구역
  마커 `superdomain:*`, README 설치 명령.

## 8. 작업 순서

개명은 마지막이다(D5). 중간 단계에서는 기존 이름의 마커·프리픽스를 그대로 쓰다가 마지막에 한
번에 치환해야 diff가 깨끗하다.

1. **삭제** — fitness·scaffold 스킬, `profiles/` 전체, styles·structure 지식 6종, 관련
   테스트·픽스처.
2. **파서·검사기 재편** — `parse_domain.py` 신설(새 템플릿), `check_imports.py` 축소,
   `parse_style.py`·`resolve_rules.py` 제거, 새 테스트.
3. **스킬 8개 수술** + 에이전트 개명·훅 경로 변경.
4. **거버넌스·지식·README 정리** — `domain-template.md` 재작성, rule-vocabulary 흡수·삭제,
   지식 12종 손질, INDEX 재생성, README 재작성.
5. **일괄 개명** — 전 저장소 문자열 치환(superarchitect → superdomain), 리포지토리·디렉터리
   개명, 설치 명령 검증.

각 Phase 종료 시 검증: 전체 테스트 통과 + 죽은 참조 grep(`fitness`·`scaffold`·`스타일`·
`resolve_rules` 등이 유지 파일에 남지 않았는지).

## 9. 범위 밖 (YAGNI)

- 기존 `superarchitect:*` 마커·`ARCHITECTURE.md`와의 하위 호환 계층 — 이행 대상 프로젝트가
  없다.
- 새 아키텍처 검증의 재도입 여지(플러그인 분리, 확장 포인트) — 필요가 증명될 때 논의한다.
- kt/java 외 언어 지원 확대 — check_imports·check_invariants의 현 지원 범위를 유지한다.
- 용어집(보편언어) — 기존 원칙대로 superglossery에 위임.

## 10. 성공 기준

1. 스킬 8개·스크립트 6개·에이전트 1개·훅 1개가 전부 실재하고, 아키텍처(스타일·레이어·모듈
   구성) 개념이 유지 파일 어디에도 남지 않는다.
2. `DOMAIN.md` 템플릿이 파서 게이트를 통과하는 완본 예시와 함께 `domain-template.md`에
   정본화된다.
3. `check_imports.py`가 관계 표 allow-list만으로 컨텍스트 격리를 판정하고, baseline 래칫이
   동결(init)·소비(check_imports)·축소(migrate) 전 경로에서 동작한다.
4. 전체 테스트가 통과하고, 유지 스크립트의 기존 테스트 손실이 0건이다.
5. 저장소·플러그인·마켓플레이스·스킬 프리픽스·마커가 전부 superdomain으로 일관되고, 새 설치
   명령이 실제로 동작한다.
