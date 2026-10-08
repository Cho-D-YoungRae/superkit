# superglossary 0.7.0 재설계 — LLM이 읽고 고치는 md 용어집

- 날짜: 2026-10-07
- 상태: 구현됨(0.7.0). 최종 리뷰에서 더한 것 — 사전이 없을 때 이름을 짓다 불리면 만들기 전에 묻는다, check는 기존 관례를 따른 금지 단어도 보고한다, 같은 단어의 활용형(executed_at)은 같은 단어로 본다
- 대체: `2026-06-20-glossary-feature-design.md`, `2026-07-09-usability-improvements-design.md`와 그 계획 문서 둘(구현과 함께 삭제한다. 이력은 git에 남는다)

## 1. 목표

superglossary를 **LLM이 읽고 고치는 md 용어집**으로 다시 만든다. 사람과 Claude가 같은 단어 목록을 보고 이름을 짓게 하는 목적은 그대로 두고, 그 목적에 비해 무거웠던 장치를 걷어 낸다.

0.6.0까지는 `glossary.json`(원본) → `core.md`·`terms.md`(생성물)를 1,000줄짜리 Python CLI가 관리하고, 그 CLI를 사용자 프로젝트마다 복사했다. 0.3~0.6 CHANGELOG의 상당수가 이 구조의 비용(stale 감지, 스키마 마이그레이션, 복사본 버전 드리프트, lint 노이즈·스톱워드, 구버전 블록 해시, `.gitignore` 경고)이었다.

원칙:

1. 용어집은 md 파일이 원본이자 읽는 대상이다. 생성물·중간 형식(JSON)을 두지 않는다.
2. 스크립트를 두지 않는다. 중복 확인·분해·검토는 LLM이 하고, 판단이 걸린 확정은 사용자가 한다.
3. 용어집은 필요할 때 읽는다. 지침 파일에는 `@import` 없이 포인터 한 줄만 둔다(매 세션 컨텍스트 비용을 없앤다).
4. 같은 저장소의 superdomain 관례를 따른다 — 산출물은 `docs/<플러그인>/`, 스킬의 기준 문서는 `${CLAUDE_SKILL_DIR}/<이름>-guide.md`, 포인터 줄은 묻고 넣는다.

### 비목표

- 결정적 강제(lint, CI·pre-commit 차단). 필요해지면 따로 설계한다
- 구버전(`.claude/superglossary/`) 자동 감지·이행 코드. 사용자가 한 명(noguesstoday)이라 손으로 옮긴다
- 분류(category) 필드, `relatedElements`, 스톱워드 설정

## 2. 확정된 결정

| # | 결정 |
|---|---|
| D1 | 용어집은 사용자 프로젝트의 `docs/superglossary/glossary.md`다. 분리 뒤에는 같은 디렉터리의 `<도메인>.md`가 더해진다 |
| D2 | 표의 열은 `한글 \| 영문 \| 축약 \| 금지 \| 설명`이다. 한글 가나다순으로 정렬한다 |
| D3 | 지침 파일에는 포인터 한 줄만 넣는다. `@import`는 쓰지 않는다 |
| D4 | 용어는 단어별로 등록한다. 합성어의 영문이 부분 영문의 조합과 다를 때만 합성어를 한 항목으로 등록하고, 이 예외는 사용자 확인을 받는다 |
| D5 | 용어가 300개를 넘으면 도메인별 분리를 **제안**한다. 자동으로 나누지 않는다 |
| D6 | 스킬은 `glossary`(생성·추가·수정·분리)와 `check`(변경 검토) 둘이다. `init`·`add`는 없앤다 |
| D7 | 에이전트는 `glossary-scanner`(brownfield 스캔, `model: sonnet`) 하나다. `check-analyzer`는 없앤다 |
| D8 | CLI·`bin/`·테스트·`scripts/bump_version.py`·플러그인 CI 워크플로를 없앤다. 버전의 출처는 `plugin.json` 하나다 |
| D9 | 버전은 0.7.0이다(0.x에서 마이너 버전이 호환되지 않는 변경을 담는다) |

## 3. 용어집 파일 형식

### 분리 전 — `docs/superglossary/glossary.md` 한 파일

