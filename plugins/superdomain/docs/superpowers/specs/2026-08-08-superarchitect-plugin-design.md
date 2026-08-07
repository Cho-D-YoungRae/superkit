# superarchitect — Claude Code 플러그인 설계 스펙

- 날짜: 2026-08-08
- 상태: 승인됨 (브레인스토밍 세션 확정안)
- 역할: **이 문서가 유일한 요구사항 소스다.** 1차 설계안을 대체하며, 브레인스토밍에서 확정된 결정(부록 A)과 검증된 외부 사실(부록 B)을 반영했다.
- 다음 단계: superpowers:writing-plans로 구현 계획 작성. Phase 단위로 진행하고, 각 Phase가 끝나면 검증 절차를 실행한 뒤 멈춰서 사용자 확인을 받는다.

## 0. 시작 전 참고

- 플러그인 스펙·라이브러리 버전은 2026-08-07에 공식 문서로 검증 완료(부록 B). 구현 중 어긋나는 동작을 발견하면 공식 문서를 재확인한다.
- 개발 루프: `claude --plugin-dir .`로 로컬 테스트. SKILL.md 본문 변경은 즉시 반영되지만 plugin.json·hooks·agents 변경은 `/reload-plugins` 또는 재시작이 필요하다.

## 1. 이 플러그인이 해결하는 문제

- Claude Code는 세션마다 아키텍처 해석이 달라진다: DDD 적용 방식, 도메인별 아키텍처 스타일 선택, 미시 컨벤션(패키지 구조, 의존 방향, 네이밍)이 매번 재추측된다.
- LLM 리뷰에만 의존하면 리뷰 자체가 세션별로 흔들려 문제가 재귀한다.
- 아키텍처 문서는 시간이 지나면 코드와 어긋난다(문서 부패). 낡은 문서는 낡은 코드를 낳는다.

superarchitect는 문서 기반 아키텍처·도메인 거버넌스로 이 문제를 푼다. 질문을 통해 구조와 도메인을 명확히 하고, 그 결과를 사람과 Claude가 함께 읽는 문서로 고정하고, 선언된 것을 결정적으로 강제한다.

## 2. 설계 원칙 — 모든 구현 판단의 기준

1. **SSOT는 md 문서다**: 구조의 진실은 저장소 루트의 `ARCHITECTURE.md`, 도메인의 진실은 `docs/architecture/domain/<context>.md`다. ARCHITECTURE.md는 자유롭게 쓰는 문서이되, 플러그인이 정의한 결정 템플릿(필수 섹션·라벨 필드·표)을 반드시 포함한다 — 템플릿이 곧 스키마다. `scripts/parse_architecture.py`가 이 템플릿을 결정적으로 파싱·검증하고, 다른 스크립트들은 이 파서를 공유해 ARCHITECTURE.md를 즉석에서 읽는다 — 중간 캐시 파일(json 등)은 두지 않는다. 훅이 쓰는 `summary.md`와 문서 내 다이어그램 구역은 파생물이며 손으로 편집하지 않는다. 별도 설정 파일(yaml 등)도 두지 않는다.
2. **결정적 검증 우선**: 의존 방향·패키지 배치·네이밍·불변식 테스트 커버리지처럼 기계적으로 판정 가능한 것은 생성된 코드(Konsist/ArchUnit 테스트, 검사 스크립트)로 강제한다. LLM 리뷰는 의미론적 판단에만 쓴다.
3. **예방 > 검증 > 리뷰**: SessionStart 훅으로 매 세션에 요약을 주입하고, scaffold로 처음부터 올바른 구조를 생성한다. 리뷰는 마지막 방어선이다.
4. **언어 불문 코어 + 언어 프로파일**: 도메인 분류·바운디드 컨텍스트·ADR·문서 스키마는 언어 무관 코어. 강제와 스캐폴드는 `profiles/`에 격리한다. v1은 `kotlin-spring`, `java-spring` 두 프로파일을 구현하고 그 외 언어는 추후 대응한다.
5. **Progressive disclosure**: 각 SKILL.md는 절차 중심으로 500줄 이하. 상세 지식은 `references/`에 두고 필요할 때만 읽게 한다.
6. **권장 프리셋 + 개방형 스타일, 폐쇄형 규칙 어휘**: 플러그인은 검증된 스타일 프리셋(layered-simple, layered-domain, hexagonal, clean)을 권장하되 강제하지 않는다. 프로젝트는 자체 스타일을 정의할 수 있다 — 단, 모든 스타일(프리셋 포함)은 플러그인이 정의한 **규칙 어휘(rule primitive)**의 조합으로 선언되어야 한다. 폐쇄적인 것은 어휘뿐이고, 스타일은 어휘의 조합으로서 개방이다. 일관성의 강제 대상은 "어떤 스타일이냐"가 아니라 **"선언한 스타일을 지키느냐"**다 — 선언되지 않은 임의 변형은 강제할 방법이 없으므로 수용하지 않는다.
7. **도메인 우선(domain-first)**: 도메인 모델은 선행 분석으로 완성하는 것이 아니라 질문 주도 세션으로 반복해서 명확해지고 코드와 함께 자란다. 필요하면 이벤트 스토밍으로 시작한다. 구현 순서는 항상 inside-out이다 — 도메인 코어(불변식·애그리거트·VO) → 얇은 퍼사드 → 포트/어댑터 → 인터페이스·배치 같은 기계적 작업. 용어집(보편언어)은 이 플러그인이 만들지 않는다 — superglossery 플러그인에 위임하고 통합 지점만 제공한다.
8. **단순하게 시작**: 의심스러우면 더 단순한 쪽을 택한다(YAGNI). 파생 파일·상태·설정은 필요가 증명될 때만 추가한다. 특히 지식 베이스에 문서를 추가하는 마찰을 최소로 유지한다 — 이 플러그인의 가치는 개발자가 스터디하며 지식을 계속 쌓아 넣는 데서 나오기 때문이다.

## 3. 저장소 구조

이 저장소가 곧 플러그인이다(`.claude-plugin/plugin.json`이 루트에 위치). 플러그인 컴포넌트(skills/, agents/, hooks/)와 별개로, 플러그인 자체를 보완할 때 쓰는 **저장소 로컬 스킬**을 `.claude/skills/`에 둔다 — 이 저장소를 연 세션에서만 노출되고 플러그인 설치 대상에는 배포되지 않는다.

```
superarchitect/
├── .claude-plugin/
│   └── plugin.json              # name: superarchitect, version: 0.1.0 (필수 필드는 name뿐)
├── .claude/
│   └── skills/
│       └── add-knowledge/SKILL.md   # 저장소 로컬 스킬 — 지식 베이스 추가 (§7)
├── skills/                      # 플러그인 배포 스킬 10개 → /superarchitect:<skill>
│   ├── init/SKILL.md
│   ├── scaffold/SKILL.md
│   ├── review/SKILL.md
│   ├── fitness/SKILL.md
│   ├── adr/SKILL.md
│   ├── sync/SKILL.md
│   ├── evolve/SKILL.md
│   ├── migrate/SKILL.md
│   ├── model/SKILL.md
│   └── apply/SKILL.md
├── agents/
│   └── arch-reviewer.md
├── hooks/
│   └── hooks.json
├── scripts/
│   ├── session_summary.sh       # SessionStart 훅용
│   ├── parse_architecture.py    # 결정 템플릿 파서·검증기 — 다른 스크립트가 import해 공유 (stdlib)
│   ├── check_imports.py         # python3 stdlib만 사용
│   ├── collect_signals.py       # python3 stdlib만 사용
│   ├── check_invariants.py      # domain 문서 불변식 ID ↔ 테스트 태그 대조 (stdlib)
│   └── build_index.py           # knowledge 메타 → INDEX.md 재생성 (stdlib)
├── references/
│   ├── INDEX.md                 # 생성물 — 전체 문서 카탈로그, 라우팅 진입점
│   ├── governance/              # 플러그인 운영 정본
│   │   ├── architecture-template.md
│   │   ├── rule-vocabulary.md   # 폐쇄형 규칙 어휘(primitive) 정본
│   │   ├── adr-template.md
│   │   ├── evolution-signals.md
│   │   ├── knowledge-doc-template.md
│   │   └── domain-doc-template.md
│   └── knowledge/               # 아키텍처 지식 베이스 — 계속 확장되는 참고자료
│       ├── strategic/           # domain-classification, bounded-contexts, context-mapping, event-storming
│       ├── styles/              # 권장 프리셋: layered-simple, layered-domain, hexagonal, clean — 변형별 1파일
│       ├── tactical/            # aggregates, value-objects, domain-events, repositories-domain-services, persistence
│       ├── patterns/            # cqrs, event-sourcing, outbox
│       └── structure/           # module-composition, package-conventions
└── profiles/
    ├── README.md                # 프로파일 계약 — 제3 프로파일 추가 = 계약 구현
    ├── kotlin-spring/
    │   ├── rule-mappings.md     # rule primitive → Konsist 코드 매핑
    │   ├── templates/           # 프리셋 스타일별 scaffold 템플릿 (4종 각각)
    │   └── examples/            # 좋은/나쁜 사례 각 1개 (짧게)
    └── java-spring/
        ├── rule-mappings.md     # rule primitive → ArchUnit 코드 매핑
        ├── templates/
        └── examples/
```

