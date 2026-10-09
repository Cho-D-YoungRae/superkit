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
