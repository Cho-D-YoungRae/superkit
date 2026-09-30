# Changelog

이 플러그인의 버전은 [Semantic Versioning](https://semver.org/lang/ko/)을 따른다. 1.0.0 전에는
마이너 버전이 호환되지 않는 변경을 담을 수 있다.

## 0.5.1 — 2026-09-30

skill-creator 기준으로 스킬을 검토해, 스킬이 불려야 할 때 불리도록 설명을 다듬고 이전 버전 대응을 뺐다.

### Added

- `evals/conventions/`: conventions 스킬의 평가 정의(프롬프트 3개, 채점 기준 16개)와 예제 프로젝트(주문·결제·포인트). skill-creator로 스킬 있음·없음을 비교해 돌린다.
- `conventions`: 코드를 다 쓴 뒤 이번 변경에 해당하는 필수 항목만 다시 확인하는 단계. 트랜잭션 위치·현재 시각·예외 위치·외부 호출은 흔한 습관과 달라 놓치기 쉽다.

### Changed

- 네 스킬의 설명(description)이 무엇을 하는지와 언제 쓰는지를 함께 말한다.
  - `domain`: 외부 접점, 의존 방향, 양방향 해소를 더했다.
  - `conventions`: 코드를 쓰기 전에 먼저 쓰고, 컨벤션을 말하지 않아도 해당하며, 사소한 수정에는 쓰지 않는다.
  - `review`와 `domain`: 서로의 몫을 한 줄씩 적어, "DOMAIN.md 검토"처럼 겹치는 요청이 맞는 스킬로 가게 했다.
- `domain`의 정책 질문: 기능마다 따로 묻지 않고, 도메인마다 초안을 제안해 한 번에 확인받는다. 돈·상태·재화가 걸린 기능부터 다룬다.
- 컨벤션의 적용 범위: 규칙은 백엔드 애플리케이션 전반에 적용하고, 예시만 Kotlin·Spring·JPA다. 스킬과 리뷰가 동작하는 파일은 그대로 Kotlin·Java다.
- 이유 없이 적힌 금지 두 곳에 이유를 붙였다(domain의 한 번에 한 질문, adr의 옛 ADR 본문 보존).

### Removed

- 0.3.x 형식 대응: `domain`의 0.3.x 파일 다시 쓰기 절차, `review`의 0.3.x 파일 안내, README의 "이전 버전에서 올라왔다면" 절. 0.3.x 형식 DOMAIN.md는 더 이상 알아보지 않는다.

## 0.5.0 — 2026-09-30

외부 시스템과 맞닿은 도메인을 구분하고, 도메인 사이 의존을 한 방향으로 유지하는 기준을 더했다. 커머스 예제에서 얻은 도메인 설계·코딩 관행(동시성, 돈 기록, 계층, 트랜잭션 위치 등)도 더했다. 기존 DOMAIN.md는 그대로 쓸 수 있다.

### Added

- DOMAIN.md의 선택 필드
  - `외부`: 도메인이 맞닿은 외부 시스템과 주고받는 것. 없으면 내부 도메인이다.
  - `개념`: 대표 개념과 다른 도메인이 직접 쓰는 개념만 적는다(새로 온 사람이 꼭 알아야 할 것).
  - `미정`: 아직 정하지 못한 정책. 정해지면 `규칙`으로 옮긴다.
  - 기반 도메인 줄: 모든 도메인이 의존하는 도메인은 관계 표 아래에 `모든 도메인이 참조: <key>` 한 줄로 적는다.
- domain-guide 「외부 접점」: 외부 도메인의 복잡성(모델·용어·상태 코드)과 외부 시스템의 복잡성(타임아웃·실패·장애)을 외부 접점 도메인 안에 가두는 기준과, 연동이 커졌을 때의 분리 기준.
- domain-guide 「관계의 방향」
  - 도메인 사이 의존은 한 방향이다. 중심 도메인과 내부 도메인이 의존받고, 외부 접점 도메인과 흐름의 뒤 단계가 의존한다(결제 → 주문, 정산 → 결제).
  - 반대 흐름은 이벤트나 배치·조회로 푼다. 알면 안 되는 상대를 가리킬 때는 자기 타입(`ReviewTarget(type, id)`)이나 상관 키로 든다.
  - 여러 원천을 모아 계산하는 도메인은 적재 부분만 원천에 의존하고, 계산은 대상 모델만 읽는다.
  - 방향 기준에는 우선순위가 있다. 외부와 맞닿은 중심 도메인도 의존받는다(외부의 복잡성은 그 도메인의 가장자리에서 끝낸다).
  - 순서가 필요한 흐름은 어느 도메인에도 속하지 않는 위 계층(컨트롤러 등)이 차례로 부르고, 이 호출은 도메인 사이 의존으로 세지 않는다.
- 이름 신호: 어디에나 붙는 소유자·주체(`User` 등)를 붙인 개념 이름(`UserCoupon` 대신 `OwnedCoupon`).
- 컨벤션 새 항목
  - `필수`: 「도메인 사이 의존은 한 방향으로만 둔다」, 「계층은 한 방향으로만 참조한다」, 「JPA 엔티티 매핑」, 「트랜잭션은 서비스가 아니라 리포지토리에 건다」, 「동시에 바뀔 수 있는 값은 동시성 제어 수단을 정한다」, 「외부 응답과 오류는 경계에서 우리 타입으로 바꾼다」, 「외부 호출은 DB 트랜잭션 밖에서 한다」.
  - `지향`: 「상태 값은 최소로 둔다」, 「돈·재화의 기록은 고치지 않고 쌓는다」.
- 기존 컨벤션 보완
  - 조회 조건으로 `canXxx()` 검증을 대신하지 않는다.
  - 감사용 시각을 기간 규칙에 쓰지 않는다.
  - application 리포지토리는 이름이 아니라 역할로 정한다.
  - 이벤트는 쓰기와 같은 트랜잭션 안에서 발행하고, 구독 쪽 쓰기는 전용 리포지토리 메서드의 `REQUIRES_NEW`로 한다.
  - 외부 콜백 값은 우리 기록과 대조하고, 되돌릴 수 없는 외부 작업이 성공한 뒤의 실패 처리를 미리 정한다. 외부 호출 전에 요청을 먼저 기록하는 것을 지향한다.
  - 조건이 붙은 조회는 걸러져야 할 데이터와 함께 테스트한다.
- `domain`
  - 외부 접점 후보를 찾아 보여 주고, 방향은 가이드 기준으로 제안하며, 양방향 관계는 한 방향으로 정하자고 제안한다.
  - 기능마다 정책(취소·환불 시 복구, 수정·삭제, 유효기간·한도, 중복·어뷰징)을 묻는다.
  - 중심 도메인 후보가 여럿이면 경계를 두세 가지로 그려 고르게 한다.
  - 기반 도메인은 사용자에게 확인받은 뒤에만 적는다.
- `conventions`: 내부 도메인에 외부 호출이 들어가거나 관계 표와 반대 방향의 의존이 생기면 코드를 쓰기 전에 알린다.
- domain-reviewer
  - 외부 영향이 번지는지(내부 도메인의 외부 직접 호출, 외부 타입·오류 유출, `외부` 누락)를 본다.
  - 양방향·순환 의존과 방향이 가이드 기준과 맞는지 본다.
  - `개념`의 품질, 기반 도메인 줄, 한 트랜잭션의 허용 조건, 조율 계층의 호출을 반영해 판단한다.
- convention-reviewer는 한 방향 규칙을 코드에서 본다.

### Changed

- 관계 표 규칙: "한 쌍에 한 줄" → "한 쌍에는 한 방향만". 같은 방향에 방식이 여럿이면 한 줄에 `·`로 함께 적는다.
- 관계 표 읽는 법을 적었다: `도메인`이 `의존 대상`을 안다(부르거나, 이벤트를 구독하거나, ID 타입·모델을 쓰거나, 데이터를 읽는다). 이벤트는 구독하는 쪽이 `도메인`이다. 발행하는 쪽을 앞에 적었던 행은 뒤집는다.
- 방식 값에 `데이터 읽기`(상대의 뷰나 테이블을 읽기 전용으로 읽음)를 더했다.
- 경계 신호 "한 트랜잭션 안에서 두 도메인의 저장소를 쓴다"에 허용 조건을 더했다. 흐름의 뒤 단계가 의존 방향대로 앞 단계를 함께 확정해야 하고 원자성이 꼭 필요하면 허용한다(결제 승인 뒤 주문·쿠폰·포인트 반영).

### 이행

꼭 해야 할 이행은 없다. 다만 새 기준으로 다시 보면 좋은 곳이 있다. `/superdomain:review 전체`가 빠진 곳과 어긋난 곳을 알려 준다.

- 외부 시스템과 맞닿은 도메인에 `외부`를 더한다.
- 관계 표에 같은 쌍이 두 방향으로 있으면 한 방향으로 정리한다.
- 내부 도메인이 외부 접점 도메인에 의존하거나, 흐름의 앞 단계가 뒤 단계에 의존하는 행은 방향을 다시 본다.
- 서비스에 트랜잭션을 거는 프로젝트는 새 컨벤션과 다르다(JPA 엔티티를 직접 쓰는 얇은 곳은 예외). 그대로 두려면 프로젝트 CLAUDE.md에 그 규칙을 적는다(프로젝트 규칙이 우선한다).

플러그인 업데이트 명령은 0.4.1 절과 같다.

## 0.4.1 — 2026-09-30

0.4.0을 보정한다. 산출물 위치를 0.3.x와 같은 `docs/superdomain/`으로 되돌려, 0.3.x에서 올라올 때 파일을 옮기지 않아도 된다. 경로가 바뀌는 것은 0.4.0 배치(`docs/DOMAIN.md`·`docs/adr/`)로 이미 옮긴 프로젝트뿐이다.

### Changed

- 산출물 위치: `docs/DOMAIN.md` → `docs/superdomain/DOMAIN.md`, `docs/adr/` → `docs/superdomain/adr/`. 플러그인이 관리하는 문서를 한 폴더에 모은다.
- 0.3.x 판정: `domain`·`review`가 위치 대신 형식(`## 컨텍스트:` 절)으로 0.3.x 파일을 알아보고, 새 형식으로 다시 쓰자고 안내한다. `domain`은 다시 쓴 뒤 남은 0.3.x 산출물을 지우자고 제안한다.
- `adr`: 쓸 결정의 기준을 "되돌리기 비싼 기술·도메인 결정"에서 "비싸거나 중요한 결정"으로 넓혔다. 작업을 마칠 때 그런 결정이 있었으면 먼저 기록을 제안한다.
- CLAUDE.md 포인터: `domain`·`adr`이 동의를 받아 결정 기록 줄(`- 결정 기록: docs/superdomain/adr/ …`)도 추가한다. 이 줄이 있으면 Claude가 작업을 마칠 때 기록할 결정이 있었는지 돌아본다.
- 컨벤션 「외부 자원은 인터페이스 뒤에 둔다」: `필수` → `지향`. 인터페이스 없이 구체 클래스로 감싸도 된다.
- 컨벤션 「정적 호출은 컴포넌트로 감싼다」: 이유를 "정적 메서드는 테스트에서 모킹하기 어렵다"로 고치고, 감싼 컴포넌트는 모킹해도 된다고 적었다. 「모킹은 외부 자원에만 쓴다」도 이에 맞췄다.
- 컨벤션 「JPA 클래스 이름」: `@Embeddable` 클래스는 `XxxEmbedded` → `XxxEmbeddable`.
- `domain`: 용어집 관련 문구를 뺐다.

### 이행 절차

플러그인을 먼저 올린다: `claude plugin marketplace update superdomain` 다음 `claude plugin update superdomain@superdomain`. 프로젝트 범위로 설치했다면 그 프로젝트 디렉터리에서 `--scope project`를 붙인다. 적용하려면 세션을 다시 시작한다.

0.3.x에서 올라오는 경우 — 0.4.0의 이행 절차 대신 이것을 따른다. 대상 프로젝트의 git 루트에서:

1. `/superdomain:domain`으로 `docs/superdomain/DOMAIN.md`를 새 형식으로 다시 쓴다. `docs/superdomain/contexts/*.md`의 불변식 중 핵심은 도메인의 "규칙"으로 옮긴다.
2. `docs/superdomain/conventions/`의 팀 규약을 먼저 프로젝트 CLAUDE.md로 옮긴 뒤, `docs/superdomain/`의 `summary.md`, `contexts/`, `state/`, `conventions/`를 지운다(1단계를 마치면 스킬이 제안한다). ADR이 `../contexts/<이름>.md`를 가리키고 있었다면 그 링크를 지우거나 `../DOMAIN.md`의 해당 도메인 절로 바꾼다.
3. CLAUDE.md 등에서 지운 파일을 가리키는 참조를 고친다.

   ```bash
   git grep -nE 'summary\.md|superdomain/(contexts|state|conventions)'
   ```

0.4.0 배치로 이미 옮긴 경우:

1. `mkdir -p docs/superdomain` 다음 `git mv docs/DOMAIN.md docs/superdomain/DOMAIN.md`
2. ADR이 있으면 `git mv docs/adr docs/superdomain/adr`. ADR 안의 `../DOMAIN.md` 링크는 그대로 맞는다.
3. CLAUDE.md의 포인터 줄 등 옛 경로를 가리키는 참조를 고친다.

   ```bash
   git grep -nE 'docs/(DOMAIN\.md|adr/)'
   ```

## 0.4.0 — 2026-09-30

플러그인을 도메인 정의·리뷰·ADR에 집중하도록 다시 설계했다. 설계는
`docs/superpowers/specs/2026-09-29-superdomain-redesign-design.md`에 있다.

### Breaking

- 스킬이 `domain`·`review`·`adr`·`conventions` 넷으로 바뀌었다. `init`·`model`·`apply`·`sync`·`evolve`·`migrate`는 없어졌다.
- 산출물은 `docs/DOMAIN.md`와 `docs/adr/` 둘뿐이다. `docs/superdomain/`의 `summary.md`·`contexts/`·`state/`·`conventions/`는 더 이상 쓰지 않는다.
- DOMAIN.md 형식이 바뀌었다. 도메인마다 역할·기능·분류·코드(선택: 규칙·하지 않는 것)를 적고, 관계는 `도메인 | 의존 대상 | 방식 | 설명` 표로 적는다. 파서가 없으므로 형식은 사람과 Claude가 읽기 위한 것이다.
- 검사 스크립트(`parse_domain.py`·`check_imports.py`·`check_invariants.py`·`collect_signals.py`·`layout.py`·`build_index.py`)와 SessionStart 훅이 없어졌다. 도메인 경계와 코딩 컨벤션은 `review` 스킬의 리뷰 에이전트가 확인한다. python3가 더 이상 필요 없다.
- `references/`(governance·knowledge)가 없어졌다. 쓸 만한 내용은 `skills/domain/domain-guide.md`로 옮겼고, 코딩 기준은 새로 쓴 `skills/conventions/conventions.md`에 있다.

### Added

- `conventions` 스킬과 코딩 컨벤션 문서. Kotlin·Java(Spring·JPA) 코드를 쓸 때 적용한다.
- `convention-reviewer` 에이전트(`model: sonnet`). `domain-reviewer`는 새로 썼다(`model: opus`).
- `review`가 두 리뷰어를 병렬로 호출해 한 리포트로 합친다. 인자는 `[domain|code] [경로 | 커밋 범위 | 전체]`다.

### 이행 절차 (0.3.x → 0.4.0)

플러그인을 먼저 올린다: `claude plugin marketplace update superdomain` 다음 `claude plugin update superdomain@superdomain`(적용하려면 세션을 다시 시작한다). 그다음 대상 프로젝트의 git 루트에서 아래를 따른다.

1. `git mv docs/superdomain/DOMAIN.md docs/DOMAIN.md`
2. `/superdomain:domain`으로 새 형식으로 다시 쓴다. 옛 `docs/superdomain/contexts/*.md`의 불변식 중 핵심은 도메인의 "규칙"으로 옮긴다.
3. `git mv docs/superdomain/adr docs/adr`. ADR 안의 `../DOMAIN.md` 링크는 옮긴 뒤에도 그대로 맞는다.
4. `docs/superdomain/`의 나머지(`summary.md`, `contexts/`, `state/`, `conventions/`)를 지운다. `conventions/`의 팀 규약은 프로젝트 CLAUDE.md로 옮긴다. ADR이 `../contexts/<이름>.md`를 가리키고 있었다면 그 링크를 지우거나 `../DOMAIN.md`의 해당 도메인 절로 바꾼다.
5. CLAUDE.md 등에서 `docs/superdomain/`을 가리키는 참조를 찾아 고친다.

   ```bash
   git grep -n 'docs/superdomain/'
   ```

## 0.3.0 — 2026-09-29

### Breaking

- **산출물 위치가 `docs/superdomain/` 아래로 바뀌었다.** 스크립트·훅·스킬은 새 배치만 읽는다.

  | 0.2.x | 0.3.0 |
  |---|---|
  | `DOMAIN.md` | `docs/superdomain/DOMAIN.md` |
  | `docs/domain-summary.md` | `docs/superdomain/summary.md` |
  | `docs/domain/<컨텍스트>.md` | `docs/superdomain/contexts/<컨텍스트>.md` |
  | `docs/domain.md` (단일 컨텍스트) | `docs/superdomain/contexts/<컨텍스트>.md` — 특례 폐지 |
  | `docs/domain/baseline.jsonl` | `docs/superdomain/state/baseline.jsonl` |
  | `docs/domain/review-log.jsonl` | `docs/superdomain/state/review-log.jsonl` |
  | `docs/decisions/*.md` | `docs/superdomain/adr/*.md` |
  | `docs/conventions/<key>.md` | `docs/superdomain/conventions/<key>.md` |

  네 스크립트의 인자는 `docs/superdomain/DOMAIN.md`다. 옛 배치를 받으면 exit 2로 멈추고 이행
  명령을 출력한다. 스킬도 0단계에서 같은 파서를 돌려 옛 배치·이행 미완이면 멈춘다
  (`skill-protocol.md` §3).
- **ADR 파일명이 `yyyy-MM-dd-slug.md`다**(8e9e646). 0.2.0 버전 번호를 올리지 않고 들어간 변경이라
  0.2.0 설치본 사용자에게는 이번에 처음 도달한다.
- **`DOMAIN.md`의 라벨은 섹션 머리에서만 읽는다.** `###` 아래의 `- 키: 값` 모양 줄과 코드 펜스 안의
  내용은 선언이 아니다. 닫히지 않은 코드 펜스는 파서 오류다.
- **domain-reviewer 출력의 `rationale`이 `observation`·`basis`·`suggestion`·`question`으로 나뉘었다.**
- 지식 문서: `read_when`은 스킬 이름 리스트만 허용한다. `## 적용 기준`·`## 규칙`은 헤딩만 있고
  본문이 비면 draft다.

### Added

- `scripts/layout.py` — 산출물 경로의 유일한 정본과 옛 배치 감지.
- `check_imports.py --json`의 위반·강등 부채에 `from_context`·`to_context`.
- SessionStart 훅이 옛 배치를 보면 이행 안내 한 줄을 낸다.
- 정본 `skill-protocol.md`(스킬 공통 규약·라우팅)와 `derived-artifacts.md`(파생물·선언 편집).
- MIT `LICENSE`, CI(`unittest`, INDEX 최신성).

### Fixed

- BOM으로 시작하는 Kotlin/Java 소스의 격리 위반이 누락되던 것. `DOMAIN.md`·jsonl의 BOM도 읽는다.
- 코드 펜스·자유 서술 속 라벨이 컨텍스트 선언을 조용히 바꾸던 것.
- 퇴역 라벨이 문서 머리·모르는 섹션에서는 무시되던 것.
- 스킬 description 사이의 라우팅 모순(분류·관계 변경의 담당).
- 용어집 플러그인 이름(`superglossary`)과 서브에이전트 호출명(`superdomain:domain-reviewer`).
- 요약을 읽지 못하면 훅이 비정상 종료하던 것.
- UTF-8이 아닌 로케일에서 `collect_signals.py`가 트레이스백으로 죽을 수 있던 것.

### 이행 절차 (0.2.x → 0.3.0)

플러그인을 올리기 전에 옛 경로로 세 스크립트를 한 번 돌려 `OK:` 줄과 위반·부채 건수를 적어 두면
4단계에서 대조할 수 있다.

1. 대상 프로젝트의 git 루트에서 파서를 새 경로로 돌려 이행 명령을 받는다(선언 파일이 아직
   없어도 된다).

   ```bash
   python3 <플러그인>/scripts/parse_domain.py docs/superdomain/DOMAIN.md
   ```

   exit 2와 함께 `mkdir -p …`와 `git mv …` 줄이 나온다. **있는 파일만** 나열된다. 새 선언을 이미
   옮겼는데 옛 산출물이 남아 있으면 "이행이 끝나지 않았습니다"와 남은 목록이 나온다 — 옮기거나
   (이미 옮긴 사본이면) 지운다.
2. 나온 `mkdir -p`와 `git mv`를 그대로 실행한다. `docs/domain.md`(단일 컨텍스트 문서)가 있었다면
   목적지의 `<컨텍스트 이름>`을 `DOMAIN.md`의 유일한 `## 컨텍스트:` 이름으로 바꿔 실행한다.
3. 옛 경로를 가리키는 참조를 저장소 전체에서 찾아 고친다. 모노레포면 하위 프로젝트의 CLAUDE.md·
   문서·코드 주석에도 있다.

   ```bash
   git grep -nE 'docs/decisions/|docs/domain/|docs/domain-summary\.md|docs/domain\.md|\(DOMAIN\.md\)|\.\./DOMAIN\.md|\.\./decisions/|\.\./domain/|\.\./domain\.md' -- .
   ```

   잡힌 줄은 세 갈래로 나눈다. **링크**(`[…](…)`)와 **지금 읽히는 지시**(어느 디렉터리의
   CLAUDE.md든, README, 코드 주석)는 아래 규칙대로 새 경로로 고친다. **기록물** — `accepted` ADR
   본문의 서술, 이미 끝난 계획·설계 문서의 작업 서술 — 은 그 시점의 사실이라 그대로 두고 링크만
   고친다. `docs/decisions.md`처럼 이름만 비슷한 다른 파일은 대상이 아니다.

   `docs/decisions/` → `docs/superdomain/adr/`, `docs/domain/` → `docs/superdomain/contexts/`,
   `docs/domain-summary.md` → `docs/superdomain/summary.md`. `DOMAIN.md`에서 ADR을 가리키던 상대
   링크(`docs/decisions/x.md`)는 이제 같은 디렉터리 기준이므로 `adr/x.md`다. ADR끼리의 상대 링크는
   그대로 둔다. `DOMAIN.md`가 컨텍스트 문서를 `docs/domain/x.md`로 가리켰다면 이제
   `contexts/x.md`다. 옛 자리에서 `../../DOMAIN.md`로 선언을 가리키던 링크(컨텍스트 문서·ADR)는
   이제 `../DOMAIN.md`다. 옛 컨텍스트 문서와 ADR이 서로를 가리키던 `../decisions/`·`../domain/`
   링크는 `../adr/`·`../contexts/`다(ADR이 `../domain.md`를 가리켰다면
   `../contexts/<컨텍스트 이름>.md`).

   CLAUDE.md에 0.2.x `init`이 제안한 한 줄(도메인 경계·요약 경로)을 넣었다면
   `docs/superdomain/DOMAIN.md`·`docs/superdomain/summary.md`로 고친다. pre-commit 훅·CI가
   스크립트에 넘기는 인자도 `docs/superdomain/DOMAIN.md`로 바꾼다. 옮긴 `summary.md`의 마지막 줄
   `상세: DOMAIN.md`는 `상세: docs/superdomain/DOMAIN.md`로 고친다(0.3.0 생성 형식 —
   `references/governance/derived-artifacts.md` §2). 매 세션 주입되는 파일이라 옛 경로가 남으면
   안 된다.
4. 파서와 두 검사를 새 경로로 돌려 이행 전과 결과가 같은지 확인한다.

   ```bash
   python3 <플러그인>/scripts/parse_domain.py docs/superdomain/DOMAIN.md
   python3 <플러그인>/scripts/check_imports.py docs/superdomain/DOMAIN.md
   python3 <플러그인>/scripts/check_invariants.py docs/superdomain/DOMAIN.md
   ```

   `OK:` 줄의 프로젝트·컨텍스트 개수와 위반 건수가 이행 전과 같아야 한다.
5. `git mv`만 담은 커밋과 링크 치환 커밋으로 나눠 남기면 이력 추적이 쉽다.

무엇을 superdomain 산출물로 보는지는 소유가 확실한 것만이다. 마커(`<!-- superdomain:template`)가
있는 루트 `DOMAIN.md`가 있으면 옛 자리의 파일을 전부 이행 목록에 넣는다. 없으면
`docs/domain/*.md`·`docs/domain.md`는 `## 불변식` 제목과 `INV-` 행이 함께 있을 때(제목만 있는 팀
문서는 옮길 불변식이 없으므로 넣지 않는다), `docs/domain-summary.md`는
생성물 헤더(`GENERATED by superdomain`)가 있을 때만 넣는다. `docs/decisions/`·`docs/conventions/`는
옛 루트 `DOMAIN.md`가 있을 때만 넣는다 — 팀이 따로 쓰던 같은 이름의 폴더·문서를 옮기라고 하지 않는다.

## 0.2.0 — 2026-08-17

- superarchitect → superdomain 재편. 도메인(DDD) 거버넌스에 집중하고 아키텍처 스타일·레이어
  규칙을 들어냈다(`docs/superpowers/specs/2026-08-17-superdomain-refocus-design.md`).
