# Changelog

이 플러그인의 버전은 [Semantic Versioning](https://semver.org/lang/ko/)을 따른다. 1.0.0 전에는
마이너 버전이 호환되지 않는 변경을 담을 수 있다.

## 0.3.0 — 2026-10-02

### Changed

- 배포 위치: [superkit](https://github.com/Cho-D-YoungRae/superkit) 마켓플레이스로 옮겼다. 설치 ID가 `llm-wiki@llm-wiki`에서 `llm-wiki@superkit`으로 바뀌므로, 옛 마켓플레이스를 지우고 다시 설치해야 한다.
- `wiki-init`이 새 위키에 포인터 `CLAUDE.md`를 만들지 않는다. Claude Code가 v2.1.277부터 `CLAUDE.md`가 없으면 `AGENTS.md`를 직접 읽기 때문이다. 위키 폴더에 `CLAUDE.md`(또는 `.claude/CLAUDE.md`)가 원래 있으면 예전처럼 `@AGENTS.md` 임포트를 덧붙인다. 기존 위키의 포인터는 그대로 둬도 된다.
- 플러그인을 수정하는 세션용 지침을 `CLAUDE.md`에서 `AGENTS.md`로 옮겼다.
