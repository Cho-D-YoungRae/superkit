# Changelog

이 플러그인의 버전은 [Semantic Versioning](https://semver.org/lang/ko/)을 따른다. 1.0.0 전에는
마이너 버전이 호환되지 않는 변경을 담을 수 있다.

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