`knowledge/`의 주제 디렉터리는 **정확히 1단계로 고정**한다. 주제 아래 추가 중첩은 build_index.py가 오류로 거부한다 — "디렉터리가 계속 깊어질" 수 없는 구조. 새 주제 = 디렉터리 생성이면 끝(등록 절차 없음).

## 4. 구조 선언 — ARCHITECTURE.md 결정 템플릿

구조 SSOT는 저장소 루트의 `ARCHITECTURE.md` 한 파일이다. yaml 같은 별도 설정 문법을 쓰지 않는다(근거: 부록 A-2). 대신 플러그인이 결정 템플릿을 정의한다: 반드시 존재해야 하는 섹션, 라벨 필드(`- 키: 값`), 표의 집합이다. 템플릿이 곧 스키마 역할을 한다 — 어떤 내용이 결정되어야 하는지는 템플릿이 알려주고, 결정 없이는 파서가 통과시키지 않는다. 템플릿 밖의 서술은 완전히 자유다(파서는 아는 섹션·라벨만 읽고 나머지는 무시한다) — 이것이 다양한 구조·서술에 대응하는 확장 지점이다.

### 4.1 템플릿 스켈레톤

```markdown
# <프로젝트명> — Architecture
<!-- superarchitect:template v1 -->

## 프로젝트: backend                 ← 거버넌스 대상마다 반복 (1개 이상 필수)
- 경로: backend                      (저장소 루트 기준 상대경로. 단일 레포는 ".". 미생성 경로 허용 — 설계 선행)
- 프로파일: kotlin-spring            (profiles/ 하위 디렉토리명)
- 기본 패키지: com.acme
- 아키텍처 테스트 위치: architecture-test/src/test/kotlin/arch   (프로젝트 경로 기준)

## 컨텍스트 맵                       ← 생성 구역 (mermaid — 컨텍스트·관계·애플리케이션)

## 컨텍스트: claim                   ← 컨텍스트마다 이 섹션을 반복
- 프로젝트: backend                  (프로젝트가 1개뿐이면 생략 가능 — 파서가 유일 프로젝트로 귀속)
- 분류: core                        (core | supporting | generic)
- 스타일: hexagonal                 (프리셋 이름 또는 custom/<name> → docs/architecture/styles/<name>.md)
- 모듈 구성: multi-module            (multi-module | single-module | app-embedded)
- 패턴: cqrs, outbox                (knowledge/patterns/ 문서 키)
- 규칙 예외: -hex.ports-owned-inside (ADR-0002)   ← 제외에는 근거 ADR 필수
- 이행: layered-simple → hexagonal   (점진 이행 중일 때만)

| 모듈 | 경로 | 레이어 |               ← multi-module·single-module일 때 필수. 경로는 소속 프로젝트 루트 기준
|---|---|---|
| claim-domain | claim/domain | domain |
| claim-application | claim/application | application |
| claim-adapter-in | claim/adapter-in | adapter |
| claim-adapter-out | claim/adapter-out | adapter |

### 관계
| 상대 | 유형 | 계약 |
|---|---|---|
| policy | customer-supplier | claim-events-v1 |

### 구조 다이어그램                   ← 생성 구역 (mermaid)
### 근거                            ← 자유 서술 — 어떤 소제목이든 추가 가능

## 컨텍스트: admin
- 분류: generic
- 스타일: layered-simple             ← JPA 엔티티 직접 사용 허용 — 이 변형의 정의적 특징
- 모듈 구성: single-module           ← 컨텍스트당 모듈 1개 + 내부 레이어 패키지

| 모듈 | 경로 | 레이어 |
|---|---|---|
| admin | admin | all |
```

### 4.2 멀티 애플리케이션·app-embedded 실현 (imstargg 형태)

실전 멀티모듈에는 "실행 단위(애플리케이션) 모듈 여러 개 + 역할별 공유 모듈 + 앱 내부의 레이어-우선 패키지"로 구성되는 형태가 있다(검증 사례: imstargg-backend — core-api/core-admin/core-batch/core-worker 4개 앱, infrastructure/client/support 공유 모듈, 앱 내부는 `com.imstargg.core.domain.<도메인영역>` 식 레이어-우선 패키지). 이 형태에서 컨텍스트는 모듈이 아니라 **여러 앱 모듈에 걸친 패키지들**로 실현된다. 프로젝트 섹션의 선택 요소 세 가지가 이를 선언한다:

```markdown
## 프로젝트: imstargg-backend
- 경로: imstargg-backend
- 프로파일: kotlin-spring
- 기본 패키지: com.imstargg
- 아키텍처 테스트 위치: architecture-test/src/test/kotlin

### 애플리케이션                ← 실행 단위 (선택 — 멀티 앱일 때)
| 이름 | 모듈 경로 | 포함 컨텍스트 |
|---|---|---|
| core-api | core/core-api | brawlstars, statistics, operation, renewal |
| core-batch | core/core-batch | brawlstars, statistics |
| core-worker | core/core-worker | brawlstars |
| core-admin | core/core-admin | all |

### 공용 모듈                   ← 컨텍스트에 속하지 않는 공유 모듈 (선택)
| 모듈 | 경로 | 역할 |
|---|---|---|
| core-enum | core/core-enum | shared-kernel |
| db-core | infrastructure/db-core | infrastructure |
| brawlstars-client | client/brawlstars-client | client |
| logging | support/logging | support |

### 패키지 규약                 ← app-embedded 컨텍스트가 있을 때 필수 (레이어 → 패턴, {컨텍스트}·{앱} 변수)
| 레이어 | 패턴 |
|---|---|
| domain | com.imstargg.core.domain.{컨텍스트}.. |
| application | com.imstargg.core.application.{컨텍스트}.. |
| presentation | com.imstargg.core.{앱}.. |    ← {컨텍스트} 없는 패턴 = 컨텍스트 비분할 레이어

## 컨텍스트: brawlstars
- 프로젝트: imstargg-backend
- 분류: core
- 스타일: layered-domain
- 모듈 구성: app-embedded       ← 모듈 표 없음 — 패키지 규약이 실현을 정의
```

### 4.3 파싱 계약과 규칙 (정본: `references/governance/architecture-template.md`)

1. **섹션 열거**: `## 프로젝트: <name>` 헤딩이 거버넌스 대상 프로젝트를(1개 이상 필수), `## 컨텍스트: <name>` 헤딩이 컨텍스트를 열거한다. 각 섹션 아래의 라벨 필드, 알려진 표(`### 애플리케이션`, `### 공용 모듈`, `### 패키지 규약`, 컨텍스트의 첫 표=모듈 표, `### 관계`)를 읽는다. 알려지지 않은 헤딩·문단·소제목은 무시한다 — 자유 확장 지점.
2. **정규 값만 허용**: 분류는 `core | supporting | generic`, 모듈 구성은 `multi-module | single-module | app-embedded`, 스타일은 프리셋 이름 또는 `custom/<name>`, 공용 모듈 역할은 `shared-kernel | infrastructure | client | support`, 관계 유형은 DDD 컨텍스트 매핑 유형(`partnership, customer-supplier, conformist, acl, open-host, published-language`)만. `parse_architecture.py`가 필수 결정 누락·비정규 값·깨진 참조를 **라인 번호와 함께** 오류로 보고한다.
3. **실현 정규화 원칙**: 어떤 실현 형태(모듈 표·패키지 규약)든 파서가 **"컨텍스트 × 레이어 → 패키지 패턴 집합"으로 정규화**하고, fitness·check_imports·collect_signals는 정규화 결과만 소비한다. Konsist/ArchUnit 규칙은 패키지 패턴 기반이므로 강제 파이프라인이 실현 형태와 무관해진다. 모듈 정보(경로)는 sync(존재 대조)와 scaffold(생성 위치)가 사용한다.
4. **app-embedded 제약**: 해당 컨텍스트가 있으면 소속 프로젝트에 패키지 규약 표와 애플리케이션 표가 필수(없으면 오류), 컨텍스트의 모듈 표는 두지 않는다(있으면 오류). 같은 프로젝트의 app-embedded 컨텍스트들은 같은 규약을 공유하므로 같은 스타일이어야 하며, 규약 표의 레이어 이름은 그 스타일이 선언한 레이어 이름과 일치해야 한다(파서 검증).
5. **선언에서 파생되는 표준 규칙** (모두 어휘의 forbid-import 인스턴스로 fitness가 생성):
   - 공용 모듈 → 앱/컨텍스트 코드 의존 금지(역할 공통). `shared-kernel`만 도메인 레이어에서 import 허용, 나머지 역할은 domain-pure 컨텍스트의 domain 레이어에서 금지(기존 domain 규칙에 자연 포함).
   - 애플리케이션 봉쇄: 앱은 "포함 컨텍스트"로 선언된 컨텍스트의 코드만 참조(`all` 허용). 컨텍스트·공용 코드는 앱 코드에 의존 금지(조립은 앱에서만).
   - 컨텍스트 간 직접 참조는 기본 금지, "관계" 표에 선언된 쌍만 허용 — 관계 표가 문서화를 넘어 결정적 강제의 입력이 된다(유형별 허용 방향 해석은 architecture-template.md가 정본).
