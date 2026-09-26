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
- **Python 3.9+** — CLI(`glossary.py`)가 `python3` 실행에 의존합니다(외부 패키지 0, 표준 라이브러리만 사용).
  macOS·주요 Linux 배포판에는 기본 탑재되어 있습니다. Windows 네이티브 환경에서는 [python.org](https://www.python.org/downloads/) 설치가 필요하며, 명령이 `python3`이 아니라 `python`일 수 있습니다.

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
   → .claude/superglossary/ 생성(glossary.json·core.md·terms.md·glossary.py)
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
| CLI | `templates/glossary.py` | 의존성 0의 독립 CLI (`init`/`build`/`add`/`update`/`remove`/`list`/`lookup`/`lint`/`version`/`help`) |
| 실행 파일 | `bin/superglossary` | 플러그인이 `PATH`에 노출하는 같은 CLI — 어디서든 `superglossary <서브커맨드>`로 실행 |

## 데이터 및 로딩

`/superglossary:init` 실행 시 사용자 프로젝트에 다음 파일들이 생성됩니다.

```
.claude/superglossary/
  glossary.json   — 용어 원본 데이터(SSOT, 스키마 버전·금지 변형·스톱워드 설정 포함). 사람·스크립트가 편집하는 유일한 원천
  core.md         — [생성물] Claude 상시 로드용 핵심 용어 요약(직접 편집 금지)
  terms.md        — [생성물] 설명·관련 요소까지 담은 전체 용어 목록(개발자가 훑어보기 좋음)
  glossary.py     — 용어사전 관리 CLI (init/build/add/update/remove/list/lookup/lint/version/help, templates/glossary.py 복사본)
```

**상시 로드**: init이 `.claude/CLAUDE.md`에 `@superglossary/core.md` import와 네이밍 규칙 블록을 자동으로 넣습니다. 이후 Claude가 세션마다 용어를 자동 참조합니다. `core.md`·`terms.md`는 `glossary.json`에서 생성되므로 직접 편집하지 말고, JSON을 고치면 `glossary.py build`로 재생성합니다. 손으로 고친 JSON에 구조 오류(필드 누락·타입 오류)나 용어 간 충돌(영문·축약어 중복 등)이 있으면 CLI가 어디가 틀렸는지 알려 주고, 충돌이 남은 사전은 저장·빌드하지 않습니다.

**팀 공유**: 용어사전은 팀이 공유해야 가치가 있습니다. `.claude/superglossary/`와 `.claude/CLAUDE.md`를 **git에 커밋**하세요. `.gitignore`가 `.claude/`를 무시하면 init이 경고와 함께 해결 패턴(`.claude/*` + `!.claude/superglossary/`)을 안내합니다.

## 기존 프로젝트에 도입 (brownfield)

코드가 이미 있는 프로젝트에서 `/superglossary:init`을 실행하면, 용어 후보·혼용을 스캔할지 물어봅니다. 동의하면 `glossary-scanner`가 다음을 반환합니다.

- **단일어 후보** — 엔티티·컬럼·주요 변수에서 추출한 핵심 개념(복합어는 분해).
- **혼용 리포트** — 같은 개념에 쓰인 영문 변형과 빈도(예: 사용자 → `user`×120 / `member`×45 / `customer`×12).

혼용 건은 **표준 1개**를 고르면, 탈락한 변형을 금지 목록으로 보존하며 등록됩니다.

```bash
python3 .claude/superglossary/glossary.py add 회원 member --avoid "customer,user"
```

이후 비표준 사용처는 **자동으로 바꾸지 않고**, `check`의 lint가 `[위반]`으로 지속 보고해 점진적으로 수렴시킵니다.

## 용어 조회·관리 (CLI)

Claude를 거치지 않고 개발자가 직접 사전을 다룰 때 씁니다. 실행 방법은 두 가지이며 동작은 같습니다.

```bash
superglossary <서브커맨드>                              # 플러그인이 PATH에 노출 (어느 하위 디렉토리에서든)
python3 .claude/superglossary/glossary.py <서브커맨드>   # 프로젝트 복사본 (플러그인 없이도, CI에서도)
```

`superglossary`는 현재 디렉토리에서 위로 올라가며 `.claude/superglossary/`를 찾으므로 프로젝트 안 어디서 실행해도 됩니다(`SUPERGLOSSARY_DIR`로 직접 지정할 수도 있습니다). 항상 설치된 플러그인의 최신 CLI가 돌기 때문에, 프로젝트 복사본이 오래됐을 때 생기는 버전 차이를 피할 수 있습니다. 복사본은 플러그인을 설치하지 않은 팀원과 CI를 위해 유지됩니다. 아래 예시는 복사본 형태로 적었습니다.

| 서브커맨드 | 용도 | 예시 |
|---|---|---|
| `lookup <질의>` | 한 용어의 상세(설명·관련·금지)를 조회 | `... lookup 회원` |
| `list` | 전체 용어를 간결히 나열 | `... list` |
| `add <한글> <영문> [축약어]` | 등록 (`--desc`, `--related`, `--avoid` 옵션. 축약어는 `--abbreviation`으로도 지정) | `... add 청구 claim --desc "요금 청구"` |
| `update <한글>` | 지정 필드만 수정 (`--english`/`--abbreviation`/`--desc`/`--related`/`--avoid`). `--avoid ""`처럼 빈 값을 주면 목록을 비움 | `... update 청구 --english billing` |
| `remove <한글>` | 삭제 | `... remove 청구` |
| `lint [--all] <paths...>` | 코드 대조 (`[위반]`/`[후보]`, 디렉토리는 재귀 탐색, `.claude/`는 제외, `--all`은 스톱워드 필터 해제) | `... lint src/` |
| `build` | `glossary.json` → `core.md`·`terms.md` 재생성 | `... build` |
| `version` / `help` | CLI 버전 / 사용법 | `... version` |

`add`/`update`/`remove`는 자동으로 재빌드합니다. 출력 예시:

```console
$ python3 .claude/superglossary/glossary.py lookup 회원
회원 → member
  금지: customer, user

$ python3 .claude/superglossary/glossary.py lint src/OrderService.java
[위반]
customer	member(회원)	8	src/OrderService.java
[후보]
delivery	3	src/OrderService.java
```

`[위반]` 행은 `토큰 · 표준영문(한글) · 빈도 · 파일`, `[후보]` 행은 `토큰 · 빈도 · 파일`입니다. 이상이 없으면 `이상 없음` 한 줄만 출력됩니다.

CLI는 입력을 조용히 버리지 않습니다. 모르는 옵션(`--description` 등), 값이 빠진 옵션, 남는 인자는 오류로 알립니다. `lint`에 존재하지 않는 경로를 주면 경고하고, 모든 경로가 없으면 오류로 멈춥니다.

### 스톱워드 조정 (lint 노이즈 줄이기)

`lint`는 언어 키워드·표준 타입·기술 계층 어휘 약 250개를 후보에서 제외합니다. 프로젝트마다 노이즈는 다르므로 `glossary.json`에서 조정할 수 있습니다.

```json
{
  "schemaVersion": 1,
  "stopwords": {
    "add": ["acme", "svc"],
    "remove": ["repository"]
  },
  "terms": [ ... ]
}
```

- `add` — 매번 후보로 올라오지만 용어가 아닌 토큰(사내 접두사, 프레임워크 식별자)을 제외합니다.
- `remove` — 기본 스톱워드에 있지만 이 프로젝트에서는 도메인 핵심어인 단어를 후보로 되살립니다(예: 금융 도메인의 `position`).

대소문자는 무시하며, **금지 변형(`avoid`)은 스톱워드보다 우선**합니다 — `avoid`에 등록된 토큰은 스톱워드에 있어도 `[위반]`으로 잡힙니다. 후보 목록이 짧아지면 `check` 스킬이 서브에이전트로 넘기지 않고 인라인으로 처리하는 비율이 올라갑니다.

## 데이터 스키마 버전

`glossary.json`의 `schemaVersion` 필드는 데이터 구조의 버전입니다(CLI 버전과 별개이며, 구조가 바뀔 때만 올라갑니다).

- CLI가 **아는 것보다 낮은** 버전을 만나면 메모리에서 자동으로 올리고, `/superglossary:init` 재실행 시 파일에 반영합니다. `schemaVersion`이 없는 0.4.0 이전 파일도 그대로 읽힙니다.
- CLI가 **아는 것보다 높은** 버전을 만나면 조용히 오작동하는 대신 오류로 중단하고 CLI 갱신을 안내합니다. 팀원마다 플러그인 버전이 달라도 사전이 깨지지 않습니다.

## 업그레이드

플러그인 업데이트 후 각 프로젝트에서 `/superglossary:init`을 재실행하면 CLI 복사본이 최신으로 갱신됩니다. `glossary.json`과 기존 `.claude/CLAUDE.md` 블록은 보존됩니다.

- 현재 CLI 버전 확인: `python3 .claude/superglossary/glossary.py version`
- CLAUDE.md 블록 문구까지 최신화하려면: `.claude/CLAUDE.md`의 `## 용어 사전` 섹션을 지우고 init을 재실행

## 자동 트리거 (선택)

기본 설정에는 포함되지 않습니다. 필요한 경우 아래 예시를 참고해 프로젝트에 맞게 추가하세요.

### pre-commit (경고 전용)

```bash
# .husky/pre-commit 예시 — 스테이징된 파일만 검사, exit code 무시(경고만 출력)
files=$(git diff --cached --name-only --diff-filter=ACMR)
[ -n "$files" ] && echo "$files" | xargs python3 .claude/superglossary/glossary.py lint || true
```

검사 대상 경로는 반드시 넘겨야 합니다 — 인자 없이 `lint`를 실행하면 사용법 오류가 납니다.

### CI에서 생성물 stale 검사

```yaml
# GitHub Actions 예시
- name: 용어사전 stale 검사
  run: |
    python3 .claude/superglossary/glossary.py build
    git diff --exit-code .claude/superglossary/
    # 위 명령이 실패하면 빌드 결과물이 커밋과 다른 것 (stale)
```

`git diff`가 비어야 정상입니다. 비어 있지 않으면 `glossary.py build`를 재실행한 뒤 커밋하세요.

## 기여

브랜치 전략·커밋 규칙·릴리즈 절차는 [CONTRIBUTING.md](CONTRIBUTING.md)를 참고하세요.

## 출처

이 플러그인의 용어사전 개념은 강의 **[「김영한의 실전 데이터베이스 - 설계 1편, 현대적 데이터 모델링 완전 정복」](https://www.inflearn.com/course/김영한-실전-데이터베이스-설계1편/dashboard?cid=338886)** 의 '용어 사전' 파트를 참고했습니다.

## 라이선스

[MIT](LICENSE)
