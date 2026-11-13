# superglossary Codex 전환

현재 0.8.0 갱신 결정은 문서 끝의 **2026-11-13** 절을 따른다. 앞의 0.7.0 종료 리비전 사전·관례 예외·이전 안내는 당시 전환 기록이며 현재 규칙이 아니다.

확인일: 2026-10-09. 원본 Git 기준: `e71ae9bacbaa7b7afe42c0ae533216ecc5285b3d` (`main`). 최초 생성이며 이전 대상·사용자 수정·관리 기준은 없었다.

## 범위

- 원본: `plugins/superglossary/`, name `superglossary`, 업무 버전 `0.7.0`.
- 대상: `plugins/superglossary-codex/`, 같은 name·버전. portable 루트 `plugin.json`과 `skills/`를 배포한다.
- 대상 표면: 로컬 Codex 데스크톱 수동 설치용 패키지. 현재 세션의 `collaboration.spawn_agent`는 `fork_turns: "none"`을 지원한다. 특정 도구가 모든 클라이언트에 있다고 가정하지 않는다.
- 최초 생성 요청은 파일 작성과 검증만 포함했다. 원본·카탈로그·개인/프로젝트 설정을 보존했다. 이후 사용자의 noguesstoday 설치 요청으로 등록·배포를 추가한 내역은 이 문서 끝에 기록한다.
- 사용자는 앞선 superdomain 전환에서 패키지 내부 역할 문서와 서브에이전트를 선택했으며, 읽기 전용·재위임 금지가 원본 도구 차단과 같지 않음을 수용했다. 이번 스캐너에도 같은 전환 방식을 적용한다고 작업 전에 알렸다. 강제 도구 제한이 동등하다는 보장은 하지 않는다.

## 확인한 근거

2026-10-09에 다음 공식 문서 본문을 열어 확인했다. 공개 디렉터리 제출 제약을 로컬 패키지 제약으로 일반화하지 않는다.

