# 독립 리뷰 이력

확인일: 2026-10-09. 리뷰어: 별도 새 컨텍스트의 `superdomain_port_review`. 파일 수정·설치·추가 위임 없이 검토했다.

판정: **pass**. 미해결 must_fix 및 권고 없음.

## 검토 범위와 상태

최초 검토는 원본 네 스킬·두 리뷰어·가이드/템플릿·manifest/README/라이선스와 전환본 17개 파일 전체다. 입력·기본값·범위, 사용자 확인, 독립 위임과 실패 처리, 판단·출력 계약, 내부 리소스, 설치 안내·검증 기록을 대조했다. 과거 CHANGELOG 및 0.4.0 개발 기록은 배포에서 제외된 근거를 확인했다. 기존 대상이 없는 최초 생성이므로 기존 사용자 수정 보존·갱신 충돌은 해당하지 않는다.

재검토는 R1 수정과 README의 언어 범위 설명에 한정했다. 원본과 나머지 대상 파일이 이전 검토 상태와 동일함을 확인했다.

| 상태 파일 | SHA-256 | 용도 |
|---|---|---|
| `source-state.json` | `23bf2beca718717d7dbbe5cf73f0febbe8c7bf6919bb58b69bf50aa0a5ac9aeb` | 시작·1차·최종 리뷰에서 같은 원본 후보를 확인 후 확정 |
| 임시 `target-candidate.json` | `d4c807f87aec9ab3bd6d045d233aed3912c28b1b8f5a482ff545337d645cea02` | 1차 전체 리뷰 대상 |
| 최초 생성 확정 대상 스냅샷 | `b58fd9686c77d3b4f033face368612567af6712eb880417192c0e505adff2910` | README 수정 후 `target-candidate-v2.json`을 재검토하고 확정 |
| `managed-paths.json` | `912c895369c24189934ffd76f51ac742e9f571da93aca2cef802912e8729a4ff` | 검토한 17개 파일 목록 |

후보 디렉터리: `/private/tmp/superdomain-codex-dw9bt86b/`. 이 표는 최초 생성 때 검토한 상태를 기록한다. 이후 배치 변경에서는 target-state.json이 새 검토 상태로 갱신되며, 그 결과는 이 문서 끝에 추가한다.

## 검증 근거

리뷰어가 직접 확인·실행한 내용:

