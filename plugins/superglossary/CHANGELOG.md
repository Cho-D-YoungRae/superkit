# Changelog

이 프로젝트의 모든 주요 변경 사항을 이 파일에 기록합니다.

형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)를 따르며,
이 프로젝트는 [유의적 버전(SemVer)](https://semver.org/lang/ko/)을 따릅니다.

## [Unreleased]

### Added

- 커맨드 `/superglossary:init` — 사용자 프로젝트에 용어사전 초기화 (`commands/init.md`)
- 커맨드 `/superglossary:add` — 새 용어 추가 (`commands/add.md`)
- 스킬 `glossary-check` — 작업 결과물의 용어 일관성 검사 (`skills/glossary-check/SKILL.md`)
- 서브에이전트 `check-analyzer` — 검사 결과 분석 (`agents/check-analyzer.md`)
- 서브에이전트 `glossary-scanner` — 코드·문서에서 용어 스캔, model: sonnet (`agents/glossary-scanner.md`)
- CLI `templates/glossary.mjs` — 의존성 0의 독립 CLI (서브커맨드: `init`/`build`/`add`/`update`/`remove`/`list`/`lookup`/`lint`)
- 테스트 스위트 (`tests/`, node:test, 24개)

## [0.1.0] - 2026-06-20

### Added

- 플러그인 매니페스트 (`.claude-plugin/plugin.json`)
- 자체 호스팅 마켓플레이스 (`.claude-plugin/marketplace.json`)
- 버전 관리 스크립트 (`scripts/bump-version.mjs`) 및 `package.json` 스크립트
- 프로젝트 문서: `CLAUDE.md`, `CONTRIBUTING.md`, `README.md`
- MIT 라이선스
- PR 템플릿 (`.github/PULL_REQUEST_TEMPLATE.md`)

[Unreleased]: https://github.com/Cho-D-YoungRae/superglossary/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Cho-D-YoungRae/superglossary/releases/tag/v0.1.0
