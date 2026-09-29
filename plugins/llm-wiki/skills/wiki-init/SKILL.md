---
name: wiki-init
description: 새 LLM 위키 스캐폴드 생성 또는 기존 위키 업그레이드 (인터뷰 → 렌더링 → 사전요건 체크)
argument-hint: "[대상 디렉토리]"
---

# /llm-wiki:wiki-init — 위키 생성·업그레이드

당신은 llm-wiki 플러그인의 init 절차를 수행한다. 템플릿 원본은 `${CLAUDE_PLUGIN_ROOT}/templates/`에 있다. 템플릿 엔진은 없다 — 아래 지시에 따라 직접 치환·제거한다.

**도구 사용**: 템플릿·`ARCHITECTURE.md` 같은 플러그인 파일은 위키 밖에 있으므로 Read·Glob·Grep 도구로 읽는다(셸 `ls`·`cat`·`grep`은 작업 디렉토리 밖이라 차단되거나 권한 확인을 부른다). 렌더링 결과는 Write 도구로 쓰고, 기존 파일 병합은 Edit 도구로 한다 — `sed`·`awk`·셸 스크립트로 변환하지 않는다(권한 확인을 부르고 조건 블록 처리가 틀리기 쉽다). Bash는 `mkdir -p`·`git init`·`uv --version`에만, `cd` 없이 대상의 절대 경로로 쓴다.

## 0. 대상 디렉토리

`$ARGUMENTS`가 경로면 그 디렉토리(없으면 생성), 비어 있으면 현재 디렉토리를 대상으로 한다.

## 1. 모드 판별

대상에 `.llm-wiki/config.yaml`이 있으면 **업그레이드 모드**(§B), 없으면 **신규 모드**(§A).

## A. 신규 모드

### A1. 인터뷰

1. **목적**(자유 서술): "이 위키의 목적과, 위키가 답해야 할 핵심 질문 2~3개는 무엇인가요?" → `purpose.md` 재료.
2. 나머지 세 가지는 예/아니오라서 **AskUserQuestion 한 번(질문 3개)으로 함께 묻는다**(도구가 없으면 한 번에 하나씩):
   - **옵시디언**: "옵시디언을 뷰어로 쓸 건가요?" → yes: `obsidian: true`, link_style 기본 `wikilink`(사용자가 markdown을 원하면 존중) / no: `obsidian: false`, `link_style: markdown`.
   - **유튜브**: "유튜브 영상을 소스로 쓸 건가요?" → yes면 A2에서 uv 확인으로 연결.
   - **git**: "git 저장소로 관리할까요?"

### A2. 사전요건 체크

`uv --version`을 실행한다. 실패했고 유튜브 답이 yes였다면: "유튜브 자막 추출에 uv가 필요합니다 — macOS: `brew install uv`, 기타: https://docs.astral.sh/uv/getting-started/installation/" 를 안내한다. **어느 경우든 스캐폴드는 계속 진행한다.**

### A3. 기존 파일 보존 — 덮어쓰기 금지

대상은 이미 파일이 있는 프로젝트·노트 폴더일 수 있다. 렌더링 전에 아래 파일이 있는지 확인하고, **있는 파일은 덮어쓰지 않는다**:

| 이미 있는 파일 | 처리 |
|------|------|
| `CLAUDE.md` | 내용을 보존한다. `@AGENTS.md` 줄이 없으면 파일 끝에 빈 줄 하나를 두고 `CLAUDE.md.tmpl` 내용을 덧붙인다 |
| `AGENTS.md` (llm-wiki managed 마커 없음) | 렌더링한 템플릿의 "사용자 확장 영역" 아래로 기존 내용을 그대로 옮긴다. 쓰기 전에 결과 구조를 보여주고 승인받는다 |
| `AGENTS.md` (managed 마커 있음) | config 없이 마커만 있는 비정상 상태다 — 상황을 보고하고 중단한다 |
| `purpose.md` · `wiki/index.md` · `wiki/overview.md` | 그대로 둔다 |
| `wiki/log.md` | 그대로 두고 A4의 init 항목만 끝에 append한다 |
| `.gitignore` | 빠진 줄(`raw/.cache/`, `.DS_Store`)만 끝에 append한다 |
| `.obsidian/app.json` | 기존 키는 유지하고 A4의 권장 키 중 없는 것만 추가한다 |
| `.git/` | `git init`을 생략한다 |

보존·병합한 파일은 A6 완료 안내에서 목록으로 알린다.

### A4. 스캐폴드 생성

디렉토리 생성(`mkdir -p` 한 번, 대상의 절대 경로로): `raw/sources/`, `raw/assets/`, `raw/archive/`, `raw/.cache/`, `wiki/reports/`, `wiki/entities/`, `wiki/concepts/`, `wiki/sources/`, `wiki/synthesis/`, `.llm-wiki/`.

템플릿 렌더링 — 템플릿을 Read로 읽어 아래대로 바꾼 결과를 Write로 쓴다(A3의 보존 규칙이 우선한다):

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