- `validate.cjs`: 공식 schema로 manifest valid, 네 스킬·17개 파일·내부 링크 29개 통과. README 수정 후에도 재실행했다.
- `check_git_scopes.py`: 기준 브랜치 누락, 기본 범위, 공백 경로, 커밋 범위, 리비전 자료 읽기, 빈 범위 통과.
- 원본·대상의 후보 대비 스냅샷 비교에서 추가·변경·삭제 없음. 1차/2차 후보 사이 변경은 README 하나뿐이다.
- 가이드·컨벤션·ADR 템플릿·LICENSE 네 파일의 원본 대비 바이트 동일성, 후보·공식 스키마 SHA-256 일치.
- [공식 패키징](https://developers.openai.com/plugins/build/plugins), [스킬](https://learn.chatgpt.com/docs/build-skills), [서브에이전트](https://learn.chatgpt.com/docs/agent-configuration/subagents) 문서와 패키지 구조·표시 정보·선택 방식·custom agent 설명 대조.

메인에게 전달받은 결과로 구분한 내용:

- 독립 임시 경로에 패키지만 복사한 검사.
- skill-creator `quick_validate.py` 네 스킬 통과.
- 원본 `claude plugin validate .` 통과.
- 작업 시작 대비 원본 불변성.

## 지적과 조치

| ID | 구분 | 상태 | 원본 근거 | 대상 위치 | 문제와 사용자 영향 | 조치·검증 |
|---|---|---|---|---|---|---|
| R1 | suggestion | resolved | `plugins/superdomain/README.md:64` | `plugins/superdomain-codex/README.md:39` (이동 전에도 같은 행) | 도메인 리뷰까지 Kotlin·Java로 제한하는 것으로 읽힐 여지가 있었음 | 메인이 언어 범위를 명확히 수정. 리뷰어가 원본 의미와 일치함을 직접 재확인 |

1차 판정은 권고 1건과 함께 pass였고, 메인이 자발적으로 수정한 뒤 재검토에서도 pass를 받았다. must_fix는 없었다.

## 미검증

실제 설치·스킬 발견/선택, 모델의 사용자 확인 준수, 새 컨텍스트 병렬 위임과 실패 처리, 실제 프로젝트 문서 생성·변경은 실행하지 않았다. 요청 범위 밖이므로 파일 생성 완료를 막지는 않지만 런타임 통과를 의미하지 않는다.

도구 차단은 미검증 기능이 아니라 **사용자가 선택한 전환 방식에서 제공하지 않는 기능**이다. 읽기 전용·재위임 금지를 행동 지침으로 전달하며, README와 실행 계약에 원본과의 강제력 차이를 명시했다.

## 2026-10-09: 배치 변경의 독립 리뷰

판정: **pass**. 리뷰어는 별도 새 컨텍스트의 `superdomain_layout_review`다. 미해결 must_fix·suggestion 없음. 파일 수정·설치·추가 위임 없이 검토했다.

검토 범위는 이동 전후 패키지·기준 상태, 전환 스킬 문서 2개, 저장소 안내, Codex 카탈로그, CI와 검사 코드, 전환 기록의 경로다. 변경되지 않은 업무 규칙은 위 최초 리뷰를 재사용했다. 패키지 17개에 추가·삭제가 없고 README 설치 안내와 manifest homepage만 변경되었음을 확인했다.

검토한 상태(후보 디렉터리 `/private/tmp/superdomain-layout-04ralrrn/`):

| 상태 파일 | SHA-256 |
|---|---|
| source-before.json | `23bf2beca718717d7dbbe5cf73f0febbe8c7bf6919bb58b69bf50aa0a5ac9aeb` |
| target-before.json | `b58fd9686c77d3b4f033face368612567af6712eb880417192c0e505adff2910` |
| target-candidate.json → 현재 target-state.json | `8acef553f64dbeae63ad2acfb5a3fb0f0d86f84ba1bad4a632baa38d8090b59a` |
| managed-paths-before.json | `912c895369c24189934ffd76f51ac742e9f571da93aca2cef802912e8729a4ff` |
| support-files-candidate.json | `bf7ddf361408ca36d28e2c037580b8c6d8cca28a0ea898e7944d4e3abbf88b50` |

직접 실행·확인한 검증:

- `check_repository.py --target-state <후보>` 통과. 카탈로그 경로·manifest 이름·수동 설치 정책과 기존 위치 우선 정책을 확인했다.
- 패키지와 독립 복사본의 schema/스킬/링크 검사 각각 4 skills, 17 files, 29 links 통과.
- 원본·대상·독립 복사본의 후보 대비 추가·변경·삭제 없음. 지원 파일 후보는 리뷰 종료까지 동일했다.
- Git 범위 fixture, tree_state 단위검사 6개, workflow YAML·트리거 검사와 git diff 공백 검사 통과.
- OpenAI 공식 패키징/마켓플레이스 문서와 setup-node 공식 사용법에서 사용한 형식·액션을 확인했다.

전달받은 결과로 구분한 검증: skill-creator 형식 검사 5개, 기존 marketplace CI Python 코드, `claude plugin validate .`.

| ID | 구분 | 상태 | 원본 근거 | 대상 위치 | 문제와 사용자 영향 | 필요한 조치·검증 |
|---|---|---|---|---|---|---|
| 없음 | — | — | — | — | 지적 없음 | — |

미검증: GitHub workflow의 실제 실행, 앱의 카탈로그 발견·설치·스킬 선택·모델 실행. 로컬 검증과 독립 리뷰 pass가 런타임 통과를 뜻하지 않는다.

리뷰 후 메인은 검토된 후보를 target-state.json으로 확정하고 기본 check_repository 검사로 다시 확인했다. 원본 기준·관리 목록은 보존했다. 이 결과 기록과 기준 확정 외에 리뷰한 파일 내용은 바꾸지 않았다.

## 2026-11-12: 0.8.0 반영의 독립 리뷰

판정은 1차 pass(권고 2건), 권고 조치 뒤 재검토 pass다. must_fix는 없었다. 별도 새 컨텍스트의 리뷰어가 읽기 전용으로, 재위임 없이 검토했다.

검토 범위는 원본과 전환본의 0.8.0 변경 전부(HEAD 대비 작업 트리 diff의 대응 파일: 가이드, 컨벤션 문서 둘, 스킬 세 개, 리뷰어 문서 둘, manifest, README), 전환본의 실행 계약(`dispatch.md`)과 `agents/openai.yaml` 넷, 전환 기록의 0.8.0 절, 관리 파일 목록, 검사 코드다. 원본에 더해진 설계 문서 여섯 개는 배포본 제외 대상이라 머리말만 읽었다.

검토한 상태(후보 디렉터리 `$TMPDIR/superdomain-080/`):

| 상태 파일 | SHA-256 |
|---|---|
| source-candidate.json → 현재 source-state.json | `c6edba9a1740dde2778856d2b16de7aa5d01e33f246264fad67fe6edddb9942e` |
| target-candidate.json (1차 검토) | `9a00656b81114ec58c571e354113b0b7419e615818ab4ff302f2ebc1bf27fb91` |
| target-candidate2.json (재검토) → 현재 target-state.json | `36f0ada5a0b2be5571f4c066f4631dfee178b2424f7bf00c2a4f7c399e79ec7f` |

리뷰어가 직접 실행·확인한 검증:

- 바이트 복사 세 파일(`domain-guide.md`, `conventions.md`, `architecture-tests.md`)이 원본과 `cmp`로 같다.
- 손으로 합친 다섯 파일은 원본과 전환본의 변경 줄을 대조했고, 차이는 기존 변형(상대 링크, 스킬을 가리키는 표기, Codex 표기, "읽기 전용 검색(rg 등)", frontmatter·실행 계약 문단)뿐이다.
- 이번 변경으로 전환본에 Claude 전용 표기(`/superdomain:`, `${CLAUDE_SKILL_DIR}`, `${CLAUDE_PLUGIN_ROOT}`, 플랫폼을 가리키는 "Claude")가 새로 들어가지 않았다. 바이트 복사 파일의 새 줄도 플랫폼 중립이다.
- 전환본 `.md`의 상대 링크는 ADR 템플릿의 기존 자리표시자·예시 파일명을 빼고 모두 풀린다.
- 두 후보는 검토 시점의 파일과 추가·변경·삭제가 없다. 두 전환본 후보의 차이는 `skills/review/references/dispatch.md` 한 파일뿐이다. 관리 파일 18개와 후보의 파일 목록이 같다.
- `check_repository.py --target-state <후보>`는 카탈로그·manifest 검사를 통과하고 원본 기준 상태 비교에서 멈췄다(기준 상태가 0.7.0의 것이라 예상된 실패다). 그 뒤의 전환본 후보 비교와 관리 파일 검사는 리뷰어가 직접 재현해 확인했다.

| ID | 구분 | 상태 | 원본 근거 | 대상 위치 | 문제와 사용자 영향 | 필요한 조치·검증 |
|---|---|---|---|---|---|---|
| S1 | suggestion | resolved | `agents/domain-reviewer.md` 정의 검토의 간결성 검사, `domain-guide.md` 「간결하게 쓰는 기준」의 분량 | `skills/review/references/dispatch.md` 허용 작업 | "글자 수 세기"가 방법을 정하지 않아, 리뷰어가 계약 위반을 걱정해 눈대중으로 세거나 해석이 갈릴 수 있었다 | "글자 수 세기(파일을 읽기만 하는 한 줄 명령으로 세고 파일을 쓰지 않는다)"로 고치고 후보를 다시 떠 재검토받았다. 재검토 pass |
| S2 | suggestion(절차) | resolved | `plugins/superdomain/docs/superpowers/**`(미추적 여섯 개) | `source-state.json` | 원본 기준 상태에 아직 git에 없는 설계 문서 여섯 개가 들어 있다. 이 문서들을 커밋하지 않으면 깨끗한 체크아웃(CI)에서 `check_repository.py`가 실패한다 | 기준 상태와 설계 문서 여섯 개를 같은 커밋에 넣는다. 이 기록을 쓰는 시점에는 사용자가 커밋을 허락하지 않아 모든 변경이 작업 트리에 있다. 같은 날 비교 범위 조정을 이 브랜치에 가져와 풀렸다: 설계 문서가 없어도 검사가 통과한다. 비교 범위 조정이 기준 상태와 같이 또는 먼저 들어가야 성립한다([decisions.md](decisions.md)의 "2026-11-12: 비교 범위 조정을 이 브랜치에 합침") |

미검증: `check_git_scopes.py`·`validate.cjs`·`claude plugin validate .`는 리뷰어가 아니라 메인이 실행했다(decisions.md의 0.8.0 절). Codex 설치·런타임 동작과 리뷰어가 실제로 글자 수를 세는 방식은 확인하지 않았다. 로컬 검증과 독립 리뷰 pass가 런타임 통과를 뜻하지 않는다.

리뷰 후 메인은 검토된 후보를 `source-state.json`·`target-state.json`으로 확정하고 기본 `check_repository.py` 검사로 다시 확인했다. 이 결과 기록과 기준 확정 외에 리뷰한 파일 내용은 바꾸지 않았다.

## 2026-11-12: 0.9.0 반영의 독립 리뷰

판정은 pass(권고 2건)다. must_fix는 없었다. 별도 새 컨텍스트의 리뷰어가 읽기 전용으로, 재위임 없이 검토했다. 0.8.0의 기준 상태(해시)와 견줘 0.9.0에서 바뀐 파일만 봤다(원본 9개, 전환본 7개, 추가·삭제 없음).

검토 범위는 원본과 전환본의 `skills/adr/SKILL.md`·`skills/adr/adr-template.md` 전문, `skills/domain/SKILL.md`의 바뀐 세 곳, 전환본의 `plugin.json`·`skills/adr/agents/openai.yaml`·`README.md`, 원본 manifest와 `conventions.md`의 변경, 전환 기록의 0.9.0 절과 함께 고친 세 줄, 관리 파일 목록, 검사 코드다.

검토한 상태(후보 디렉터리는 세션 스크래치패드의 `baseline090/`):

| 상태 파일 | SHA-256 |
|---|---|
| source-candidate.json → 현재 source-state.json | `e77e74d6bdf3ad9417413cf3a57f1082428dc2b82e5a02ab75f1228dec2b2435` |
| target-candidate.json → 현재 target-state.json | `747bbc8c4f358688cbb0da633a805035139229005c201c2ece241b8eb7cca98f` |

리뷰어가 직접 실행·확인한 검증:

- 바이트 복사 두 파일(`adr-template.md`, `conventions.md`)이 원본과 `cmp`로 같다.
- adr 스킬의 원본과 전환본의 차이는 정해 둔 변형 다섯뿐이다("다음 세션의 Codex다", 템플릿 상대 링크와 링크 해석 문단, domain 스킬을 가리키는 표기 두 곳, 6절 포인터 항목의 대상 지침 파일 설명, 포인터 줄의 스킬 표기). 모드, 쓰는 기준과 예시, 확정 절차, 병합 전/뒤에 고쳐도 되는 것, `바뀜`·`대체됨` 줄, 찾아 읽기, 후속 제안, 하지 않는 것은 문장이 같다.
- domain 스킬의 바뀐 세 곳은 원본과 같다. 포인터 줄은 원본 두 곳이 서로 같고 전환본 두 곳이 서로 같으며, 둘의 차이는 스킬을 가리키는 표기뿐이다.
- 전환본에 Claude 전용 표기가 새로 남지 않았다(남은 것은 README의 기반 버전 문장과 "Claude Code 버전과의 차이" 절처럼 전부터 있던 비교 문맥이다). 없어진 상태·모드의 말(`proposed`·`accepted`·`superseded`·부분 조정·40~60줄)은 전환본과 원본의 스킬·에이전트 문서에 없다.
- 전환본 `.md`의 상대 링크는 템플릿 예시의 파일 이름 둘과 자리표시자를 빼고 모두 풀린다.
- 두 후보는 검토 시점의 파일과 추가·변경·삭제가 없다. 관리 파일 18개가 후보의 파일 목록과 같다. `check_repository.py --target-state <후보>`는 카탈로그·manifest 검사를 통과하고 원본 기준 상태 비교에서 멈췄다(기준이 0.8.0의 것이라 예상된 실패다). 멈춰서 돌지 않은 검사는 리뷰어가 직접 재현했다.
- 실행 환경과의 긴장은 없다. 병합 여부는 git으로 판단할 수 있고, "하위 에이전트"는 다른 작업의 일부로 쓰일 때를 설명하는 문장일 뿐 이 스킬이 띄우라는 지시가 아니다.

| ID | 구분 | 상태 | 원본 근거 | 대상 위치 | 문제와 사용자 영향 | 필요한 조치·검증 |
|---|---|---|---|---|---|---|
| S1 | suggestion | resolved | 0.9.0 템플릿에는 상태가 없다 | `decisions.md` 컴포넌트 대응표의 `adr-template.md` 행 | 보존할 조건이 "상태와 메타데이터·본문 형식"으로 남아, 다음 전환자가 상태를 보존 대상으로 오해할 수 있다 | "머리 줄·결정 블록·`바뀜`/`대체됨` 줄의 형식, 적지 않는 것, 분량"으로 고쳤다 |
| S2 | suggestion | resolved | 0.8.0 기준 대비 계획 문서도 바뀌었다 | `decisions.md` 0.9.0 절의 바뀐 파일 목록 | 바뀐 설계 문서로 스펙만 적혀 있었다. 배포본에서 제외되는 파일이라 동작에는 영향이 없다 | 계획 문서를 목록에 더했다 |

0.8.0 리뷰의 S2(원본 기준 상태에 아직 커밋되지 않은 설계 문서가 들어 있다)는 그대로 열려 있다. 기준 상태와 설계 문서 여섯 개를 같은 커밋에 넣어야 한다. (이 리뷰 뒤에 풀렸다: [decisions.md](decisions.md)의 "2026-11-12: 비교 범위 조정을 이 브랜치에 합침".)

미검증: `claude plugin validate .`·`check_git_scopes.py`·`validate.cjs`는 메인이 실행했다(decisions.md의 0.9.0 절). Codex 설치·런타임의 ADR 신규·바꿈과 포인터 줄 추가는 확인하지 않았다. 로컬 검증과 독립 리뷰 pass가 런타임 통과를 뜻하지 않는다.

리뷰 후 메인은 권고 둘을 전환 기록에 반영하고, 검토된 후보를 `source-state.json`·`target-state.json`으로 확정한 뒤 기본 `check_repository.py` 검사로 다시 확인했다. 리뷰한 원본과 전환본의 파일은 바꾸지 않았다.

## 2026-11-12: 0.9.0 릴리스 전 고침의 독립 리뷰

판정은 pass다. must_fix는 없었고 권고 2건은 반영한 뒤 재검토에서 resolved가 됐다. 별도 새 컨텍스트의 리뷰어가 읽기 전용으로, 재위임 없이 검토했다. 0.9.0 반영의 기준 상태와 견줘 바뀐 파일만 봤다(원본 7개, 전환본 3개, 추가·삭제 없음).

검토 범위는 원본의 `CHANGELOG.md`·`agents/domain-reviewer.md`·`skills/adr/SKILL.md`·`skills/domain/SKILL.md`와 설계 문서 셋, 전환본의 `skills/adr/SKILL.md`·`skills/domain/SKILL.md`·`skills/review/references/domain-reviewer.md`다. 연결된 가이드(기본 뼈대, 알려진 어긋남), 템플릿의 `바뀜`·`대체됨` 규칙, adr 스킬의 모드 표도 함께 읽었다.

검토한 상태(후보 디렉터리는 세션 스크래치패드의 `baseline090b/`와, 권고를 반영한 뒤의 `baseline090c/`):

| 상태 파일 | SHA-256 |
|---|---|
| 첫 검토의 source-candidate.json | `ed81ba6868228d1ee6fd0716cd66253d0dfd91c5436f547e3b7751319c53343f` |
| 첫 검토의 target-candidate.json | `5f9108c597d5f1926bc6aff02243cac0cb185b2324aff25ecb84a4f8322a8df7` |
| 재검토의 source-candidate.json → 현재 source-state.json | `74ea8af13350a57cf2b4b5f69bbd58856969f9317bf2ec91a9389fa7fe7bd9df` |
| 재검토의 target-candidate.json → 현재 target-state.json | `4ad5e65f9f2b310ce6dc73b5c580f69e4a5664a39a3297d874a38bf8b5ce9ee7` |

리뷰어가 직접 실행·확인한 검증:

- 이전 기준과 견준 변경 범위가 위 목록과 같고, 후보는 검토 시점의 파일과 추가·변경·삭제가 없다. 관리 파일 18개가 후보의 파일 목록과 같다.
- 바이트 복사 파일(`adr-template.md`, `conventions.md`, `architecture-tests.md`, `domain-guide.md`)과 `LICENSE`가 원본과 `cmp`로 같다.
- 고친 문장(리뷰어 형식 항목, domain 수정 모드 1번, adr 2절 머리와 3절)이 원본과 전환본에서 같은 글자다. 남은 차이는 0.9.0 반영 때 정해 둔 전환본 전용 변형뿐이다.
- 옛 문장("필수 필드", "2절대로", "같은 주제의 기록이 있으면")이 배포 파일에 남아 있지 않다. CHANGELOG 0.8.0 절에 동작 변화 셋과 `미정`의 세 갈래가 있다.
- 리뷰어 형식 항목의 네 칸이 가이드의 뼈대와 맞고, `미정`의 세 갈래가 가이드의 `알려진 어긋남` 정의와 맞으며, adr 2절 머리가 1절 모드 표와 템플릿의 `바뀜` 규칙과 어긋나지 않는다.
- `check_repository.py --target-state <후보>`는 카탈로그·패키지 검사를 통과하고 원본 기준 상태 비교에서 멈췄다(기준이 이전 것이라 예상된 실패다). 멈춰서 돌지 않은 검사는 리뷰어가 직접 재현했다. `check_git_scopes.py`와 `claude plugin validate .`는 통과했다.

| ID | 구분 | 상태 | 원본 근거 | 대상 위치 | 문제와 사용자 영향 | 필요한 조치·검증 |
|---|---|---|---|---|---|---|
| R1 | suggestion | resolved | adr 스킬 3절, 2절 끝의 형식 문단 | 전환본 adr 스킬의 같은 두 곳 | 3절을 "2절의 1~9번대로 쓰고"로 고치자 9번 뒤의 번호 없는 문단(형식은 지침 파일이 정한다)이 범위에서 빠졌다. 바꿈으로 새 ADR을 쓸 때 지침 파일이 정한 형식을 따르라는 규칙이 글자로는 적용되지 않는다 | "2절의 1번부터 끝까지 따라 쓰고"로 고쳤다. 원본과 전환본이 같은 글자이고 2절 머리로 되돌아가지 않는다 |
| R2 | suggestion | resolved | `CHANGELOG.md` 0.8.0 이행 절의 `미정` 항목 | 없음(배포 제외) | 이행 안내는 "정한 방향과 다른 코드", 스킬·리뷰어·가이드는 "정한 방향·경계와 다른 코드"였다. 동작에는 영향이 없다 | CHANGELOG와 0.8.0 설계 문서의 같은 문장을 "방향·경계"로 맞췄다 |

0.8.0 리뷰의 S2(원본 기준 상태에 아직 커밋되지 않은 설계 문서가 들어 있다)는 그대로 열려 있다. 기준 상태와 설계 문서 여섯 개를 같은 커밋에 넣어야 한다. (이 리뷰 뒤에 풀렸다: [decisions.md](decisions.md)의 "2026-11-12: 비교 범위 조정을 이 브랜치에 합침".)

미검증: `validate.cjs`는 메인이 실행했다(decisions.md의 이번 절). Codex 설치·런타임은 확인하지 않았다. 이전 기준 시점의 파일 내용은 해시만 남아 있어, 전환본 전용 변형이 그대로라는 것은 지금의 차이가 0.9.0 절의 대응표와 맞는지로 확인했다. 로컬 검증과 독립 리뷰 pass가 런타임 통과를 뜻하지 않는다.
