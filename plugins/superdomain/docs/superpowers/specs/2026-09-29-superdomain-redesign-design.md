# superdomain 0.4.0 재설계 — 설계 스펙

- 날짜: 2026-09-29
- 상태: 구현됨(0.4.0). 0.4.1에서 산출물 경로를 `docs/superdomain/`으로 되돌리는 등 일부가 바뀌었다 — `CHANGELOG.md`의 0.4.1 참고
- 대체: `2026-09-29-superdomain-audit.md`(점검 초안 — 이 문서로 대체하고 삭제한다)와 그 이전의 스펙·계획 전부

## 1. 목표

superdomain을 **도메인 정의, 리뷰, 결정 기록**에 집중하는 작은 플러그인으로 다시 만든다.

| 의도 | 0.4.0에서 맡는 곳 |
|---|---|
| 도메인을 명확하게 정의한다 | `domain` 스킬 → `docs/DOMAIN.md` |
| 도메인 간 관계를 명확하게 한다 | `docs/DOMAIN.md`의 관계 표 + `domain-reviewer`의 코드 검토 |
| 도메인 로직이 드러나는 코드를 쓴다 | `conventions` 스킬(작성 중 적용) + `convention-reviewer`(리뷰) |
| 기술 결정을 기록한다 | `adr` 스킬 → `docs/adr/` |

원칙:

1. 아키텍처를 문서로 특정하지 않는다. 코드가 권장 방식(코딩 컨벤션)을 따르는지 리뷰로 확인한다.
2. 스크립트를 두지 않는다. 판단은 리뷰 에이전트가 하고, 확정은 사용자가 한다.
3. 지식은 주제마다 파일 하나에 둔다. 그 주제를 다루는 스킬과 리뷰 에이전트가 같은 파일을 읽는다.
4. 스킬은 superpowers 방식을 따른다. description에는 언제 쓰는지만 적고, 질문은 한 번에 하나씩 하고, 확정은 사용자 확인 뒤에 한다.
5. 에이전트의 모델은 에이전트 파일에 명시하고, 스킬이 호출할 때 덮어쓰지 않는다.

### 비목표

- ARCHITECTURE.md 같은 아키텍처 명세, 스타일 프리셋
- 결정적 강제(검사 스크립트, ArchUnit 테스트 생성). 필요해지면 따로 설계한다
- 용어집. superglossary가 맡는다
- 컨텍스트별 상세 문서(`contexts/*.md`). 핵심 규칙은 DOMAIN.md의 "규칙"에 적는다
- 0.3.x 배치의 자동 감지·이행 코드. CHANGELOG 안내로 대신한다

## 2. 확정된 결정

| # | 결정 |
|---|---|
| D1 | 스킬은 `domain`·`review`·`adr`·`conventions` 넷이다. init·model·apply·sync·evolve·migrate와 저장소 전용 study는 없앤다 |
| D2 | `conventions` 스킬을 둔다(코드 작성 중에 컨벤션 적용). 리뷰 에이전트와 같은 `conventions.md`를 읽는다 |
| D3 | 에이전트는 `domain-reviewer`(`model: opus`)와 `convention-reviewer`(`model: sonnet`)다 |
| D4 | 스크립트는 0개다. `scripts/`·`tests/`·CI를 없앤다 |
| D5 | SessionStart 훅과 `summary.md`를 없앤다. `domain` 스킬이 끝날 때 동의를 받아 대상 CLAUDE.md에 포인터 한 줄을 추가한다 |
| D6 | 대상 프로젝트 산출물은 `docs/DOMAIN.md`와 `docs/adr/`다 |
| D7 | `review`는 스킬 하나가 두 에이전트를 병렬로 호출해 한 리포트로 합친다 |
| D8 | DOMAIN.md에는 도메인별 역할·기능·분류·코드(선택: 규칙·하지 않는 것)와 관계 표를 적는다 |
| D9 | `references/`(governance 7종, knowledge 12종)를 없앤다. 쓸 만한 내용은 `domain-guide.md`로 흡수한다 |
| D10 | 명칭은 "코딩 컨벤션"이다 |
| D11 | 컨벤션은 파일 하나(`conventions.md`)이고, 항목마다 강도(`필수`/`지향`)를 단다 |
| D12 | 컨벤션 항목은 14개다(§7.2) |
| D13 | `canXxx()` 패턴은 `지향`이다. 목적은 도메인의 검증 로직을 밖으로 드러내는 것이다 |
| D14 | 결과가 매번 달라지는 정적 호출은 컴포넌트로 감싼다(`UuidHolder`는 예시). 반환은 문자열보다 타입(`UUID`)으로 한다 |

사용자 답이 없어 기본값으로 정한 것(검토 때 바꿀 수 있다):

