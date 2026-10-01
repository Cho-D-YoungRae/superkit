# superdomain

도메인 로직이 드러나는 코드를 돕는 Claude Code 플러그인.

- 도메인마다 역할·기능·관계를 `docs/superdomain/DOMAIN.md` 한 파일에 정의한다.
- 외부 시스템과 맞닿은 도메인을 구분해 외부의 복잡성을 가두고, 도메인 사이 의존을 한 방향으로 유지한다.
- 변경이 도메인 정의와 코딩 컨벤션을 따르는지 리뷰한다.
- 비싸거나 중요한 결정을 ADR로 남기고, 작업을 마칠 때 기록할 결정이 있으면 제안한다.

아키텍처를 문서로 정하지 않는다. 대신 코드가 권장 방식(코딩 컨벤션)을 따르는지 리뷰로 확인한다. 스크립트가 없어서 Claude Code 말고는 설치할 것이 없다.

## 설치

Claude Code 세션 안에서:

```
/plugin marketplace add Cho-D-YoungRae/superdomain
/plugin install superdomain@superdomain
```

터미널에서:

```bash
claude plugin marketplace add Cho-D-YoungRae/superdomain
```

```bash
claude plugin install superdomain@superdomain
```

## 스킬

| 스킬 | 언제 쓰나 |
|---|---|
| `/superdomain:domain` | 도메인을 처음 정의하거나, 도메인을 추가·분리·병합하거나, 역할·관계를 바꿀 때 |
| `/superdomain:review` | 커밋·PR 전에 변경이 도메인 정의와 코딩 컨벤션을 따르는지 볼 때, 도메인이 너무 커지지 않았는지 점검할 때 |
| `/superdomain:adr` | 비싸거나 중요한 결정을 기록하거나, ADR을 승인·대체할 때. 작업을 마칠 때 기록할 결정이 있으면 먼저 제안한다 |
| `/superdomain:conventions` | Kotlin·Java 코드를 쓸 때 코딩 컨벤션을 적용한다. `.kt`·`.java` 작업에서 자동으로 걸린다 |

`review`의 인자는 `[domain|code] [경로 | 커밋 범위 | 전체]`다. 인자가 없으면 현재 브랜치의 변경과 커밋하지 않은 변경을 두 관점으로 모두 본다.

## 에이전트

| 에이전트 | 모델 | 하는 일 |
|---|---|---|
| `domain-reviewer` | opus | 도메인 정의와 코드를 도메인 경계 관점에서 검토한다. domain·review 스킬이 호출한다 |
| `convention-reviewer` | sonnet | Kotlin·Java 코드를 코딩 컨벤션 기준으로 검토한다. review 스킬이 호출한다 |

둘 다 읽기 전용이고, 모델은 에이전트 파일에서만 정한다.

## 대상 프로젝트에 생기는 파일

| 경로 | 무엇 |
|---|---|
| `docs/superdomain/DOMAIN.md` | 도메인별 역할·기능·분류·코드 위치(선택: 개념·외부 접점·규칙·미정)와 도메인 간 관계 |
| `docs/superdomain/adr/yyyy-MM-dd-slug.md` | 결정 기록 |

`domain`·`adr` 스킬은 동의를 받아 대상 CLAUDE.md에 두 경로를 가리키는 포인터 줄을 추가할 수 있다. ADR 줄이 있으면 Claude가 작업을 마칠 때 기록할 결정이 있었는지 돌아보고 제안한다.

## 언어 범위

도메인 정의·도메인 리뷰·ADR은 언어와 무관하다. 코딩 컨벤션과 컨벤션 리뷰는 Kotlin·Java(Spring·JPA) 전용이다. 대상 프로젝트의 CLAUDE.md에 다른 규칙이 있으면 그 규칙이 우선한다. 컨벤션이 맞지 않는 프로젝트에서는 그 프로젝트에서 플러그인을 끈다.

## 이전 버전에서 올라왔다면

0.3.x에서 올라오면 파일 위치는 그대로이고 DOMAIN.md를 새 형식으로 다시 쓴다. 0.4.0 배치(`docs/DOMAIN.md`·`docs/adr/`)에서 올라오면 두 경로를 `docs/superdomain/` 아래로 옮긴다. 자세한 절차는 [CHANGELOG](CHANGELOG.md)의 0.4.1 이행 절차에 있다.

## 저장소 구조

```
.claude-plugin/          plugin.json, marketplace.json — 이 저장소가 플러그인이자 마켓플레이스다
skills/
  domain/                SKILL.md, domain-guide.md (DOMAIN.md 형식과 경계·분류 판단 기준)
  review/                SKILL.md
  adr/                   SKILL.md, adr-template.md
  conventions/           SKILL.md, conventions.md (코딩 컨벤션)
agents/                  domain-reviewer.md, convention-reviewer.md
docs/superpowers/        설계 스펙과 구현 계획
```

지식 파일(`domain-guide.md`, `conventions.md`)은 주제마다 하나이고, 해당 스킬과 리뷰 에이전트가 같은 파일을 읽는다.

## 로컬 개발

```bash
claude --plugin-dir /path/to/superdomain
```

스킬은 `/superdomain:<스킬명>`으로 노출된다. SKILL.md를 포함해 플러그인 파일을 고쳤다면 `/reload-plugins`로 반영한다.

구조 검증:

```bash
claude plugin validate --strict .claude-plugin/plugin.json
```

```bash
claude plugin validate --strict .claude-plugin/marketplace.json
```

```bash
claude plugin validate --strict skills
```

```bash
claude plugin validate --strict agents
```
