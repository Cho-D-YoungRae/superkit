# superdomain

도메인 로직이 드러나는 코드를 돕는 Claude Code·Codex 플러그인.

- 도메인마다 역할·기능·관계를 `docs/superdomain/DOMAIN.md` 한 파일에 정의한다.
- 외부 시스템과 맞닿은 도메인을 구분해 외부의 복잡성을 가두고, 도메인 사이 의존을 한 방향으로 유지한다.
- 변경이 도메인 정의와 코딩 컨벤션을 따르는지 리뷰한다.
- 비싸거나 중요한 결정을 ADR로 남기고, 작업을 마칠 때 기록할 결정이 있으면 제안한다.

아키텍처를 문서로 정하지 않는다. 대신 코드가 권장 방식(코딩 컨벤션)을 따르는지 리뷰로 확인한다. 의존 방향처럼 결정적으로 검사할 수 있는 규칙은 대상 프로젝트의 아키텍처 테스트(Spring Modulith·Konsist·ArchUnit)로 지키도록 구성 방법을 안내하고, 리뷰는 테스트가 덮지 않는 것을 본다. 플러그인에는 스크립트가 없어서 Claude Code나 Codex 말고는 설치할 것이 없다.

## 설치

### Claude Code

Claude Code 세션 안에서:

```
/plugin marketplace add Cho-D-YoungRae/superkit
/plugin install superdomain@superkit
```

터미널에서:

```bash
claude plugin marketplace add Cho-D-YoungRae/superkit
```

```bash
claude plugin install superdomain@superkit
```

superdomain은 [superkit](../../README.md) 마켓플레이스로 배포된다. 0.5.1 이하를 `superdomain@superdomain`으로 설치했다면 그 마켓플레이스를 지우고(`claude plugin marketplace remove superdomain`) 위 명령으로 다시 설치한다.

### Codex에서 쓰기

Codex도 같은 플러그인 폴더를 읽는다. 터미널에서:

```bash
codex plugin marketplace add Cho-D-YoungRae/superkit
```

```bash
codex plugin add superdomain@superkit
```

데스크톱 앱은 Plugins Directory의 **superkit for Codex**에서 설치한다. 0.9.0 이하의 Codex 전환본(`plugins/superdomain-codex`)을 설치했다면 설치 ID는 그대로이니 0.10.0으로 다시 설치한다. 스킬은 `superdomain:review`처럼 같은 이름으로 나열되므로, 스킬 목록에서 고르거나 "superdomain 리뷰 main..HEAD"처럼 요청한다. review와 domain의 독립 검토에는 새 컨텍스트의 서브에이전트가 필요하고, 두 관점 리뷰는 리뷰어 둘을 동시에 띄울 수 있어야 한다.

Claude Code와 다른 점:

- 리뷰어는 Claude Code 에이전트로 등록되지 않는다. review·domain 스킬이 [실행 계약](skills/review/references/dispatch.md)대로 서브에이전트를 띄워 `agents/`의 정의를 역할 문서로 넘긴다.
- 리뷰어의 읽기 전용·재위임 금지는 지시문으로만 지킨다. Claude Code처럼 도구를 막지 않으며, 샌드박스나 custom agent를 자동으로 설치하지 않는다.
- 모델은 지정하지 않는다(`opus`·`sonnet`은 Claude 모델 별칭이다). 서브에이전트 도구가 받으면 `reasoning_effort`를 domain-reviewer `high`, convention-reviewer `medium`으로 준다.
- conventions의 `paths`(`.kt`·`.java` 자동 적용)는 Codex에서 쓰이지 않는다. 설명으로 선택되므로, 반드시 적용할 작업에서는 스킬을 직접 고른다.
- Codex에서는 설치와 스킬 목록까지 확인했고(CLI 0.160.0), 실제 세션에서 리뷰어를 띄워 돌려 보지는 않았다.

## 스킬

| 스킬 | 언제 쓰나 |
|---|---|
| `/superdomain:domain` | 도메인을 처음 정의하거나, 도메인을 추가·분리·병합하거나, 역할·관계를 바꿀 때 |
| `/superdomain:review` | 커밋·PR 전에 변경이 도메인 정의와 코딩 컨벤션을 따르는지 볼 때, 도메인이 너무 커지지 않았는지 점검할 때 |
| `/superdomain:adr` | 비싸거나 중요한 결정을 기록하거나, 기록해 둔 결정이 바뀌었을 때, 정해진 것을 바꾸기 전에 관련 기록을 찾을 때. 작업을 마칠 때 기록할 결정이 있으면 먼저 제안한다 |
| `/superdomain:conventions` | Kotlin·Java 코드를 쓸 때 코딩 컨벤션을 적용한다. `.kt`·`.java` 작업에서 자동으로 걸린다 |