- 컨트롤러 슬라이스 테스트는 application 계층을 모킹해도 된다. 근거: imstargg CLAUDE.md도 모킹 규칙을 "Service/Component 테스트 의존성 처리" 절에 두어 범위를 한정한다.
- DB는 모킹할 수 있지만, application 리포지토리는 실제 DB로 검증하는 것을 지향한다. 근거: imstargg CLAUDE.md의 같은 절("내부 데이터 계층은 실 DB, 외부 시스템만 MockK — stub-and-verify는 호출 결합도만 검증한다").
- `Clock`과 Holder 컴포넌트는 모킹하지 않고 `Clock.fixed(...)`나 상속한 가짜로 바꿔 끼운다.
- DB가 필요한 검증 객체의 이름은 `XxxEligibility`로 한다.
- 컨벤션 예시 코드는 Kotlin으로 통일한다. Java로 주신 `UuidHolder`도 같은 모양의 Kotlin으로 옮긴다.
- `docs/superpowers/`의 옛 스펙·계획은 지운다(git 이력에는 남는다). 이 스펙과 이어질 구현 계획만 남긴다.
- 버전은 0.4.0으로 한다.

## 3. 저장소 구성

```
.claude-plugin/
  plugin.json                 version 0.4.0, description·keywords 갱신
  marketplace.json            description·keywords 갱신
skills/
  domain/
    SKILL.md
    domain-guide.md           DOMAIN.md 형식 + 경계·분류 판단 기준 (domain-reviewer도 읽음)
  review/
    SKILL.md
  adr/
    SKILL.md
    adr-template.md
  conventions/
    SKILL.md
    conventions.md            코딩 컨벤션 (convention-reviewer도 읽음)
agents/
  domain-reviewer.md
  convention-reviewer.md
docs/superpowers/
  specs/2026-09-29-superdomain-redesign-design.md   이 문서
  plans/2026-09-29-superdomain-redesign.md          다음 단계에서 작성
README.md
CHANGELOG.md
LICENSE
.gitignore                    `__pycache__/` 줄 삭제
```

plugin.json의 description은 "도메인 정의(DOMAIN.md), 도메인·코딩 컨벤션 리뷰, ADR로 도메인 로직이 드러나는 코드를 돕는다"로 바꾼다. keywords는 `ddd`, `domain-driven-design`, `bounded-context`, `code-review`, `conventions`, `adr`, `kotlin`, `spring`, `korean`이다.

### 지우는 것

| 대상 | 규모 |
|---|---|
| `skills/{init,model,apply,sync,evolve,migrate}/` | 스킬 6개 |
| 기존 `skills/{adr,review}/SKILL.md`, `agents/domain-reviewer.md` | 새로 쓴다 |
| `scripts/` | Python 6개 + 셸 1개, 3,195줄 |
| `tests/` | 4,261줄, 테스트 414개 |
| `hooks/` | SessionStart 훅 |
| `references/` | governance 7, knowledge 12, INDEX — 4,444줄 |
| `.claude/skills/study/` | 저장소 전용 스킬 |
| `.github/workflows/ci.yml` | CI |
| `docs/superpowers/`의 옛 스펙 3·계획 9·점검 초안 | 약 8,500줄 |

## 4. 대상 프로젝트 산출물

| 경로 | 무엇 | 쓰는 스킬 |
|---|---|---|
| `docs/DOMAIN.md` | 도메인별 역할·기능·분류·코드와 관계 | domain |
| `docs/adr/yyyy-MM-dd-slug.md` | 결정 기록 | adr |

플러그인은 그 밖의 파일(요약, 상태, 로그)을 만들지 않는다. 대상 CLAUDE.md에는 사용자가 동의할 때만 아래 한 줄을 넣는다.

```
- 도메인 정의: docs/DOMAIN.md (도메인의 역할·관계를 바꾸는 작업 전에 읽는다)
```

## 5. 스킬

공통 규칙:

- description에는 "언제 쓰는가"만 적고 절차를 요약하지 않는다. 헷갈리기 쉬운 이웃이 있으면 "쓰지 않는 경우"를 한 줄 적는다.
- 작업 기준은 git 루트다.
- 파일 생성·수정·삭제 같은 확정은 사용자 확인 뒤에 한다. 판단은 근거와 함께 적극적으로 제안한다.
- SKILL.md는 150줄 이하를 목표로 짧게 쓰고, 판단 기준은 지식 파일에 둔다.

### 5.1 domain

```yaml
name: domain
description: 프로젝트의 도메인을 처음 정의할 때, 도메인을 추가·분리·병합하거나 역할·관계를 바꿀 때, docs/DOMAIN.md가 없거나 코드와 맞지 않을 때 사용한다. "도메인 정의", "도메인 나눠줘", "바운디드 컨텍스트 정리", "DOMAIN.md" 같은 요청이 해당한다.
```

흐름 (superpowers brainstorming 방식):

1. **맥락 파악**: `docs/DOMAIN.md`가 있으면 수정 모드, 없으면 새로 정의한다. CLAUDE.md·README·모듈과 패키지 구조·최근 커밋을 읽는다. 코드가 없으면 제품이 무엇인지부터 묻는다.
2. **기준 읽기**: 도메인 후보를 내기 전에 `${CLAUDE_SKILL_DIR}/domain-guide.md`를 읽는다.
3. **질문**: 한 번에 하나씩 묻고, 가능하면 선택지와 추천을 함께 낸다. 목적은 역할·기능·경계·관계를 확정하는 것이다.
4. **도메인 목록 제안**: 후보마다 근거(가이드의 경계 기준)를 붙이고 확인받는다.
5. **섹션별 작성**: 도메인마다 역할·기능·분류·코드(선택: 규칙·하지 않는 것)를 쓰고 확인받는다. 이어서 관계 표를 쓰고 확인받는다.
6. **저장 후 자체 검토**: `docs/DOMAIN.md`에 쓰고, `superdomain:domain-reviewer`를 정의 검토 모드로 호출한다. 지적 중 무엇을 반영할지 사용자와 정한다.
7. **사용자 검토**: 파일을 검토해 달라고 요청한다.
8. **후속**: 도메인 분리·병합 같은 큰 결정이면 `/superdomain:adr`을 제안한다. 대상 CLAUDE.md에 포인터가 없으면 추가를 제안한다.