- obsidian yes면 `.obsidian/app.json`을 config에 맞춰 쓴다 — 옵시디언이 vault로 인식하고, 사람이 옵시디언에서 직접 붙여넣는 첨부·만드는 링크도 규약과 `wiki_check`에 맞게 한다:
  - 공통: `"attachmentFolderPath": "raw/assets"`
  - link_style=markdown: `"useMarkdownLinks": true`, `"newLinkFormat": "relative"`
  - link_style=wikilink: `"useMarkdownLinks": false`

### A5. git (yes인 경우)

1. `git init "<대상 절대 경로>"` (`.git/`이 있으면 생략)
2. `.gitignore` — 내용: `raw/.cache/` 와 `.DS_Store` 두 줄(A3 규칙대로 기존 파일엔 빠진 줄만 추가).
3. 빈 디렉토리 8곳(`raw/sources` `raw/assets` `raw/archive` `wiki/reports` `wiki/entities` `wiki/concepts` `wiki/sources` `wiki/synthesis`)에 빈 `.gitkeep`을 Write로 생성.
4. 커밋은 하지 않는다 — 첫 커밋 명령(`git add -A && git commit -m "init: llm-wiki"`)만 안내한다.

### A6. 완료 안내

- 생성된 구조 요약과, A3에서 보존·병합한 파일 목록을 보여준다.
- 대상이 현재 디렉토리가 아니면: 위키 규약(`CLAUDE.md` → `AGENTS.md`)은 그 디렉토리에서 연 세션에만 로드되므로 `cd <대상> && claude`로 새 세션을 열라고 안내한다.
- obsidian yes였으면: 이 디렉토리를 옵시디언 vault로 열 수 있고, **Web Clipper** 브라우저 확장으로 웹 문서를 저장한 뒤(저장 위치를 `raw/sources/`로 지정 권장) 인자 없는 `/llm-wiki:wiki-ingest`로 쌓인 파일을 한꺼번에 인제스트할 수 있으며, **graph view**로 위키 연결망을 볼 수 있다고 안내한다.
- 다음 단계 예시를 제시한다: `/llm-wiki:wiki-ingest https://youtu.be/<영상ID>` 또는 `/llm-wiki:wiki-ingest ~/notes/some-note.md`.

## B. 업그레이드 모드

1. 위키 `AGENTS.md`의 `<!-- llm-wiki:managed:start schema_version=N -->`에서 N을 읽는다 — **이 마커가 기준**이고 config의 `schema_version`은 사본이다. `${CLAUDE_PLUGIN_ROOT}/templates/AGENTS.md.tmpl`의 schema_version M과 비교한다.
   - 마커가 없거나 start/end 짝이 맞지 않으면: 사용자 영역을 건드리지 않고는 안전하게 교체할 수 없다 — 상황을 보고하고, 원하면 템플릿 managed 블록을 파일 맨 위에 새로 넣는 안을 diff로 보여주고 승인받은 경우에만 적용한다.
2. **N = M**: "이미 최신 (schema_version N)"을 보고한다. config `obsidian: true`인데 `.obsidian/app.json`에 A4의 권장 키가 없으면 추가를 제안한다(승인 시 없는 키만 추가). 그 밖엔 종료.
3. **N > M**: 위키가 이 플러그인보다 새 스키마로 만들어졌다 — **아무것도 바꾸지 않고**, `/plugin` 메뉴에서 llm-wiki를 최신으로 업데이트하라고 안내한 뒤 종료한다(다운그레이드 금지).
4. **N < M**: 현재 `.llm-wiki/config.yaml`의 `link_style`·`obsidian` 값으로 템플릿의 새 managed 블록을 렌더링(A4의 조건 블록 규칙과 동일)하고, 기존 managed 블록과의 **diff를 사용자에게 보여주고 승인받는다**. `${CLAUDE_PLUGIN_ROOT}/ARCHITECTURE.md`의 "스키마 버전 이력"(Grep 도구로 찾아 Read)에서 vN 다음부터 vM까지의 항목으로 무엇이 왜 바뀌는지 함께 요약한다(여러 버전을 건너뛰어도 최신 블록으로 한 번에 교체한다).
5. 승인 시: 마커 사이 내용만 교체한다(마커 밖 사용자 영역은 그대로 보존). config에 템플릿 신버전이 요구하는 새 키가 있으면 기본값으로 추가하되 기존 값은 유지하고, config의 `schema_version`을 M으로 맞춘다. `wiki/log.md`에 `## [날짜] init | 스키마 업그레이드 vN→vM`을 append한다.
6. 거부 시 아무것도 바꾸지 않는다.

## 금지

- 기존 위키 콘텐츠(페이지, log 기존 항목, purpose 본문) 수정 금지. init은 스캐폴드와 스키마만 다룬다.
- 대상 디렉토리에 이미 있던 파일을 덮어쓰기 금지(A3).