`review`의 인자는 `[domain|code] [경로 | 커밋 범위 | 전체]`다. 인자가 없으면 현재 브랜치의 변경과 커밋하지 않은 변경을 두 관점으로 모두 본다.

## 에이전트

| 에이전트 | 모델 | 하는 일 |
|---|---|---|
| `domain-reviewer` | opus | 도메인 정의와 코드를 도메인 경계 관점에서 검토한다. domain·review 스킬이 호출한다 |
| `convention-reviewer` | sonnet | Kotlin·Java 코드를 코딩 컨벤션 기준으로 검토한다. review 스킬이 호출한다 |

둘 다 읽기 전용이고, 모델은 에이전트 파일에서만 정한다. Codex에서는 같은 파일을 서브에이전트의 역할 문서로 쓴다(위 "Codex에서 쓰기").

## 대상 프로젝트에 생기는 파일

| 경로 | 무엇 |
|---|---|
| `docs/superdomain/DOMAIN.md` | 도메인별 역할·기능·분류·패키지(필요할 때: 외부·규칙·하위 도메인·개념·하지 않는 것·알려진 어긋남)와 도메인 간 관계 |
| `docs/superdomain/adr/yyyy-MM-dd-slug.md` | 결정 기록(결정마다 이유·버린 안·받아들인 비용) |

`domain`·`adr` 스킬은 동의를 받아 대상 지침 파일에 두 경로를 가리키는 포인터 줄을 추가할 수 있다. 대상은 프로젝트 루트의 AGENTS.md이고, 루트에 CLAUDE.md나 `.claude/CLAUDE.md`가 있으면 그 파일이다(그때 Claude Code는 AGENTS.md를 읽지 않는다. Codex는 CLAUDE.md를 자동으로 읽지 않는다). 포인터 줄은 두 런타임이 함께 읽으므로 스킬을 이름으로 가리킨다. ADR 줄이 있으면 에이전트가 작업을 마칠 때 기록할 결정이 있었는지 돌아보고 제안한다.

## 언어 범위

도메인 정의·도메인 리뷰·ADR은 언어와 무관하다. 코딩 컨벤션의 규칙은 백엔드 애플리케이션 전반에 적용되지만, 컨벤션 스킬과 컨벤션 리뷰는 Kotlin·Java(Spring·JPA) 파일에서 동작하고 예시도 Kotlin으로 적었다. 대상 프로젝트의 지침 파일(AGENTS.md·CLAUDE.md)에 다른 규칙이 있으면 그 규칙이 우선한다. 컨벤션이 맞지 않는 프로젝트에서는 그 프로젝트에서 플러그인을 끈다.

## 저장소 구조

```
.claude-plugin/          plugin.json (Codex도 이 파일을 읽는다. 카탈로그는 superkit 루트의
                         .claude-plugin/marketplace.json(Claude)과 .agents/plugins/marketplace.json(Codex))
skills/
  domain/                SKILL.md, domain-guide.md (DOMAIN.md 형식과 경계·분류 판단 기준)
  review/                SKILL.md, references/dispatch.md (Agent 도구가 없는 런타임의 리뷰어 실행 계약)
  adr/                   SKILL.md, adr-template.md
  conventions/           SKILL.md, conventions.md (코딩 컨벤션), architecture-tests.md (아키텍처 테스트 구성)
  */agents/openai.yaml   Codex 스킬 목록의 표시 이름·설명 (Claude Code는 쓰지 않는다)
agents/                  domain-reviewer.md, convention-reviewer.md (Claude Code 에이전트이자 Codex 역할 문서)
tests/                   레이아웃 불변식과 review의 Git 범위 (표준 라이브러리만)
docs/superpowers/        설계 스펙과 구현 계획
```

지식 파일(`domain-guide.md`, `conventions.md`)은 주제마다 하나이고, 해당 스킬과 리뷰 에이전트가 같은 파일을 읽는다.

스킬과 에이전트는 Claude Code와 Codex가 함께 읽는다. Claude 자리표시자(`${CLAUDE_SKILL_DIR}` 등)를 쓰는 파일은 제목 아래에 런타임 메모를 두고, 메모에는 `$`로 시작하는 치환 표기를 쓰지 않는다. Agent 도구에 기대는 단계에는 실행 계약으로 가는 경로를 함께 적는다. `tests/`가 이를 검사한다.

## 로컬 개발

```bash
claude --plugin-dir /path/to/superkit/plugins/superdomain
```

스킬은 `/superdomain:<스킬명>`으로 노출된다. SKILL.md를 포함해 플러그인 파일을 고쳤다면 `/reload-plugins`로 반영한다.

구조 검증(이 디렉터리에서):

```bash
claude plugin validate --strict .claude-plugin/plugin.json
```

```bash
claude plugin validate --strict skills
```

```bash
claude plugin validate --strict agents
```

테스트(이 디렉터리에서):

```bash
python3 -m unittest discover -s tests -q
```