수정 모드는 이렇게 진행한다: 무엇을 바꿀지 확인한다 → 바뀌는 부분의 전·후를 보여 준다 → 확인받는다 → 반영한다 → 도메인을 추가·분리·병합했으면 6단계 자체 검토를 한다.

기존 파일이 0.3.x 형식(`## 컨텍스트:`·`- 패키지:`·`### 관계` 표 등)이면 새 형식으로 전체를 다시 쓰자고 제안한다. 옛 `docs/superdomain/contexts/*.md`가 남아 있으면 그 불변식을 "규칙" 후보로 읽는다. 감지 코드를 따로 두지 않고, 스킬 본문의 이 안내로 처리한다(CHANGELOG 이행 2단계가 이 경로를 쓴다).

하지 않는 것: 코드 작성, 패키지·디렉터리 생성, 용어 정의 작성.

### 5.2 review

```yaml
name: review
description: 커밋·PR 전에 변경이 도메인 정의(docs/DOMAIN.md)와 코딩 컨벤션을 따르는지 검토할 때, 도메인이 너무 커지거나 경계가 흐려지지 않았는지 점검할 때 사용한다. "도메인 리뷰", "컨벤션 리뷰", "superdomain 리뷰" 같은 요청이 해당한다. 버그·보안 중심의 일반 코드 리뷰에는 쓰지 않는다.
argument-hint: "[domain|code] [경로 | 커밋 범위 | 전체]"
```

description의 마지막 문장은 다른 플러그인의 일반 코드 리뷰 스킬과 구별하려고 둔다.

흐름:

1. **대상 결정**
   - 기본값은 기준 브랜치와의 merge-base부터 HEAD까지의 변경 + 커밋하지 않은 변경이다. 기준 브랜치는 `origin/HEAD`가 가리키는 브랜치이고, 알 수 없으면 묻는다.
   - 인자로 경로, 커밋 범위, `전체`(프로젝트 전체 점검)를 받는다.
   - `전체`가 아닌데 변경이 없으면 알리고 끝낸다.
2. **관점 결정**: 인자가 `domain`이면 도메인만, `code`면 컨벤션만, 없으면 둘 다 본다.
   - `docs/DOMAIN.md`가 없으면 도메인 리뷰를 건너뛰고 `/superdomain:domain`을 안내한다.
   - 대상에 `.kt`·`.java`가 없으면 컨벤션 리뷰를 건너뛰고 그 사실을 알린다.
   - 두 관점이 모두 건너뛰어지면 이유를 알리고 끝낸다.
3. **병렬 호출**: 한 메시지에서 `superdomain:domain-reviewer`와 `superdomain:convention-reviewer`를 호출한다.
   - 넘기는 것: 모드(변경/전체), 프로젝트 루트, 변경 범위를 보는 git 명령과 파일 목록, DOMAIN.md 경로.
   - 세션 이력은 넘기지 않는다. `model`은 지정하지 않는다.
4. **합치기**: 심각도(Critical → Important → Minor) 순으로 정렬하고, 같은 위치의 같은 지적은 하나로 합친다. 두 리뷰어의 판단이 충돌하면 둘 다 보여 준다. 질문은 따로 모은다.
5. **보고와 후속**
   - 코드 수정은 사용자가 요청할 때만 한다. 리뷰어의 지적이 틀렸다고 보이면 근거와 함께 그렇게 말한다.
   - DOMAIN.md를 바꿔야 하면 `/superdomain:domain`을, 결정을 남겨야 하면 `/superdomain:adr`을 안내한다.

하지 않는 것: 자동 수정, 결과 파일 저장, 리뷰어 모델 덮어쓰기.

### 5.3 conventions

```yaml
name: conventions
description: Kotlin·Java(Spring·JPA) 코드에서 도메인 모델·서비스·리포지토리·엔티티·테스트를 작성하거나 고칠 때 사용한다.
paths: ["**/*.kt", "**/*.java"]
```

본문(40줄 안팎):

- 코드를 쓰기 전에 `${CLAUDE_SKILL_DIR}/conventions.md`를 읽고 따른다.
- 대상 프로젝트 CLAUDE.md의 규칙과 충돌하면 프로젝트 규칙을 따른다.
- `필수` 규칙에서 벗어나야 하면 그 이유를 사용자에게 말한다. `지향` 규칙은 가능한 한 따른다.
- DOMAIN.md의 분류가 generic인 도메인이나, 어드민·워커·배치처럼 도메인 로직이 얇은 곳에서는 영속성 예외를 쓸 수 있다.
- 기존 코드가 컨벤션과 달라도 이번 변경 범위에서만 컨벤션을 따른다. 넓은 정리는 제안만 한다.

