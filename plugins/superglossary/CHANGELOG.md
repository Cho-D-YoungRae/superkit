# Changelog

이 프로젝트의 모든 주요 변경 사항을 이 파일에 기록합니다.

형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)를 따르며,
이 프로젝트는 [유의적 버전(SemVer)](https://semver.org/lang/ko/)을 따릅니다.

## [Unreleased]

## [0.4.0] - 2026-08-20

### Changed

- **BREAKING**: CLI 런타임을 Node.js에서 **Python 3(표준 라이브러리만)**으로 이관 — `templates/glossary.mjs` → `templates/glossary.py`.
  호출 방식이 `node .claude/superglossary/glossary.mjs …` → `python3 .claude/superglossary/glossary.py …`로 바뀝니다.
  Claude Code가 네이티브 바이너리로 배포되어 `node` 런타임이 더 이상 보장되지 않는 반면, python3는 macOS·주요 Linux에 기본 탑재됩니다.
  **업그레이드 방법**: 각 프로젝트에서 `/superglossary:init`을 재실행하면 새 CLI가 배포되고 기존 `glossary.json`은 보존됩니다.
  이전 `glossary.mjs` 복사본과 `.claude/CLAUDE.md`의 `node …` 안내 문구는 수동으로 정리하세요(`## 용어 사전` 섹션 삭제 후 init 재실행).
- 저장소 개발 도구도 Python으로 통일 — `scripts/bump-version.mjs` → `scripts/bump_version.py`, 테스트는 `node:test` → `unittest`(65개). `package.json` 제거.

### Fixed

- `lint`가 디렉토리 인자를 조용히 무시하던 문제 — 이제 재귀 탐색합니다(`.git`·`node_modules`·`dist` 등 생성물 디렉토리와 바이너리 파일은 제외). 기존에는 README 예시인 `lint src/`가 항상 `이상 없음`을 출력했습니다.
- 인자 없는 `lint`가 `이상 없음`을 출력하던 문제 — 이제 사용법 오류로 종료합니다. `check` 스킬은 검사 대상이 없으면 lint를 호출하지 않습니다.

## [0.3.0] - 2026-07-09

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

[Unreleased]: https://github.com/Cho-D-YoungRae/superglossary/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/Cho-D-YoungRae/superglossary/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/Cho-D-YoungRae/superglossary/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Cho-D-YoungRae/superglossary/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Cho-D-YoungRae/superglossary/releases/tag/v0.1.0
