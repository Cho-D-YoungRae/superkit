# superglossary for Codex

프로젝트 용어를 `docs/superglossary/`의 Markdown 표로 관리하고 코드 변경의 이름을 검토하는 Codex 플러그인이다. Claude 원본 0.7.0의 단어별 등록·합성어 예외·금지 단어·도메인 분리 규칙을 사용한다. 별도 CLI나 데이터 생성 스크립트는 없다.

## 사용

설치 후 Codex의 스킬 선택에서 아래 스킬을 고르거나 이름과 함께 요청한다.

| 스킬 | 요청 예 | 동작 |
| --- | --- | --- |
| `$superglossary:glossary` | 용어집 만들어줘 / 체결 용어 추가 | 생성·추가·수정·삭제·도메인 분리 |
| `$superglossary:check` | 이름을 용어집과 대조해줘 / `src/order/` / `main..HEAD` | 위반·추가 후보 보고. 코드와 사전은 수정하지 않음 |

glossary는 이름을 짓다가 필요한 단어가 사전에 없을 때 자동 선택될 수도 있다. 기존 용어집에 일반 단어를 추가할 때는 한 줄로 알린다. 최초 생성은 사용자의 생성 요청이나 동의가 필요하며, 이미 생성 요청을 받았다면 다시 묻지 않는다. 합성어를 한 항목으로 두는 예외, 기존 코드 스캔, 지침 포인터 추가, 도메인 분리는 사용자 확인을 거친다. 수정·삭제는 사용자가 요청할 때만 한다. 용어가 300개를 넘으면 분리를 제안한다.

형식과 등록 규칙의 기준은 [glossary-guide.md](skills/glossary/glossary-guide.md)다. Claude와 Codex는 같은 `docs/superglossary/`를 사용한다. 기존 사용자 데이터를 플랫폼별로 복제하거나 이동하지 않는다.

## 설치

이 디렉터리 자체가 패키지 루트다. `plugin.json`, `skills/`, `LICENSE`를 함께 배포한다. `.codex-plugin/`이나 다른 플러그인의 파일은 필요하지 않다.

superkit의 Codex 카탈로그는 이 패키지를 `superglossary@superkit`으로 등록한다. 프로젝트 범위로 사용하려면 프로젝트 `.codex/config.toml`에 다음 설정을 합친다. 이미 `marketplaces.superkit`이 있으면 테이블을 중복해서 만들지 않고 기존 설정을 확인한다.

```toml
[marketplaces.superkit]
source_type = "git"
source = "https://github.com/Cho-D-YoungRae/superkit.git"
ref = "main"

[plugins."superglossary@superkit"]
enabled = true
```

신뢰한 프로젝트에서 마켓플레이스를 새로고침하면 설정한 플러그인을 받을 수 있다. 패키지 캐시는 공용이지만 위 활성화 설정은 해당 프로젝트 범위다. CLI에서는 프로젝트 루트에서 `codex plugin marketplace upgrade superkit`으로 Git 소스를 갱신할 수 있다. 데스크톱에서 마켓플레이스를 새로고침하고 새 채팅에서 스킬을 확인한다. 자세한 구조는 [OpenAI 공식 패키징 문서](https://developers.openai.com/plugins/build/plugins)를 따른다.

## 실행 조건과 차이

- 파일 읽기·검색·편집을 사용할 수 있는 로컬 Codex 데스크톱이 대상이다. Git 변경/커밋 범위 검토에는 Git이 필요하다. Git이 없는 디렉터리에서는 명시한 경로를 검토한다.
- 기존 코드 스캐너는 새 컨텍스트의 서브에이전트가 필요하다. [실행 계약](skills/glossary/references/scanner-dispatch.md)에 따라 모델은 세션 설정을 상속한다. Claude의 `sonnet` 고정은 유지하지 않는다.
- 원본 스캐너는 Read/Grep/Glob만 허용한다. Codex 전환본은 읽기 전용·재위임 금지를 지침으로 전달하며, 같은 도구 차단을 보장하지 않는다. 별도 custom agent나 사용자 설정을 자동 설치하지 않는다.
- 프로젝트 지침 파일의 기존 정책과 포인터 추가 확인을 보존한다. 기존 CLAUDE 계열 파일에 쓴 포인터는 Codex에서 자동 로드된다고 가정하지 않으며, 다음 세션에 그 파일을 명시적으로 읽도록 안내한다. 대상 지침 파일이 없으면 새로 만들지 않고 포인터를 제안한다.
- 실제 모델의 자동 선택·사용자 확인·스캐너 실행은 사용하는 클라이언트에서 별도로 검증해야 한다. 패키지 검사는 이 동작의 실행 검증을 대신하지 않는다.

## 기존 용어집

0.7.0 Markdown 용어집은 그대로 사용한다. 0.6.0 이하의 `.claude/superglossary/glossary.json`을 쓰던 프로젝트는 사용자가 이전을 요청할 때 `korean`→한글, `english`→영문, `abbreviation`→축약, `avoid`→금지(쉼표 구분), `description`→설명으로 옮긴다. `relatedElements`·`stopwords`는 새 형식에서 쓰지 않는다. 이전 표의 내용·행 수를 확인하고 기존 문서가 있으면 충돌을 먼저 해결한다. 옛 데이터·CLI나 지침의 import 블록 삭제는 별도로 확인하며 자동으로 지우지 않는다.

## 출처와 라이선스

[Claude 원본](https://github.com/Cho-D-YoungRae/superkit/tree/main/plugins/superglossary)의 Codex 전환본이다. 원본의 용어사전 개념은 [김영한의 실전 데이터베이스 강의](https://www.inflearn.com/course/김영한-실전-데이터베이스-설계1편/dashboard?cid=338886)의 용어 사전 부분을 참고했다. [MIT](LICENSE).
