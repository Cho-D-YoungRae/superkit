# superglossary

프로젝트별 도메인 용어를 파일(`GLOSSARY.md`)로 관리하고, Claude가 일관된 용어를 사용하도록 돕는 **Claude Code 플러그인**입니다. 현재는 운영 인프라만 구성된 매니페스트-only 상태이며, 용어사전 기능(스킬)은 추후 추가합니다.

## 저장소 구조

- `.claude-plugin/plugin.json` — 플러그인 매니페스트. **`version` 필드가 버전의 유일한 출처**입니다.
- `.claude-plugin/marketplace.json` — 자체 호스팅 마켓플레이스(`source: "./"`).
- `scripts/bump-version.mjs` — 버전 갱신·검증 스크립트.
- 컴포넌트(`skills/`, `commands/`, `agents/`, `hooks/`)는 추후 추가하며 **반드시 저장소 루트**에 둡니다. `.claude-plugin/` 안에는 매니페스트(JSON)만 넣습니다.

## 로컬 개발·검증

- 매니페스트 검증: `claude plugin validate .`
- 로컬 로드: `claude --plugin-dir .` (세션 중 변경 적용은 `/reload-plugins`)

## 버전·릴리즈

- 버전은 **SemVer**. 변경 시 `pnpm bump <version>`(= `scripts/bump-version.mjs`)으로 `plugin.json`을 갱신합니다.
- `version`을 올려야만 사용자에게 업데이트가 배포되므로, 릴리즈마다 반드시 bump 합니다.
- 일관성 점검: `pnpm version:check`.
- 전체 브랜치 전략·커밋 규칙·릴리즈 절차는 [CONTRIBUTING.md](CONTRIBUTING.md)를 따릅니다.

## Git flow 요약

- 상시 브랜치: `main`(릴리즈), `develop`(통합 개발).
- 작업은 `develop`에서 `feature/*`·`fix/*`로 분기 → `develop`로 PR. 릴리즈는 `develop` → `main` PR 후 태그.
