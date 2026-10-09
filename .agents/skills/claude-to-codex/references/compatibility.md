# 전환 판단표

확인일: 2026-10-09. 아래는 전환 설계의 출발점이다. 사용 중인 클라이언트와 배포 경로에 적용되는 최신 문서를 확인한다. 공식 문서의 공개 제출 제약을 로컬 실행 제약으로 일반화하지 않는다.

## 패키징과 배포

[Claude 매니페스트](https://code.claude.com/docs/en/plugins-reference)와 [Codex 패키징](https://developers.openai.com/plugins/build/plugins)을 대조한다.

| 대상 | 전환 결정 |
|---|---|
| `.claude-plugin/plugin.json` | 새 Codex 패키지는 루트 `plugin.json`과 Agent Plugins 스키마를 우선한다. 기존 `.codex-plugin/plugin.json`도 지원되는 호환 형식이다. |
| 커스텀 컴포넌트 경로·인라인 선언 | 매니페스트와 기본 위치의 결합 규칙을 확인한 뒤 실제 배포 대상을 수집한다. 기본 `skills/`만 복사하면 빠질 수 있다. |
| Codex 확장 | portable 형식에서는 `extensions.com.openai`에 둔다. 이 객체와 `.codex-plugin/plugin.json` overlay는 병합되지 않으므로 두 곳에 설정을 나눠 쓰지 않는다. |
| 카탈로그 | 요청 시 `.agents/plugins/marketplace.json`에 대상 패키지를 등록한다. `source.path`의 기준은 마켓플레이스 루트다. 기존 항목·정책을 보존한다. |
| 리소스 경로 | 매니페스트 경로는 패키지 루트 기준 `./`로 시작하고 내부에 머물러야 한다. 스킬 문서의 상대 링크 기준과 혼동하지 않는다. |

실제로 존재하는 정보만 manifest에 넣는다. URL·저자·로고·인증 요구를 발명하지 않는다. 패키지 이름은 기존 설치 ID와 호출 관계를 고려해 유지한다.

[공식 Claude 플러그인 전환 가이드](https://developers.openai.com/plugins/guides/submit-claude-plugin)는 **공개 제출**도 다룬다. 그 경로에서는 commands·agents의 재사용 동작을 skills로 옮기며, hooks를 포함한 공개 제출은 허용되지 않는다. 로컬 데스크톱 수동 설치는 별도로 판단한다. MCP 없는 제출에서 MCP 설정을 제외한다는 지침을 로컬 MCP 미지원으로 읽지 않는다.

## 스킬과 명령

원본 의미: [Claude skills](https://code.claude.com/docs/en/skills). 대상 계약: [Codex skills](https://learn.chatgpt.com/docs/build-skills).

| Claude 요소 | 보존할 의미와 Codex 처리 |
|---|---|
| `SKILL.md`, references, scripts, assets | 업무 내용과 필요한 파일을 유지한다. Codex용 `name`·`description`을 채운다. |
| `commands/*.md` | 사용자 작업 단위의 `skills/<name>/SKILL.md`로 옮긴다. 같은 이름의 기존 스킬과 충돌하면 호출 관계를 확인한다. |
| `disable-model-invocation: true` | 기존 명시적 호출 정책을 `agents/openai.yaml`의 `policy.allow_implicit_invocation: false`로 표현한다. |
| `user-invocable: false` | 모델용 보조 스킬이라는 뜻이다. 자동 호출을 금지하는 설정으로 뒤집지 않는다. 사용자 메뉴 숨김의 동등 기능은 별도 확인한다. |
| `allowed-tools` | Claude 스킬에서는 나열한 도구의 사전 허용이며 도구 화이트리스트가 아니다. Codex의 권한 확대 설정으로 번역하지 않는다. |
| `disallowed-tools` | 원본의 도구 제거 요구를 보존할 실제 제한 수단을 검토한다. 본문에 “쓰지 말라”는 지시만 추가한 것은 같은 강제가 아니다. |
| `context: fork`, `agent`, `background` | 별도 컨텍스트와 실행 수명 요구다. [에이전트 문서](agents-and-hooks.md)에 따라 호출까지 구현한다. |
| `$ARGUMENTS`, 위치/이름 인자, `argument-hint` | 인자 의미·기본값·누락 처리를 본문 입력 계약으로 옮긴다. Codex가 같은 문자열을 자동 치환한다고 가정하지 않는다. |
| 셸 전처리, `!`와 백틱 | 실행 시점·입력·출력이 있는 명시적 도구 단계로 바꾼다. 원본을 읽는 동안 실행하지 않는다. |
| `model`, `paths`, `when_to_use`, 스킬별 `hooks` 등 | 현재 지원을 확인하고 판단 기준·트리거·실행 지시로 보존할지 선택한다. 인식되지 않는 키를 남겨 같은 동작을 기대하지 않는다. |

원본에 없는 명시적 호출 제한을 부작용이 있다는 이유만으로 추가하지 않는다. `agents/openai.yaml`의 기본 자동 호출 정책은 유지하며 기존 UI·의존성 설정을 보존한다. `agents/openai.yaml`은 UI/호출 메타데이터이고 서브에이전트 등록 파일이 아니다.

## 도구·경로·생성물

- `Read/Glob/Grep/Bash/Write/Edit/Skill/Agent/AskUserQuestion/TodoWrite` 이름을 고정 치환하는 표를 만들지 않는다. 대상 세션에서 실제 제공되는 파일·셸·편집·질문·계획·위임 도구를 사용하게 한다. 질문 도구가 없으면 일반 대화로 입력받되 필요한 승인 자체는 생략하지 않는다.
- `WebFetch`의 요약 결과와 원문 다운로드는 같은 기능이 아니다. 원문 충실도가 필요한 워크플로는 원문 확보 도구/헬퍼를 유지하고, 검색 결과나 요약으로 원문을 대체하지 않는다.
- `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_SKILL_DIR}`, 세션 변수는 **해석되는 위치**를 확인한다. Codex 훅의 호환 환경변수가 스킬 본문의 셸 실행에도 항상 존재한다는 뜻은 아니다. 패키지의 실제 설치 위치로 경로를 해석한다.
- 생성된 프로젝트 스킬은 `.agents/skills/`를 사용한다. 패키지 내부의 `skills/`, 프로젝트의 `.agents/skills/`, 개인 설치 디렉터리를 구별한다.
- 사용자의 `AGENTS.md`와 기존 `CLAUDE.md`를 읽어 충돌을 파악한다. Codex에 필요한 지침은 `AGENTS.md` 또는 명시적으로 읽는 참조에 연결한다. Claude의 `@파일` 문법이 Codex에서도 자동 import된다고 가정하지 않는다.
- 원본의 `.claude/skills/`가 사용자에게 생성하는 템플릿인지, 개발자의 dogfood인지 구별한다. 생성기 코드·템플릿·내부 참조·기존 데이터 업그레이드까지 함께 살핀다.

## MCP와 그 밖의 기능

[Claude MCP](https://code.claude.com/docs/en/mcp), [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp), [공개 전환 가이드](https://developers.openai.com/plugins/guides/submit-claude-plugin)를 필요한 경우 확인한다.

- 서버 구현은 재사용할 수 있어도 설정 형식·transport·환경변수·인증 연결은 따로 검증한다. portable `mcp.json`은 transport `type` 등을 확인해야 하므로 `.mcp.json`의 파일명만 바꾸지 않는다.
- 도구 이름/서버 namespace가 달라지면 스킬의 호출도 맞춘다. `.app.json`의 등록 서비스 참조와 로컬/원격 MCP 서버 설정은 같은 것이 아니다.
- `userConfig` 설치 질문과 `${user_config.*}` 치환을 그대로 기대하지 않는다. 일회성 입력, 문서화한 로컬 설정/환경변수, 인증이 필요한 연결 중 실제 용도에 맞게 설계한다. 자격증명 값을 패키지에 복사하지 않는다.
- LSP, output styles, channels, monitors, themes, plugin dependencies는 일대일 대응을 가정하지 않는다. 핵심 동작이 이 기능에 의존하면 현재 대상의 지원 수단을 확인하고, 대체 불가능하면 해당 기능을 `blocked`로 남긴다. dependency 이름만 지우고 호출은 남겨두지 않는다.
