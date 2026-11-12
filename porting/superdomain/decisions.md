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
| `skills/adr/SKILL.md` | 동일 위치 | adapt | 신규/바꿈/제안과 찾아 읽기, 사실 확인, 병합된 기록의 문장 보존, `바뀜` 줄과 새 기록의 짝, 포인터 동의 | 원문 대조, 상대 경로 검사, 독립 리뷰 |
| `skills/adr/adr-template.md` | 동일 위치 | copy | 머리 줄·결정 블록·`바뀜`/`대체됨` 줄의 형식, 적지 않는 것, 분량 | 원본과 바이트 동일성 |
| `${CLAUDE_SKILL_DIR}`, `${CLAUDE_PLUGIN_ROOT}`, Agent 호출 | 실제 SKILL.md 기준 내부 상대 링크를 해석하여 절대 경로 전달 | adapt | 사용자 프로젝트 cwd·개발 머신·다른 플러그인에 의존하지 않음 | 독립 임시 경로에 패키지만 옮겨 내부 링크 29개 해결 |
| `/superdomain:*`, `$ARGUMENTS`, `argument-hint` | 자연어/스킬 선택, 요청 안의 인자 해석, 본문 사용법 | adapt | domain/code/경로/커밋 범위/전체 입력과 기본값 유지 | 입력 표·예시·분기 대조 |
| 사용자 프로젝트 출력 | 기존 `docs/superdomain/DOMAIN.md`, `docs/superdomain/adr/`, 지침 포인터 | adapt | 데이터 경로 유지, 동의 전 문서 변경 금지, 병합된 ADR의 문장 보존(바뀐 결정에는 `바뀜` 줄만 더한다). 생성되는 포인터도 Codex 사용법으로 변경 | 템플릿·실제 저장 지시 함께 검토 |
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
5. ADR 신규·바꿈에서 동의·문장 보존·`바뀜` 줄과 새 기록의 짝, AGENTS/기존 CLAUDE 포인터 처리.

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

## 2026-10-09: 원본 0.6.1 반영

원본 superdomain이 0.6.1로 올라가 컨벤션에 「라이브러리·DB가 이미 구현한 기능은 테스트하지 않는다」(`지향`)를 더하고, 「모킹은 외부 자원에만 쓴다」의 실제 DB 조회 테스트 범위를 조건을 직접 쓴 조회로 좁혔다. 쓰기 전에 원본·전환본을 기존 기준과 비교했으며 추가·수정·삭제가 없었다.

- 원본에서 바뀐 파일: `.claude-plugin/plugin.json`(0.6.1), `CHANGELOG.md`, `skills/conventions/conventions.md`.
- 전환본 반영: `skills/conventions/conventions.md`를 원본에서 그대로 복사했다(대응표의 `copy`, 바이트 동일). `plugin.json`의 `version`과 README의 기반 버전을 0.6.1로 바꿨다. `CHANGELOG.md`는 대응표대로 배포본에서 제외한다.
- 스킬·역할 문서·호출 방식·권한·경로·트리거는 바뀌지 않았다. 관리 파일 목록(17개)도 그대로다.
- 독립 리뷰: 생략했다. `copy`로 분류한 파일의 바이트 복사와 버전 표기 변경뿐이라 전환 판단(adapt·replace)이 새로 생기지 않는다. 생략을 독립 리뷰 통과로 기록하지 않는다.
- 기준 상태: 검사 통과 뒤 `source-state.json`·`target-state.json`을 다시 만들었다.

검증 결과: `check_repository.py`, `check_git_scopes.py`, tree_state 단위 검사 6개, `claude plugin validate .` 통과. 원본·전환본 conventions.md 바이트 동일, 두 manifest의 이름·버전(superdomain 0.6.1) 일치 확인. conventions.md에는 내부 링크가 없어 링크 수는 바뀌지 않는다. `validate.cjs`의 공식 스키마 검사는 로컬에서 실행하지 않았으므로 PR의 `superdomain-codex` CI 결과로 확인한다. 이 스크립트는 스키마·심볼릭 링크·스킬 frontmatter·내부 링크만 검사하며 버전 값이나 README 본문은 검사하지 않는다. 런타임은 미검증이다.

## 2026-10-11: 원본 0.7.0 반영