알려진 트레이드오프: 플러그인이 켜진 모든 프로젝트의 Kotlin·Java 작업에서 이 스킬이 걸릴 수 있다. "프로젝트 규칙이 우선한다"는 문장으로 충돌을 줄이고, 맞지 않는 프로젝트에서는 플러그인을 끈다.

### 5.4 adr

```yaml
name: adr
description: 되돌리기 비싼 기술·도메인 결정을 내렸거나 그 결정을 기록으로 남겨야 할 때, 기존 ADR을 승인하거나 대체할 때 사용한다. "ADR 써줘", "결정 기록", "ADR 승인", "ADR 대체" 같은 요청이 해당한다.
```

모드와 규율(0.3.0 adr 스킬에서 유지하는 것):

- **신규**
  - ADR로 쓸 결정인지부터 판단한다. 되돌리기 비싼가, 실제로 대안 중에서 골랐는가, 나중에 누군가 "왜?"라고 물을 것인가를 본다. 해당하지 않으면 쓰지 않고 이유를 말한다. 판단이 서지 않으면 쓴다.
  - 한 ADR에는 결정 하나만 담는다.
  - 한 번에 하나씩 묻는다: 제목(결정문), 문제 상황, 결정, 검토한 대안, 결과.
  - 검토한 대안은 실제로 검토된 것만 적는다. 기각 이유도 사용자에게서 받고, 지어내지 않는다.
  - 부정적 결과가 비어 있으면 한 번 더 묻는다.
  - 분량은 한 화면(40~60줄)이다.
  - 파일은 `docs/adr/yyyy-MM-dd-slug.md`이고, 상태는 `proposed`로 시작한다.
- **승인**: 확인받고 `proposed`를 `accepted`로 바꾼다.
- **대체**: 새 ADR은 `accepted`로 쓰고 `대체함:` 링크를 단다. 옛 ADR은 `superseded`로 바꾸고 `대체됨:` 링크를 단다. 옛 ADR 본문은 고치지 않고 머리만 고친다.
- **부분 조정**: 새 ADR 본문에 무엇을 조정하는지 적고, 옛 ADR 머리에 `조정됨:` 링크를 단다. 옛 ADR은 `accepted`로 둔다.
- 결정이 도메인 정의를 바꾸면 `/superdomain:domain`을 안내한다. DOMAIN.md 편집은 domain 스킬이 한다.

`adr-template.md`는 0.3.0 템플릿을 그대로 쓴다(제목=결정문, 상태·날짜·관련, 문제 상황, 결정, 근거와 검토한 대안 표, 결과: 긍정·부정·후속 작업). 여기에 상태 생명주기(proposed → accepted → superseded)를 짧게 덧붙인다.

## 6. 에이전트

공통:

- 읽기 전용이다. 작업 트리·인덱스·브랜치를 바꾸지 않고, git은 `diff`·`log`·`show`만 쓴다.
- `disallowedTools: Agent`로 다른 에이전트를 띄우지 않는다.
- 근거 없는 지적을 하지 않는다. 모든 지적에 위치(파일:줄 또는 DOMAIN.md 절)와 기준(가이드 절 또는 컨벤션 항목 이름)을 붙인다. 확신이 없으면 지적이 아니라 질문으로 남긴다.
- 지식 파일은 에이전트 본문의 `${CLAUDE_PLUGIN_ROOT}` 경로로 읽는다(공식 문서상 플러그인 에이전트 본문에서 치환된다). 검증(§9-3)에서 치환되지 않는 것으로 드러나면, 호출하는 스킬이 지식 파일의 절대 경로를 호출 프롬프트에 넣어 넘긴다. 스킬 본문에서는 `${CLAUDE_PLUGIN_ROOT}`·`${CLAUDE_SKILL_DIR}`가 치환된다.
- 출력 형식은 두 에이전트가 같다(review 스킬이 합칠 수 있도록).

````markdown
### 지적
#### Critical — 고치지 않으면 버그·데이터 손상·경계 붕괴로 이어진다
#### Important — `필수` 규칙 위반, 분명한 경계 신호
#### Minor — `지향` 미준수, 개선 제안
- `경로:줄` 무엇이 문제인가 — 기준: <가이드 절 / 컨벤션 항목> — 제안
### 질문
### 검토 범위
````

### 6.1 domain-reviewer

```yaml
name: domain-reviewer
description: 도메인 정의(docs/DOMAIN.md)나 코드 변경을 도메인 경계 관점에서 검토하는 읽기 전용 리뷰어. superdomain의 review·domain 스킬이 호출한다.
model: opus
tools: Read, Grep, Glob, Bash
disallowedTools: Agent
```

본문:

- 시작할 때 `${CLAUDE_PLUGIN_ROOT}/skills/domain/domain-guide.md`를 읽는다. 판단 기준은 이 파일이다.
- **정의 검토 모드**(domain 스킬이 호출): DOMAIN.md만 본다. 형식, 각 도메인 정의의 품질(역할이 한 문장인가, 기능이 역할 안에 있는가, 이름), 분리·병합 신호, 관계 표의 타당성을 본다.
- **변경 검토 모드**(review 스킬이 호출): DOMAIN.md의 "코드"로 파일을 도메인에 연결한 뒤 본다.
  - 변경된 코드가 맞는 도메인에 있는가
  - 새 도메인 간 의존(import·호출)이 관계 표에 있는가
  - 다른 도메인 객체를 직접 참조하는가, 도메인을 넘는 트랜잭션이 있는가, 두 도메인이 같은 테이블에 쓰는가, 다른 도메인의 용어가 새어 들어오는가
  - 이 변경이 도메인의 역할 밖 기능을 더하는가(너무 커지는 신호)
  - DOMAIN.md를 고쳐야 하는 변경인가(새 도메인이나 관계가 생김)