```markdown
# 용어 사전

이름(클래스·변수·함수·컬럼·테이블·API 필드)에 쓰는 단어 목록이다. /superglossary:glossary가 관리한다.

- 단어별로 등록하고 조합해 쓴다 (체결수량 → 체결 execution + 수량 quantity → execution_quantity).
- 축약어는 축약 열에 있는 것만 쓴다. 금지 열의 단어는 쓰지 않고 영문 열의 표준을 쓴다.
- 기존 모듈을 고칠 때는 그 모듈의 기존 이름을 따르고, 임의로 이름을 바꾸지 않는다.

| 한글 | 영문 | 축약 | 금지 | 설명 |
| --- | --- | --- | --- | --- |
| 식별자 | identifier | id |  | 데이터를 고유하게 식별하는 값. {엔티티}_id 형식 |
| 이름 | name |  |  | 대상을 지칭하는 명칭 |
| 일시 | datetime | at |  | 날짜와 시각. created_at처럼 _at 접미사로 쓴다 |
```

- 새로 만들 때 넣는 기본 용어는 위 셋이다(0.6.0의 초기 데이터와 같다).
- 금지 열은 쉼표로 구분한 단어들이다. 설명은 한두 구절로 쓴다.

### 분리 후

```
docs/superglossary/
  glossary.md   ← 규칙 + 도메인 index + 공통 용어 표
  <도메인>.md    ← 같은 표 형식, 그 도메인 용어만
```

`glossary.md`의 index 표:

```markdown
## 도메인

| 도메인 | 파일 | 코드 범위 | 설명 |
| --- | --- | --- | --- |
| 기준정보 | reference.md | noguesstoday-backend/**/reference/** | 종목·시장·법인 |
```

- 분리 뒤 `glossary.md`는 규칙, `## 도메인`(index 표), `## 공통 용어`(용어 표) 순서다.
- **코드 범위**는 지금 다루는 파일 경로로 어느 도메인 파일을 읽을지 고르는 데 쓴다.
- 여러 도메인이 함께 쓰는 용어(식별자·일시·이름 등)는 `glossary.md`의 공통 표에 남긴다.
- 한 용어는 정확히 한 파일에만 둔다.
- 도메인 이름은 프로젝트에 도메인 정의 문서(예: `docs/superdomain/DOMAIN.md`)가 있으면 그 이름을 따른다.
- 도메인 파일은 `# <도메인> 용어` 제목 아래 같은 열의 표 하나를 둔다. 규칙은 `glossary.md`에만 적는다.

## 4. 등록 규칙

- **단어별로 등록한다.** `매도호가체결`을 한 행으로 두지 않고 단어마다 한 행을 둔다. 이미 있는 단어는 다시 넣지 않고 조합해 쓴다.
- **나누는 기준은 영문이다.** 합성어의 영문이 부분 영문을 이어 붙인 것과 같으면 나눈다. 다르면 합성어를 한 항목으로 등록한다.

| 예 | 처리 | 이유 |
|---|---|---|
| 체결수량 → 체결 + 수량 | 나눈다 | execution + quantity |
| 매도호가 → ask | 한 항목 | 업계 용어(매수호가는 bid) |
| 국제증권식별번호 → isin | 한 항목 | 표준 약어 |
| 재시도 → retry | 한 항목 | 영문이 한 단어 |

- **누가 확정하나:** 단어별 등록은 Claude가 스스로 하고 한 줄로 알린다. 합성어를 한 항목으로 두는 예외는 도메인 지식이 걸린 판단이라 근거와 함께 사용자 확인을 받는다.
- **충돌:** 한글·영문·축약이 기존 항목과 겹치거나, 영문·축약이 다른 항목의 금지 단어면 등록하지 않고 기존 항목을 보여 준다. 분리된 뒤에는 `docs/superglossary/` 전체에서 찾는다.
- **금지 단어**는 단어 단위로 적는다(`cust_no`가 아니라 `cust`).

## 5. 스킬과 에이전트

### `glossary` 스킬

- 파일: `skills/glossary/SKILL.md`, `skills/glossary/glossary-guide.md`
- frontmatter:
  - `description` 초안: "프로젝트 용어 사전(docs/superglossary/)을 만들고 고친다. 용어를 추가·수정·삭제하고, 많아지면 도메인별 파일로 나눈다. 코드에 새 이름(클래스·변수·함수·컬럼·테이블·API 필드)을 지어야 하는데 쓸 단어가 사전에 없으면 사용자가 말하지 않아도 사용한다. "용어 추가", "사전에 등록", "용어집 만들어줘", "용어 사전 정리·분리" 같은 요청이 해당한다. 변경된 코드가 사전을 따르는지 검토하는 일은 check가 맡는다."
  - `argument-hint: "[용어 | 요청]"`
  - `allowed-tools: Read, Grep, Glob, Edit, Write, Agent, Bash(git rev-parse:*)`