6. **스타일은 선언되어야 한다**: 커스텀 스타일은 `docs/architecture/styles/<name>.md`에 프리셋과 같은 선언 형식(레이어 목록 + rule primitive 인스턴스 + id — 역시 라벨·표 기반)으로 정의한다. 선언 없는 임의 변형은 모든 스킬이 거부하고 가장 가까운 프리셋 또는 커스텀 스타일 선언 절차를 안내한다.
7. **규칙 어휘는 폐쇄형이다**: 스타일이 선언할 수 있는 규칙은 `references/governance/rule-vocabulary.md`의 primitive와 그 파라미터 조합뿐이다. 초기 어휘 5종: `layer-order`, `forbid-import`, `confine-type`, `naming-suffix`, `forbid-sibling-dependency`(동일 레이어 내 특정 suffix 타입 간 의존 금지 — "서비스끼리 참조 금지"용). 어휘 밖 검증이 필요하면 어휘에 정식 등록(정의 + 두 프로파일 매핑)하는 것이 유일한 확장 경로다. "규칙 예외"의 제외에는 근거 ADR을 반드시 함께 기록한다(review가 인용). `*.domain-pure` 제거처럼 스타일의 정체성에 해당하는 규칙이라면, 예외 대신 스타일 자체를 layered-simple로 바꾸는 것이 맞지 않은지 먼저 검토하게 한다.
8. **이행과 baseline 래칫**: "이행" 필드가 있으면 init이 목표 스타일 기준의 현재 위반 전량을 `baseline.jsonl`로 동결한다. 이후 review/fitness는 baseline에 있는 위반 = warn(기존 부채), 없는 위반 = blocker로 판정한다 — 부채는 늘 수 없고 줄기만 하는 래칫이다. baseline은 migrate(§6.8)로만 축소되며, 비면 이행 필드를 제거한다. 출발 스타일은 가장 가까운 근사 기록일 뿐 정밀할 필요 없다 — 실제 차이는 전부 baseline이 흡수한다.
9. **캐시 없음**: 중간 캐시 파일(json 미러 등)은 만들지 않는다 — check_imports.py, collect_signals.py 등 다른 스크립트는 parse_architecture의 파서 함수를 import해 ARCHITECTURE.md를 즉석 파싱한다. 수백 줄 md 파싱은 밀리초라 캐시가 불필요하고, 캐시가 없으면 재생성 누락으로 인한 드리프트도 원천 차단된다.
10. **템플릿 버전 관리**: 상단 `<!-- superarchitect:template v1 -->` 마커로 버전을 표시한다. 해석이 갈리면 architecture-template.md가 정본이며, 템플릿 변경은 버전 마커를 올리고 마이그레이션 노트를 남긴다.

### 4.4 요구 변형 커버리지 보증

사용자가 요구한 구현 변형이 어휘·선언으로 표현됨을 설계 단계에서 보증한다:

| 요구 사례 | 표현 방법 |
|---|---|
| 레이어드 3계층 vs 4계층 | 스타일 선언의 레이어 목록 자체가 자유 — `layer-order`는 선언된 순서에 적용 |
| 서비스끼리 참조 금지 | `forbid-sibling-dependency(layer=application, suffix=Service)` |
| JPA 엔티티 vs 순수 객체 | `confine-type`(JPA 엔티티를 어댑터에 격리) — layered-simple만 이 규칙 없음 |
| 멀티 앱 + 레이어-우선 패키지 (imstargg) | `app-embedded` + 애플리케이션·공용 모듈·패키지 규약 표 (§4.2) |

## 5. 대상 프로젝트에 생성·관리되는 산출물

모노레포 대응 원칙: **SSOT와 모든 산출물은 git 루트에 고정**한다(근거: 부록 A-1). 컨텍스트는 도메인 개념이라 프로젝트 소속과 무관하게 루트가 맞고, 프로젝트를 넘는 도메인 관계도 한 문서에서 표현된다. 전제: 모노레포 = 단일 git 저장소. git submodule 등 멀티 레포 워크스페이스는 v1 범위 외로 명시한다.

```
ARCHITECTURE.md              # 구조 SSOT (루트) — 결정 템플릿 + 본문 + 생성 구역 다이어그램
docs/architecture/
├── summary.md               # 파생물 — SessionStart 훅이 그대로 주입 (30줄 이내)
├── domain/                  # 도메인 SSOT — 컨텍스트별 도메인 모델 문서 (model·apply·review가 관리)
│   └── <context>.md         # 불변식(ID)·애그리거트·VO·도메인 이벤트·도메인 서비스·열린 질문 + mermaid
├── styles/                  # (선택) 커스텀 스타일 선언 — 프리셋과 같은 형식
├── conventions/             # (선택) 프로젝트 고유 컨벤션 문서 — §11.1 문서 표준을 따름
├── review-log.jsonl         # review가 append — evolve의 입력
├── baseline.jsonl           # init이 동결한 기존 위반(래칫) — migrate로만 축소, 비면 삭제
└── decisions/
    ├── 0001-record-architecture-decisions.md
    └── ...
```

- 컨텍스트가 하나뿐인 프로젝트는 `domain/<context>.md` 대신 `docs/architecture/DOMAIN.md` 한 파일로 통합할 수 있다.
- 모든 파생물 상단에 다음 헤더를 넣는다: `<!-- GENERATED by superarchitect from ARCHITECTURE.md — 직접 수정 금지, 결정 템플릿 또는 SSOT 문서를 수정할 것 -->`
- ARCHITECTURE.md 본문의 "생성 구역"은 `<!-- superarchitect:generated:... -->` 마커로 감싸고 스킬만 갱신한다 — 그 밖의 본문은 자유 서술이다. 결정 템플릿을 변경하는 모든 스킬은 종료 전에 `parse_architecture.py`로 검증을 통과시키고, summary.md와 생성 구역(컨텍스트 맵·컨텍스트별 구조 mermaid)을 갱신한다.
- 다이어그램은 전부 mermaid로 작성한다 — 사람과 Claude가 같은 파일을 읽는 이해용 산출물이며, 구조적 사실의 검증은 다이어그램이 아니라 fitness 테스트(Konsist/ArchUnit)가 담당한다. 같은 결정 템플릿에서 이해용(mermaid)과 검증용(테스트 코드)이 각각 생성되므로 둘은 어긋날 수 없다. 컨텍스트 맵에는 애플리케이션(실행 단위)과 컨텍스트의 관계도 표현한다.
- 플러그인의 `references/knowledge/`가 일반 지식이라면 `conventions/`는 프로젝트 로컬 지식이다 — "우리 프로젝트에서 DTO 변환은 이렇게 한다" 수준의 규칙. 같은 문서 표준(§11.1)을 따르고, review·scaffold는 두 계층을 모두 참조하며 같은 key가 충돌하면 로컬이 우선한다.
- `domain/<context>.md`는 `governance/domain-doc-template.md` 표준을 따른다: 불변식은 `INV-<CONTEXT>-NNN` ID·서술·상태(proposed | confirmed)를 갖고, 애그리거트·VO·도메인 이벤트·도메인 서비스 목록(경계·흐름은 mermaid 병기), 그리고 열린 질문(다음 논의 안건 — model과 review가 append) 섹션으로 구성한다. 용어 정의는 이 문서에 쓰지 않는다 — superglossery가 관리하는 용어집을 참조만 한다. domain 문서는 domain-pure 스타일(hexagonal·layered-domain·clean 및 domain-pure를 포함한 커스텀) 컨텍스트에 필수, layered-simple 컨텍스트에는 선택이다.

## 6. 플러그인 스킬 명세 (10개)

공통 규칙:

- 커맨드는 `/superarchitect:<skill>` 네임스페이스로 노출된다.
- init을 제외한 모든 스킬은 시작 시 ARCHITECTURE.md의 결정 템플릿을 로드한다(스크립트는 parse_architecture의 공유 파서로 직접 읽는다). 없으면 "superarchitect가 초기화되지 않았습니다"라고 안내하고 `/superarchitect:init`을 권한 뒤 중단한다.
- description은 트리거의 유일한 근거다: 무엇을 하는지 + 언제 쓰는지(구체적 한국어/영어 트리거 문구 포함, 다소 적극적으로) + 언제 쓰지 않는지를 모두 담는다. when-to-use 정보는 본문이 아니라 description에 둔다. 상한은 1,536자(검증됨).
- SKILL.md 본문은 절차와 판단 기준만. 지식이 필요하면 references 파일 경로를 명시하고 "이 시점에 읽어라"라고 지시한다.
- 지식 참조 프로토콜: 지식이 필요하면 먼저 `references/INDEX.md`를 읽고 필요한 문서만 골라 읽는다. `knowledge/`를 통째로 또는 디렉토리 단위로 읽는 것은 금지. 읽을 문서는 (a) 대상 컨텍스트의 `스타일`·`패턴` 선언, (b) INDEX의 `read_when` 메타, (c) 대상 프로젝트 `conventions/`·`styles/` 존재 여부로 결정한다.

