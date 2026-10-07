# superglossary

프로젝트 용어 사전을 md 표로 관리하고, 에이전트가 같은 단어로 이름을 짓게 돕는 플러그인이다. 스킬 둘과 서브에이전트 하나로 이루어지며 스크립트는 없다. 저장소 공통 규칙(브랜치·커밋·버전·태그, 사용자 프로젝트 지침 파일)은 루트 [AGENTS.md](../../AGENTS.md)를 따른다.

## 구조

- `.claude-plugin/plugin.json` — 매니페스트. `version`이 버전의 유일한 출처다.
- `skills/glossary/` — 용어 사전 생성·추가·수정·분리. `glossary-guide.md`가 형식·등록 규칙·분리 절차의 유일한 출처다.
- `skills/check/` — 코드 변경이 용어 사전을 따르는지 검토해 보고한다. 형식은 `../glossary/glossary-guide.md`를 읽는다.
- `agents/glossary-scanner.md` — brownfield 용어 스캔. glossary 스킬의 생성 단계에서만 부른다.
- `docs/superpowers/` — 설계 스펙과 구현 계획.

## 규칙

- 스크립트를 두지 않는다. 판단은 스킬과 에이전트가 하고, 판단이 걸린 확정은 사용자가 한다. 꼭 필요해지면 그 스킬 디렉터리 안에 둔다.
- 사용자 프로젝트의 산출물은 `docs/superglossary/`의 md 파일뿐이다. 지침 파일에는 포인터 한 줄만 넣고 `@import`는 쓰지 않는다.
- 용어 사전 형식이나 규칙을 바꾸면 `glossary-guide.md`를 고치고, 그 내용을 요약한 SKILL.md 문구가 어긋나지 않는지 함께 본다.

## 검증

저장소 루트에서 실행한다.

- 매니페스트·스킬 검증: `claude plugin validate . && claude plugin validate plugins/superglossary`
- 로컬 로드: `claude --plugin-dir plugins/superglossary` (세션 중 변경 적용은 `/reload-plugins`)
