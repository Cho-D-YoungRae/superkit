# superglossary

프로젝트별 도메인 용어를 파일로 관리하고, Claude가 일관된 용어를 사용하도록 돕는 **Claude Code 플러그인**입니다. v0.2.0부터 스킬·서브에이전트·CLI를 포함한 용어사전 기능이 구현되어 있습니다.

## 저장소 구조

- `.claude-plugin/plugin.json` — 플러그인 매니페스트. **`version` 필드가 버전의 유일한 출처**입니다.
- `.claude-plugin/marketplace.json` — 자체 호스팅 마켓플레이스(`source: "./"`).
- `scripts/bump_version.py` — 버전 갱신·검증 스크립트.
- `skills/` — 스킬 정의 (`init/`, `add/`, `check/` — 각 디렉토리에 `SKILL.md`).
- `bin/superglossary` — 플러그인이 `PATH`에 노출하는 CLI 진입점. `templates/glossary.py`를 그대로 실행합니다.
- `agents/` — 서브에이전트 정의 (`check-analyzer.md`, `glossary-scanner.md`).
- `templates/glossary.py` — 사용자 프로젝트에 배포되는 CLI 원본 (Python 3 표준 라이브러리만 사용, 외부 패키지 0).
- `tests/` — 테스트 스위트 (표준 라이브러리 `unittest`). `tests/fixtures/legacy-claude-md/`는 구버전 CLI의 init을 실제로 실행해 얻은 CLAUDE.md로, `LEGACY_BLOCK_SHA256` 검증에 쓰입니다.
- `.github/workflows/ci.yml` — PR·push마다 테스트·버전 일관성·`bin/` 진입점을 검증(Python 3.9/3.13).
- `.claude-plugin/` 안에는 매니페스트(JSON)만 넣습니다.

## 컴포넌트 규칙

- `skills/`, `agents/`, `bin/`은 **반드시 저장소 루트**에 둡니다.
- CLI 로직은 `templates/glossary.py` 한 곳에만 둡니다. `bin/superglossary`는 그 파일을 로드해 실행하는 얇은 진입점이며, 로직을 복제하지 않습니다.
- 용어사전 데이터는 사용자 프로젝트의 `.claude/superglossary/`에 생성됩니다(glossary.json·core.md·terms.md·glossary.py).
- `glossary.json`의 구조를 바꾸면 `SCHEMA_VERSION`을 올리고 `migrate()`에 업그레이드 경로를 추가합니다. CLI 버전(`VERSION`)과는 별개입니다.

## 로컬 개발·검증

- 매니페스트 검증: `claude plugin validate .`
- 로컬 로드: `claude --plugin-dir .` (세션 중 변경 적용은 `/reload-plugins`)
- 테스트 실행: `python3 -m unittest discover -s tests`

## 버전·릴리즈

- 버전은 **SemVer**. 변경 시 `python3 scripts/bump_version.py <version>`으로 `plugin.json`과 CLI `VERSION` 상수를 함께 갱신합니다.
- `version`을 올려야만 사용자에게 업데이트가 배포되므로, 릴리즈마다 반드시 bump 합니다.
- 일관성 점검: `python3 scripts/bump_version.py --check`.
- 전체 브랜치 전략·커밋 규칙·릴리즈 절차는 [CONTRIBUTING.md](CONTRIBUTING.md)를 따릅니다.

## Git flow 요약

- 상시 브랜치: `main`(릴리즈), `develop`(통합 개발).
- 작업은 `develop`에서 `feature/*`·`fix/*`로 분기 → `develop`로 PR. 릴리즈는 `develop` → `main` PR 후 태그.
