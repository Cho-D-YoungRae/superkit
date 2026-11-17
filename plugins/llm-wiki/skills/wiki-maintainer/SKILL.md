---
name: wiki-maintainer
description: llm-wiki로 생성된 위키(.llm-wiki/ 디렉토리 존재)에서 작업할 때 반드시 사용. 페이지 생성·편집·질의·정리·소스 제거(retire), 사용자가 위키 내용을 묻거나 자료를 추가·정리하거나 위키를 인용해 답할 때 모두 해당. 위키 저장소 안에서의 모든 운영 판단에 필요.
user-invocable: false
---

# wiki-maintainer — 위키 운영

> **런타임 메모** — 이 스킬은 Claude Code와 Codex가 함께 쓴다. Claude Code는 읽기 전에 본문의 `$` 자리표시자를 치환한다. 치환되지 않은 채 보이면(Codex 등) `CLAUDE_PLUGIN_ROOT`는 플러그인 루트(이 SKILL.md가 있는 `skills/<스킬>/`의 두 단계 위), `CLAUDE_SKILL_DIR`는 이 SKILL.md가 있는 디렉토리, `ARGUMENTS`는 사용자가 이 스킬을 부르며 함께 준 인자로 읽고, 경로는 절대 경로로 바꿔 명령에 넣는다. Read·Glob·Grep·Write·Edit·AskUserQuestion 같은 도구 이름과 `/llm-wiki:<스킬>` 호출 표기도 Claude Code 기준이다 — 그 런타임의 같은 수단으로 바꿔 쓴다.

## 1원칙

**위키의 `AGENTS.md`를 읽고 따르라.** 그 파일이 이 위키의 헌법이다 — 페이지 타입 4종, frontmatter 스펙, 링크·네이밍 규칙, Ingest/Query/Lint/Retire 워크플로, log 규약 전부. 이 스킬은 그 규칙을 복제하지 않는다. 플러그인 환경에서만 가능한 보강만 담는다.

## 세션 시작

`.llm-wiki/config.yaml` → `purpose.md` → `wiki/log.md` 최근 항목(Grep 도구로 `^## \[` 헤딩을 뽑아 마지막 10개) 순으로 읽는다.

## 플러그인 보강

- 도구 사용: 파일 읽기·찾기는 Read·Glob·Grep 도구로 한다. Bash는 `cd` 없이 명령 하나에 위키 파일을 절대 경로로 가리킨다 — `cd`·`&&`로 이은 복합 명령과 셸 변수는 사용자 권한 확인을 부른다.
- 기계 lint(읽기 전용, exit 1 = 발견):

  ```bash
  uv run "${CLAUDE_PLUGIN_ROOT}/skills/source-extract/scripts/wiki_check.py" --root "<위키 루트>" --format md
  ```

- 통계: 같은 스크립트에 `--stats` (타입별 페이지 수·소스 수·마지막 lint 날짜).
- 인제스트 대기 원본: 같은 스크립트에 `--pending` (log에 sha가 없는 `raw/sources/` 파일과, `part n/m`에서 멈춘 청크 인제스트 — 인자 없는 `/llm-wiki:wiki-ingest`가 처리한다).
- 소스 추출(유튜브 자막·장문 PDF 분할·웹 저장·로컬 복사): `llm-wiki:source-extract` 스킬의 레시피를 따른다.
- 정형 워크플로는 슬래시 커맨드(워크플로 스킬)로: 인제스트 `/llm-wiki:wiki-ingest`, 정합성 점검 `/llm-wiki:wiki-lint`, 현황 `/llm-wiki:wiki-status`, 스키마 업그레이드 `/llm-wiki:wiki-init`.

## 주의

- 스크립트는 stdout·캐시(`raw/.cache/`)에만 쓴다. `wiki/` 반영(페이지 생성·편집·index·log)은 항상 에이전트가 판단해서 한다.
- `AGENTS.md` 자체의 수정은 사용자 승인 후에만 한다(공진화 조항).