원본 superdomain이 0.7.0으로 올라가 컨벤션에 「아키텍처 규칙은 테스트로 강제한다」(`지향`)와 구성 문서 `skills/conventions/architecture-tests.md`를 더하고, 두 리뷰어가 대상 프로젝트의 아키텍처 테스트를 근거로 쓰게 했다(이슈 #6). 쓰기 전에 원본·전환본을 기존 기준과 비교했다. 전환본은 기준과 같았고, 원본은 아래 파일만 바뀌었다.

- 원본에서 바뀐 파일: `.claude-plugin/plugin.json`(0.7.0), `CHANGELOG.md`, `README.md`, `agents/domain-reviewer.md`, `agents/convention-reviewer.md`, `docs/superpowers/specs/2026-09-29-superdomain-redesign-design.md`, `skills/conventions/SKILL.md`, `skills/conventions/conventions.md`, `skills/domain/SKILL.md`, `skills/domain/domain-guide.md`. 새 파일: `skills/conventions/architecture-tests.md`.

| 원본 컴포넌트/동작 | Codex 대상 파일/호출 방식 | 처리 | 보존할 조건 | 검증 방법 |
|---|---|---|---|---|
| `skills/conventions/conventions.md` 새 항목 | `skills/conventions/conventions.md` | copy | 바이트 동일 | `cmp` |
| `skills/conventions/architecture-tests.md`(새 파일) | `skills/conventions/architecture-tests.md`(관리 목록에 추가) | copy | 바이트 동일, 외부 링크는 Spring 공식 문서만 | `cmp`, 내부 링크 검사 |
| `skills/domain/domain-guide.md` 허용 관계 테스트 | `skills/domain/domain-guide.md` | copy | 바이트 동일 | `cmp` |
| `skills/conventions/SKILL.md` 설명·1단계 | 같은 파일 | adapt | 설명에 아키텍처 테스트 추가, `${CLAUDE_SKILL_DIR}` 대신 상대 링크 `[architecture-tests.md](architecture-tests.md)` | 링크 검사 |
| `skills/domain/SKILL.md` 수정 모드 2단계 | 같은 파일 | adapt | 문장 동일, 코드 수정은 하지 않고 알리기만 한다 | diff |
| `agents/domain-reviewer.md` 시작 4단계·「아키텍처 테스트가 있을 때」·변경/전체 점검 항목 | `skills/review/references/domain-reviewer.md` | adapt | 문장 동일, `Grep` 대신 기존 표기인 "읽기 전용 검색(rg 등)", 테스트를 실행하지 않음 | 원본과 diff |
| `agents/convention-reviewer.md` 시작 5단계·「아키텍처 테스트가 있을 때」 | `skills/review/references/convention-reviewer.md` | adapt | 같은 방식 | 원본과 diff |
| `.claude-plugin/plugin.json` 버전 | `plugin.json` `version`, README 기반 버전 | adapt | 0.7.0 | 값 확인 |
| `README.md`, `CHANGELOG.md`, 스펙 | 없음 | omit | 기존 대응표대로 배포본에서 제외(README는 Codex 전용 README 유지) | — |

- 리뷰어의 아키텍처 테스트 탐색은 읽기 전용 검색과 읽기뿐이며 테스트를 실행하지 않는다. 기존 실행 계약(dispatch.md)의 읽기 전용·재위임 없음 조건과 커밋 범위 리뷰의 `git show <해시>:<경로>` 규칙이 그대로 적용된다.
- 스킬 진입점·인자·호출 흐름·권한·트리거 경로는 바뀌지 않았다. 관리 파일은 17개에서 18개가 됐다.
- 동작(리뷰어 판단 기준)에 영향을 주는 갱신이라 독립 리뷰를 받는다.

검증(리뷰 전): 세 복사본 `cmp` 동일. 패키지 `.md`의 상대 링크(정규식 `](경로)`로 센 원시 계수, 자리표시자 포함)에서 깨진 것은 ADR 템플릿의 기존 자리표시자·예시 파일명뿐이다. 리뷰어가 validate.cjs 방식으로 재현한 해석 링크 30개는 모두 정상이다. `check_git_scopes.py` 통과, tree_state 단위 검사 6개 통과, `claude plugin validate .`와 원본 디렉터리의 `claude plugin validate --strict .claude-plugin/plugin.json`·`--strict skills`·`--strict agents` 통과. `check_repository.py`는 원본 기준을 갱신하기 전이라 원본 변경을 보고하며 실패한다(예상한 결과). `validate.cjs`의 공식 스키마 검사는 로컬에서 실행하지 않았으므로 PR의 `superdomain-codex` CI로 확인한다. 런타임은 미검증이다.

독립 리뷰: 별도 새 컨텍스트의 리뷰어가 1차 pass로 판정하고 권고 3건을 남겼다. 조치 뒤 재검토도 pass다. 리뷰어는 Spring Modulith 2.1.1 jar와 Konsist 0.17.3 소스로 예시 API 시그니처를 대조했다.

| ID | 구분 | 상태 | 내용 | 조치 |
|---|---|---|---|---|
| R1 | suggestion(원본 내용) | resolved | architecture-tests.md가 Konsist에 없는 baseline(위반 고정) 기능을 안내했다 | 원본을 "ArchUnit은 `FreezingArchRule`, Konsist는 범위를 좁히거나 `@Suppress(\"konsist.<테스트 이름>\")`"로 고치고 대상에 다시 복사했다 |
| R2 | suggestion(전환) | dismissed | 커밋 범위 리뷰에서 테스트 소스 검색이 작업 트리를 볼 수 있다 | 역할 문서의 실행 계약(끝점 `git show`, 작업 트리를 섞지 않음)이 새 단계에도 적용되고 원본과 동작이 같아 Codex 전용 문구를 더하지 않았다. 리뷰어가 근거를 확인했다 |
| R3 | suggestion(기록) | resolved | 링크 수·strict 검사 명령을 재현할 수 없었다 | 위 검증 문장을 계수 방법과 실제 명령으로 고쳤다 |

최종 상태: 리뷰한 후보(`source-candidate2.json` sha256 `70db1dcfe259abe681eb3433ed475179ae9423c104f23c8ac95ed8530cb26879`, `target-candidate2.json` sha256 `1ec8f726baa5c854f0881ff3c00484eba2524f1421a467213e41f6818612d736`)와 현재 파일이 같음을 확인한 뒤 `source-state.json`·`target-state.json`을 그 후보로 확정했다. 미검증: `validate.cjs`의 공식 스키마 검사(PR CI로 확인), 예시 코드의 실제 컴파일, Codex 설치·런타임. 상태: 생성·갱신 완료, 런타임 미검증.

## 2026-11-10: 원본 기준 비교 범위 조정

`check_repository.py`가 원본 폴더 전체를 `source-state.json`과 비교해서, 전환하지 않는 설계 문서를 원본에 더하기만 해도 실패했다. 반대로 CI 경로 트리거에는 원본 폴더가 없어 원본만 바꾼 PR에서는 이 검사가 돌지 않았다. 두 가지를 함께 고쳤다. 전환본과 대응표는 바뀌지 않았다.

- **비교에서 빼는 경로:** 대응표에서 `omit`인 `CHANGELOG.md`와 `docs/superpowers/` 아래 전체. 대응표에는 스펙·계획 두 파일만 적혀 있지만, 같은 폴더에 새로 생기는 설계 문서도 같은 분류로 본다.
- **계속 비교하는 경로:** 그 밖의 모든 원본 파일. `README.md`(`adapt`)와 `LICENSE`(`copy`)는 전환 입력이므로 그대로 비교한다. 0.7.0 반영 표가 README 변경을 `omit`으로 적은 것은 그 변경을 전환본에 옮기지 않았다는 뜻이고, 파일의 분류는 처음 대응표의 `adapt`다. 빼는 목록에 없는 경로는 새로 생기기만 해도 실패하므로 새 스킬 파일이나 새 컴포넌트 폴더(hooks·commands 등)를 놓치지 않는다.
- **구현:** `check_repository.py`가 `tree_state.py compare` 결과에서 위 경로를 거른다. 경로는 원본 루트 기준이고 파일은 완전 일치, 폴더는 접두사로 판정한다(`skills/domain/CHANGELOG.md`는 빠지지 않는다). 걸러 낸 차이는 검사가 통과해도 한 줄로 출력한다. 기준을 `snapshot --paths-file`로 좁히는 방식은 새 스킬 파일 추가를 잡지 못해 쓰지 않았다. `tree_state.py`는 고치지 않았다.
- **기준 상태:** `source-state.json`·`target-state.json`·`managed-paths.json`과 전환본은 바꾸지 않았다. `source-state.json`에는 빼는 경로의 해시가 그대로 남아 있고, `tree_state.py compare`를 직접 실행하면 그 경로의 차이도 보고한다. 통과 여부는 `check_repository.py`로 판단한다.
- **CI:** `.github/workflows/superdomain-codex.yml`의 `push`·`pull_request` 경로에 `plugins/superdomain/**`를 더했다. 원본의 전환 대상 파일을 바꾼 PR은 전환본과 기준 상태를 함께 갱신해야 통과한다.
- **독립 리뷰:** 생략했다. 전환 판단(대응표)과 전환본은 그대로이고 검사 범위만 조정했다. 생략을 독립 리뷰 통과로 기록하지 않는다.

검증 결과: 임시 변경을 하나씩 만들고 `check_repository.py`를 실행한 뒤 되돌렸다. 통과 — `docs/superpowers/specs/x.md` 추가, `CHANGELOG.md` 수정, `docs/superpowers/plans/`의 계획 삭제. 실패(AssertionError가 해당 경로를 지목) — `skills/domain/x.md` 추가, `skills/domain/SKILL.md` 한 글자 수정, `agents/domain-reviewer.md` 삭제, `.claude-plugin/plugin.json`·`README.md`·`LICENSE` 수정, `skills/domain/CHANGELOG.md` 추가, `hooks/hooks.json` 추가. 되돌린 뒤 `check_repository.py`, `check_git_scopes.py`, tree_state 단위 검사 6개, `claude plugin validate .` 통과. GitHub의 실제 workflow 실행은 미검증이다.

## 2026-11-12: 원본 0.8.0 반영

원본 superdomain이 0.8.0으로 올라가 도메인 가이드에 `외부`를 맡는 도메인의 기준과 「간결하게 쓰는 기준」을 넣고, DOMAIN.md 형식을 기본 뼈대와 필요할 때만 쓰는 칸으로 나눴다(칸 이름 `코드` → `패키지`, `미정` 칸 삭제). domain 스킬, 두 리뷰어, 컨벤션 문서가 거기에 맞춰 바뀌었다. 쓰기 전에 원본·전환본·이 기록을 함께 읽었다.

- 원본에서 바뀐 파일: `.claude-plugin/plugin.json`(0.8.0), `CHANGELOG.md`, `README.md`, `agents/domain-reviewer.md`, `agents/convention-reviewer.md`, `skills/domain/SKILL.md`, `skills/domain/domain-guide.md`, `skills/conventions/SKILL.md`, `skills/conventions/conventions.md`, `skills/conventions/architecture-tests.md`, `skills/adr/SKILL.md`, 그리고 `docs/superpowers/` 아래의 설계 문서 여섯 개(0.8.0과 0.9.0의 검토서·스펙·계획).

| 원본 컴포넌트/동작 | Codex 대상 파일/호출 방식 | 처리 | 보존할 조건 | 검증 방법 |
|---|---|---|---|---|
| `skills/domain/domain-guide.md` 형식·「간결하게 쓰는 기준」·「외부 접점」·조합 코드 | `skills/domain/domain-guide.md` | copy | 바이트 동일. 플랫폼 이름을 쓰지 않는다("에이전트가 함께 읽는다") | `cmp` |
| `skills/conventions/conventions.md` 머리말 "외부 자원"·조합 코드, `architecture-tests.md` 모듈 감지 | 같은 위치 | copy | 바이트 동일 | `cmp` |
| `skills/domain/SKILL.md` 체크리스트 1·3~8단계, 수정 모드, 하지 않는 것 | 같은 파일 | adapt | 문장 동일. 포인터 줄은 "고칠 때는 superdomain의 domain 스킬로 고친다"로 끝난다. 상대 링크와 "Codex" 표기는 기존대로 | 원본과 diff, 표식 문자열 검사 |
| `skills/conventions/SKILL.md` 3단계의 첫 경우 | 같은 파일 | adapt | 문장 동일. 스킬을 가리키는 기존 표기 유지 | 원본과 diff |
| `skills/adr/SKILL.md` 6절 첫 항목 | 같은 파일 | adapt | 문장 동일. 기존 링크 `[domain 스킬](../domain/SKILL.md)` 유지 | 원본과 diff |
| `agents/domain-reviewer.md` 모드별 항목·지키는 것 | `skills/review/references/domain-reviewer.md` | adapt | 문장 동일. 0.7.0 형식 문서의 `코드` 칸을 `패키지`로 읽는 문장 포함. `Grep` 대신 "읽기 전용 검색(rg 등)" | 원본과 diff, 표식 문자열 검사 |
| `agents/convention-reviewer.md` 시작 3단계·보고하지 않는 것 | `skills/review/references/convention-reviewer.md` | adapt | 같은 방식 | 원본과 diff |
| 리뷰어의 분량 검사(글자 수를 유니코드 문자 수로 센다) | `skills/review/references/dispatch.md` 허용 작업 | adapt | "글자 수 세기(파일을 읽기만 하는 한 줄 명령으로 세고 파일을 쓰지 않는다)"만 더한다. 파일 생성·테스트/빌드 실행 금지는 그대로 | 문구 확인 |
| `.claude-plugin/plugin.json` 버전 | `plugin.json` `version`, README 기반 버전 | adapt | 0.8.0 | 값 확인 |
| `README.md`, `CHANGELOG.md`, 설계 문서 | 없음 | omit | 기존 대응표대로 배포본에서 제외 | — |

- 스킬 진입점·인자·호출 흐름·권한·트리거 경로는 바뀌지 않았다. 관리 파일은 18개 그대로다.
- 리뷰어가 분량을 잴 때 글자 수를 세야 하므로, 실행 계약(`skills/review/references/dispatch.md`)의 허용 작업에 "글자 수 세기"를 더했다(Codex 전용 조정). 읽기 전용·재위임 없음 조건은 그대로다.
- 리뷰어의 판단 기준과 domain 스킬의 질문 절차가 바뀌므로 독립 리뷰를 받는다.

검증(리뷰 전): 세 복사본 `cmp` 동일. `validate.cjs`(ajv 8.18.0, js-yaml 4.1.1, 공식 스키마 1.0.0)로 manifest valid, 스킬 4개, 파일 18개, 해석 링크 30개. 원본과 전환본의 대응 파일에 같은 표식 문자열이 있는지와 전환본에 Claude 전용 표기가 없는지 검사했다. `claude plugin validate .`와 `check_git_scopes.py` 통과.

기준 확인: 원본의 가이드와 리뷰어는 실제 프로젝트 두 곳의 DOMAIN.md로 확인했다(원본 설계 문서의 "기준 확인 결과"). 전환본의 리뷰어 참고 문서는 같은 문장을 담지만 Codex 런타임에서 돌려 보지는 않았다.

독립 리뷰: 별도 새 컨텍스트의 리뷰어가 1차 pass(권고 2건)로 판정했다. S1(실행 계약의 "글자 수 세기"가 방법을 정하지 않는다)은 문구를 고치고 전환본 후보를 다시 떠 재검토 pass를 받았다. S2(원본 기준 상태에 아직 커밋되지 않은 설계 문서 여섯 개가 들어 있다)는 절차 권고이고, 기준 상태와 그 문서들을 같은 커밋에 넣어 지킨다. 지적과 조치는 [review.md](review.md)의 "2026-11-12: 0.8.0 반영의 독립 리뷰"에 있다.

최종 상태: 리뷰한 후보(`source-candidate.json` sha256 `c6edba9a1740dde2778856d2b16de7aa5d01e33f246264fad67fe6edddb9942e`, `target-candidate2.json` sha256 `36f0ada5a0b2be5571f4c066f4631dfee178b2424f7bf00c2a4f7c399e79ec7f`)와 현재 파일이 같음을 확인한 뒤 `source-state.json`·`target-state.json`을 그 후보로 확정했고, 기본 `check_repository.py`가 통과했다. 미검증: Codex 설치·런타임, review 스킬이 리뷰어를 부르는 실제 호출 경로(원본 쪽 확인도 CLI 인증이 만료돼 리뷰어 문서를 지침으로 준 하위 에이전트로 했다). 상태: 갱신 완료, 런타임 미검증.

## 2026-11-12: 원본 0.9.0 반영

원본 superdomain이 0.9.0으로 올라가 ADR을 결정을 내린 때의 이유를 남기는 기록으로 다시 정했다. 템플릿과 adr 스킬을 다시 썼고(결정 블록, 적지 않는 것, 글자 수 분량, `바뀜` 줄, 모드 신규·바꿈·제안, 요지를 먼저 보이는 확정, 찾아 읽기), 상태(`proposed`·`accepted`·`superseded`)와 승인·대체·부분 조정 모드를 없앴다. 지침 파일의 결정 기록 포인터 줄, 컨벤션의 이유를 남기는 자리, domain 스킬의 수정 모드도 거기에 맞췄다. 쓰기 전에 원본·전환본·이 기록을 함께 읽었다. 위 컴포넌트 대응표의 adr 스킬 행과 사용자 프로젝트 출력 행, 남은 런타임 검증 5번을 새 동작에 맞춰 고쳤다.

- 원본에서 바뀐 파일: `.claude-plugin/plugin.json`(0.9.0), `CHANGELOG.md`, `README.md`, `skills/adr/SKILL.md`, `skills/adr/adr-template.md`, `skills/conventions/conventions.md`, `skills/domain/SKILL.md`, 그리고 설계 문서 둘(`docs/superpowers/specs/`의 ADR 설계 문서에 구현 전 시험 결과가 더해졌고, `docs/superpowers/plans/`의 ADR 구현 계획의 지시문 두 곳을 구현에 맞췄다).

| 원본 컴포넌트/동작 | Codex 대상 파일/호출 방식 | 처리 | 보존할 조건 | 검증 방법 |
|---|---|---|---|---|
| `skills/adr/adr-template.md` 새 판 | 같은 위치 | copy | 바이트 동일 | `cmp` |
| `skills/conventions/conventions.md`의 이유를 남기는 자리, ADR을 파일 이름으로 가리키기 | 같은 위치 | copy | 바이트 동일 | `cmp` |
| `skills/adr/SKILL.md` 새 판 | 같은 위치 | adapt | 문장 동일. 변형 다섯: "다음 세션의 Codex다", 템플릿 상대 링크와 링크 해석 문단, `/superdomain:domain` 대신 "superdomain의 [domain 스킬](../domain/SKILL.md)", 6절 포인터 항목의 대상 지침 파일 설명은 전환본 문구, 포인터 줄은 "superdomain의 adr 스킬로" | 원본과 diff, 표식 문자열 검사 |
| `skills/domain/SKILL.md` 8단계 포인터 줄·옛 줄 교체 문장, 수정 모드 1번 | 같은 위치 | adapt | 문장 동일. 포인터 줄은 adr 스킬의 전환본 줄과 글자가 같다 | 두 줄 비교 |
| adr 스킬의 설명 | `skills/adr/agents/openai.yaml` `short_description` | adapt | 없어진 모드(승인·대체·부분 조정)를 말하지 않는다 | 문구 확인 |
| `.claude-plugin/plugin.json` 버전 | `plugin.json` `version`, README 기반 버전·스킬 표·산출물 줄 | adapt | 0.9.0 | 값 확인 |
| `README.md`, `CHANGELOG.md`, 설계 문서 | 없음 | omit | 기존 대응표대로 배포본에서 제외 | — |

- 스킬 진입점·인자·권한·트리거 경로는 바뀌지 않았다. 관리 파일은 18개 그대로다.
- adr 스킬의 동작(모드, 확정 절차, 병합된 기록을 다루는 법)이 바뀌므로 독립 리뷰를 받는다.
- 포인터 줄은 원본의 두 곳과 전환본의 두 곳이 같은 뜻이고, 다른 것은 스킬을 가리키는 표기뿐이다.

검증(리뷰 전): 두 복사본 `cmp` 동일. `validate.cjs`(ajv 8.18.0, js-yaml 4.1.1, 공식 스키마 1.0.0)로 manifest valid, 스킬 4개, 파일 18개, 해석 링크 31개. 전환본 adr 스킬에 Claude 전용 표기와 없어진 모드의 말이 없는지, 포인터 줄이 전환본 두 곳에서 같은지 검사했다. `claude plugin validate .`와 `check_git_scopes.py` 통과.

구현 전 시험: 원본의 템플릿과 스킬은 하위 에이전트로 조정·블록만 읽기·판단·쓰기를 시험했고 모두 통과했다(원본 ADR 설계 문서의 "구현 전 시험 결과"). 전환본은 같은 문장을 담지만 Codex 런타임에서 돌려 보지는 않았다.

독립 리뷰: 별도 새 컨텍스트의 리뷰어가 pass(권고 2건)로 판정했다. must_fix는 없었고 권고는 둘 다 이 기록의 정확성에 관한 것이다. S1(컴포넌트 대응표의 `adr-template.md` 행이 아직 "상태"를 보존 조건으로 적고 있다)과 S2(바뀐 파일 목록에 계획 문서가 빠졌다)를 고쳤다. 전환본과 원본은 리뷰한 후보 그대로라 다시 검토받지 않았다. 지적과 조치는 [review.md](review.md)의 "2026-11-12: 0.9.0 반영의 독립 리뷰"에 있다.

최종 상태: 리뷰한 후보(`source-candidate.json` sha256 `e77e74d6bdf3ad9417413cf3a57f1082428dc2b82e5a02ab75f1228dec2b2435`, `target-candidate.json` sha256 `747bbc8c4f358688cbb0da633a805035139229005c201c2ece241b8eb7cca98f`)와 현재 파일이 같음을 확인한 뒤 `source-state.json`·`target-state.json`을 그 후보로 확정했고, 기본 `check_repository.py`가 통과했다. 미검증: Codex 설치·런타임(ADR 신규·바꿈, 포인터 줄 추가). 상태: 갱신 완료, 런타임 미검증.

## 2026-11-12: 원본 0.9.0의 릴리스 전 고침

원본 0.9.0을 릴리스하기 전에, 전체 리뷰가 Minor로 남긴 것 가운데 넷을 사용자 결정으로 고쳤다. 버전은 0.9.0 그대로다.

- 원본에서 바뀐 파일: `agents/domain-reviewer.md`, `skills/domain/SKILL.md`, `skills/adr/SKILL.md`, `CHANGELOG.md`, 그리고 설계 문서 셋(`docs/superpowers/specs/`의 두 설계 문서에 고친 문장과 "릴리스 전에 고친 것" 절이 더해졌고, `docs/superpowers/plans/`의 ADR 구현 계획의 지시문 한 곳을 고친 문장에 맞췄다).

| 원본 컴포넌트/동작 | Codex 대상 파일/호출 방식 | 처리 | 보존할 조건 | 검증 방법 |
|---|---|---|---|---|
| `agents/domain-reviewer.md` 정의 검토의 형식 항목: `미정` 항목의 갈 곳 셋(`규칙`, `알려진 어긋남`, 지운다), "필수 필드" 대신 "기본 뼈대의 역할·기능·분류·패키지가 도메인마다 있는가" | `skills/review/references/domain-reviewer.md` | adapt | 고친 두 문장이 원본과 같다 | 문자열 검사 |
| `skills/domain/SKILL.md` 수정 모드 1번의 `미정` 문장 | 같은 위치 | adapt | 문장 동일 | 문자열 검사 |
| `skills/adr/SKILL.md` 2절 머리(기록해 둔 결정을 바꾸면 바꿈, 같은 주제에 결정을 더하면 새 기록), 3절의 "2절의 1번부터 끝까지 따라 쓰고" | 같은 위치 | adapt | 문장 동일. 0.9.0 반영의 변형 다섯은 그대로다 | 원본과 diff |
| `CHANGELOG.md`, 설계 문서 | 없음 | omit | 기존 대응표대로 배포본에서 제외 | — |

- 스킬 진입점·인자·권한·트리거 경로는 바뀌지 않았다. 관리 파일은 18개 그대로다.
- adr 스킬의 신규·바꿈 판단과 리뷰어의 제안 문구가 바뀌므로 독립 리뷰를 받는다.

검증(리뷰 전): 고친 문장이 원본·전환본·설계 문서에 같은 글자로 있는지와 옛 문장이 남지 않았는지를 검사했다. 바이트 복사 네 파일은 `cmp`로 원본과 같다. adr 스킬의 원본과 전환본의 차이는 줄 수가 0.9.0 반영 때와 같다. `validate.cjs`(ajv 8.18.0, js-yaml 4.1.1, 공식 스키마 1.0.0)로 manifest valid, 스킬 4개, 파일 18개, 해석 링크 31개. `claude plugin validate .`와 `check_git_scopes.py` 통과.

시험(원본의 문구, 하위 에이전트, 조건마다 한 번): adr 스킬은 임시 git 저장소에서 고치기 전·후 문구로 "같은 주제에 결정을 더하는" 요청을, 고친 문구로 "기록해 둔 결정을 바꾸는" 요청을 돌렸다. 세 실행 모두 파일 결과가 기대와 같았고, 고치기 전 문구에서는 바꿈인지 신규인지를 먼저 물었다(원본 ADR 설계 문서의 "릴리스 전에 고친 것"). 리뷰어는 `미정` 칸에 어긋난 코드를 적은 항목이 섞인 문서로 정의 검토를 돌렸고 항목을 따로 다뤘다(원본 0.8.0 설계 문서의 "릴리스 전에 고친 것"). 전환본은 같은 문장을 담지만 Codex 런타임에서 돌려 보지는 않았다.

독립 리뷰: 별도 새 컨텍스트의 리뷰어가 pass(권고 2건)로 판정했다. must_fix는 없었다. R1(3절을 "2절의 1~9번대로 쓰고"로 고치자 2절 끝의 번호 없는 형식 문단이 범위에서 빠졌다)은 "2절의 1번부터 끝까지 따라 쓰고"로 고쳤고, R2(CHANGELOG 이행 안내의 "정한 방향과 다른 코드"가 스킬·리뷰어의 "정한 방향·경계와 다른 코드"와 달랐다)는 CHANGELOG와 0.8.0 설계 문서의 문장을 맞췄다. 파일이 바뀌었으므로 새 후보로 같은 리뷰어에게 바뀐 범위를 재검토받았고 pass(R1·R2 resolved, 새 지적 없음)였다. 지적과 조치는 [review.md](review.md)의 "2026-11-12: 0.9.0 릴리스 전 고침의 독립 리뷰"에 있다.

재검토 뒤의 시험: 3절의 마지막 문구로 "기록해 둔 결정을 바꾸는" 요청을 한 번 더 돌렸다. 바꿈으로 처리했고, 옛 기록의 결정 1 아래에 `바뀜` 줄과 새 기록 링크만 붙었으며, 새 기록의 `버린 안`에 옛 결정이 옛 파일 링크와 함께 있다.

최종 상태: 재검토한 후보(`source-candidate.json` sha256 `74ea8af13350a57cf2b4b5f69bbd58856969f9317bf2ec91a9389fa7fe7bd9df`, `target-candidate.json` sha256 `4ad5e65f9f2b310ce6dc73b5c580f69e4a5664a39a3297d874a38bf8b5ce9ee7`)와 현재 파일이 같음을 확인한 뒤 `source-state.json`·`target-state.json`을 그 후보로 확정했고, 기본 `check_repository.py`가 통과했다. 미검증: Codex 설치·런타임. 상태: 갱신 완료, 런타임 미검증.

## 2026-11-12: 비교 범위 조정을 이 브랜치에 합침

위 「2026-11-10: 원본 기준 비교 범위 조정」은 다른 작업 트리에서 커밋 없이 만든 변경이다. 사용자의 지시로 0.8.0·0.9.0 반영과 같은 브랜치에 가져왔다. 전환본과 대응표, 기준 상태는 이 일로 바뀌지 않았다.

- **가져온 것:** 여덟 파일. `.github/workflows/superdomain-codex.yml`, `.github/workflows/superglossary-codex.yml`, 루트 `AGENTS.md`, `CONTRIBUTING.md`, 두 `check_repository.py`, `porting/superglossary/decisions.md`는 그 작업 트리의 파일과 바이트가 같다. `porting/superdomain/decisions.md`(이 파일)는 두 쪽이 같은 자리 뒤에 절을 붙여 그대로는 합쳐지지 않았다. 2026-11-10 절을 글자 그대로 가져와 날짜순으로 넣었다.
- **독립 리뷰:** 받지 않았다. 2026-11-10 절이 적은 대로 검사 범위만 조정한 변경이고, 가져오면서 내용을 바꾸지 않았다. 생략을 독립 리뷰 통과로 기록하지 않는다.
- **0.8.0 리뷰의 S2:** 풀렸다. 설계 문서 여섯 개가 없는 체크아웃에서도 `check_repository.py`가 통과한다. 비교 범위 조정이 기준 상태와 같이 또는 먼저 들어가야 성립하고, 이 브랜치에서는 같이 들어간다. 설계 문서 여섯 개는 그래도 같은 PR에 넣는다(스펙과 계획이 이 변경의 근거다).

검증 결과: 작업 트리에서 두 플러그인의 `check_repository.py`와 `check_git_scopes.py`, tree_state 단위 검사 6개, `claude plugin validate .`가 통과했다. 두 workflow 파일은 YAML로 읽히고 `push`·`pull_request` 경로에 원본 폴더가 있다. 미추적 설계 문서 여섯 개를 뺀 사본(저장소 밖 임시 폴더)에서 옛 검사 스크립트는 그 여섯 경로를 `removed`로 지목하며 실패했고, 가져온 스크립트는 걸러 낸 경로를 한 줄로 출력하고 통과했다. 같은 사본에서 `skills/adr/SKILL.md`에 한 글자를 더하면 가져온 스크립트도 그 경로를 지목하며 실패한다. 사본 시험은 로컬에서 한 것이고, GitHub의 실제 workflow 실행은 미검증이다.