- **전체 점검 모드**: 위 항목에 더해 DOMAIN.md와 실제 구조의 어긋남(적힌 코드 위치가 없음, DOMAIN.md에 없는 도메인처럼 보이는 패키지)과 도메인별 크기·응집 신호를 본다.
- 보고하지 않는 것: 코딩 컨벤션(convention-reviewer의 몫), 스타일.
- 모듈이 다른 같은 이름의 모델은 DOMAIN.md "코드"에 따로 적혀 있으면 중복으로 지적하지 않는다.

### 6.2 convention-reviewer

```yaml
name: convention-reviewer
description: Kotlin·Java 코드를 superdomain 코딩 컨벤션 기준으로 검토하는 읽기 전용 리뷰어. superdomain의 review 스킬이 호출한다.
model: sonnet
tools: Read, Grep, Glob, Bash
disallowedTools: Agent
```

본문:

- 시작할 때 `${CLAUDE_PLUGIN_ROOT}/skills/conventions/conventions.md`를 읽는다.
- 대상 프로젝트의 CLAUDE.md(루트와 모듈)를 읽고, 컨벤션과 충돌하는 규칙은 프로젝트 규칙을 따른다.
- `docs/DOMAIN.md`가 있으면 분류와 코드 위치를 읽어 영속성 예외를 판단한다.
- 변경 검토 모드에서는 변경된 줄과 그 줄이 속한 선언만 본다. 변경 밖의 기존 위반은 보고하지 않는다.
- 전체 점검 모드에서는 도메인·application 패키지부터 읽고, 읽은 범위를 "검토 범위"에 적는다.
- 심각도: `필수` 위반은 Important, `지향` 미준수는 Minor다. 실제 결함으로 이어질 때만 Critical이다.
- 지적마다 컨벤션 항목 이름을 인용한다.

## 7. 지식 파일

### 7.1 `skills/domain/domain-guide.md` 초안

````markdown
# 도메인 가이드

`docs/DOMAIN.md`의 형식과, 도메인 경계를 긋고 검토하는 기준이다. domain 스킬과 domain-reviewer가 함께 읽는다.

## DOMAIN.md 형식

```markdown
# <제품명> 도메인

<제품이 무엇을 하는지 1~2문장>

## order — 주문
- 역할: 고객의 구매 요청을 받아 결제 완료까지의 상태를 관리한다
- 기능: 주문 생성, 주문 취소, 주문 내역 조회
- 분류: core
- 코드: order-api `com.acme.order`
- 규칙: 배송이 시작된 주문은 취소할 수 없다
- 하지 않는 것: 배송 추적 (→ delivery)

## 관계
| 도메인 | 의존 대상 | 방식 | 설명 |
|---|---|---|---|
| order | payment | 동기 호출 | 결제 승인을 요청한다 |
| delivery | order | 이벤트 | 결제 완료된 주문으로 배송을 만든다 |
```

- **제목**: `## <key> — <이름>`. key는 영문 소문자와 하이픈이고, 관계 표에서 쓴다.
- **역할**: 한 문장. 두 문장이 필요하면 도메인이 둘일 수 있다.
- **기능**: 이 도메인이 제공하는 일. 화면이나 API 목록이 아니다.
- **분류**: `core` · `supporting` · `generic` (아래 분류 기준).
- **코드**: 모듈과 패키지. 여러 모듈에 걸치면 모두 적고, 모듈마다 모델이 따로 있으면 그렇게 적는다(예: `core-api: 조회 모델, core-worker: 동기화 모델`).
- **규칙**(선택): 핵심 비즈니스 규칙 3~5개.
- **하지 않는 것**(선택): 헷갈리기 쉬운 이웃 책임과 그 책임을 맡는 도메인.
- **관계**: 한 쌍에 한 줄. 방식은 `ID 참조` · `동기 호출` · `이벤트` · `데이터 공유` 중 하나다. 데이터 공유(두 도메인이 같은 테이블에 씀)는 경계 문제의 신호다.
- 용어 정의는 쓰지 않는다(용어집의 몫).
- 도메인 맵(mermaid)은 선택이다. 쓴다면 관계 표를 원본으로 삼는다.

## 경계를 긋는 기준

위에 있는 기준이 우선한다.

1. **언어와 생명주기**: 같은 단어가 서로 다른 상태 전이를 가지면 다른 도메인이다. 필드 구성만 다르면 같은 도메인의 다른 뷰다.
   - 예: 판매의 주문(결제 완료 → 취소)과 물류의 주문(접수 → 출고)은 다른 도메인이다.