description 작성 예시 (init):

```yaml
---
name: init
description: >
  프로젝트의 아키텍처 거버넌스를 초기화한다 — 질문을 통해 바운디드 컨텍스트 식별, 핵심/일반/지원 분류,
  컨텍스트별 아키텍처 스타일 결정을 거쳐 루트 ARCHITECTURE.md(결정 템플릿 + 본문)와 파생물
  (summary, ADR)을 생성. 사용자가 "아키텍처 초기화", "아키텍처 셋업",
  "architecture init", "/superarchitect:init"을 요청할 때, 새 프로젝트에 아키텍처 기준을
  잡아달라고 할 때, 또는 다른 superarchitect 스킬이 ARCHITECTURE.md 부재를 발견했을 때 반드시 사용.
  이미 초기화된 프로젝트의 일상적 검토·수정에는 사용하지 않는다(review/sync 사용).
---
```

### 6.1 init

1. ARCHITECTURE.md가 이미 있으면 재초기화 여부를 확인한다.
2. **후보 프로젝트를 감지한다** — 빌드 파일 기준으로 넓게: `settings.gradle(.kts)`/`pom.xml` → JVM, `package.json` → Node, `go.mod` → Go 등. 감지 단계에서는 아무것도 제외하지 않는다. **거버넌스 대상 제안 기준은 프로파일 매칭**이다: 해당 스택에 대응하는 프로파일이 `profiles/`에 있는 후보만 제안한다(v1은 kotlin-spring·java-spring뿐이므로 결과적으로 JVM 프로젝트만 제안되지만, "백엔드라서"가 아니라 "프로파일이 있어서"다). 프로파일 없는 후보는 "감지됨 — 대응 프로파일 없음, 범위 외"로 표시만 하고 숨기지 않는다. 스택 세부 추정(예: package.json 의존성의 nest/express vs react/next)은 안내 문구 품질용으로만 쓰고 제외 판정에는 쓰지 않는다. 최종 확정은 항상 사용자다. 추후 nodejs-backend나 frontend 프로파일이 추가되면 같은 감지 로직이 해당 프로젝트를 자동으로 제안 대상에 올린다 — 구조 변경 불필요.
3. **후보가 0개면(그린필드) 신규 설계 인터뷰 모드로 진입한다** — 오류가 아니다. 질문 주도 인터뷰: "이 시스템이 해결하는 문제를 한 문단으로 말하면?", "서로 다른 용어를 쓰는 업무 영역이 있나?", "함께 바뀌는 것과 따로 바뀌는 것은?", 팀·배포 단위·규모. 한 번에 하나씩 묻고, 답을 즉시 문서 초안에 반영한다. 프로젝트 섹션의 경로는 "예정 경로"로 선언되고 ARCHITECTURE.md가 설계서로 먼저 성립한다(코드 생성은 scaffold 담당). 도메인이 흐릿하면 이벤트 스토밍 세션(`/superarchitect:model`의 스토밍 모드)을 먼저 제안한다.
4. 기존 프로젝트면 모듈 구조·패키지·의존 관계를 스캔해 바운디드 컨텍스트 후보와 현재 스타일 추정(모듈 구성 3형 중 어느 실현인지 포함)을 제시하고 사용자와 확정한다. 멀티 앱 형태면 애플리케이션·공용 모듈·패키지 규약 표를 함께 도출한다.
5. 컨텍스트별 분류를 확정한다 — `references/knowledge/strategic/domain-classification.md`의 질문 체크리스트를 사용. 분류에 따른 스타일 기본값(프리셋)을 제안하되 최종 결정은 사용자가 한다. 프리셋이 맞지 않으면 커스텀 스타일 선언(§4.3 규칙 6)을 안내한다.
6. ARCHITECTURE.md(결정 템플릿 + 본문 골격 + 생성 구역)를 작성한다. 기존 프로젝트에서 현재와 목표가 다르면 "이행" 필드(출발 → 목표)를 기록하고, 목표 기준 현재 위반 전량을 스캔해 `baseline.jsonl`로 동결한다(§4.3 규칙 8). 즉시 리팩터링을 요구하지 않는다 — 초기화는 현실을 기록하는 단계이고, 이행은 migrate 스킬이 점진적으로 담당한다. 현상 유지를 원하면 이행 필드 없이 현재 스타일을 선언하면 된다. 그린필드면 baseline·이행은 당연히 없다.
7. 파생물을 생성한다: summary.md, 생성 구역 다이어그램, decisions/0001(아키텍처 결정 기록 채택), 초기 주요 결정은 0002+.
8. CLAUDE.md에 ARCHITECTURE.md 참조 한 줄 추가를 제안한다(선택).
9. (선택) 결정적 검사 묶음(check_imports.py, check_invariants.py, superglossery가 있으면 그 check까지)을 대상 프로젝트의 git pre-commit 훅으로 설치할지 제안한다 — 매 커밋이 결정적 게이트를 통과하게 만드는 장치다. 이것은 git 훅이지 Claude Code 훅이 아니므로 v1 훅 정책(SessionStart만)과 무관하다. 마지막으로 `/superarchitect:fitness` 실행을 권한다.

### 6.2 scaffold

트리거: 새 프로젝트/컨텍스트/모듈/기능의 골격 생성 요청, 또는 sync가 "선언됐는데 없음" 드리프트에서 생성을 선택했을 때.

1. **신규 프로젝트 증분 등록**: 기존 모노레포에 새 백엔드가 생기면 프로젝트 인터뷰(경로·프로파일·기본 패키지·테스트 위치, 필요시 애플리케이션·공용 모듈·패키지 규약)를 거쳐 프로젝트 섹션을 추가한다 — 신규 컨텍스트 등록과 대칭.
2. **프로젝트 골격 생성**: 선언됐지만 디스크에 없는 프로젝트를 만나면 프로젝트 골격 자체를 생성한다 — 디렉터리, settings.gradle(.kts), 빌드 스크립트, 선언된 앱·모듈·패키지 골격까지 프로파일 템플릿으로. gradle wrapper는 생성하지 않고 명령을 안내한다.
3. 대상 컨텍스트의 스타일 확인(신규 컨텍스트면 분류 인터뷰 후 결정 템플릿에 등록) → 프리셋이면 `profiles/<profile>/templates/<style>/` 템플릿으로, 커스텀 스타일이면 스타일 선언(레이어·규칙)으로부터 골격을 유도 생성 — Gradle 모듈, 패키지, 포트/어댑터 인터페이스, 테스트 골격. app-embedded 컨텍스트면 각 소속 앱 모듈에 패키지 규약대로 레이어 패키지 골격을 생성한다.
4. 모듈/애플리케이션 표 갱신 → 파생물 재생성 → fitness 갱신 권유. 템플릿 변수는 `{{context}}`, `{{basePackage}}` 등을 치환한다. 컨텍스트에 `패턴`이 선언돼 있으면 해당 지식 문서를 읽고 골격에 반영한다(예: cqrs → command/query 패키지 분리).

### 6.3 review

1. 대상을 결정한다 (기본: git diff, 인자로 경로/브랜치 지정 가능).
2. 결정적 검사 먼저: fitness 테스트가 있으면 해당 Gradle task 실행. 없거나 빠른 검사가 필요하면 `scripts/check_imports.py`(정규화된 패키지 패턴 기반 import·의존 방향 검사)와 `scripts/check_invariants.py`(domain 문서의 confirmed 불변식마다 대응 테스트 태그 존재 확인)를 실행한다. superglossery가 설치돼 있으면 용어 검증은 그쪽 check에 위임하고 중복 검사하지 않는다.
3. 남은 의미론 검토는 arch-reviewer 서브에이전트에 위임한다: 도메인 로직 누출, 애그리거트 경계 침범, 분류 대비 과잉/과소 설계, 기존 패턴과 다른 "제2의 방식" 도입. 위임 전에 INDEX에서 대상 컨텍스트의 `스타일`·`패턴`에 해당하는 knowledge 문서와 프로젝트 `conventions/`·`styles/` 문서를 선별해 경로 목록으로 함께 전달한다.
4. 리포트: 항목별 rule id(또는 semantic 태그), 분류(위반 | 누락 | 드리프트 | 추가 논의), 심각도(blocker/warn/info), 근거 ADR 인용, 수정 제안. "추가 논의"로 분류된 항목은 해당 컨텍스트 `domain/<context>.md`의 열린 질문 섹션에 append해 다음 모델링 세션의 안건으로 만든다.
5. 결과를 `review-log.jsonl`에 append한다: `{"date","rule","path","severity","note"}`.

### 6.4 fitness

