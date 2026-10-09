# superglossary Codex 전환

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