2. **데이터 소유**: 한 테이블에 쓰는 도메인은 하나다. 둘이 쓰면 경계를 다시 긋거나 한쪽을 읽기 전용으로 만든다.
3. **일관성**: 두 데이터가 잠시 어긋날 때 누가 무엇을 잘못하는지 구체적으로 나오면 같은 도메인에 둔다. 그렇지 않으면 나눠도 된다.
4. **변경 주체**: 변경마다 늘 두 팀의 승인이 필요하면 경계 후보다. 팀은 자주 바뀌므로 가장 약한 기준이다.

이렇게는 긋지 않는다.

- 실행 단위(api·batch·admin·worker)로 나누지 않는다. 같은 도메인을 드러내는 통로일 뿐이다.
- 테이블(엔티티) 하나마다 도메인 하나를 붙이지 않는다.
- "나중에 커질 것 같아서" 미리 나누지 않는다. 잘못 그은 경계를 지우는 것이 더 비싸다.

## 잘못 그은 경계의 신호

**너무 크다 (분리를 검토한다)**
- 역할을 한 문장으로 말할 수 없거나, 기능이 서로 무관한 묶음으로 갈린다.
- 한 도메인 안에서 같은 단어가 다른 생명주기를 가진다. 상태 필드가 여러 개인 엔티티가 신호다.
- 서로 다른 이유와 주기로 바뀌는 코드가 섞여 있다.

**너무 작다 (병합을 검토한다)**
- 규칙 없는 CRUD 하나뿐이다.
- 이웃 도메인과 늘 함께 바뀐다.
- 유스케이스 하나를 처리하는 데 경계를 세 번 이상 넘나든다.

**관계가 어긋난다**
- 관계 표에 없는 의존(import·호출)이 있다.
- 다른 도메인의 객체를 필드로 직접 참조한다(ID로 참조해야 한다).
- 한 트랜잭션 안에서 두 도메인의 저장소를 쓴다.
- 두 도메인이 같은 테이블에 쓴다.
- 다른 도메인의 용어와 타입이 이 도메인의 모델에 새어 들어온다.
- 도메인 사이에 순환 의존이 있다.

**이름이 도메인 용어가 아니다**
- `common`·`util`·`core`·`etc`, 팀 이름, 실행 단위 이름. 도메인 이름을 붙일 수 없다면 도메인 경계가 아니다.

## 분류 기준

1. "경쟁사와 똑같이 만들면 무엇을 잃는가"에 구체적인 답이 나오면 **core**다.
2. 아니고, 요구의 80% 이상을 채우는 상용·오픈소스 제품 이름을 댈 수 있으며, 실패 비용(1시간 중단, 한 달간 조용히 틀린 데이터)이 낮으면 **generic**이다.
3. 그 밖은 **supporting**이다. 애매하면 supporting이다.

변경이 잦다는 이유만으로 core가 되지는 않는다.

분류는 코딩 컨벤션을 얼마나 엄격하게 적용할지 정한다. core·supporting에는 순수 도메인 모델과 컨벤션을 전부 적용하고, generic은 JPA 엔티티를 직접 써도 된다.

## 같은 이름, 다른 모델

모듈마다 책임이 다르면 같은 이름의 모델이 따로 있을 수 있다(조회 모듈의 `Player`와 동기화 모듈의 `Player`). DOMAIN.md의 "코드"에 그렇게 적혀 있으면 중복이 아니다.

**통합 기준**: 사본이 서로 어긋나면 곧 버그가 되는 비즈니스 규칙(예: 비율 계산의 분모)만 한곳으로 모은다. 우연히 닮은 코드는 중복을 유지하고 각각 테스트로 고정한다.
````

### 7.2 `skills/conventions/conventions.md` 초안

````markdown
# 코딩 컨벤션

도메인 로직이 드러나고 테스트하기 쉬운 코드를 쓰기 위한 규칙이다. conventions 스킬과 convention-reviewer가 함께 읽는다.

- 적용 범위: Kotlin·Java, Spring, JPA.
- 대상 프로젝트의 CLAUDE.md나 문서에 다른 규칙이 있으면 그 규칙이 우선한다.
- `필수`는 벗어날 때 이유가 있어야 하고, `지향`은 가능한 한 따른다.
- 도메인 로직이 중요한 곳(DOMAIN.md 분류 core·supporting)에는 전부 적용한다. 분류가 generic인 도메인, 그리고 어드민·워커·배치처럼 도메인 로직이 얇은 곳은 「JPA는 인프라에 둔다」의 예외를 쓸 수 있다.

## 값은 타입으로 표현한다 `지향`
문자열·원시 타입 대신 의미 있는 타입을 쓴다. 단일 값은 `value class`로 감싸고 생성할 때 검증한다. 여러 값과 행위가 함께 다니면 data class로, 컬렉션에 붙는 로직은 일급 컬렉션으로 모은다.
- 이유: 잘못된 값이 생성 시점에 막히고, 타입이 곧 문서가 된다.

```kotlin
@JvmInline
value class Email(val value: String) {
    init { require("@" in value) { "invalid email: $value" } }
}
```

## 도메인 행위는 canXxx()로 실행 조건을 드러낸다 `지향`
실행 조건이 있는 행위는 그 조건을 `canXxx(): Boolean`으로 공개하고, `xxx()`는 시작할 때 `check(canXxx())`로 스스로를 지킨다. `Xxx`에는 도메인 동사를 쓴다(`canCancel()`/`cancel()`).
- 이유: 검증 로직이 도메인 안에 있으면서도 밖에서 물어볼 수 있다. application은 `canXxx()`로 먼저 확인하고 비즈니스 예외를 던진다(→ 「도메인은 표준 예외만 던진다」).

