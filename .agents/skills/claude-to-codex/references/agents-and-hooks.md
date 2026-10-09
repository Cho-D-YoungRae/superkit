# 에이전트·훅·권한 전환

확인일: 2026-10-09. 본문의 필드와 예는 이 날짜의 문서 기준이다. 대상 클라이언트에서 실제 노출되는 도구와 설정을 다시 확인한다.

## 에이전트는 프롬프트와 실행 계약을 함께 옮긴다

원본: [Claude subagents](https://code.claude.com/docs/en/sub-agents).
대상: [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents).

원본에서 역할 지침 외에 도구 집합, 상속/고정 모델, preload 스킬, 컨텍스트 전달, memory, 격리 worktree, background, 최대 턴, MCP, hook을 조사한다. Claude의 plugin agent는 일부 필드(`hooks`, `mcpServers`, `permissionMode`)를 무시하므로 선언과 실제 원본 동작을 구별한다.

Codex의 프로젝트/개인 custom agent는 `.codex/agents/` 또는 `~/.codex/agents/`의 TOML 파일이다. 현재 필수 필드는 `name`, `description`, `developer_instructions`다. **이것은 플러그인의 `agents/*.md`나 패키지 안의 `.codex/agents/`를 설치만 하면 자동 등록한다는 근거가 아니다.**

플러그인을 자립적으로 배포할 때는 다음을 기준으로 고른다:

1. **패키지 내부 역할 문서 + 위임하는 스킬**: 역할을 스킬의 `references/`에 두고, 호출자가 실제 서브에이전트 도구에 역할 지침과 입력·출력 계약을 전달한다. 해당 역할을 자동 등록된 `agent_type`처럼 호출하지 않는다.
2. **프로젝트에 설치하는 custom agent**: 도구 강제·설정이 필요한 경우 확인된 TOML 설정을 패키지 자산으로 제공한다. 셋업 스킬이 대상 프로젝트의 기존 파일과 충돌을 점검한 뒤 배치하고, 실제 발견·선택·권한 적용을 검증한다. 전환 작업 자체에서 개인 설정에 설치하지 않는다.

호출자가 전달할 계약:

```text
역할: 패키지에 포함된 리뷰 지침
입력: 프로젝트 루트, 기준 문서, 대상 파일/변경 범위
컨텍스트: 원본이 요구하는 새 컨텍스트 또는 대화 전달 범위
행동 범위: 읽기/쓰기 경로, 외부 작업 범위, 추가 위임 가능 여부
출력: 근거 위치와 판정, 검토 범위, 불확실성
```

기본값이 대화 전체 복사인 도구도 있다. 별도 컨텍스트가 목적이라면 현재 도구의 인자를 확인해 필요한 자료만 전달한다. 격리된 컨텍스트와 격리된 파일시스템/worktree는 별개다. 서로의 결과를 보지 않는 독립 리뷰를 순차적인 자기 검토로 바꾸고 동등하다고 주장하지 않는다.

모델 `opus`·`sonnet`·`haiku`를 임의의 GPT 이름과 고정 대응시키지 않는다. 역할에 필요한 능력과 비용 선호를 확인하고, 별도의 요구가 없으면 현재 세션의 모델 상속을 사용하며 차이를 기록한다. 원본 frontmatter에 모델 이름이 있다는 사실만으로 특정 제공자/모델의 동일성이 필수라고 간주하거나 실행을 차단하지 않는다. 사용자가 특정 모델·기능 보존을 명시했거나 원본 기능이 그 모델에 의존할 때 대응 선택을 결정한다. 모델 설정과 reasoning effort의 호환성도 확인한다.

`tools`·`disallowedTools`를 프롬프트로 옮기면 강제력이 달라진다. Codex custom agent의 sandbox 등은 후보이지만 원본과 같은 도구 집합을 강제하는지는 별도 확인한다. 필요한 강제가 제공되지 않으면 그 차이를 기록하고, 핵심 안전 조건이면 해당 경로를 완료 처리하지 않는다. 서브에이전트를 쓸 수 없는 환경에서는 필수 격리/독립성이 유지되는 지원 경로를 안내한다.

## 훅은 이벤트 이름만 맞추지 않는다

원본: [Claude hooks](https://code.claude.com/docs/en/hooks).
대상: [Codex hooks](https://learn.chatgpt.com/docs/hooks).
배포 제한: [Codex 패키징](https://developers.openai.com/plugins/build/plugins#bundled-mcp-servers-and-lifecycle-hooks).

현재 패키징 문서는 훅을 **Codex 데스크톱 수동 설치**에서 지원하고 공개 디렉터리 제출에서는 제외하도록 한다. 클라우드·CLI 등 다른 표면에 같은 보장을 확장하지 않는다. 이벤트 문서에 훅이 있어도 패키지 전달 경로의 지원과 신뢰 절차가 충족되어야 한다.

훅마다 비교할 항목:

| 항목 | 검증할 것 |
|---|---|
| 발생 시점 | 이벤트 지원, matcher 대상, 성공/실패/중단/백그라운드 종료 시점 |
| 입력 | 실제 stdin JSON, 정규화된 도구 이름, 명령 필드, cwd |
| 출력 | stdout JSON·stderr·exit code가 문맥 추가, 거절, 실행 중단 중 무엇을 하는가 |
| 활성화 | 선언 위치, 기본 파일 발견, 중복 로드, 사용자 신뢰 필요 여부 |
| 실패 | 원본의 실패 시 차단/비차단 동작과 timeout이 보존되는가 |

현재 Codex의 shell/unified exec 훅은 `Bash`로 매칭하고 `tool_input.command`를 사용한다. `apply_patch`는 `Edit`/`Write` alias로도 매칭된다. 따라서 `Bash`라는 문자열만 보고 무조건 재작성하지 않는다. 실제 입력/출력 fixture로 검사한다.

`PostToolUse` 피드백은 이미 실행한 부작용을 되돌리지 않는다. `PreToolUse`도 모든 실행 경로의 완전한 보안 경계로 가정하지 않는다. handler 종류·각 이벤트별 지원 출력은 최신 문서로 확인한다.

플러그인 훅에는 `PLUGIN_ROOT`/`PLUGIN_DATA` 및 Claude 호환 변수가 제공된다. 이는 일반 스킬에서 실행한 모든 셸 명령의 환경변수 보장이 아니다.

훅을 제공하지 않는 전환본은 원본 `hooks/hooks.json`을 무심코 복사해 기본 탐색으로 실행되게 하지 않는다. 선택한 manifest 형식에서 훅 설정을 명시적으로 비우거나 해당 파일을 배포에서 제외한다. 자동 리마인더를 스킬 내 수동 단계로 대체하면 자동성이 달라졌다는 사실을 보고한다. 필수 차단 훅을 단순 경고로 약화시키지 않는다.

## 권한·프로젝트 설정

Claude `.claude/settings*.json`의 allow/deny, permission mode, MCP 설정이 Codex에 그대로 적용되지는 않는다. 데이터 형식, 실행 권한, 모델의 행동 지침을 각각 구분한다.

- 읽기 금지 경로를 지침에 적었다는 사실만으로 sandbox에서 읽기가 차단되었다고 보고하지 않는다.
- 원본이 생성하는 보호 설정뿐 아니라 그 설정을 점검하는 audit 코드도 전환한다.
- 부모의 현재 권한/샌드박스와 실제 대상 세션의 제한을 확인한다. 에이전트 템플릿만 보고 적용되었다고 판정하지 않는다.
- 값 대신 자격증명 위치·참조 방식만 보존한다. 네트워크·시크릿·실제 인프라 없이도 가능한 fixture 검증을 우선한다.
