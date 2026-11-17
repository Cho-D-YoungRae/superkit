# superkit

Claude Code 플러그인과 그 Codex 지원을 관리하는 플러그인 모음이자 마켓플레이스.

| 플러그인 | 하는 일 |
|---|---|
| [superdomain](plugins/superdomain) | 도메인 정의(DOMAIN.md), 도메인·코딩 컨벤션 리뷰, ADR로 도메인 로직이 드러나는 코드를 돕는다 |
| [superglossary](plugins/superglossary) | 프로젝트별 용어사전을 관리하고 일관된 용어 사용을 돕는다 |
| [infra](plugins/infra) | 인프라 하네스(인벤토리·변경기록·직접 제어)를 구성하고 운영한다 |
| [superrelease](plugins/superrelease) | 프로젝트를 분석해 그 프로젝트 전용 릴리스 툴킷을 저장소에 만들어 준다 |
| [llm-wiki](plugins/llm-wiki) | LLM이 유지보수하는 개인 위키 — 위키 부트스트래핑과 소스 추출 툴벨트 |
| [clean-code](plugins/clean-code) | 『Clean Code』의 원칙을 챕터별 레퍼런스로 담아, 코드를 쓰고 리팩터링하고 리뷰할 때 적용하게 한다 |
| [pstack](plugins/pstack) | poteto(Lauren Tan)의 pstack — 깊게 파고 적게 쓰는 엄격한 에이전트 워크플로. upstream(cursor/plugins)을 그대로 옮기고 Codex 어댑터를 더했다 |

플러그인은 `plugins/<이름>/`에 둔다. [superdomain](plugins/superdomain)·[superglossary](plugins/superglossary)·[llm-wiki](plugins/llm-wiki)·[pstack](plugins/pstack)은 같은 폴더를 Claude Code와 Codex가 함께 쓴다. 따로 두던 Codex 전환본(`plugins/<이름>-codex/`)은 모두 공용 폴더로 합쳤고, 그 전환 기록은 `porting/<이름>/`에 이력으로 남아 있다.

## 설치

### Codex

저장소의 `.agents/plugins/marketplace.json`에는 공용 플러그인 넷이 있다. 설치 ID는 `superdomain@superkit`(`plugins/superdomain/`), `superglossary@superkit`(`plugins/superglossary/`), `llm-wiki@superkit`(`plugins/llm-wiki/`), `pstack@superkit`(`plugins/pstack/`)이다.

이 저장소를 프로젝트로 연 뒤 데스크톱 앱을 다시 시작하고, Plugins Directory의 **superkit for Codex** 소스에서 필요한 플러그인을 설치한다. CLI에서는 `codex plugin marketplace add Cho-D-YoungRae/superkit` 뒤 `codex plugin add <이름>@superkit`으로 설치한다. 카탈로그 등록은 자동 설치나 활성화를 의미하지 않는다. 프로젝트별 Git 소스 설정과 superglossary의 Codex 차이는 [superglossary 안내](plugins/superglossary/README.md#codex에서-쓰기)를, superdomain의 Codex 차이는 [superdomain 안내](plugins/superdomain/README.md#codex에서-쓰기)를, llm-wiki의 Codex 샌드박스 설정은 [llm-wiki 안내](plugins/llm-wiki/README.md#codex에서-쓰기)를, pstack이 Cursor 이름을 Codex에 맞추는 방식은 [pstack Codex 어댑터](plugins/pstack/docs/harness/codex.md)를 본다. 실제 모델의 문서 생성·리뷰 동작은 설치 후 별도로 검증한다.

### Claude Code

Claude Code 세션 안에서 마켓플레이스를 한 번 추가하고, 필요한 플러그인만 설치한다.

```
/plugin marketplace add Cho-D-YoungRae/superkit
/plugin install superdomain@superkit
/plugin install superglossary@superkit
/plugin install infra@superkit
/plugin install superrelease@superkit
/plugin install llm-wiki@superkit
/plugin install clean-code@superkit
/plugin install pstack@superkit
```

pstack은 upstream 마켓플레이스(`pstack@cursor-plugins`)에도 있다. 둘 다 설치하면 같은 `/pstack:*` 명령과 `~/.claude/rules/pstack-models.md`를 함께 쓰므로 하나만 켠다.

터미널에서:

```bash
claude plugin marketplace add Cho-D-YoungRae/superkit
```

```bash
claude plugin install superglossary@superkit
```

업데이트를 자동으로 받으려면 `/plugin` → **Marketplaces** → `superkit` → **Enable auto-update**를 켠다.

### 예전 저장소에서 옮겨 오는 경우

superdomain·superglossary·superrelease·llm-wiki는 원래 저장소마다 마켓플레이스가 따로 있었다(`superdomain@superdomain`, `superglossary@superglossary`, `superrelease@superrelease`, `llm-wiki@llm-wiki`). 옛 마켓플레이스를 지우면 그 플러그인도 함께 제거되므로, 지운 뒤 위 명령으로 다시 설치한다.

```bash
claude plugin marketplace remove superdomain
```

```bash
claude plugin marketplace remove superglossary
```

프로젝트 `.claude/settings.json`의 `enabledPlugins`에 옛 ID가 있으면 `<이름>@superkit`으로 바꾼다.

## 지침 파일

플러그인은 사용자 프로젝트의 지침 파일로 `AGENTS.md`를 쓴다. 프로젝트에 `CLAUDE.md`가 있으면 Claude Code가 기본 설정에서 `AGENTS.md`를 읽지 않으므로, 그런 프로젝트에서는 `CLAUDE.md`를 쓴다.

## 기여

브랜치 전략·커밋 규칙·릴리즈 절차는 [CONTRIBUTING.md](CONTRIBUTING.md)를, 저장소 구조와 작업 규칙은 [AGENTS.md](AGENTS.md)를 본다.

## 라이선스

[MIT](LICENSE)