- SKILL.md 본문(짧게 유지 — 이름을 지을 때마다 불릴 수 있다):
  1. **찾기**: git 루트(`git rev-parse --show-toplevel`)의 `docs/superglossary/glossary.md`를 읽는다. 없으면 생성 모드로 간다. index가 있으면 코드 범위로 해당 도메인 파일과 공통 표를 읽는다.
  2. **추가**: 4장의 규칙대로 분해·충돌 확인 뒤 맞는 파일의 표에 가나다순으로 넣는다. 스스로 추가했으면 작업을 이어 가기 전에 "용어 등록: 회원 → member" 한 줄로 알린다. 충돌이면 멈추고 기존 항목을 보여 준다.
  3. **수정·삭제**: 사용자가 요청할 때만 한다. 영문을 바꾸면 옛 영문을 금지 열에 넣을지 묻는다(기존 코드에 옛 이름이 남기 때문이다).
  4. **생성**: guide의 템플릿으로 `glossary.md`를 만든다. 코드가 이미 있으면 용어 스캔 여부를 묻고, 동의하면 `glossary-scanner`를 부른다. 사용자가 고른 후보를 등록한다(혼용 건은 표준 하나를 고르고 나머지는 금지 열에 둔다). 끝으로 포인터 줄을 넣을지 묻는다.
  5. **분리**: 추가 뒤 용어가 300개를 넘으면 분리를 제안한다. 동의하면 guide의 절차로 도메인 목록을 제안·확인받고 옮긴다.
- 포인터 줄: 대상은 프로젝트 루트의 `AGENTS.md`다. 루트에 `CLAUDE.md`·`.claude/CLAUDE.md`·`CLAUDE.local.md`가 있으면 그 파일이다(그때 Claude Code는 `AGENTS.md`를 읽지 않는다). 대상 파일이 없으면 만들지 않고 줄을 제안만 한다.

  ```
  - 용어 사전: docs/superglossary/glossary.md (이름을 짓기 전에 읽는다. 없는 단어는 /superglossary:glossary로 추가한다)
  ```

- `glossary-guide.md`: 3장의 두 형식 템플릿, 4장의 등록 규칙과 예시, 분리 절차(도메인 후보 제안 → 확인 → 파일 생성 → 공통 용어 판정 → index 작성 → 원래 표에서 제거). 생성·분리·예외 판단 때 읽는다.
- 하지 않는 것: 코드를 리네이밍하지 않는다. 사용자 확인 없이 지침 파일을 고치거나 분리하지 않는다.

### `check` 스킬

- 파일: `skills/check/SKILL.md`
- frontmatter:
  - `description` 초안: "코드 변경의 이름(클래스·변수·함수·컬럼·테이블·API 필드)이 용어 사전(docs/superglossary/)을 따르는지 검토해 표로 보고한다. 금지 단어, 등록된 개념의 다른 영문, 등록되지 않은 축약어, 사전에 추가할 후보를 찾는다. 작업을 마친 뒤나 커밋·PR 전, "용어 검사", "네이밍 점검", "사전이랑 맞는지 확인" 같은 요청에 사용한다. 코드는 고치지 않는다. 용어를 추가·수정하는 일은 glossary가 맡는다."
  - `argument-hint: "[경로 | 커밋 범위]"`
  - `allowed-tools: Read, Grep, Glob, Bash(git rev-parse:*), Bash(git diff:*), Bash(git status:*), Bash(git ls-files:*)`
- 흐름:
  1. **용어집**: 없으면 `/superglossary:glossary`로 만들자고 제안하고 끝낸다.
  2. **대상**: 인자가 없으면 staged·unstaged 변경과 untracked 파일, 경로나 커밋 범위가 주어지면 그 범위. 대상이 없으면 "검사할 변경이 없습니다"로 끝낸다.
  3. **읽기**: 변경 파일 경로에 맞는 도메인 파일과 공통 표를 읽는다(분리 전이면 `glossary.md`만).
  4. **대조**: 추가된 줄에서 새로 생긴 이름을 단어로 나눠 본다. ① 금지 단어 사용 ② 등록된 개념을 다른 영문으로 씀 ③ 등록되지 않은 축약어 ④ 반복 등장하는 미등록 단어(추가 후보). 일반 영어·라이브러리 식별자는 빼고, 기존 모듈의 컨벤션은 존중한다.
  5. **보고**: 위반 표(`파일:줄 | 이름 | 사전 표준 | 사유`)와 추가 후보 표(`한글(추정) | 영문 | 근거`). 코드는 고치지 않는다. 추가 후보는 `glossary`로 등록할지 묻는다.
- 서브에이전트 없이 메인 세션에서 처리한다(변경분만 보므로 충분하다).

