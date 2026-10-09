# superdomain: Claude to Codex 전환 기록

## 범위와 출처

- 확인일: 2026-10-09.
- 원본: `plugins/superdomain/`, `superdomain` 0.6.0.
- 원본 저장소 리비전: `74507b6557a0514fe5276cff36f85c28b747f132`. 원본 디렉터리에는 시작 시 미커밋 변경이 없었다.
- 대상: `plugins/superdomain-codex/`. **로컬 Codex 데스크톱에 수동 설치할 독립 플러그인**이다. CLI·IDE·클라우드·공개 디렉터리 지원을 검증하지 않았다.
- 최초 생성이다. 기존 대상·관리 기준·사용자 수정 파일은 없었다. 원본·원본 버전·Claude 마켓플레이스는 수정하지 않는다. 최초 생성에는 등록·설치·개인 설정 변경·커밋·게시를 포함하지 않았다. 이후 사용자 요청으로 저장소 내 배치와 Codex 카탈로그·CI를 추가한 이력은 아래에 별도로 기록한다.
- 업무 버전은 원본 0.6.0을 유지한다. Codex 전환의 별도 결정·검증 이력은 이 문서에 남긴다.

## 확인한 지원 근거

모두 2026-10-09에 실제 본문을 확인했다.

| 근거 | 이 전환에 적용한 내용 |
|---|---|
| [OpenAI 플러그인 패키징](https://developers.openai.com/plugins/build/plugins) | portable 루트 `plugin.json`, 기본 `skills/`, OpenAI 표시 정보의 `extensions.com.openai`, 로컬 마켓플레이스 등록 후 데스크톱 설치 경로 |
| [Agent Plugins 1.0.0 JSON Schema](https://agent-plugins.org/schemas/1.0.0/plugin.schema.json) | 루트 manifest를 다운로드한 공식 스키마로 검증. OpenAI 확장 객체 내부는 이 스키마의 의미 검증 대상이 아니므로 공식 예시의 표시 필드만 사용 |
| [Codex 스킬](https://learn.chatgpt.com/docs/build-skills) | name/description, 스킬의 실제 경로 제공, 명시적·설명 기반 선택, optional `agents/openai.yaml` 표시 정보 |
| [Codex 서브에이전트](https://learn.chatgpt.com/docs/agent-configuration/subagents) | 프로젝트 custom agent는 별도 `.codex/agents/*.toml` 설정이다. 플러그인 역할 문서의 자동 등록으로 취급하지 않는다 |
| [Claude 스킬](https://code.claude.com/docs/en/skills) | `paths`에 따른 자동 활성화, `argument-hint`와 인자·경로 치환의 원본 의미 |
| [Claude 서브에이전트](https://code.claude.com/docs/en/sub-agents) | 원본 model과 tools/disallowedTools의 실행 계약. 역할 프롬프트만으로 같은 강제를 제공한다고 주장할 수 없음 |
| 현재 세션의 `collaboration.spawn_agent` 스키마 | `fork_turns: "none"`으로 작성 대화 없이 새 컨텍스트를 만들고 `task_name`과 역할 문서·입력을 전달할 수 있음. 도구 이름을 고정 전제하지 않고 설치 후 실제 도구를 확인하도록 작성 |

공식 스키마 파일 SHA-256: `0a4aad95ce337878ad38802ebf0daa3fde76abe3f65400c86bcbb1ec0b3ab883`.

## 컴포넌트 대응표

원본은 15개 파일이다. manifest에 커스텀 경로·인라인 구성은 없고, 원본 marketplace 항목은 이름·설명·분류·키워드·source만 선언한다. 별도 commands·hooks·MCP·settings·실행 스크립트·생성기 코드는 없다.

| 원본 컴포넌트/동작 | Codex 대상 파일/호출 방식 | 처리 | 보존할 조건 | 검증 방법 |
|---|---|---|---|---|
| `.claude-plugin/plugin.json` | 루트 `plugin.json` | adapt | ID·0.6.0·저자·MIT·업무 설명 유지. homepage는 Codex 패키지 위치로 변경 | 공식 스키마 파싱, 원본 메타데이터 대조 |
| `skills/domain/SKILL.md` | 같은 패키지 상대 위치 | adapt | 한 번에 한 질문, 역할·정책·관계 확인 후 저장, 수정 전후 제시, 정의 리뷰, ADR·포인터 제안 | 원본 대조, 스킬 형식, 독립 리뷰 |
| `skills/domain/domain-guide.md` | 동일 위치 | copy | DOMAIN.md 형식, 방향·외부 접점·예외·분류 판단 전체 보존 | 원본과 바이트 동일성 |
| `skills/conventions/SKILL.md` | 동일 위치, 설명과 본문에 Kotlin·Java 적용 범위 | adapt | 작성 전 기준 읽기, 프로젝트 규칙 우선, 수정 범위와 필수/지향 처리, 작성 후 확인 | 형식 검사, 업무 절차 대조; 자동 선택은 런타임 미검증 |
| `skills/conventions/conventions.md` | 동일 위치 | copy | 규칙과 예외·예제 보존 | 원본과 바이트 동일성 |
| `skills/review/SKILL.md` | 동일 위치 + `references/dispatch.md` | adapt | 관점/대상/기본값, 두 독립 리뷰 병렬 실행, 누락 자료·삭제 파일·새 파일 처리, 근거·심각도·병합·후속 계약 | Git fixture, 경로 검사, 독립 리뷰; 모델의 실제 선택·위임은 별도 |
| `agents/domain-reviewer.md` | `skills/review/references/domain-reviewer.md` | replace | 정의/변경/전체 모드와 경계 판단·출력 계약; 작성 대화와 다른 리뷰 결과를 공유하지 않음 | 직접 원문 대조, 호출자와 역할의 링크·입력 계약 검토 |
| `agents/convention-reviewer.md` | `skills/review/references/convention-reviewer.md` | replace | 변경 줄·선언 범위, Kotlin·Java, 필수/지향의 심각도, 프로젝트 예외, 출력 계약 | 직접 원문 대조, 호출자와 역할의 링크·입력 계약 검토 |
| agent `model: opus/sonnet` | 호출자가 model·reasoning을 지정하지 않음 | adapt | 역할 판단은 보존하며 Codex 세션 설정 상속. 모델 품질·비용 동일성은 보장하지 않음 | 호출 계약 확인 |
| agent `tools`, `disallowedTools: Agent` | dispatch와 각 역할의 읽기 전용·재위임 금지 지침 | replace | **도구 강제와 동등하지 않음. 사용자 선택으로 이 차이를 수용** | 사용자 답변 아래 기록, 문서·호출 패킷의 제한 확인 |
| `skills/adr/SKILL.md` | 동일 위치 | adapt | 신규/제안/승인/대체/부분 조정, 사실 확인, 본문 보존, 양방향 메타데이터 링크, 포인터 동의 | 원문 대조, 상대 경로 검사, 독립 리뷰 |
| `skills/adr/adr-template.md` | 동일 위치 | copy | 상태와 메타데이터·본문 형식 | 원본과 바이트 동일성 |
| `${CLAUDE_SKILL_DIR}`, `${CLAUDE_PLUGIN_ROOT}`, Agent 호출 | 실제 SKILL.md 기준 내부 상대 링크를 해석하여 절대 경로 전달 | adapt | 사용자 프로젝트 cwd·개발 머신·다른 플러그인에 의존하지 않음 | 독립 임시 경로에 패키지만 옮겨 내부 링크 29개 해결 |
| `/superdomain:*`, `$ARGUMENTS`, `argument-hint` | 자연어/스킬 선택, 요청 안의 인자 해석, 본문 사용법 | adapt | domain/code/경로/커밋 범위/전체 입력과 기본값 유지 | 입력 표·예시·분기 대조 |
| 사용자 프로젝트 출력 | 기존 `docs/superdomain/DOMAIN.md`, `docs/superdomain/adr/`, 지침 포인터 | adapt | 데이터 경로 유지, 동의 전 문서 변경 금지, 기존 ADR 본문 보존. 생성되는 포인터도 Codex 사용법으로 변경 | 템플릿·실제 저장 지시 함께 검토 |
| `README.md` | Codex 전용 README | adapt | 기능·언어 범위·설치 전제·차이·한계 안내 | 설치 설명과 패키지 구조 대조 |
| `LICENSE` | 동일 위치 | copy | MIT와 저작권 표기 | 바이트 동일성 |
| `CHANGELOG.md` | 배포본 제외, 출처 버전·Codex 이력은 이 기록 | omit | Claude 과거 설치·업그레이드 이력을 Codex 실행 지시로 배포하지 않음. 원본에는 유지 | 원본 목록과 패키지 목록 대조 |
| `docs/superpowers/specs/2026-09-29-superdomain-redesign-design.md`, `docs/superpowers/plans/2026-09-29-superdomain-redesign.md` | 배포본 제외 | omit | 0.4.0 개발 설계·구현 기록이며 현재 런타임 지침이 아님 | 현행 SKILL·가이드로 모든 기능 대응 확인 |
| 원본에 없는 UI 정보 | 네 스킬의 `agents/openai.yaml` | adapt | 표시 이름·설명만 추가. agent 등록이나 explicit-only 정책 아님 | 실제 YAML 파서, 허용된 표시 필드 확인 |

## 사용자와 합의한 차이 및 Codex 전용 결정

1. **리뷰어 제한:** 2026-10-09 사용자가 “플러그인 내부 역할 문서 + 서브에이전트 (권장): 읽기 전용·재위임 금지를 지침으로 전달하며, 원본과 같은 도구 차단은 보장하지 않음”을 선택했다. 따라서 별도 custom agent 설치 없이 역할 문서를 전달한다. 부모 권한 상속과 지침의 차이를 README·실행 계약에 명시했다. 도구 제거·읽기 전용 sandbox 강제를 검증했다고 보고하지 않는다.
2. **컨텍스트·병렬성:** 현재 도구의 새 컨텍스트 옵션을 확인해 사용한다. 둘 다 활성화되면 두 리뷰어를 먼저 시작하고 결과를 기다린다. 도구·컨텍스트·동시 실행 자원이 없으면 미검토를 알리고 완료로 처리하지 않는다.
3. **모델:** 원본 모델 계열을 임의의 GPT 모델로 대응시키지 않고 세션 설정을 상속한다. 원본의 업무 규칙은 특정 공급자 API에 의존하지 않는다.
4. **conventions 활성화:** Claude `paths`를 Codex frontmatter에 남기지 않는다. 같은 Kotlin·Java 범위를 설명·본문으로 한정하고 기본 implicit 선택을 유지한다. 파일만으로 반드시 로딩된다는 보장은 없어 README에 명시적 선택 방법을 안내했다.
5. **프로젝트 지침:** AGENTS.md와 기존 CLAUDE.md 계열을 읽는다. 저장소 AGENTS.md의 “기존 CLAUDE.md가 있으면 그 파일에 포인터를 쓴다” 정책과 사용자 동의를 보존했다. Codex 자동 로딩까지 보장하는 문구는 제거하고 기존 CLAUDE.md에 썼다면 다음 세션에서 명시적으로 읽도록 안내한다. 이 저장소에는 CLAUDE.md 계열을 만들지 않는다.
6. **커밋 범위의 문맥:** 원본의 “작업 트리 변경과 새 파일을 넣지 않는다”를 실행 시에도 지키도록 A·B를 해시로 고정하고 코드·DOMAIN.md·프로젝트 지침을 B의 `git show`로 읽게 했다. 패키지 기준 문서는 현재 설치본을 사용한다. 공백 경로와 셸 인용도 명시했다.
7. **범위:** 실제 설치 없이 스킬 선택·모델 위임을 통과로 주장하지 않는다. 이번 패키지에는 실행 코드·훅·MCP 서버나 프로젝트 설정 설치기가 없다.

## 실행한 검증

| 검사 | 결과와 의미 |
|---|---|
| 공식 plugin schema + JSON/YAML 파싱 + SKILL frontmatter + 내부 링크 | `validate.cjs`: 17개 파일, 스킬 4개, 내부 링크 29개 통과. OpenAI 확장 표시 필드는 공식 예시와 대조했으며 schema가 내부 의미를 강제하지는 않음 |
| 독립 배치 | 패키지만 공백을 포함한 임시 디렉터리로 복사하고 다른 cwd에서 같은 검증 통과. 원본 디렉터리 없이 내부 리소스가 해결됨 |
| 공통 규칙과 저작권 | domain-guide·conventions·adr-template·LICENSE 4개가 원본과 바이트 동일 |
| skill-creator `quick_validate.py` | 스킬 4개 모두 `Skill is valid!` |
| Git 명령 fixture | `check_git_scopes.py`: origin/HEAD 없음, 기본 범위의 committed/staged/unstaged/untracked/deleted, 공백 경로, 커밋 범위 제외, B의 코드·DOMAIN 내용, 빈 범위 확인 |
| 원본 marketplace | `claude plugin validate .` 통과. 이것을 Codex 검증으로 취급하지 않음 |
| 원본 불변성과 no-op 비교 | 원본 15개 파일의 스냅샷은 작업 시작 후보와 동일. 대상 스냅샷 두 번이 바이트 동일. 완료 후 기준 비교를 다시 수행한다 |

재현 명령(저장소 루트, Node.js의 `ajv` v8·`js-yaml`, Python 3 필요):

```bash
curl --fail --silent --show-error https://agent-plugins.org/schemas/1.0.0/plugin.schema.json --output /tmp/superdomain-plugin.schema.json
node porting/superdomain/validate.cjs plugins/superdomain-codex /tmp/superdomain-plugin.schema.json
python3 porting/superdomain/check_git_scopes.py
claude plugin validate .
python3 .agents/skills/claude-to-codex/scripts/tree_state.py compare porting/superdomain/source-state.json plugins/superdomain
python3 .agents/skills/claude-to-codex/scripts/tree_state.py compare porting/superdomain/target-state.json plugins/superdomain-codex
```

`quick_validate.py`는 세션에 제공된 skill-creator 설치 위치의 도구를 사용한다. 독립 배치 검사는 패키지를 임시 경로로 복사한 뒤 위 Node 검사에 그 경로를 넘겨 재현한다. 이 검사들은 모델의 실제 행동을 테스트하지 않는다.

## 최초 생성의 독립 리뷰

검토 전 후보(기준 파일 확정 전):

- `/private/tmp/superdomain-codex-dw9bt86b/source-candidate.json`: `23bf2beca718717d7dbbe5cf73f0febbe8c7bf6919bb58b69bf50aa0a5ac9aeb`
- `/private/tmp/superdomain-codex-dw9bt86b/target-candidate.json`: `d4c807f87aec9ab3bd6d045d233aed3912c28b1b8f5a482ff545337d645cea02`
- 관리 파일 목록 후보: `/private/tmp/superdomain-codex-dw9bt86b/managed-paths-candidate.json`.

판정: **pass**. 별도 새 컨텍스트의 `superdomain_port_review` 리뷰어가 원본·대상 전체를 직접 대조하고, 메인의 문구 수정 후 해당 범위를 재검토했다. 전체 결과와 직접/전달받은 검증 구분은 [review.md](review.md)에 기록했다.

| ID | 구분 | 최종 상태 | 지적 | 메인의 조치 | 재검토 |
|---|---|---|---|---|---|
| R1 | suggestion | resolved | README 언어 범위 설명이 도메인 리뷰까지 Kotlin·Java로 한정하는 것으로 읽힐 수 있음 | 도메인 정의·도메인 리뷰·ADR은 언어 무관, 컨벤션 스킬·리뷰는 Kotlin·Java라고 명시 | 리뷰어가 원본 README:64와 대상 README:39 대조, 변경 파일이 README 하나임을 확인, schema·링크 재검증 후 pass |

미해결 must_fix·권고는 없다. 최종 대상 후보는 `/private/tmp/superdomain-codex-dw9bt86b/target-candidate-v2.json`, SHA-256 `b58fd9686c77d3b4f033face368612567af6712eb880417192c0e505adff2910`이다. 원본 후보와 관리 목록은 처음 검토한 상태에서 바뀌지 않았다.

최종 파일이 재검토한 후보와 동일함을 확인한 뒤 `source-state.json`, `managed-paths.json`(17개), `target-state.json`으로 확정했다. 원본 15개 파일은 작업 시작과 동일하다. 기준 확정 뒤 원본·대상 compare 결과는 모두 추가/변경/삭제 없음이고, 반복 비교로 파일 내용·mtime이 바뀌지 않았다. 신규 패키지 17개와 전환 기록만 추가했으며 기존 파일 변경·삭제는 없다. **생성 완료, 런타임 미검증**으로 마무리한다.

## 남은 런타임 검증

설치·개인 설정 변경은 이번 요청 범위 밖이므로 다음은 미검증이다. 파일 검사나 Git fixture로 대체했다고 주장하지 않는다.

1. 저장소 카탈로그를 데스크톱에서 실제로 발견·설치한 뒤 스킬 4개 발견 및 중복 이름 선택.
2. Kotlin·Java 작업의 암묵적 conventions 선택, 명시적 선택 시 코드 작성 전 기준 적용.
3. DOMAIN 신규/수정의 사용자 확인과 정의 리뷰, 두 관점 동시 리뷰의 실제 새 컨텍스트·입력·출력·실패 보고.
4. 리뷰어의 지침 준수(무수정·재위임 없음). **강제 도구 차단은 설계상 제공하지 않는다.**
5. ADR 신규·승인·대체·부분 조정에서 동의·본문 보존·양방향 링크, AGENTS/기존 CLAUDE 포인터 처리.

설치 후에는 작은 샘플 프로젝트에서 이 시나리오를 실행하고 전후 Git diff와 실행 로그로 확인한다. 원본 갱신 시에는 저장한 상태와 현재 파일을 먼저 비교하고, 사용자 추가 파일을 보존한다. 기존 리뷰는 원본·대상·전환 조건에 변화가 없을 때만 재사용한다.

## 2026-10-09: 저장소 배치와 등록 변경

사용자가 검토 후 추천 방향으로 진행해 달라고 요청했다. 원본과 기존 전환본을 기준 상태와 먼저 비교했으며 추가·수정·삭제가 없었다.

- 패키지를 `codex/plugins/superdomain/`에서 `plugins/superdomain-codex/`로, 기록을 `codex/porting/superdomain/`에서 `porting/superdomain/`으로 이동했다. 설치 ID `superdomain`, 업무 버전 0.6.0, portable 루트 `plugin.json`을 유지한다.
- 패키지 내부 변경은 manifest의 homepage와 README 설치 안내뿐이다. 스킬·역할·가이드·템플릿·LICENSE는 이전 검토 상태를 유지한다. 기존 파일을 덮어쓰거나 사용자가 추가한 파일을 지우지 않았다.
- 전환 스킬의 신규 출력 기본값을 `plugins/<plugin-name>-codex/`, 기록 기본값을 `porting/<plugin-name>/`으로 바꿨다. 기존 전환본은 기록된 위치를 우선하며 자동 이동하지 않는다.
- `.agents/plugins/marketplace.json`에 이름 `superkit`, 표시 이름 `superkit for Codex`, 플러그인 `superdomain`, 경로 `./plugins/superdomain-codex`를 등록했다. installation은 `AVAILABLE`, authentication은 공식 예시의 `ON_INSTALL`을 사용한다. MCP·외부 연결이 없어 플러그인 인증 흐름을 추가하는 설정은 아니다. Claude 카탈로그는 수정하지 않았다.
- `.github/workflows/superdomain-codex.yml`에 패키지/카탈로그/전환 기록 변경 시의 스키마·내부 참조·독립 배치·기준 상태·Git 범위 검사를 연결했다. 원격 CI 실행은 아직 하지 않았다.
- 루트 AGENTS.md·README·CONTRIBUTING에 플랫폼별 위치·설치·검증과 Claude 릴리스 명령 적용 범위를 반영했다.

추가 근거: [공식 저장소 마켓플레이스 형식](https://developers.openai.com/plugins/build/plugins#marketplace-metadata), [setup-node 공식 사용법](https://github.com/actions/setup-node/blob/main/README.md)을 2026-10-09 확인했다. 등록은 저장소 파일 변경이며 앱 설치·활성화·개인 설정 변경은 수행하지 않았다.

재현 검사:

```bash
node porting/superdomain/validate.cjs plugins/superdomain-codex /tmp/superdomain-plugin.schema.json
python3 porting/superdomain/check_repository.py
python3 porting/superdomain/check_git_scopes.py
python3 -m unittest discover -s .agents/skills/claude-to-codex/tests -q
```

이동 직전 대상 기준의 SHA-256은 `b58fd9686c77d3b4f033face368612567af6712eb880417192c0e505adff2910`이다. 이 변경의 검증과 별도 리뷰를 완료한 뒤 대상 기준만 갱신한다. 원본 기준과 관리 파일 목록은 그대로 보존한다. 검증 결과: 새 위치와 공백을 포함한 독립 복사본의 manifest·스킬 4개·파일 17개·내부 링크 29개 통과, 카탈로그/후보 상태 검사 통과, Git 범위 fixture 통과, tree_state 단위 검사 6개 통과, 전환 스킬 포함 스킬 형식 검사 5개 통과, 기존 Claude marketplace CI 코드와 `claude plugin validate .` 통과, workflow YAML·트리거 확인. `check_repository.py --target-state <후보 경로>`로 기존 기준을 덮어쓰지 않고 검증했다. GitHub의 실제 workflow 실행과 앱 설치·런타임은 미검증이다. 최종 상태: 별도 새 컨텍스트의 `superdomain_layout_review`가 pass로 판정했다. 지적은 없었다. 검토한 대상 후보 SHA-256 `8acef553f64dbeae63ad2acfb5a3fb0f0d86f84ba1bad4a632baa38d8090b59a`와 현재 파일이 같음을 확인한 뒤 target-state.json을 확정했다. source-state.json과 managed-paths.json은 이동 전과 바이트 동일하다. 최종 기본 검사와 반복 비교가 파일을 바꾸지 않음을 확인했다. 리뷰 근거는 review.md의 배치 변경 절에 기록했다.
