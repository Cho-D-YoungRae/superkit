# Changelog

이 프로젝트의 모든 주요 변경 사항을 이 파일에 기록합니다.

형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)를 따르며,
이 프로젝트는 [유의적 버전(SemVer)](https://semver.org/lang/ko/)을 따릅니다.

## [Unreleased]

### Added

- `avoid`(금지 변형) 필드 — brownfield 표준화 결정을 보존, `lint`가 결정론적으로 위반 확정 (`--avoid` 플래그)
- `lint` 스톱워드 필터(`--all`로 해제)·토큰별 등장 파일 출력·`[위반]`/`[후보]` 섹션 분리
- `lookup` 상세 출력(설명·관련·금지), `version`/`help` 서브커맨드
- stale 감지 경고(list/lookup/lint), `.gitignore` 무시 경고(init), glossary.json 부재 시 친절한 에러
- `pnpm bump`가 CLI `VERSION` 상수를 plugin.json과 동기화, `version:check`가 일치 검증

### Changed

- 커맨드(`commands/`)를 스킬(`skills/init`·`skills/add`)로 전환 — 호출명 `/superglossary:init`·`/superglossary:add`는 동일
- `glossary-check` 스킬을 `check`로 개명(`/superglossary:check`) + 하이브리드 검사(후보 10개 이하 인라인, 초과 시 check-analyzer)
- add 스킬이 Claude 자율 등록의 단일 진입점 — 사용자 프로젝트 CLAUDE.md 블록 갱신(신규 init부터)
- `lint` 출력 형식 변경(섹션·파일 위치), init의 데이터 디렉토리를 스크립트 위치 기준으로 통일

### Fixed

- 생성 표의 `|`·개행 이스케이프, english↔abbreviation 교차 충돌 검사, core.md 분할 안내(스펙 §6) 구현

## [0.2.0] - 2026-06-21

### Added

- 커맨드 `/superglossary:init` — 사용자 프로젝트에 용어사전 초기화 (`commands/init.md`)
- 커맨드 `/superglossary:add` — 새 용어 추가 (`commands/add.md`)
- 스킬 `glossary-check` — 작업 결과물의 용어 일관성 검사 (`skills/glossary-check/SKILL.md`)
- 서브에이전트 `check-analyzer` — 코드↔사전 양방향 의미 검토, model: sonnet (`agents/check-analyzer.md`)
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

[Unreleased]: https://github.com/Cho-D-YoungRae/superglossary/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/Cho-D-YoungRae/superglossary/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Cho-D-YoungRae/superglossary/releases/tag/v0.1.0
