# Changelog

이 플러그인의 버전은 [Semantic Versioning](https://semver.org/lang/ko/)을 따른다. 1.0.0 전에는
마이너 버전이 호환되지 않는 변경을 담을 수 있다.

## 0.1.0 — 2026-10-01

[superkit](https://github.com/Cho-D-YoungRae/superkit) 마켓플레이스로 처음 배포한다(`infra@superkit`).

### Changed

- init이 만드는 하네스 지침 파일이 `CLAUDE.md`에서 `AGENTS.md`(`harness-AGENTS.md` 템플릿)로 바뀌었다. 하네스에 `CLAUDE.md` 계열 파일이 이미 있으면 Claude Code가 `AGENTS.md`를 읽지 않으므로, `AGENTS.md`를 만들지 않고 기존 `CLAUDE.md`에 덧붙일지 묻는다.
- 이 플러그인을 수정하는 세션용 지침도 `CLAUDE.md`에서 `AGENTS.md`로 옮겼다.

### Fixed

- PostToolUse hook 명령이 `${CLAUDE_PLUGIN_ROOT}` 경로를 따옴표로 감싼다. 경로에 공백이 있으면 명령이 쪼개져 실패하던 문제다.
