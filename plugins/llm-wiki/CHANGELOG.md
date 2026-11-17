# Changelog

이 플러그인의 버전은 [Semantic Versioning](https://semver.org/lang/ko/)을 따른다. 1.0.0 전에는
마이너 버전이 호환되지 않는 변경을 담을 수 있다.

## 0.4.0 — 2026-11-17

### Added

- Codex 지원: 같은 플러그인 폴더를 Codex 카탈로그(`.agents/plugins/marketplace.json`)에도 등록했다. `codex plugin add llm-wiki@superkit`으로 설치한다. 스킬마다 런타임 메모를 두어 Codex가 치환하지 않는 경로 자리표시자·인자를 푸는 법을 적었고, Skill 도구·포크 실행·PDF 직접 읽기·WebFetch가 없을 때의 폴백을 더했다. Codex 샌드박스 설정은 README에 있다.
- `wiki_check.py`가 중단된 청크 인제스트를 알린다. 장문 PDF 원본의 마지막 log 기록이 `part n/m (pages a-b)`(n < m)이면 `--pending`에 `part`와 함께 나오고, lint는 `ingest-partial`로 보고한다. 전에는 첫 청크만 반영해도 대기 목록과 lint 어디에도 나오지 않았다.
- `pdf_chunk.py`의 manifest가 텍스트가 거의 없는 쪽을 알린다(`empty_pages`·`empty_page_count`, part마다의 `empty_page_count`, stderr 경고). 일부 쪽에만 텍스트 레이어가 있는 스캔본은 경고 없이 빈 청크가 됐다. 예전 캐시는 다음 실행 때 같은 분할로 다시 만든다.

### Fixed

- 웹 URL 중복 확인이 쿼리까지 비교한다. 쿼리를 뗀 주소로만 찾아서, `?id=`·`?p=`로 글을 가르는 사이트에서는 다른 글을 "이미 인제스트된 소스"로 건너뛸 수 있었다. 추적용 쿼리(`utm_*` 등)는 계속 무시한다.

### Changed

- `wiki_check.py`의 안내 문구가 `/llm-wiki:…` 대신 스킬 이름(`wiki-ingest 스킬` 등)을 쓴다.

위키 스키마는 그대로다(schema_version 2). 기존 위키는 업그레이드할 것이 없다.

## 0.3.0 — 2026-10-02

### Changed

- 배포 위치: [superkit](https://github.com/Cho-D-YoungRae/superkit) 마켓플레이스로 옮겼다. 설치 ID가 `llm-wiki@llm-wiki`에서 `llm-wiki@superkit`으로 바뀌므로, 옛 마켓플레이스를 지우고 다시 설치해야 한다.
- `wiki-init`이 새 위키에 포인터 `CLAUDE.md`를 만들지 않는다. Claude Code가 v2.1.277부터 `CLAUDE.md`가 없으면 `AGENTS.md`를 직접 읽기 때문이다. 위키 폴더에 `CLAUDE.md`(또는 `.claude/CLAUDE.md`)가 원래 있으면 예전처럼 `@AGENTS.md` 임포트를 덧붙인다. 기존 위키의 포인터는 그대로 둬도 된다.
- 플러그인을 수정하는 세션용 지침을 `CLAUDE.md`에서 `AGENTS.md`로 옮겼다.
