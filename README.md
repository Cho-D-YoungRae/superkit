# superkit

Claude Code 플러그인 모음이자 마켓플레이스.

| 플러그인 | 하는 일 |
|---|---|
| [superdomain](plugins/superdomain) | 도메인 정의(DOMAIN.md), 도메인·코딩 컨벤션 리뷰, ADR로 도메인 로직이 드러나는 코드를 돕는다 |
| [superglossary](plugins/superglossary) | 프로젝트별 용어사전을 관리하고 일관된 용어 사용을 돕는다 |
| [infra](plugins/infra) | 인프라 하네스(인벤토리·변경기록·직접 제어)를 구성하고 운영한다 |
| [superrelease](plugins/superrelease) | 프로젝트를 분석해 그 프로젝트 전용 릴리스 툴킷을 저장소에 만들어 준다 |
| [llm-wiki](plugins/llm-wiki) | LLM이 유지보수하는 개인 위키 — 위키 부트스트래핑과 소스 추출 툴벨트 |

## 설치

Claude Code 세션 안에서 마켓플레이스를 한 번 추가하고, 필요한 플러그인만 설치한다.

```
/plugin marketplace add Cho-D-YoungRae/superkit
/plugin install superdomain@superkit
/plugin install superglossary@superkit
/plugin install infra@superkit
/plugin install superrelease@superkit
/plugin install llm-wiki@superkit
```

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
