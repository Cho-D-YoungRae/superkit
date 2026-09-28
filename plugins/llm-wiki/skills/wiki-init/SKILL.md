---
name: wiki-init
description: 새 LLM 위키 스캐폴드 생성 또는 기존 위키 업그레이드 (인터뷰 → 렌더링 → 사전요건 체크)
argument-hint: "[대상 디렉토리]"
---

# /llm-wiki:wiki-init — 위키 생성·업그레이드

당신은 llm-wiki 플러그인의 init 절차를 수행한다. 템플릿 원본은 `${CLAUDE_PLUGIN_ROOT}/templates/`에 있다. 템플릿 엔진은 없다 — 아래 지시에 따라 직접 치환·제거한다.

## 0. 대상 디렉토리

`$ARGUMENTS`가 경로면 그 디렉토리(없으면 생성), 비어 있으면 현재 디렉토리를 대상으로 한다.

## 1. 모드 판별

대상에 `.llm-wiki/config.yaml`이 있으면 **업그레이드 모드**(§B), 없으면 **신규 모드**(§A).

## A. 신규 모드

### A1. 인터뷰 — 반드시 한 번에 하나씩 질문한다

1. **목적**: "이 위키의 목적과, 위키가 답해야 할 핵심 질문 2~3개는 무엇인가요?" → `purpose.md` 재료.
2. **옵시디언**: "옵시디언을 뷰어로 쓸 건가요?" → yes: `obsidian: true`, link_style 기본 `wikilink`(사용자가 markdown을 원하면 존중) / no: `obsidian: false`, `link_style: markdown`.
3. **유튜브**: "유튜브 영상을 소스로 쓸 건가요?" → yes면 A2에서 uv 확인으로 연결.
4. **git**: "git 저장소로 관리할까요?"

### A2. 사전요건 체크

`uv --version`을 실행한다. 실패했고 유튜브 답이 yes였다면: "유튜브 자막 추출에 uv가 필요합니다 — macOS: `brew install uv`, 기타: https://docs.astral.sh/uv/getting-started/installation/" 를 안내한다. **어느 경우든 스캐폴드는 계속 진행한다.**

### A3. 스캐폴드 생성

디렉토리 생성: `raw/sources/`, `raw/assets/`, `raw/archive/`, `raw/.cache/`, `wiki/reports/`, `wiki/entities/`, `wiki/concepts/`, `wiki/sources/`, `wiki/synthesis/`, `.llm-wiki/`.

템플릿 렌더링:

- `config.yaml.tmpl` → `.llm-wiki/config.yaml`: `{{LANGUAGE}}`=사용자 대화 언어(기본 ko), `{{OBSIDIAN}}`=true|false, `{{LINK_STYLE}}`=markdown|wikilink, `{{YT_LANGS}}`=`ko, en`.
- `AGENTS.md.tmpl` → `AGENTS.md`: 조건 블록 처리 — 채택한 스타일의 `<!-- if:markdown -->`/`<!-- if:wikilink -->` 블록은 **마커 주석만 제거**하고 내용을 남긴다. 미채택 블록은 마커째 통삭제. `<!-- if:obsidian -->`도 동일(obsidian=false면 삭제). **`llm-wiki:managed:start/end` 마커는 반드시 남긴다** — 업그레이드의 기준점이다.
- `CLAUDE.md.tmpl` → `CLAUDE.md`: 그대로 복사(치환 없음).
- `purpose.md.tmpl` → `purpose.md`: `{{PURPOSE}}`에 목적 서술, `{{KEY_QUESTIONS}}`에 핵심 질문 불릿 2~3개.
- `index.md.tmpl` → `wiki/index.md`, `log.md.tmpl` → `wiki/log.md`, `overview.md.tmpl` → `wiki/overview.md`: 그대로 복사.
- `wiki/log.md` 끝에 init 항목을 append:

  ```markdown
  ## [YYYY-MM-DD] init | 위키 생성

  설정: obsidian=<값>, link_style=<값>, git=<값>
  ```

- obsidian yes면 `.obsidian/` 디렉토리를 만들고 `.obsidian/app.json`에 `{}`를 쓴다(옵시디언이 vault로 인식하게).

### A4. git (yes인 경우)

1. `git init`
2. `.gitignore` 생성 — 내용: `raw/.cache/` 와 `.DS_Store` 두 줄.
3. 빈 디렉토리 8곳(`raw/sources` `raw/assets` `raw/archive` `wiki/reports` `wiki/entities` `wiki/concepts` `wiki/sources` `wiki/synthesis`)에 `.gitkeep` 생성.
4. 커밋은 하지 않는다 — 첫 커밋 명령(`git add -A && git commit -m "init: llm-wiki"`)만 안내한다.

### A5. 완료 안내

- 생성된 구조 요약을 보여준다.
- obsidian yes였으면: 이 디렉토리를 옵시디언 vault로 열 수 있고, **Web Clipper** 브라우저 확장으로 웹 문서를 저장한 뒤(저장 위치를 `raw/sources/`로 지정 권장) 그 파일을 인제스트할 수 있으며, **graph view**로 위키 연결망을 볼 수 있다고 안내한다.
- 다음 단계 예시를 제시한다: `/llm-wiki:wiki-ingest https://youtu.be/<영상ID>` 또는 `/llm-wiki:wiki-ingest ~/notes/some-note.md`.

## B. 업그레이드 모드

1. 위키 `AGENTS.md`에서 `<!-- llm-wiki:managed:start schema_version=N -->`의 N을 읽고, `${CLAUDE_PLUGIN_ROOT}/templates/AGENTS.md.tmpl`의 schema_version과 비교한다.
2. 같으면 "이미 최신 (schema_version N)"을 보고하고 종료한다.
3. 다르면: 현재 `.llm-wiki/config.yaml`의 `link_style`·`obsidian` 값으로 템플릿의 새 managed 블록을 렌더링(A3의 조건 블록 규칙과 동일)하고, 기존 managed 블록과의 **diff를 사용자에게 보여주고 승인받는다**.
4. 승인 시: 마커 사이 내용만 교체한다(마커 밖 사용자 영역은 그대로 보존). config에 템플릿 신버전이 요구하는 새 키가 있으면 기본값으로 추가하되 기존 값은 유지하고, config의 `schema_version`을 갱신한다. `wiki/log.md`에 `## [날짜] init | 스키마 업그레이드 vN→vM`을 append한다.
5. 거부 시 아무것도 바꾸지 않는다.

## 금지

- 기존 위키 콘텐츠(페이지, log 기존 항목, purpose 본문) 수정 금지. init은 스캐폴드와 스키마만 다룬다.
