# superdomain for Codex

도메인 정의, 도메인·코딩 컨벤션 리뷰, ADR을 제공하는 Codex 플러그인이다. Claude Code용 superdomain **0.6.0**의 업무 규칙을 기반으로 한다.

## 스킬

설치 후 스킬 선택기에서 superdomain의 해당 스킬을 선택하거나 아래처럼 요청한다. 같은 이름의 다른 스킬이 있으면 플러그인 이름을 함께 지정한다.

| 스킬 | 예시 | 동작 |
|---|---|---|
| [domain](skills/domain/SKILL.md) | “superdomain으로 프로젝트 도메인을 정의해줘” | 역할·경계·관계를 확인받고 DOMAIN.md 작성·수정 |
| [review](skills/review/SKILL.md) | “superdomain 리뷰”, “superdomain 리뷰 code src/”, “superdomain 리뷰 domain 전체”, “superdomain 리뷰 main..HEAD” | 독립된 도메인·컨벤션 리뷰를 합쳐 보고 |
| [conventions](skills/conventions/SKILL.md) | “superdomain 컨벤션을 적용해서 Kotlin 서비스를 수정해줘” | 코드 작성 전에 규칙을 읽고 변경 범위에 적용 |
| [adr](skills/adr/SKILL.md) | “superdomain으로 이 결정을 ADR로 남겨줘” | 신규·승인·대체·부분 조정과 기록 제안 |

review의 입력은 `[domain|code] [경로 | 커밋 범위 | 전체]`다. 기본값은 기준 브랜치의 merge-base 이후 커밋·미커밋·새 파일 모두다. 명시적 커밋 범위는 그 리비전만 검토한다. DOMAIN.md가 없으면 도메인 관점을, 대상에 삭제되지 않은 Kotlin·Java 파일이 없으면 컨벤션 관점을 건너뛴다. 일반적인 버그·보안 리뷰는 다루지 않는다.

## 필요한 환경과 설치

- 로컬 Codex 데스크톱, 프로젝트 파일 읽기·검색 및 Git 사용 환경.
- review와 domain의 독립 검토에는 새 컨텍스트의 서브에이전트 실행이 필요하다. 두 관점 리뷰는 리뷰어 두 명을 동시에 실행할 수 있어야 한다.
- 이 디렉터리가 패키지 루트다. `plugin.json`, `skills/`, `LICENSE`를 함께 배포한다. 원본 Claude 플러그인이나 superkit의 다른 디렉터리에 런타임 의존하지 않는다.
- superkit 저장소의 Codex 카탈로그에는 이 패키지가 `superdomain`으로 등록되어 있다. 저장소를 프로젝트로 연 뒤 데스크톱 앱을 다시 시작하고, Plugins Directory에서 **superkit for Codex** 소스를 선택해 설치한다. 저장소의 폴더 이름은 `superdomain-codex`이며 설치할 플러그인 이름은 `superdomain`이다. 다른 위치에 배포할 때는 [공식 패키징 안내](https://developers.openai.com/plugins/build/plugins#build-your-own-curated-plugin-list)에 따라 그 마켓플레이스에 패키지 경로를 등록한다. 카탈로그 등록만으로 설치되거나 활성화되지는 않는다.

## Claude Code 버전과의 차이

- `/superdomain:…` 명령 대신 Codex 스킬 선택 또는 자연어 요청을 사용한다.
- 두 리뷰어의 규칙은 [역할 문서](skills/review/references/dispatch.md)로 묶었다. 새 컨텍스트를 사용하고 모델은 세션 설정을 상속한다. opus·sonnet을 고정하지 않는다.
- 읽기 전용·재위임 금지는 리뷰어에게 전달하는 **지침**이다. 원본의 도구 allowlist/denylist와 같은 차단을 강제하지 않으며, 별도 샌드박스나 프로젝트 custom agent를 자동 설치하지 않는다.
- conventions는 Kotlin·Java 작업에 맞춘 설명으로 선택된다. Claude의 `paths`와 같은 파일 패턴 기반 자동 로딩은 보장하지 않는다. 반드시 적용할 작업에서는 스킬을 명시적으로 선택한다.
- 스킬 UI의 `agents/openai.yaml`은 표시 정보이며 리뷰어 등록 설정이 아니다.

## 사용자 프로젝트에 남는 파일

- `docs/superdomain/DOMAIN.md`: domain이 사용자 확인 후 작성·수정한다.
- `docs/superdomain/adr/yyyy-MM-dd-slug.md`: adr이 확인받은 사실과 결정만 기록한다. accepted/superseded 본문은 보존한다.
- 지침 파일의 문서 포인터: 추가할지 동의받은 뒤 기존 파일에만 쓴다. 기본은 루트 AGENTS.md이며, 기존 CLAUDE.md 계열을 쓰는 프로젝트는 해당 지침 파일 정책을 따른다. CLAUDE.md 계열을 새로 만들지 않는다. 기존 CLAUDE.md에 포인터를 썼다면 Codex의 자동 로딩을 가정하지 않고 다음 세션에서 명시적으로 읽도록 안내한다.

리뷰 결과는 자동 저장하거나 코드를 자동 수정하지 않는다. 프로젝트 지침이 공통 컨벤션보다 우선한다. 도메인 정의·도메인 리뷰·ADR은 언어와 관계없이 쓰며, 컨벤션 스킬·컨벤션 리뷰는 Kotlin·Java를 대상으로 한다.

## 검증 상태

파일·스키마·리소스 경로 검증과 전환 독립 리뷰의 결과는 저장소의 전환 기록에서 관리한다. 이 패키지를 생성하는 작업에는 실제 설치와 설치 후 모델 실행 검증이 포함되지 않는다.

MIT. 저작권과 라이선스는 [LICENSE](LICENSE)를 따른다.