각 컨텍스트의 스타일 문서(프리셋 또는 커스텀)가 선언한 규칙 인스턴스에 컨텍스트 오버라이드(규칙 예외)와 §4.3 규칙 5의 표준 파생 규칙을 적용하고, 이를 rule primitive 단위로 해석해 `profiles/<profile>/rule-mappings.md` 매핑으로 테스트 코드를 생성한다 — 소속 프로젝트의 "아키텍처 테스트 위치"에 컨텍스트별 파일로 생성/갱신. 입력은 항상 정규화된 패키지 패턴(§4.3 규칙 3)이다. 기존 파일이 있으면 diff를 보여주고 갱신한다. 생성 헤더가 훼손된(수동 수정된) 파일을 발견하면 경고하고 덮어쓸지 확인한다. 마지막에 실행 방법(`./gradlew :architecture-test:test` 등)을 안내한다.

### 6.5 adr

`references/governance/adr-template.md`(MADR 기반)로 `decisions/NNNN-slug.md`를 생성한다. status는 proposed → accepted로 관리하고, supersede 시 신·구 ADR에 양방향 링크를 걸고 구 ADR status를 superseded로 바꾼다. 결정이 기계 검증 가능한 규칙을 함의하면 스타일 선언 또는 어휘 확장과 fitness 갱신을 제안한다.

### 6.6 sync

결정 템플릿과 실제 코드를 대조한다: 선언됐는데 없는 프로젝트/모듈, 존재하는데 미선언인 모듈, 레이어 매핑 불일치, 깨진 ADR·스타일 참조, 템플릿보다 오래된 파생물(summary.md, 생성 구역). `parse_architecture.py`의 검증 오류(필수 결정 누락, 비정규 값)도 드리프트로 보고한다. 스캔 범위는 선언된 프로젝트 경로 안으로 한정한다 — 미선언 프로젝트(frontend 등)는 오검출 대상이 아니다. 각 드리프트에 대해 [**scaffold로 생성** / 코드 수정 / 문서 수정 / 무시] 선택지를 제시하고("선언됐는데 없음"은 scaffold로 생성이 1순위 — 설계 선행 상태는 오류가 아니라 정상 플로우의 중간 단계다), 선택을 반영한 뒤 파생물을 재생성한다. 드리프트의 방향을 절대 임의로 판단하지 않는다.

### 6.7 evolve

1. `scripts/collect_signals.py`로 신호 수집: git log 기반 컨텍스트별 변경 빈도와 핫스팟(파일 → 정규화 패턴으로 컨텍스트 귀속), 모듈 크기 추이, 컨텍스트 간 의존 edge 수, review-log.jsonl의 반복 위반 집계, baseline.jsonl 크기 추이(마이그레이션 진행률).
2. `references/governance/evolution-signals.md`의 해석 규칙 적용. 예: generic/supporting인데 변경 빈도 최상위 → core 재분류 검토. 동일 rule 반복 위반 → 코드가 아니라 규칙이 낡았을 가능성 → 규칙 완화 또는 ADR 재검토 제안. 특정 컨텍스트 쌍의 결합 급증 → 관계 재정의 또는 분리/병합 검토. baseline 감소가 장기간 정체 → migrate 실행을 제안하거나 목표 스타일 자체의 재검토(목표가 과했을 가능성)를 제안. review-log에서 같은 semantic 지적이 반복되면 그 규칙을 `conventions/` 문서로 승격하는 것을 제안한다 — llm-wiki처럼 리뷰 경험이 프로젝트 지식으로 축적되는 경로다.
3. 출력: 제안 리포트 + 각 제안의 ADR 초안(proposed). 자동 적용 금지 — 사용자가 수락한 제안만 문서에 반영하고 파생물과 fitness를 갱신한다. 도메인 모델 자체의 리팩터링 제안(용어·추상화 개선, 애그리거트 재편)도 이 경로로 다룬다 — 도메인은 프로젝트와 함께 발전한다.

### 6.8 migrate

기존 프로젝트를 목표 스타일로 점진 이행시키는 스킬. baseline.jsonl이 없으면 "이행할 부채가 없습니다"로 종료한다.

1. baseline을 로드해 위반을 클러스터링한다 — 모듈·패키지·rule 단위의 응집된 작업 묶음으로.
2. 우선순위를 매긴다: collect_signals.py 기준 변경 빈도가 높은 핫스팟 우선(자주 만지는 코드부터 정리해야 이득이 크다), 의존 그래프의 말단(리프)부터(안전한 순서).
3. 한 번에 한 클러스터만 계획을 제시하고, 사용자 승인 후 수행한다 — scaffold 템플릿을 재사용해 목표 구조를 만들고 코드를 이동·매핑한다. 빅뱅 리팩터링 계획은 제시하지 않는다.
4. 완료 시 fitness를 재실행해 해당 위반이 사라졌는지 확인하고 baseline에서 제거한다. baseline이 비면 이행 필드를 제거하고 이행 완료 ADR을 기록한다.

### 6.9 model — 질문 주도 도메인 모델링 세션

도메인 전문가·개발자와의 대화로 도메인 모델을 명확히 해나가는 스킬. 트리거: "도메인 모델링", "도메인 정리", "이벤트 스토밍", "미팅 내용 정리", `/superarchitect:model <context>`.

세션 유형 3가지 — 상황을 보고 제안한다:

- 인터뷰(기본): 아래 절차대로 불변식 중심 질문.
- 이벤트 스토밍: 도메인이 넓거나 처음일 때. `references/knowledge/strategic/event-storming.md`의 텍스트 진행 규약을 따른다 — 도메인 이벤트를 과거형으로 나열 → 커맨드·액터 연결 → 애그리거트 후보로 묶기 → 컨텍스트 경계·핫스팟 표시. 결과는 domain 문서(흐름 mermaid 포함)와 ARCHITECTURE.md 컨텍스트 맵에 반영한다.
- 미팅 정리: 회의록·대화 내용을 붙여넣으면 불변식 후보·결정·열린 질문으로 구조화한다.

1. 대상 컨텍스트의 `domain/<context>.md`를 로드한다(없으면 `domain-doc-template.md`로 생성). 기존 열린 질문이 있으면 그것부터 안건으로 올린다.
2. 한 번에 하나씩 질문한다 — 불변식을 끌어내는 질문에 집중: "이 규칙은 ~한 경우에도 성립하나요?", "깨지면 어떤 비용이 발생하나요?", "누가/언제 이 결정을 내리나요?", 경계 사례·동시 변경·시점 문제. 답변은 즉시 `INV-<CONTEXT>-NNN` 불변식 후보(proposed)로 문서화한다.
3. 불변식이 모이면 knowledge/tactical/ 문서를 기준으로 애그리거트 경계·VO·도메인 이벤트 후보를 제안하고 확인받는다.
4. 합의된 항목은 confirmed로 승격하고, 결론 나지 않은 것은 열린 질문에 남긴다 — 분석을 완결하려 하지 않는다. 문서는 세션을 거듭하며 코드와 함께 자란다.
5. 새 도메인 용어가 등장하면 superglossery(`/glossary:add`)에 등록을 제안한다 — 이 문서에 용어 정의를 쓰지 않는다.
6. 종료 시 이번 세션에서 confirmed된 항목을 요약하고 `/superarchitect:apply`를 권한다.

### 6.10 apply — 도메인 문서를 코드로

domain 문서에 표현됐지만 코드에 없는 것을 찾아 구현하는 스킬. 트리거: "도메인 문서 적용", `/superarchitect:apply <context>`.

1. confirmed 항목 중 미구현을 추출한다: 테스트 소스에서 불변식 태그 스캔, 애그리거트·VO 타입 존재 확인.
2. inside-out 순서로 구현한다: 도메인 코어(애그리거트·VO와 불변식을 강제하는 로직) → 각 불변식당 `@Tag("INV-<CONTEXT>-NNN")` 테스트 → 필요한 최소한의 퍼사드·포트. proposed 항목은 구현하지 않는다(먼저 model로 확정).
3. 구현 중 발견한 모호함·모순은 임의로 해석하지 않고 열린 질문 섹션에 추가한다.
4. 완료 후 check_invariants.py와 fitness를 실행해 결정적 게이트를 통과시킨다.

## 7. 저장소 로컬 스킬 — add-knowledge

플러그인 배포 스킬이 아니다. 이 플러그인 저장소를 보완·개선할 때 쓰는 스킬로, `.claude/skills/add-knowledge/SKILL.md`에 두며 이 저장소를 연 세션에서만 노출된다. 이름은 gstack 전역 스킬 `/learn`(Manage project learnings)과의 혼동을 피해 `add-knowledge`로 확정(부록 A-4).

절차:

1. 입력을 받는다: 대화 내용, URL, 붙여넣은 노트 등 스터디 결과물.
2. `references/governance/knowledge-doc-template.md` 기반으로 초안을 작성한다 — summary(필수)와 가능하면 적용 기준·규칙 골격까지.
3. 주제를 결정한다: 기존 `knowledge/` 주제 디렉터리를 제시하고, 맞는 것이 없으면 신규 디렉터리를 만든다(1단계 고정).
4. `scripts/build_index.py`를 실행해 INDEX를 재생성하고, draft 여부를 안내한다.
5. 커밋을 제안한다.