```kotlin
data class Order(val status: OrderStatus) {
    fun canCancel(): Boolean = status == OrderStatus.PAID

    fun cancel(): Order {
        check(canCancel()) { "cannot cancel order in $status" }
        return copy(status = OrderStatus.CANCELED)
    }
}
```

## 도메인 모델은 불변을 기본으로 한다 `지향`
도메인 모델의 필드는 `val`로 두고, 상태를 바꾸는 행위는 새 객체를 반환한다(`copy`).
- 예외: JPA 엔티티를 도메인으로 직접 쓰는 곳(→ 「JPA는 인프라에 둔다」).

## 계산은 도메인, 조회는 리포지토리 `필수`
DB에서 가져오는 일은 리포지토리가 맡고, 가져온 값으로 계산·집계·판단하는 일은 도메인 객체(`create()` 같은 팩토리 포함)가 맡는다. 서비스는 둘을 잇기만 한다.
- 이유: 도메인 로직이 한곳에 모이고, DB 없이 단위 테스트할 수 있다.

```kotlin
val rows = matchRepository.findAll(period)      // 조회
val stats = WinRateStatistics.create(rows)      // 계산
```

## 다른 도메인은 ID로 참조한다 `필수`
도메인 객체는 다른 도메인의 객체를 필드로 들지 않고 ID(가능하면 값 타입)로 참조한다. 여러 도메인의 데이터를 조합해야 하면 application 계층에서 조합한다.
- 이유: 도메인 경계가 코드에서도 유지되고, 한 도메인의 변경이 다른 도메인 모델로 번지지 않는다.

## 자명하지 않은 규칙은 KDoc으로 남긴다 `지향`
집계 규칙, 정합성 제약, "왜 이렇게 하지 않았는지" 같은 결정은 클래스·메서드 KDoc에 이유와 함께 남긴다. 코드가 무엇을 하는지는 쓰지 않는다.

## 도메인은 표준 예외만 던진다 `필수`
도메인 객체는 `require`·`check`·`error` 같은 표준 예외만 쓴다. 에러 코드를 담은 비즈니스 예외(`CoreException` 등)는 application 계층(서비스, application 리포지토리)이 `canXxx()`로 먼저 확인한 뒤 던진다.
- 이유: 도메인은 응답 규칙을 몰라도 되고, 도메인 안의 예외는 "확인 없이 호출했다"는 프로그래밍 오류 신호로 남는다.

```kotlin
// application
if (!order.canCancel()) throw CoreException(ErrorType.ORDER_NOT_CANCELABLE)
orderRepository.save(order.cancel())
```

## DB가 필요한 검증은 판정 객체로 모은다 `지향`
검증에 DB의 사실(데이터가 있는지 등)이 필요할 때는 이렇게 한다.
- 사실 하나면 리포지토리의 boolean 조회로 충분하다(`isDeleted(id)`).
- 여러 사실이 조합된 규칙이면, 리포지토리가 사실을 담은 도메인 객체 `XxxEligibility`를 만들어 돌려주고 판정은 그 객체가 한다. application은 판정 결과를 보고 비즈니스 예외를 던진다.
- 이유: 규칙이 도메인 객체에 남아 DB 없이 테스트할 수 있다.
- 이름: `Condition`(Spring·검색 조건), `Validation`(Bean Validation), `Specification`(Spring Data JPA)은 기존 개념과 겹치므로 쓰지 않는다.

```kotlin
class PublishEligibility(
    private val hasActiveListing: Boolean,
    private val isSellerBlocked: Boolean,
) {
    fun isEligible(): Boolean = !hasActiveListing && !isSellerBlocked
}
```

## 현재 시각은 Clock에서 얻는다 `필수`
인자 없는 `now()`를 쓰지 않고, 주입받은 `Clock`에서 얻는다(`clock.instant()`, `LocalDateTime.now(clock)`). 도메인 메서드는 `Clock` 대신 `now`를 인자로 받는 것을 지향한다.
- 이유: 테스트에서 시간을 고정할 수 있고, 도메인이 시간의 출처에 의존하지 않는다.
- 테스트: `Clock`은 모킹하지 않고 `Clock.fixed(...)`를 쓴다.
- 예외: 감사용 생성·수정 시각(`@CreationTimestamp` 등).

```kotlin
fun canRenew(now: Instant): Boolean = ...     // 도메인
renewal.canRenew(clock.instant())             // application
```

## 정적 호출은 컴포넌트로 감싼다 `필수`
`UUID.randomUUID()`나 `Random`처럼 결과가 매번 달라지는 정적 호출은 컴포넌트로 감싸 주입받는다. 반환값은 문자열보다 타입(`UUID`)으로 둔다.
- 이유: 테스트에서 값을 고정할 수 있다.
- 테스트: 모킹하지 않고, 감싼 컴포넌트를 상속해 고정 값을 돌려주는 가짜로 바꿔 끼운다(Kotlin은 `kotlin("plugin.spring")`이 `@Component` 클래스를 열어 두므로 상속할 수 있다).