| 근거 | 적용 내용 |
| --- | --- |
| [OpenAI 패키징](https://developers.openai.com/plugins/build/plugins) | 루트 portable manifest, 기본 skills 경로, `extensions.com.openai` 표시 메타데이터, 별도 카탈로그 등록 |
| [Codex 스킬](https://learn.chatgpt.com/docs/build-skills) | name/description과 보조 리소스, UI YAML, implicit invocation 기본값 유지 |
| [Codex 서브에이전트](https://learn.chatgpt.com/docs/agent-configuration/subagents) | custom agent 설정과 플러그인 역할 문서를 구분. 세션 도구에 필요한 입력을 전달 |
| [Claude 플러그인](https://code.claude.com/docs/en/plugins-reference) | manifest 선언과 기본 디렉터리 조사 |
| [Claude 스킬](https://code.claude.com/docs/en/skills) | 인자 힌트·스킬 디렉터리 변수·도구 사전 허용을 별도로 전환 |
| [Claude 에이전트](https://code.claude.com/docs/en/sub-agents) | 에이전트 tools allowlist와 sonnet 고정 확인. Codex 행동 지침과 강제력 차이 기록 |

현재 원본에는 manifest 추가 경로·commands·hooks·MCP·settings·실행 파일·프로젝트 스킬 생성기가 없다. 두 SKILL.md, guide, scanner와 README의 사용/이전 안내가 배포 동작의 입력이다. AGENTS.md와 개발 스펙·계획의 목표·비목표·구조를 확인해 개발 자료로 분류했으며 자동 실행 대상으로 취급하지 않는다.

## 컴포넌트 대응

| 원본 컴포넌트/동작 | Codex 대상 파일/호출 방식 | 처리 | 보존할 조건 | 검증 방법 |
| --- | --- | --- | --- | --- |
| `.claude-plugin/plugin.json` | `plugin.json` | adapt | name·version·저자·MIT·keywords 유지, 설명·homepage를 전환본에 맞춤 | 공식 portable schema, 원본 필드 대조 |
| `skills/glossary/SKILL.md` | 같은 스킬 경로 | adapt | 자동 등록 트리거, 생성 동의, 충돌·수정/삭제 조건, 가나다순, 300개 초과 분리 제안, 사용자 확정 | 원본 대조·형식 검사·독립 리뷰 |
| glossary의 `argument-hint`·`allowed-tools` | 본문의 입력 계약·실제 세션 도구 | adapt | 인자 의미와 단계 유지. 권한 사전 허용을 Codex 권한 확대나 강제 화이트리스트로 옮기지 않음 | frontmatter 잔여 필드 검사 |
| glossary 생성 중 Agent 호출 | `skills/glossary/references/scanner-dispatch.md` | replace | 동의 후 새 컨텍스트, 자료만 전달, 결과 대기, 사용자 후보 선택 | 호출자·계약·실패 경로 대조 |
| `agents/glossary-scanner.md` | `skills/glossary/references/glossary-scanner.md` | adapt | 단어·혼용·예외 후보의 세 출력, 근거 위치, 실측 빈도, 노이즈/기존 용어 제외, 사용자 표준 선정 | 원본/역할 대조. 추가로 집계 기준·미검토 범위 표시 |
| scanner `tools: Read, Grep, Glob` | 읽기·검색 전용 행동 지침 | replace | 편집·외부 작업·재위임 금지 의도. 도구 제거/샌드박스 강제는 제공하지 않음 | README·호출·역할 간 동일한 제한 확인 |
| scanner `model: sonnet` | 부모 Codex 세션 모델 상속 | replace | 별도 제공자 모델을 임의 GPT 모델로 매핑하지 않음 | dispatch에 모델 미지정 명시 |
| `skills/check/SKILL.md` | 같은 스킬 경로 | adapt | 서브에이전트 없이 변경 검토, 기본/경로/커밋 입력, 네 판단 종류, 기존 관례 예외, 두 표 출력, 파일 수정 금지 | Git fixture와 원본 대조 |
| check의 Git 범위 | `-C`, NUL 경로 목록, staged/unstaged 개별 diff, 종료 리비전 자료 읽기 | adapt | 다른 cwd·공백 경로·작업 트리와 커밋의 불일치를 피함. 잘못된 범위는 기본 범위로 바꾸지 않음 | `check_git_scopes.py` |
| `skills/glossary/glossary-guide.md` | 같은 내부 경로 | adapt | 세 기본 용어, 표 형식·이스케이프, 충돌, 활용형, 분리 전후 행 수·유일성. 플랫폼명과 호출 표기만 변경 | 허용된 문자열 치환 외 바이트 동일성 확인 |
| 사용자 생성 Markdown·지침 포인터 | 같은 `docs/superglossary/`, 기존 지침 정책 | adapt | 새 데이터 경로 없음. 동의 후 포인터 한 줄. 기존 CLAUDE 포인터 중복 방지·Codex 명시 읽기 안내. 지침 파일 자동 생성 없음 | 템플릿·스킬·README 대조 |
| README·CHANGELOG의 0.6→0.7 이전 안내 | 대상 README의 기존 용어집 절 | adapt | 옛 JSON 필드 매핑, 새 형식에서 제외되는 필드, 사용자 데이터 보존 | 필드별 대조; 실제 데이터 이전 미실행 |
| `LICENSE` | `LICENSE` | copy | 원본 MIT와 저작권 | 바이트 비교 |
| 원본 README의 Claude 설치 명령·옛 마켓플레이스 ID | Codex 설치 준비 안내 | replace | 미등록 ID를 즉시 설치 가능하다고 안내하지 않음 | 실제 카탈로그 상태 확인 |
| `AGENTS.md`, `docs/superpowers/`, 과거 CHANGELOG 전체 | 배포 제외, 이 기록에서 분류 | omit | 개발 절차·과거 CLI를 런타임 기능으로 복원하지 않음. 현재 이전 안내는 README에 보존 | 전체 원본 파일 목록 대조 |
| Codex UI 정보 | 두 `agents/openai.yaml` | adapt | 표시 정보만 제공. agent 등록·자동 호출 금지 정책 아님 | YAML parser·기본 정책 확인 |

## 주요 결정

1. `glossary`와 `check` 모두 원본의 자동 선택 가능성을 유지한다. `allow_implicit_invocation: false`를 추가하지 않는다. 호출명은 `$superglossary:glossary`·`$superglossary:check`로 안내한다.
2. 패키지 리소스는 제공된 SKILL.md의 실제 위치에서 내부 링크로 해석한다. 개발 머신·캐시·다른 플러그인을 런타임에서 참조하지 않는다. check에서 glossary guide로 가는 `../`는 같은 패키지 내부다.
3. scanner는 초기 용어집 생성 때 사용자가 코드 스캔에 동의한 경우만 호출한다. 모델·역할 자동 등록을 가정하지 않고 실패/중단은 스캔 미완료로 표시한다. 기본 용어집 생성은 스캔 실패와 별개로 보존한다.
4. scanner 빈도는 검색 결과의 실제 수치이며 단위를 명시한다. 최다 빈도는 참고로만 제공하고 표준 선정·혼용 변형의 금지 등록은 사용자에게 맡긴다.
5. 프로젝트 AGENTS.md의 지침 파일 정책을 보존한다. 기존 CLAUDE 계열을 사용하는 경우 Codex 자동 로딩을 약속하지 않는다. 같은 경로의 기존 포인터가 있으면 중복 쓰기나 무단 치환을 하지 않는다.
6. check는 커밋 범위의 종료 리비전에서 용어집과 코드를 읽게 했다. 작업 트리의 파일 유무나 다른 사전 버전으로 과거 변경을 판정하지 않는다. 추가·삭제·표시명 변경 없이 원본 사용자 진입점을 유지한다.

## 검증 명령

저장소 루트에서 실행한다. 검증 도구는 전환 기록에만 있으며 설치 패키지에 포함하지 않는다. Node.js 검사는 `ajv@8.18.0`, `js-yaml@4.1.1`이 필요하고 Python 검사는 표준 라이브러리만 사용한다.

```bash
node porting/superglossary/validate.cjs plugins/superglossary-codex "$SCHEMA_FILE"
python3 porting/superglossary/check_git_scopes.py
python3 .agents/skills/claude-to-codex/scripts/tree_state.py compare porting/superglossary/source-state.json plugins/superglossary
python3 .agents/skills/claude-to-codex/scripts/tree_state.py compare porting/superglossary/target-state.json plugins/superglossary-codex
claude plugin validate .
claude plugin validate plugins/superglossary
```

`SCHEMA_FILE`은 [공식 schema](https://agent-plugins.org/schemas/1.0.0/plugin.schema.json)를 다운로드한 실제 경로다. 독립 임시 경로에 대상 패키지만 복사한 뒤 동일한 Node 검사를 실행한다. 스킬 형식은 사용 가능한 skill-creator `scripts/quick_validate.py` 또는 실제 YAML parser로 검사한다.

## 상태와 리뷰

현재 상태: **패키지 생성·정적 검증 완료, 런타임 미검증**. 별도 새 컨텍스트의 `superglossary_port_review`가 전체 전환을 검토해 pass로 판정했다. must_fix·suggestion 모두 없음. 검토한 파일 상태와 일치함을 확인한 뒤 source-state.json·target-state.json·managed-paths.json을 확정했다. 자세한 근거·검토 상태·검증 구분은 [review.md](review.md)에 있다. 기존 파일의 갱신·삭제는 없고 원본과 두 카탈로그는 보존했다.

- 공식 schema·YAML/frontmatter·패키지 경로 검사: 2 skills, 10 files, 내부 링크 9개 통과.
- 공백을 포함한 독립 임시 위치에 패키지만 복사하여 같은 검사 통과. 원본 경로를 링크로 참조하지 않는다.
- skill-creator quick_validate 두 스킬 통과. 사용 가능한 PyYAML 의존성 경로를 프로세스에만 전달했다.
- Git fixture: staged/unstaged 별도 변경, untracked·공백 경로·ignored/삭제 파일, 커밋 전용 diff·종료 리비전 용어집, 빈/잘못된 범위 통과. 문서의 세 경로 선택 명령과 커밋 범위 diff 명령을 직접 추출해 실행했다.
- LICENSE 원본과 바이트 동일. guide는 플랫폼명·스킬 호출 표기 치환 외 바이트 동일.
- 원본 시작 스냅샷 대비 추가·변경·삭제 없음. Claude/Codex 카탈로그 내용 해시 불변. 원본과 저장소 `claude plugin validate` 통과.

실제 설치·자동 선택·질문 도구 동의·모델 판단·scanner 위임·실제 프로젝트 문서 생성/변경은 이번 요청에서 실행하지 않는다. 패키지 정적 검사와 Git fixture는 모델 실행 성공을 의미하지 않는다. 이후 런타임에서는 다음을 확인한다:

- 명시적 생성과 사전 없는 자동 호출의 동의 차이, 충돌 항목 비등록, 합성어 예외 확인, 반복 실행의 중복 방지.
- split index·공통 용어, 기존 관례의 ②·③·④ 면제와 금지 단어 ① 예외, 코드/용어집 변경 없는 check.
- scanner 동의·새 컨텍스트·집계 단위·후보 세 표·사용자 표준 선택과 도구 없음/자료 누락 실패 경로.
- 지침 파일 없음/기존 CLAUDE 파일 존재/이미 있는 포인터, 300개 초과 분리와 행 수 보존.


## 2026-10-09: noguesstoday 설치를 위한 등록·배포

사용자가 생성된 플러그인을 noguesstoday에 추가하도록 요청했다. 앞서 정한 GitHub `main` 참조·PR 병합·프로젝트 범위 설정 방식을 유지한다. 로컬 절대경로나 작업 브랜치로 설치 소스를 바꾸지 않는다.

- `.agents/plugins/marketplace.json`에 `superglossary`, `./plugins/superglossary-codex`를 추가한다. 기존 superdomain 항목과 Claude 카탈로그는 유지한다. 설치 정책은 `AVAILABLE`, 인증 정책은 기존 카탈로그와 같은 `ON_INSTALL`이다. 외부 서비스나 MCP 인증을 추가하는 것은 아니다.
- 패키지 README의 미등록 안내를 Git `main` 프로젝트 설정으로 바꾼다. 스킬·guide·scanner·manifest·버전은 이전 리뷰 상태를 유지한다.
- 저장소 안내에 새 전환본을 추가하고 `.github/workflows/superglossary-codex.yml`과 `check_repository.py`로 카탈로그·기준 상태·패키지·Git 범위를 검사한다. 기존 superdomain 검증 패턴을 따른다.
- 설치 대상의 `.codex/config.toml`에는 기존 설정을 보존하고 `[plugins."superglossary@superkit"]`의 `enabled = true`만 추가한다. 개인 Codex 설정·Claude 설정·용어집·프로젝트 지침은 바꾸지 않는다.
- 독립 재검토는 변경된 README, 카탈로그, CI와 검사 도구, 저장소 안내에 한정한다. 바뀌지 않은 업무 규칙은 최초 리뷰를 재사용한다. target-state는 재검토 뒤 갱신한다.

배포 준비 상태: 후보 검사 통과, 독립 재검토 pass(지적 없음). 검토된 target-state를 확정했다. 카탈로그·기준 상태, 두 패키지/독립 복사본, Git fixture, 상태 도구 6개 테스트, YAML·경로 트리거, Claude 카탈로그 검사와 diff 검사가 통과했다. 자세한 상태 식별자는 review.md의 추가 이력에 기록한다. 실제 설치·스킬 발견 여부는 main 병합과 프로젝트 활성화 후 별도로 확인한다. 모델의 용어집 편집·네이밍 판단·scanner 실행은 이 설치 확인에 포함하지 않는다.

## 2026-11-10: 원본 기준 비교 범위 조정

`check_repository.py`가 원본 폴더 전체를 `source-state.json`과 비교해서, 전환하지 않는 개발 문서만 바뀌어도 실패했다. 반대로 CI 경로 트리거에는 원본 폴더가 없어 원본만 바꾼 PR에서는 이 검사가 돌지 않았다. 두 가지를 함께 고쳤다. 전환본과 대응표는 바뀌지 않았다.

- **비교에서 빼는 경로:** 대응표에서 `omit`인 `AGENTS.md`와 `docs/superpowers/` 아래 전체.
- **`CHANGELOG.md`는 계속 비교한다.** 대응표는 과거 CHANGELOG 전체를 `omit`으로, 0.6→0.7 이전 안내를 `adapt`로 나눠 적었다. 원본 README는 이전 방법을 CHANGELOG의 0.7.0 항목으로 넘기므로, 전환본 README의 필드 대응은 CHANGELOG에만 있는 내용에서 왔다. 파일 단위로는 전환 입력이라 빼지 않는다. superdomain은 CHANGELOG 전체가 `omit`이라 빼는 것과 다르다.
- **계속 비교하는 경로:** 그 밖의 모든 원본 파일. 빼는 목록에 없는 경로는 새로 생기기만 해도 실패하므로 새 스킬 파일이나 새 컴포넌트 폴더를 놓치지 않는다.
- **구현:** `check_repository.py`가 `tree_state.py compare` 결과에서 위 경로를 거른다. 경로는 원본 루트 기준이고 파일은 완전 일치, 폴더는 접두사로 판정한다. 걸러 낸 차이는 검사가 통과해도 한 줄로 출력한다. `tree_state.py`는 고치지 않았다.
- **기준 상태:** `source-state.json`·`target-state.json`·`managed-paths.json`과 전환본은 바꾸지 않았다. `source-state.json`에는 빼는 경로의 해시가 그대로 남아 있고, `tree_state.py compare`를 직접 실행하면 그 경로의 차이도 보고한다. 통과 여부는 `check_repository.py`로 판단한다.
- **CI:** `.github/workflows/superglossary-codex.yml`의 `push`·`pull_request` 경로에 `plugins/superglossary/**`를 더했다. 원본의 전환 대상 파일을 바꾼 PR은 전환본과 기준 상태를 함께 갱신해야 통과한다.
- **독립 리뷰:** 생략했다. 전환 판단(대응표)과 전환본은 그대로이고 검사 범위만 조정했다. 생략을 독립 리뷰 통과로 기록하지 않는다.

검증 결과: 임시 변경을 하나씩 만들고 `check_repository.py`를 실행한 뒤 되돌렸다. 통과 — `docs/superpowers/specs/x.md` 추가, `AGENTS.md` 수정. 실패(AssertionError가 해당 경로를 지목) — `CHANGELOG.md` 수정, `skills/glossary/x.md` 추가, `skills/check/SKILL.md` 한 글자 수정, `agents/glossary-scanner.md` 삭제. 되돌린 뒤 `check_repository.py`, `check_git_scopes.py`, tree_state 단위 검사 6개, `claude plugin validate .` 통과. GitHub의 실제 workflow 실행은 미검증이다.

## 2026-11-13: 0.8.0 의미 범위와 현재 사전 검토

사용자가 Claude 원본과 Codex 전환본의 업무 규칙 개선 및 0.8.0 갱신을 함께 요청했다. 따라서 최초 전환의 원본 불변 조건 대신, 양쪽 업무 규칙을 함께 반영하고 최종 원본·대상을 검증·독립 리뷰한 뒤 새 기준 상태를 확정한다. 설치·개인 설정 변경·배포·커밋은 이 갱신 범위에 포함하지 않는다.

쓰기 전 `tree_state.py compare`로 source-state와 target-state 모두 추가·변경·삭제가 없음을 확인했다. 기존 사용자 수정 충돌이나 관리 목록 밖의 사용자 파일은 없다. 원본과 대상 위치·manifest 형식·Codex UI·스캐너 실행 계약은 유지한다.

| 변경된 원본 동작 | Codex 대상 | 처리·보존 조건 | 검증 |
| --- | --- | --- | --- |
| 의미와 적용 범위, 영문/축약 구분 | glossary-guide, glossary 스킬, scanner 역할 | 다섯 열 유지, 의미가 같으면 재사용, 표기 중복은 의미로 판단, 행의 금지를 전역 금지로 확대하지 않음 | guide의 기존 플랫폼 치환 외 동일성·독립 대조 |
| 검색 우선 읽기 | glossary/check 스킬, scanner 역할 | 규칙·인덱스 먼저 읽기, 전체 사전 검색, 설명까지 확인, 0건·잘림·불명확 시 범위 확대 또는 미검토 | 패키지 리소스 검증·외부 평가 자료 |
| 현재 사전과 코드 범위 분리 | check 스킬 | 항상 현재 작업 트리 사전으로 판정하고 커밋 코드는 실제 범위·종료 리비전에서 읽음 | 현재/종료 사전이 다른 경우와 종료 사전 부재 Git fixture |
| 사전 결정 변경의 기존 코드 영향 | check 스킬 | unstaged·staged·선택 리비전 사전 변경을 확인하고 이전·현재 표기로 현재 전체 코드의 관련 이름 검색 | 사전만 변경된 범위에서 변경 없는 코드 발견 fixture |
| JSON 이전 안내 제거 | README | 구버전 호환·자동 이전을 제공하지 않음 | 과거 이력은 보존하고 현재 사용 안내에서 제거 |
| 원본 변경의 Codex 검증 연결 | Codex CI | push와 pull_request 양쪽에 원본 경로 포함 | YAML 파싱·두 경로 필터 검사 |

이 절은 0.7.0의 종료 리비전 사전 사용, 기존 관례에 따른 명시 사전 규칙 면제, JSON 이전 안내를 대체한다. 기존 관례는 현재 사전의 명시적인 의미·표준·허용 축약·금지 결정을 무효화하지 않는다. check는 위반·추가 후보·확인 필요·미검토를 구별하며 파일과 Git 상태를 수정하지 않는다. 의미를 확정할 자료가 부족하면 표기만으로 위반을 만들거나 금지 예외를 새로 만들지 않는다.

플랫폼 계약에는 새 API나 설정을 도입하지 않는다. 2026-11-13에 [공식 Agent Plugins 1.0.0 스키마](https://agent-plugins.org/schemas/1.0.0/plugin.schema.json)를 다시 받아 기존 portable manifest를 검증했다. 읽기 전용·재위임 금지가 행동 지침이라는 차이, 세션 모델 상속, 새 컨텍스트 위임, 패키지 내부 리소스 해석을 유지한다.

갱신 상태: 업무 규칙 반영·정적 검사·독립 리뷰 완료. 새 컨텍스트의 `final_review`가 PASS(지적 없음)로 판정했고 검토한 상태를 source-state.json·target-state.json에 확정했다. 기본 인자의 repository 검사도 통과했다. 새 Git fixture는 기존 0.7.0 문서에서 현재 사전 검색 계약 부재로 먼저 실패함을 확인했다.

- 공식 schema·YAML/frontmatter·내부 링크: 2 skills, 10 files, 9 links 통과. 공백이 있는 독립 복사본에서도 같은 검사 통과.
- guide는 기존 Claude→Codex·호출 표기 치환 외 동일하고 LICENSE는 바이트 동일하다.
- Codex Git fixture: staged/unstaged 양쪽, untracked·공백·삭제·ignored, 실제 커밋 범위와 종료 코드, 현재 사전과 종료 사전의 차이·종료 사전 부재, 사전만 변경된 범위의 기존 코드 검색, 3종 사전 diff, 빈/잘못된 범위 통과.
- 원본 check는 `--skill plugins/superglossary/skills/check/SKILL.md --git-only`로 공통 Git 명령을 검증했다. 원본은 Grep 도구를 쓰므로 Codex rg 예시 검사는 이 실행에서 제외했다고 명시한다.
- `check_repository.py --source-state <후보> --target-state <후보>`로 카탈로그·관리 경로·양쪽 후보 일치 검사 통과. 후보와 독립 복사본은 `/private/tmp/superglossary-0.8.0-port-ggzcd_th/`에 있다.
- CI YAML을 파싱해 push·pull_request 양쪽 원본 경로 트리거를 확인했다. 전환 상태 도구의 단위 테스트 6개와 JavaScript 문법 검사도 통과했다.

검증 도구는 설치 패키지 밖에만 둔다. 위 정적 결과는 모델 판단·실제 설치·스캐너 위임 성공을 증명하지 않는다. 행동 평가의 실제 결과·대리 하네스의 한계는 저장소 루트 `evals/superglossary/results/`에, 독립 리뷰와 확정 상태의 SHA-256은 review.md에 기록한다. 네이티브 설치·캐시·자동 발견·scanner 위임·원격 CI 실행은 미검증이다.

행동 평가 완료: 새 컨텍스트의 별도 평가 에이전트가 원본 9개·Codex 9개 fixture를 실제 처리했고 모두 기대 행동을 충족했다. 0.7.0의 의미 중복 거부·사전만 변경 시 조기 종료 두 실패가 회복되었다. 평가한 runtime 해시는 최종 패키지와 같고 check 실행 전후 파일 해시도 보존됐다. 격리된 Claude CLI의 인증 실패로 네이티브 실행 대신 사용한 하네스이며, 각 회차의 사례들은 한 평가자 컨텍스트 안에서 진행했다. 상세 명령·응답·diff·재현법은 평가 결과에 남겼다.

릴리스 PR의 첫 원격 CI에서 Git fixture가 `rg` 실행 파일 부재로 실패했다. Git 범위 검증에는 Python 외에 Git과 ripgrep이 필요하므로 CI에서 ripgrep을 명시적으로 설치한다. 로컬에 있던 도구를 러너 기본 설치로 가정하지 않는다.

0.8.0 병합 시 원본 비교 정책도 함께 유지했다. `AGENTS.md`·`docs/superpowers/`는 계속 제외하며, 현재 패키지가 JSON 이전 안내를 제공하지 않으므로 `CHANGELOG.md`도 전부 `omit`으로 제외한다. 위 2026-11-10의 CHANGELOG 비교 유지 결정은 0.7.0에 대한 기록이다. 그 밖의 신규·수정·삭제 파일은 계속 검사하며, `--source-state`와 `--target-state` 후보 인자도 보존한다. 원본 차이는 공용 `tree_state.py compare`로 수집하고 `check_repository.py`의 `is_omitted()`가 제외 경로만 거른다.
