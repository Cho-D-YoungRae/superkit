---
name: wiki-maintainer
description: llm-wiki로 생성된 위키(.llm-wiki/ 디렉토리 존재)에서 작업할 때 반드시 사용. 페이지 생성·편집·질의·정리·소스 제거(retire), 사용자가 위키 내용을 묻거나 자료를 추가·정리하거나 위키를 인용해 답할 때 모두 해당. 위키 저장소 안에서의 모든 운영 판단에 필요.
user-invocable: false
---

# wiki-maintainer — 위키 운영

## 1원칙

**위키의 `AGENTS.md`를 읽고 따르라.** 그 파일이 이 위키의 헌법이다 — 페이지 타입 4종, frontmatter 스펙, 링크·네이밍 규칙, Ingest/Query/Lint/Retire 워크플로, log 규약 전부. 이 스킬은 그 규칙을 복제하지 않는다. 플러그인 환경에서만 가능한 보강만 담는다.

## 세션 시작

`.llm-wiki/config.yaml` → `purpose.md` → `wiki/log.md` 최근 항목(`grep '^## \[' wiki/log.md | tail -n 10`) 순으로 읽는다.

## 플러그인 보강

- 기계 lint(읽기 전용, exit 1 = 발견):

  ```bash
  uv run "${CLAUDE_PLUGIN_ROOT}/skills/source-extract/scripts/wiki_check.py" --format md
  ```

- 통계: 같은 스크립트에 `--stats` (타입별 페이지 수·소스 수·마지막 lint 날짜).
- 미인제스트 원본: 같은 스크립트에 `--pending` (log에 sha가 없는 `raw/sources/` 파일 — 인자 없는 `/llm-wiki:wiki-ingest`가 처리한다).
- 소스 추출(유튜브 자막·장문 PDF 분할·웹 저장·로컬 복사): `llm-wiki:source-extract` 스킬의 레시피를 따른다.
- 정형 워크플로는 슬래시 커맨드(워크플로 스킬)로: 인제스트 `/llm-wiki:wiki-ingest`, 정합성 점검 `/llm-wiki:wiki-lint`, 현황 `/llm-wiki:wiki-status`, 스키마 업그레이드 `/llm-wiki:wiki-init`.

## 주의

- 스크립트는 stdout·캐시(`raw/.cache/`)에만 쓴다. `wiki/` 반영(페이지 생성·편집·index·log)은 항상 에이전트가 판단해서 한다.
- `AGENTS.md` 자체의 수정은 사용자 승인 후에만 한다(공진화 조항).