트레이드오프(의도된 것): 다른 프로젝트 세션에서 발견한 지식은 그 자리에서 추가할 수 없고, 이 저장소를 열어 추가하는 워크플로다 — "플러그인을 보완할 때 사용"이라는 소유자 의도와 일치한다.

## 8. SessionStart 훅

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/scripts/session_summary.sh" }
        ]
      }
    ]
  }
}
```

- 스키마는 검증됨(부록 B). matcher는 생략한다 — startup·resume·clear·compact 전부에 적용되며, compact 후 재주입도 이득이다.
- `session_summary.sh`는 cwd에서 git 루트까지 상향 탐색하며 `docs/architecture/summary.md`를 찾아 있으면 그대로 출력하고(stdout이 세션 컨텍스트로 주입됨), 없으면 조용히 exit 0 한다. 파싱하지 않는다 — summary.md는 결정 템플릿 변경 시마다 스킬이 재생성해 두는 파생물이다. 모노레포에서 `backend/`를 cwd로 연 세션에서도 루트의 summary를 찾는다.
- summary.md 규격: 30줄 이내, 프로젝트·컨텍스트 표(이름/분류/스타일/모듈 수), 전역 핵심 규칙 3~5개, 마지막 줄에 "상세: ARCHITECTURE.md · 검토: /superarchitect:review".

## 9. arch-reviewer 에이전트

`agents/arch-reviewer.md`. 읽기 전용 도구(Read, Grep, Glob)만 허용. 입력으로 summary.md 내용, 검토 대상 파일/diff 목록, review 스킬이 선별한 지식 문서 경로 목록, 해당 컨텍스트의 `domain/<context>.md`를 받는다. 지시 사항: 전달받은 지식 문서의 "규칙"·"리뷰 체크리스트" 섹션을 판정 기준으로 삼고 그 외 knowledge를 임의 탐색하지 말 것, 결정적 검사로 잡히는 항목은 보고하지 말 것(중복 방지), 의미론 5범주(도메인 로직 누출 / 애그리거트 경계 / 불변식 행위 정합성 — 태그만 달린 빈 테스트, 불변식 의미와 다른 검증 / 과잉·과소 설계 / 제2의 방식 도입)만 검토, 불확실하면 severity=info. 출력은 JSON 배열: `[{type: violation|missing|drift|discussion, path, line?, severity, rationale, related_rule?, related_invariant?, related_adr?}]`.

## 10. 언어 프로파일 (kotlin-spring, java-spring)

두 프로파일은 같은 rule primitive 어휘를 각자의 도구로 구현한다: kotlin-spring은 Konsist(0.17.3, `com.lemonappdev:konsist`), java-spring은 ArchUnit(1.4.1, `com.tngtech.archunit:archunit`). 매핑 단위는 스타일이 아니라 primitive다 — 그래서 프리셋이든 커스텀 스타일이든 어휘 조합이기만 하면 fitness 생성이 자동으로 가능하다. 어휘의 의미 정본은 `governance/rule-vocabulary.md`, 프로파일은 그것을 코드로 번역할 뿐이다. `profiles/README.md`에 프로파일 계약(rule-mappings.md 형식, templates 디렉토리 규약, examples 규약)을 문서화해, 제3의 프로파일 추가가 "계약 구현"이 되게 한다.

- `kotlin-spring/rule-mappings.md`: primitive → Konsist 코드 패턴 매핑(파라미터 치환). 어휘 전체(5종 + 이후 확장)를 커버. 생성 코드 예시:

```kotlin
// GENERATED by superarchitect from ARCHITECTURE.md
// 수정 금지 — 규칙 변경은 스타일 선언에서. 재생성: /superarchitect:fitness
class ClaimArchitectureTest {
    @Test
    fun `claim - dependencies point inward`() {
        Konsist.scopeFromProject()
            .assertArchitecture {
                val domain = Layer("Domain", "com.acme.claim.domain..")
                val application = Layer("Application", "com.acme.claim.application..")
                val adapter = Layer("Adapter", "com.acme.claim.adapter..")
                domain.dependsOnNothing()
                application.dependsOn(domain)
                adapter.dependsOn(application, domain)
            }
    }
}
```

- `java-spring/rule-mappings.md`: 동일 primitive → ArchUnit 매핑(`ArchRuleDefinition`, `layeredArchitecture()` API). 같은 선언에서 Java 프로젝트용 아키텍처 테스트를 생성한다.
- baseline 연동: java-spring은 ArchUnit의 `FreezingArchRule`로 기존 위반 동결을 구현한다(정확히 이 용도의 내장 기능, ViolationStore 경로는 `archunit.properties`로 지정). kotlin-spring은 Konsist에 동등 기능이 없으므로, 생성된 테스트가 baseline.jsonl을 읽어 알려진 위반을 warn(리포트만)으로 강등하는 로직을 포함시킨다.
- `templates/<style>/` (프리셋 4종 각각, 프로파일별): settings.gradle(.kts) 조각, 모듈별 빌드 스크립트, 패키지 골격, 샘플 포트/어댑터/유스케이스, 테스트 골격. single-module용 패키지 경계 골격 변형과 app-embedded용 레이어 패키지 골격 변형도 제공한다. 커스텀 스타일은 템플릿 대신 스타일 선언으로부터 골격을 유도한다.
- Spring Modulith는 single-module 레이아웃의 보조 검증 수단으로 rule-mappings.md에 문서화만 한다(v1 생성 대상은 Konsist/ArchUnit만).

## 11. references — 지식 베이스 설계

references는 두 계층이다. `governance/`는 플러그인 운영 정본(스키마·어휘·템플릿·신호 규칙), `knowledge/`는 아키텍처 참고자료다. knowledge는 플러그인 개발자가 스터디하며 계속 추가·발전시키는 공간이다 — 문서가 수십 개로 늘어도 컨텍스트를 오염시키지 않아야 하고, 무엇보다 문서 하나를 추가하는 마찰이 최소여야 한다(§2 원칙 8). LLM의 판단은 세션마다 흔들리므로, 판단 기준을 이 문서들에 고정하고 스킬은 문서를 인용해 판단한다.

### 11.1 문서 표준 형식

모든 knowledge 문서(그리고 대상 프로젝트의 `conventions/` 문서)는 `governance/knowledge-doc-template.md`를 따른다. 메타 블록:

```yaml
---
summary: 한 줄 요약 (INDEX에 노출) — 유일한 필수 필드
read_when: [review, scaffold]   # 선택 — 생략 시 스킬이 INDEX의 summary로 판단
rules: [tactical.vo-immutable]  # 선택 — 이 문서가 정의하는 기계 검증 rule id
---
```

- key는 파일명, topic은 상위 디렉토리에서 자동 유도한다(convention over configuration). 문서 하나를 추가하는 데 필요한 것은 md 파일과 summary 한 줄뿐이다.
- frontmatter는 md 생태계의 표준 관례이므로 플러그인 내부 문서에만 유지하되, 파싱은 stdlib 범위에 고정한다: 단순 `키: 값` 라인과 대괄호 리스트(`[a, b]`)만 허용하고 그 외 yaml 문법은 지원하지 않는다. 대상 프로젝트의 산출물(ARCHITECTURE.md, domain 문서 등)은 결정 템플릿 방식만 쓴다.
- 성숙한 문서의 목표 구성(권장 순서): ① 개념 — 정의와 핵심 아이디어를 간결하게 ② 적용 기준 — 언제 쓰는가 / 언제 쓰지 않는가 판단 체크리스트 ③ 규칙 — 기계 검증 가능한 것은 rule primitive 조합으로 정의해 fitness와 연동하고, 불가능한 것은 리뷰 체크리스트로 서술 ④ 사례 — Kotlin 예시로 올바른 구현 1개, 안티패턴 1~2개 ⑤ 관련 문서 — 다른 문서의 key.
- 단, 초안은 자유 형식으로 추가해도 된다 — 스터디 중 얻은 지식을 일단 넣는 것이 완벽한 구조보다 우선이다. build_index.py는 "적용 기준"·"규칙" 섹션이 없는 문서를 INDEX에 `draft`로 표시하고, review·scaffold는 draft 문서를 판정 근거로 인용하지 않으며 참고로만 쓴다. 성숙의 기준: 판정 근거가 되려는 문서는 읽을거리가 아니라 판정 도구여야 한다 — 체크리스트와 규칙을 갖추면 draft가 벗겨진다.

### 11.2 INDEX.md — 라우팅 진입점

`scripts/build_index.py`가 각 문서의 frontmatter와 섹션을 읽어 INDEX.md를 생성한다(INDEX 수동 편집 금지 — SSOT 원칙의 자기 적용). 문서당 한 줄: `key | topic | summary | read_when | rules | draft여부`. 문서를 추가·수정하면 build_index.py를 재실행한다. 스크립트는 summary 누락, key(파일명) 중복, 깨진 관련 문서 링크, 주제 아래 추가 중첩을 오류로 보고한다.

이 구성은 karpathy의 llm-wiki 패턴을 따른다: 콘텐츠 카탈로그인 index를 먼저 읽어 관련 페이지를 찾은 뒤 해당 페이지로만 파고들며(전체를 컨텍스트에 올리지 않음), 문서 간 key 링크로 위키처럼 탐색하고, 수백 페이지 규모까지는 별도 검색 인프라 없이 index만으로 동작한다. build_index.py의 오류 보고(고아 문서, 깨진 링크)는 llm-wiki의 lint 단계에 해당한다.

### 11.3 v1 문서 목록

- `governance/`: architecture-template(결정 템플릿 정본 — 필수 섹션·라벨 필드·표 형식·정규 값·파싱 계약·정규화 규칙·버전 마이그레이션 정책), rule-vocabulary(폐쇄형 규칙 어휘 정본 — 각 primitive의 이름·의미·파라미터·예시: layer-order, forbid-import, confine-type, naming-suffix, forbid-sibling-dependency; 어휘 확장 절차 포함), adr-template(MADR 기반 템플릿과 작성 지침), evolution-signals(신호 정의, 기본 임계값, 해석 규칙, 제안 문구 템플릿), knowledge-doc-template, domain-doc-template.
- `knowledge/strategic/`: domain-classification(분류 판단 질문 체크리스트 — 경쟁 차별화 기여·변경 빈도·상용/오픈소스 대체 가능성·실패 비용, 분류→스타일 기본 매핑: core→hexagonal, supporting→layered-domain, generic→layered-simple — 즉 기본값은 순수 도메인 모델을 갖는 변형이고, JPA 엔티티 직접 사용은 layered-simple 선택으로만 열린다), bounded-contexts(식별 휴리스틱 — 언어·팀·트랜잭션·데이터 소유 경계), context-mapping(관계 유형 정의와 각각을 쓰는 시점), event-storming(텍스트 채팅 기반 진행 규약 — 이벤트 과거형 나열 → 커맨드·액터 → 애그리거트 후보 → 컨텍스트 경계·핫스팟, 결과를 domain 문서·컨텍스트 맵에 반영하는 규칙).
- `knowledge/styles/`: 권장 프리셋 4종 = layered-simple(controller-service-repository), layered-domain(도메인 레이어 분리 + 인터페이스/구현 분리), hexagonal, clean — 변형별 1파일이며, 각 파일은 rule primitive 인스턴스의 조합(+ 각 인스턴스의 id)으로 커스텀 스타일과 동일한 선언 형식을 쓴다. fitness 생성의 입력이므로 가장 정밀하게 작성한다. 각 문서는 영속성 모델 스탠스를 명시한다: layered-domain·hexagonal·clean은 `*.domain-pure`(도메인 모델은 JPA·프레임워크 무관 순수 Kotlin/Java, 영속 엔티티는 어댑터/인프라에 격리)를 포함하며, layered-simple만 JPA 엔티티 직접 사용을 허용한다 — 이것이 layered-simple의 정의적 특징이다.
- `knowledge/tactical/`: aggregates(경계 설정 기준, 불변식, 트랜잭션 규칙, ID 참조), value-objects(불변성, 동등성, 원시 타입 강박 회피, Kotlin data/value class 활용), domain-events(발행 위치와 시점, 명명 규칙), repositories-domain-services(책임 경계, 애플리케이션 서비스와의 구분), persistence(순수 도메인 모델 ↔ 영속 엔티티 분리 전략 — 매핑은 어댑터(out)에 위치, JPA 엔티티 타입이 어댑터 밖으로 노출되면 위반(rule 예: `persistence.entity-confined-to-adapter`), lazy loading 누수·양방향 연관 남용 등 안티패턴, JPA 직접 사용이 정당한 조건과 layered-simple로의 연결).
- `knowledge/patterns/`: cqrs(적용 판단 스펙트럼 — 같은 모델에서 호출 분리부터 저장소 분리까지, 커맨드/쿼리 규칙), event-sourcing(적용 판단 기준, 스냅샷·리플레이·스키마 진화), outbox(트랜잭션적 이벤트 발행).
- `knowledge/structure/`: module-composition(모듈 구성 3형의 정본 — multi-module: 레이어별 Gradle 모듈 / single-module: 컨텍스트당 모듈 1개 + 패키지 경계 / app-embedded: 앱 모듈 내 레이어-우선 패키지, 선택 기준과 애플리케이션·공용 모듈 규칙, imstargg형 사례 포함), package-conventions(패키지 명명과 배치 규칙, 패키지 규약 작성 지침).

patterns 문서는 특히 "언제 쓰지 않는가"를 강하게 쓴다. LLM은 화려한 패턴을 과잉 적용하는 경향이 있으므로 이 문서들이 과잉 설계의 방어선이다 — 예: event-sourcing 문서는 "대부분의 컨텍스트에는 불필요하다"에서 시작한다.

이 목록은 초기 씨앗일 뿐이다. 이후의 확장은 플러그인 개발자가 add-knowledge 스킬로 자유롭게 추가하는 몫이며, v1에서는 완벽한 내용보다 추가하기 좋은 골격이 우선이다.

### 11.4 분량과 확장

- 각 문서 100~300줄. 300줄 초과 시 목차 필수, 500줄 초과 시 문서를 분할한다.
- 새 문서 추가 = md 파일 생성 + summary 한 줄 + build_index.py 실행(또는 add-knowledge 스킬 사용). 그 이상을 요구하지 않는다(초안은 자유 형식으로 draft 등재). 이 절차를 README에 문서화한다.

## 12. 구현 순서

- **Phase 1 — 골격과 두뇌**: plugin.json, 디렉토리 구조, governance 5종(architecture-template, rule-vocabulary, adr-template, evolution-signals, knowledge-doc-template), parse_architecture.py, build_index.py, add-knowledge 로컬 스킬, 전체 knowledge 문서의 메타+요약 스텁과 INDEX, init이 읽는 문서 완성(strategic/ 3종, styles/ 4종, structure/ 2종), init 스킬, SessionStart 훅 + summary 체계.
  - 검증: ① 임시 디렉토리에 최소 Kotlin/Spring 멀티모듈 샘플을 만들고 init 실행 → ARCHITECTURE.md·파생물 생성 확인 ② 모노레포 샘플(backend/ + frontend/ 더미)에서 init → backend만 제안·등록되고 frontend는 "프로파일 없음, 범위 외"로 표시되는지, 산출물이 루트에 생기는지, backend/를 cwd로 연 새 세션에서 훅이 요약을 주입하는지 ③ 빈 저장소(그린필드)에서 init → 설계 인터뷰만으로 ARCHITECTURE.md가 성립하는지 ④ 필수 결정 하나를 지워 parse_architecture.py가 라인 번호와 함께 실패하는지 ⑤ add-knowledge로 문서 1개 추가 → INDEX 갱신·draft 표시 확인.
- **Phase 2 — 강제**: fitness, review, arch-reviewer, check_imports.py, review가 읽는 문서 완성(tactical/ 5종, patterns/ 3종).
  - 검증: ① 샘플의 domain 모듈에 spring import를 심고 fitness 실패와 review 리포트 확인 ② 샘플 컨텍스트에 `패턴: cqrs`를 선언하고 커맨드 핸들러에 조회 로직을 심어 review가 cqrs 체크리스트로 검출하는지 ③ 커스텀 스타일 문서를 하나 선언해 같은 파이프라인으로 fitness가 생성되는지 ④ app-embedded 샘플(레이어-우선 패키지 + 앱 2개)에서 패키지 규약 정규화를 거쳐 fitness가 생성되고 표준 파생 규칙(앱 봉쇄·공용 방향·컨텍스트 간 금지)이 포함되는지.
- **Phase 3 — 도메인**: model(인터뷰·이벤트 스토밍·미팅 정리), apply, check_invariants.py, domain-doc-template, strategic/event-storming.md, review의 분류 확장(추가 논의 → 열린 질문 루프).
  - 검증: 샘플에서 model 세션으로 불변식 2~3개를 confirmed로 만들고 → apply가 코드와 태그 테스트를 생성하는지 → 불변식 하나의 테스트를 지워 check_invariants.py가 실패하는지 → review의 discussion 항목이 열린 질문에 append되는지.
- **Phase 4 — 생성**: scaffold, adr.
  - 검증: ① 새 컨텍스트 scaffold → fitness 통과 ② 그린필드 샘플(Phase 1 검증 ③의 산출물)에서 scaffold가 프로젝트 골격 자체를 생성하는지 ③ 기존 모노레포에 신규 프로젝트 증분 등록이 되는지 ④ ADR 생성과 supersede 흐름.
- **Phase 5 — 유지·이행**: sync, evolve, migrate, collect_signals.py.
  - 검증: 미선언 모듈을 추가해 sync가 감지하는지(선언 프로젝트 밖 디렉터리는 무시하는지 포함), "선언됐는데 없음"에 [scaffold로 생성] 선택지가 뜨는지, 조작된 review-log로 evolve가 제안과 ADR 초안을 내는지. 프리셋과 불일치하는 레거시 샘플에서 init → baseline 동결 → 기존 위반 warn·신규 위반 blocker 판정 → migrate 1클러스터 수행 → baseline 축소까지.
- **Phase 6 — 프로파일 확장**: java-spring 프로파일(ArchUnit rule 매핑, FreezingArchRule 연동, Java 템플릿, examples).
  - 검증: 같은 선언으로 Java 샘플에서 fitness 생성·실행, scaffold로 Java 골격 생성. 이 Phase는 프로파일 계약이 실제로 언어 독립적인지 검증하는 단계다.

각 Phase 종료 시: 산출물 요약 → 검증 절차 실행 → 사용자 확인 후 다음 Phase 진행.

## 13. 하지 말 것

- kotlin-spring·java-spring 외 프로파일 구현 (프로파일 계약만 문서화해 확장 가능하게 유지)
- 스택 추측을 거버넌스 제외 판정에 사용 — "package.json이니까 frontend" 같은 판정 금지. 제외 기준은 프로파일 매칭 + 사용자 확정뿐
- 선언 없는 아키텍처 변형의 수용 — 스타일은 프리셋을 쓰거나 스타일 문서로 선언해야 하며, 선언되지 않은 구조는 강제할 수 없으므로 거부한다
- 규칙 어휘(rule primitive) 밖의 검증 규칙 임시 구현 — 어휘 확장은 governance/rule-vocabulary.md 정식 등록으로만
- SessionStart 외 Claude Code 훅 추가 (PostToolUse 검사 등은 v2 검토 사항; git pre-commit 훅은 별개)
- evolve/sync/migrate 결과의 자동 적용 — 항상 제안 후 사용자 확인
- 파생물 직접 편집을 유도하는 워크플로 — 항상 SSOT 문서(결정 템플릿·domain 문서) 경유
- 결정 템플릿의 필수 항목을 비워두거나 parse_architecture.py 검증 실패 상태로 다음 작업 진행
- 필요가 증명되지 않은 파생 파일·캐시·상태·설정의 추가 (§2 원칙 8 — 단순하게 시작)
- SKILL.md에 references 내용 인라인 (500줄 상한 준수)
- `knowledge/`를 통째로 또는 디렉토리 단위로 컨텍스트에 로드 — 항상 INDEX를 경유해 선별 로드
- knowledge 주제 디렉터리 아래 추가 중첩 (build_index.py가 거부)
- add-knowledge를 플러그인 배포 스킬(skills/)로 이동 — 저장소 로컬 유지
- 체크리스트·규칙 없는 백과사전식 지식 문서 작성 — 모든 문서는 판정 도구여야 한다
- 용어집 기능 구현 — 보편언어의 정의·관리·검증은 superglossery 플러그인 담당이며, superarchitect는 등록 제안과 check 호출 등 통합 지점만 갖는다
- 외부 패키지에 의존하는 스크립트 (bash + python3 stdlib만; Konsist/ArchUnit은 대상 프로젝트의 의존성이다. PyYAML도 금지 — frontmatter는 §11.1의 제한 문법만 파싱)

## 14. 최종 완료 기준

- 로컬 경로(`claude --plugin-dir .`) 또는 로컬 마켓플레이스로 설치되고 10개 스킬이 `/superarchitect:*`로 노출되며, 이 저장소에서 add-knowledge 로컬 스킬이 동작한다.
- 샘플 프로젝트 e2e 시나리오 1회 통과: init → scaffold(신규 컨텍스트) → 위반 코드 삽입 → review가 검출 → fitness 실패 → 수정 → sync 클린 → evolve 리포트 생성. 도메인 루프(model → apply → check_invariants → review의 열린 질문 반영)도 시나리오에 포함한다.
- 형태 커버리지: 모노레포 샘플(backend + frontend 더미, 루트 SSOT), 그린필드 샘플(설계 선행 → scaffold로 생성), app-embedded 샘플(멀티 앱 + 패키지 규약)에서 각각 핵심 플로우가 확인된다. java-spring 샘플에서는 fitness 생성·실행과 scaffold까지 확인한다.
- README.md 완비: 설치 방법, 워크플로 다이어그램(mermaid), 스킬별 사용법, ARCHITECTURE.md·domain 문서 예시, 지식 추가 절차(add-knowledge).

## 부록 A. 확정 결정 기록 (브레인스토밍, 2026-08-07~08)

| # | 결정 | 선택 | 기각한 대안 | 근거 |
|---|---|---|---|---|
| A-1 | 모노레포 문서 위치 | 루트 SSOT + 반복 가능한 프로젝트 섹션 | 백엔드 내부 배치 / 2계층 분리(전략·전술) | 도메인 관계(컨텍스트 맵)는 프로젝트 경계를 넘는 개념 → SSOT는 루트. 단일 레포는 경로 "."인 프로젝트 1개로 동일 형식 — 특수 케이스 제거. 2계층 분리는 v1엔 과설계 |
| A-2 | 구조 선언 형식 | markdown 결정 템플릿 (라벨 필드 + 표) | yaml 등 별도 설정 파일 | PyYAML은 stdlib이 아님 → yaml 채택 시 외부 의존 또는 자체 파서 필요. 라벨·표는 stdlib 라인 파싱으로 결정적으로 읽히고, 사람·Claude가 같은 문서를 읽는 목표에 부합 |
| A-3 | 지식 베이스 구조 | 주제 디렉터리 1단계 고정 (topic = 디렉터리명 자동 유도) | 완전 flat + frontmatter topic | 마찰 총량은 비슷하나 1단계 고정 + 중첩 거부로 "깊어지는 디렉터리" 우려를 구조적으로 차단. 사람 브라우징에 그룹핑 이점 |
| A-4 | 지식 추가 스킬 | 저장소 로컬 스킬 `.claude/skills/add-knowledge` | 플러그인 배포 스킬(learn) / 수동 절차만 | 지식 추가는 플러그인 소유자의 보완 작업 — 사용 프로젝트에 배포될 이유 없음. 이름은 gstack 전역 `/learn`과의 혼동 회피 |
| A-5 | java-spring 시점 | v1 포함, 마지막 Phase 6 | v2로 연기 | 프로파일 계약의 언어 독립성을 실제로 검증(어휘 설계 결함 조기 발견). 마지막 Phase라 부담 시 축소 용이 |
| A-6 | init 제외 기준 | 프로파일 매칭 (+ 사용자 확정) | package.json=frontend 등 스택 추측 | Node 백엔드 확장 시 추측 휴리스틱이 깨짐. 프로파일 추가만으로 자동 확장되는 기준이 미래 호환 |
| A-7 | 컨텍스트 실현 모델 | 3형(multi-module/single-module/app-embedded) + "컨텍스트×레이어→패키지 패턴" 정규화 | 모듈 표 단일 모델 | 실물(imstargg-backend: 앱 4개 + 레이어-우선 패키지)이 모듈 표로 선언 불가. 정규화로 강제 파이프라인을 실현 형태와 분리 |
| A-8 | 코드 없는 init | 그린필드 설계 인터뷰 + scaffold가 골격 생성 + sync에 [scaffold로 생성] | init은 기존 코드 전제 | "설계 먼저, 생성 나중" 플로우 요구. 선언→코드와 코드→선언이 같은 문서로 수렴 |

## 부록 B. 검증된 외부 사실 (2026-08-07, 공식 문서 기준)

- **plugin.json**: 위치 `.claude-plugin/plugin.json`, 필수 필드는 `name`뿐. skills/·agents/·hooks/hooks.json은 기본 위치에서 자동 검색.
- **스킬**: `skills/<name>/SKILL.md`, 커맨드는 `/<plugin-name>:<skill-name>`. description 상한 1,536자. 신규 플러그인은 commands/ 대신 skills/ 권장.
- **에이전트**: `agents/<name>.md` 플랫 파일 + frontmatter(name, description, tools, model 등).
- **훅**: `hooks/hooks.json`. SessionStart의 stdout(또는 hookSpecificOutput.additionalContext)이 세션 컨텍스트로 주입됨. `${CLAUDE_PLUGIN_ROOT}`는 훅 커맨드·SKILL.md에서 사용 가능.
- **개발 루프**: `claude --plugin-dir ./superarchitect`로 로컬 테스트. SKILL.md 본문만 핫리로드, plugin.json·hooks·agents는 `/reload-plugins` 필요.
- **Konsist 0.17.3** (`com.lemonappdev:konsist`): `Konsist.scopeFromProject().assertArchitecture { }`, `Layer(name, "pkg..")`, `dependsOn(vararg, strict)`, `dependsOnNothing()`, `doesNotDependOn()` 모두 현행.
- **ArchUnit 1.4.1** (`com.tngtech.archunit:archunit`): `FreezingArchRule.freeze(rule)` + ViolationStore(경로·갱신 정책은 `archunit.properties`) 현행.
