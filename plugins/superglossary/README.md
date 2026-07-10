# superglossary

프로젝트 용어사전 — 프로젝트별 도메인 용어를 파일로 관리하고, Claude가 일관된 용어를 사용하도록 돕는 [Claude Code](https://code.claude.com) 플러그인입니다. 개발자와 Claude가 **같은 용어집**을 참조해, 같은 개념을 매번 다르게 번역하는 일(청구 → claim / billing / charge)을 막습니다.

## 핵심 개념

이 세 가지만 알면 사전을 올바르게 쓸 수 있습니다.

- **단일어 중심.** 복합어를 통째로 등록하지 않습니다. 최소 단위 단일어만 등록하고 조합합니다 — `회원번호`가 아니라 `회원`(member) + `식별자`(id) → `member_id`. 복합어를 등록하면 사전이 비대해지고 `member_num` vs `member_id`처럼 일관성이 무너집니다.
- **축약어 통제.** 축약어는 사전에 등록된 것만 씁니다(`id`, `at` 등). 미등록 축약(`reg_dt`의 `reg`)은 위반입니다.
- **금지 변형(avoid).** 같은 개념에 쓰면 안 되는 영문 변형을 표준과 함께 보존합니다(예: `member`의 금지 = `customer`, `user`). `check`가 LLM 판단 없이 이를 `[위반]`으로 확정합니다.

로딩은 2단입니다. 압축 매핑표(`core.md`)는 세션마다 **상시 로드**되고, 상세 설명(`terms.md`)은 필요할 때만 찾습니다.

## 설치

### 전제조건

- [Claude Code](https://code.claude.com)
- **Node.js** — CLI(`glossary.mjs`)가 `node` 실행에 의존합니다(의존성은 0, Node 내장 모듈만 사용).

### 배포판 설치 (권장)

```bash
/plugin marketplace add Cho-D-YoungRae/superglossary
/plugin install superglossary@superglossary
```

### 로컬 개발용 로드

```bash
claude --plugin-dir .
# 세션 중 변경 적용 시
/reload-plugins
```

## 빠른 시작

새 프로젝트(greenfield) 기준입니다. 모두 Claude Code 세션 안에서 진행합니다.

```
1. /superglossary:init
   → .claude/superglossary/ 생성(glossary.json·core.md·terms.md·glossary.mjs)
   → .claude/CLAUDE.md에 용어사전 블록 자동 삽입(@superglossary/core.md 상시 로드)

2. /superglossary:add 회원 member
   → 단일어를 등록합니다. 복합어(회원번호)를 주면 회원+식별자로 분해해 안내합니다.
   → 인자: <한글> <영문> [축약어] [--desc "설명"]

3. (작업)  core.md가 상시 로드되므로, 검색 없이 member로 네이밍합니다.
           사전에 없는 개념을 만나면 Claude가 그 자리에서 add로 등록합니다.

4. /superglossary:check
   → 변경 파일을 사전과 대조해 [위반]·[후보]를 표로 보고합니다(자동 수정은 안 함).
```

용어를 CLI로 직접 다루는 예(개발자용)는 아래 [용어 조회·관리](#용어-조회관리-cli)를 참고하세요.

## 권장 워크플로우

작업 중에는 용어를 검색하지 않는 것이 핵심입니다 — `core.md`가 상시 로드되므로 조회 없이 영문명을 아는 상태로 코드를 씁니다.

```
1. 최초 1회  — /superglossary:init 으로 초기화 (큰 기능 전엔 다룰 핵심 개념을 사전과 정렬)
2. 작업 중   — 검색 없이 작업하되, 사전에 없는 용어를 만나면 add 스킬로 그것만 추가
3. 완료 후   — check 스킬로 일관성 검사 ([위반]은 사전이 확정, 후보는 의미 검토)
4. (선택)    — 커밋/PR 전 자동 lint (아래 '자동 트리거' 참고)
```

## 구성 요소

| 종류 | 이름 | 역할 |
|------|------|------|
| 스킬 | `/superglossary:init` | 프로젝트에 용어사전 초기화·CLI 업그레이드 (사용자 전용) |
| 스킬 | `/superglossary:add` | 새 용어 등록 — 사용자 호출 + Claude가 필요 시 자율 호출 |
| 스킬 | `/superglossary:check` | 용어 일관성 검사 (소규모는 인라인, 대규모는 서브에이전트) |
| 서브에이전트 | `check-analyzer` | 대규모 후보의 의미 기반 확정 (model: sonnet) |
| 서브에이전트 | `glossary-scanner` | 코드·문서에서 용어 후보·혼용 스캔 (model: sonnet) |
| CLI | `templates/glossary.mjs` | 의존성 0의 독립 CLI (`init`/`build`/`add`/`update`/`remove`/`list`/`lookup`/`lint`/`version`/`help`) |

## 데이터 및 로딩

`/superglossary:init` 실행 시 사용자 프로젝트에 다음 파일들이 생성됩니다.

```
.claude/superglossary/
  glossary.json   — 용어 원본 데이터(SSOT, 금지 변형 avoid 포함). 사람·스크립트가 편집하는 유일한 원천
  core.md         — [생성물] Claude 상시 로드용 핵심 용어 요약(직접 편집 금지)
  terms.md        — [생성물] 설명·관련 요소까지 담은 전체 용어 목록(개발자가 훑어보기 좋음)
  glossary.mjs    — 용어사전 관리 CLI (init/build/add/update/remove/list/lookup/lint/version/help, templates/glossary.mjs 복사본)
```

**상시 로드**: init이 `.claude/CLAUDE.md`에 `@superglossary/core.md` import와 네이밍 규칙 블록을 자동으로 넣습니다. 이후 Claude가 세션마다 용어를 자동 참조합니다. `core.md`·`terms.md`는 `glossary.json`에서 생성되므로 직접 편집하지 말고, JSON을 고치면 `glossary.mjs build`로 재생성합니다.

**팀 공유**: 용어사전은 팀이 공유해야 가치가 있습니다. `.claude/superglossary/`와 `.claude/CLAUDE.md`를 **git에 커밋**하세요. `.gitignore`가 `.claude/`를 무시하면 init이 경고와 함께 해결 패턴(`.claude/*` + `!.claude/superglossary/`)을 안내합니다.

## 기존 프로젝트에 도입 (brownfield)

코드가 이미 있는 프로젝트에서 `/superglossary:init`을 실행하면, 용어 후보·혼용을 스캔할지 물어봅니다. 동의하면 `glossary-scanner`가 다음을 반환합니다.

- **단일어 후보** — 엔티티·컬럼·주요 변수에서 추출한 핵심 개념(복합어는 분해).
- **혼용 리포트** — 같은 개념에 쓰인 영문 변형과 빈도(예: 사용자 → `user`×120 / `member`×45 / `customer`×12).

혼용 건은 **표준 1개**를 고르면, 탈락한 변형을 금지 목록으로 보존하며 등록됩니다.

```bash
node .claude/superglossary/glossary.mjs add 회원 member --avoid "customer,user"
```

이후 비표준 사용처는 **자동으로 바꾸지 않고**, `check`의 lint가 `[위반]`으로 지속 보고해 점진적으로 수렴시킵니다.

## 용어 조회·관리 (CLI)

Claude를 거치지 않고 개발자가 직접 사전을 다룰 때 씁니다. 실행 위치는 프로젝트 루트, 명령은 `node .claude/superglossary/glossary.mjs <서브커맨드>`입니다.

| 서브커맨드 | 용도 | 예시 |
|---|---|---|
| `lookup <질의>` | 한 용어의 상세(설명·관련·금지)를 조회 | `... lookup 회원` |
| `list` | 전체 용어를 간결히 나열 | `... list` |
| `add <한글> <영문> [축약어]` | 등록 (`--desc`, `--related`, `--avoid` 옵션) | `... add 청구 claim --desc "요금 청구"` |
| `update <한글>` | 지정 필드만 수정 (`--english`/`--abbreviation`/`--desc`/`--related`/`--avoid`) | `... update 청구 --english billing` |
| `remove <한글>` | 삭제 | `... remove 청구` |
| `lint [--all] <files...>` | 코드 대조 (`[위반]`/`[후보]`, `--all`은 스톱워드 필터 해제) | `... lint src/` |
| `build` | `glossary.json` → `core.md`·`terms.md` 재생성 | `... build` |
| `version` / `help` | CLI 버전 / 사용법 | `... version` |

`add`/`update`/`remove`는 자동으로 재빌드합니다. 출력 예시:

```console
$ node .claude/superglossary/glossary.mjs lookup 회원
회원 → member
  금지: customer, user

$ node .claude/superglossary/glossary.mjs lint src/OrderService.java
[위반]
customer	member(회원)	8	src/OrderService.java
[후보]
delivery	3	src/OrderService.java
```

`[위반]` 행은 `토큰 · 표준영문(한글) · 빈도 · 파일`, `[후보]` 행은 `토큰 · 빈도 · 파일`입니다. 이상이 없으면 `이상 없음` 한 줄만 출력됩니다.

## 업그레이드

플러그인 업데이트 후 각 프로젝트에서 `/superglossary:init`을 재실행하면 CLI 복사본이 최신으로 갱신됩니다. `glossary.json`과 기존 `.claude/CLAUDE.md` 블록은 보존됩니다.

- 현재 CLI 버전 확인: `node .claude/superglossary/glossary.mjs version`
- CLAUDE.md 블록 문구까지 최신화하려면: `.claude/CLAUDE.md`의 `## 용어 사전` 섹션을 지우고 init을 재실행

## 자동 트리거 (선택)

기본 설정에는 포함되지 않습니다. 필요한 경우 아래 예시를 참고해 프로젝트에 맞게 추가하세요.

### pre-commit (경고 전용)

```bash
# .husky/pre-commit 예시 — exit code 무시, 경고만 출력
node .claude/superglossary/glossary.mjs lint || true
```

### CI에서 생성물 stale 검사

```yaml
# GitHub Actions 예시
- name: 용어사전 stale 검사
  run: |
    node .claude/superglossary/glossary.mjs build
    git diff --exit-code .claude/superglossary/
    # 위 명령이 실패하면 빌드 결과물이 커밋과 다른 것 (stale)
```

`git diff`가 비어야 정상입니다. 비어 있지 않으면 `glossary.mjs build`를 재실행한 뒤 커밋하세요.

## 기여

브랜치 전략·커밋 규칙·릴리즈 절차는 [CONTRIBUTING.md](CONTRIBUTING.md)를 참고하세요.

## 출처

이 플러그인의 용어사전 개념은 강의 **[「김영한의 실전 데이터베이스 - 설계 1편, 현대적 데이터 모델링 완전 정복」](https://www.inflearn.com/course/김영한-실전-데이터베이스-설계1편/dashboard?cid=338886)** 의 '용어 사전' 파트를 참고했습니다.

## 라이선스

[MIT](LICENSE)
