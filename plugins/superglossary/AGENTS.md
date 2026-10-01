# superglossary

프로젝트별 도메인 용어를 파일로 관리하고, 에이전트가 일관된 용어를 사용하도록 돕는 플러그인입니다. 스킬·서브에이전트·CLI로 이루어져 있습니다. 저장소 공통 규칙(브랜치·커밋·버전·태그)은 루트 [AGENTS.md](../../AGENTS.md)를 따릅니다.

## 구조

- `.claude-plugin/plugin.json` — 플러그인 매니페스트. **`version` 필드가 버전의 유일한 출처**입니다. `.claude-plugin/` 안에는 매니페스트(JSON)만 넣습니다.
- `scripts/bump_version.py` — 버전 갱신·검증 스크립트.
- `skills/` — 스킬 정의 (`init/`, `add/`, `check/` — 각 디렉토리에 `SKILL.md`).
- `bin/superglossary` — 플러그인이 `PATH`에 노출하는 CLI 진입점. `templates/glossary.py`를 그대로 실행합니다.
- `agents/` — 서브에이전트 정의 (`check-analyzer.md`, `glossary-scanner.md`).
- `templates/glossary.py` — 사용자 프로젝트에 배포되는 CLI 원본 (Python 3 표준 라이브러리만 사용, 외부 패키지 0).
- `tests/` — 테스트 스위트 (표준 라이브러리 `unittest`). `tests/fixtures/legacy-claude-md/`는 구버전 CLI의 init을 실제로 실행해 얻은 CLAUDE.md로, `LEGACY_BLOCK_SHA256` 검증에 쓰입니다.
- CI는 루트 `.github/workflows/superglossary.yml` — 이 디렉토리가 바뀐 PR·push마다 테스트·버전 일관성·`bin/` 진입점을 검증합니다(Python 3.9/3.13).

## 컴포넌트 규칙

- `skills/`, `agents/`, `bin/`은 **반드시 플러그인 루트(이 디렉토리)**에 둡니다.
- CLI 로직은 `templates/glossary.py` 한 곳에만 둡니다. `bin/superglossary`는 그 파일을 로드해 실행하는 얇은 진입점이며, 로직을 복제하지 않습니다.
- 용어사전 데이터는 사용자 프로젝트의 `.claude/superglossary/`에 생성됩니다(glossary.json·core.md·terms.md·glossary.py).
- init은 사용자 프로젝트의 지침 파일에 용어사전 블록을 넣습니다. 대상은 루트 `AGENTS.md`이고, 프로젝트에 `CLAUDE.md`·`.claude/CLAUDE.md`·`CLAUDE.local.md` 중 하나라도 있으면 `.claude/CLAUDE.md`입니다. 이 규칙은 `instruction_files()` 한 곳에서 정합니다.
- `glossary.json`의 구조를 바꾸면 `SCHEMA_VERSION`을 올리고 `migrate()`에 업그레이드 경로를 추가합니다. CLI 버전(`VERSION`)과는 별개입니다.

## 로컬 개발·검증

이 디렉토리(`plugins/superglossary`)에서 실행합니다.

- 매니페스트 검증: `claude plugin validate .`
- 로컬 로드: `claude --plugin-dir .` (세션 중 변경 적용은 `/reload-plugins`)
- 테스트 실행: `python3 -m unittest discover -s tests`

## 버전

- 변경 시 `python3 scripts/bump_version.py <version>`으로 `plugin.json`과 CLI `VERSION` 상수를 함께 갱신합니다.
- 일관성 점검: `python3 scripts/bump_version.py --check`.