### `glossary-scanner` 에이전트

- 파일: `agents/glossary-scanner.md`, `model: sonnet`, `tools: Read, Grep, Glob`
- `glossary` 생성 모드에서만 부른다. 입력: 프로젝트 루트, 용어집 경로, 기준 문서(`${CLAUDE_SKILL_DIR}/glossary-guide.md`) 경로.
- 작업: 엔티티·테이블·도메인 클래스·컬럼과 주요 식별자에서 핵심 개념을 고르고 4장 규칙대로 단어로 나눈다. 같은 개념의 영문 변형을 묶고 Grep의 count 모드로 변형별 빈도를 센다(어림하지 않는다). 일반 영어·언어 키워드·생성물·의존성 디렉터리는 뺀다.
- 출력: 단어 후보(`한글 | 영문 | 축약(선택) | 근거`), 혼용 리포트(`개념 | 변형과 빈도 | 최다 빈도`), 한 항목 예외 후보(근거 포함). 표준 선정은 사용자 몫이다.

## 6. 저장소 변경

### 삭제

- `plugins/superglossary/templates/`, `bin/`, `tests/`, `scripts/`
- `plugins/superglossary/skills/init/`, `skills/add/`, `agents/check-analyzer.md`
- `plugins/superglossary/docs/superpowers/`의 이전 spec 둘과 plan 둘
- `.github/workflows/superglossary.yml` — 세 단계(테스트·버전 일치·bin 실행)가 모두 CLI용이다. 매니페스트 이름·버전 대조는 `marketplace.yml`이 모든 플러그인에 대해 한다

### 새로 쓰거나 고침

- `skills/glossary/SKILL.md`, `skills/glossary/glossary-guide.md`(새로), `skills/check/SKILL.md`, `agents/glossary-scanner.md`(다시 씀)
- `plugins/superglossary/README.md`, `plugins/superglossary/AGENTS.md`(구조·규칙 다시 씀), `CHANGELOG.md`(0.7.0 항목 — 바뀐 점과 손으로 옮기는 방법), `.claude-plugin/plugin.json`(`version` 0.7.0, `description` 갱신)
- 루트 `AGENTS.md`: "superglossary는 `scripts/bump_version.py`로 버전을 올린다" 줄과 superglossary unittest 검증 블록을 지운다
- 루트 `CONTRIBUTING.md`: superglossary unittest 명령과 bump_version 안내를 지운다

## 7. 버전·릴리스

- 브랜치 `feat/superglossary-llm-glossary`(main에서 분기) → main PR.
- `plugin.json`의 `version`을 0.7.0으로 직접 고치고 CHANGELOG를 쓴다. 병합 뒤 `plugins/superglossary`에서 `claude plugin tag --push`로 `superglossary--v0.7.0` 태그를 단다.

## 8. 검증

단위 테스트는 두지 않는다(검사할 코드가 없다).

1. 저장소 루트에서 `claude plugin validate .`
2. skill-creator 방식의 가벼운 eval. 저장소 밖 임시 디렉터리에 픽스처 프로젝트를 만들고, 새 스킬을 가진 서브에이전트로 시나리오 3개를 돌려 결과를 채팅으로 정리한다. 형식이 달라 구버전 기준 실행은 생략한다.
   1. 기본 용어 셋(식별자·이름·일시)만 있는 용어집에서 "체결 엔티티에 매도호가·체결수량·체결일시 필드 추가해줘" → 단어별 등록(`체결`·`수량`), `매도호가`는 한 항목 예외로 보고 확인을 요청하는 지점에서 멈춤, `일시` 재사용(`executed_at` 계열)
   2. 용어 300개짜리 용어집에 하나를 추가 → 추가하고 분리를 제안만 한다(파일을 나누지 않는다)
   3. `회원(member, 금지 customer)`이 있는 용어집과 `customerId`·`regDt`가 들어간 diff에 check → 금지 단어와 미등록 축약어를 보고하고 코드는 고치지 않는다
3. noguesstoday 실사용(아래 후속 작업)

## 9. 후속 작업 — noguesstoday 전환

이 설계의 범위 밖이며, 구현 뒤 같은 세션에서 손으로 한다.

- `.claude/superglossary/glossary.json`(54개)을 `docs/superglossary/glossary.md`로 옮긴다. `relatedElements`는 비어 있어 버린다.
- `AGENTS.md`의 `<!-- superglossary:begin -->` 블록을 포인터 줄로 바꾸고 `.claude/superglossary/`를 지운다.
- 플러그인 0.7.0을 반영한다(마켓플레이스 갱신 또는 `--plugin-dir`).
