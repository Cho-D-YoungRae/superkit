# superglossary

프로젝트별 도메인 용어를 파일로 관리하고, Claude가 일관된 용어를 사용하도록 돕는 **Claude Code 플러그인**입니다. v0.2.0부터 커맨드·스킬·서브에이전트·CLI를 포함한 용어사전 기능이 구현되어 있습니다.

## 저장소 구조

- `.claude-plugin/plugin.json` — 플러그인 매니페스트. **`version` 필드가 버전의 유일한 출처**입니다.
- `.claude-plugin/marketplace.json` — 자체 호스팅 마켓플레이스(`source: "./"`).
- `scripts/bump-version.mjs` — 버전 갱신·검증 스크립트.
- `commands/` — 커맨드 정의 (`superglossary-init.md`, `superglossary-add.md`).
- `skills/` — 스킬 정의 (`glossary-check.md`).
- `agents/` — 서브에이전트 정의 (`check-analyzer.md`, `glossary-scanner.md`).
- `templates/glossary.mjs` — 사용자 프로젝트에 배포되는 CLI 원본 (의존성 0).
- `tests/` — 테스트 스위트 (node:test, `pnpm test`).
- `.claude-plugin/` 안에는 매니페스트(JSON)만 넣습니다.

## 컴포넌트 규칙

- `commands/`, `skills/`, `agents/`는 **반드시 저장소 루트**에 둡니다.
- 용어사전 데이터는 사용자 프로젝트의 `.claude/superglossary/`에 생성됩니다(glossary.json·core.md·terms.md·glossary.mjs).

## 로컬 개발·검증

- 매니페스트 검증: `claude plugin validate .`
- 로컬 로드: `claude --plugin-dir .` (세션 중 변경 적용은 `/reload-plugins`)
- 테스트 실행: `pnpm test`

## 버전·릴리즈

- 버전은 **SemVer**. 변경 시 `pnpm bump <version>`(= `scripts/bump-version.mjs`)으로 `plugin.json`을 갱신합니다.
- `version`을 올려야만 사용자에게 업데이트가 배포되므로, 릴리즈마다 반드시 bump 합니다.
- 일관성 점검: `pnpm version:check`.
- 전체 브랜치 전략·커밋 규칙·릴리즈 절차는 [CONTRIBUTING.md](CONTRIBUTING.md)를 따릅니다.

## Git flow 요약

- 상시 브랜치: `main`(릴리즈), `develop`(통합 개발).
- 작업은 `develop`에서 `feature/*`·`fix/*`로 분기 → `develop`로 PR. 릴리즈는 `develop` → `main` PR 후 태그.