```kotlin
@Component
class UuidHolder {
    fun random(): UUID = UUID.randomUUID()
}
```

## JPA는 인프라에 둔다 `필수`
도메인 모델은 JPA에 의존하지 않는 순수 Kotlin·Java 클래스로 둔다. JPA 엔티티와 도메인 모델 사이의 변환은 application 계층의 리포지토리가 맡고, 서비스는 JPA 리포지토리를 직접 쓰지 않는다.
- 이유: 도메인 로직이 영속 기술의 제약(기본 생성자, 가변 필드, 지연 로딩)에 끌려가지 않는다.
- 예외: 도메인 로직이 얇은 곳(분류가 generic인 도메인, 어드민·워커·배치)은 JPA 엔티티를 직접 써도 된다.

## JPA 클래스 이름 `필수`

| 대상 | 이름 |
|---|---|
| 엔티티 | `XxxEntity` |
| Spring Data 리포지토리 | `XxxJpaRepository` (커스텀: `XxxJpaRepositoryCustom`, 구현: `XxxJpaRepositoryCustomImpl`) |
| `@Embeddable` 값 | `XxxEmbedded` |
| 조회 전용 결과 | `XxxProjection` |

## 외부 자원은 인터페이스 뒤에 둔다 `필수`
외부 API, 메시지 큐, 파일 저장소, 알림 같은 외부 자원은 application 계층에 인터페이스를 두고, 구현은 infrastructure에 둔다.
- 이유: application 코드가 특정 기술에 묶이지 않고, 테스트에서는 이 인터페이스만 대역으로 바꾸면 된다.

```kotlin
interface OrderEventPublisher { fun publish(event: OrderPaid) }     // application
class SqsOrderEventPublisher(...) : OrderEventPublisher { ... }     // infrastructure
```

## 모킹은 외부 자원에만 쓴다 `필수`
외부 자원(HTTP 클라이언트, DB, 메시지 큐 등)만 모킹한다. 도메인 객체와 내부 컴포넌트는 실제 객체를 쓰고, 값을 고정해야 하는 컴포넌트는 `Clock.fixed`나 상속한 가짜로 바꿔 끼운다.
- 이유: 모킹이 많을수록 테스트가 구현에 묶여 리팩터링 때 깨지고, 실제 동작은 검증하지 못한다.
- DB는 모킹할 수 있지만, application 리포지토리는 실제 DB로 검증하는 것을 지향한다. 모킹(stub-and-verify)은 호출만 검증하므로 실제 동작과 어긋날 수 있다.
- 예외: 컨트롤러 슬라이스 테스트는 application 계층을 모킹해도 된다.
````

## 8. 이행과 문서

### CHANGELOG 0.4.0 (Breaking)

바뀐 점을 요약하고, 0.3.x 프로젝트를 옮기는 절차를 적는다.

1. `git mv docs/superdomain/DOMAIN.md docs/DOMAIN.md`
2. `/superdomain:domain`으로 새 형식으로 다시 쓴다. 옛 `contexts/*.md`의 불변식 중 핵심은 도메인의 "규칙"으로 옮긴다.
3. `git mv docs/superdomain/adr docs/adr`. ADR 안의 `../DOMAIN.md` 링크는 옮긴 뒤에도 그대로 맞는다.
4. `docs/superdomain/`의 나머지(`summary.md`, `contexts/`, `state/`, `conventions/`)를 지운다. `conventions/`의 팀 규약은 프로젝트 CLAUDE.md로 옮긴다.
5. CLAUDE.md 등에서 `docs/superdomain/`을 가리키는 참조를 고친다.

### README

소개, 설치, 스킬 넷(언제 쓰는지), 에이전트 둘(모델), 대상 프로젝트에 생기는 파일, 0.3.x에서 옮기기(CHANGELOG 링크), 로컬 개발 순서로 새로 쓴다.

## 9. 검증

스크립트와 테스트가 없으므로 구현 후 직접 확인한다.

1. `plugin.json`·`marketplace.json`이 JSON으로 읽히고, 모든 SKILL.md와 에이전트 파일의 frontmatter가 YAML로 읽힌다.
2. `claude --plugin-dir .`로 띄워 스킬 넷(`/superdomain:domain`, `review`, `adr`, `conventions`)과 에이전트 둘이 잡히는지 확인한다.
3. 에이전트가 `${CLAUDE_PLUGIN_ROOT}` 경로의 지식 파일을 실제로 읽는지, 지정한 모델로 도는지 확인한다.
4. `conventions` 스킬의 `paths`가 Kotlin·Java 파일을 다룰 때만 걸리는지 확인한다.
5. imstargg의 최근 커밋 범위로 `/superdomain:review`를 돌려, 두 리뷰어가 병렬로 돌고 한 리포트로 합쳐지는지 본다(읽기 전용).
6. 빈 연습 저장소에서 `/superdomain:domain`으로 DOMAIN.md를 만들어 보고, 정의 검토 모드가 도는지 본다.
7. 저장소에서 옛 흔적(`check_imports`, `parse_domain`, `summary.md`, `docs/superdomain`, `references/`, 없어진 스킬 이름)을 grep해 0건인지 확인한다. CHANGELOG의 이행 안내는 제외한다.
