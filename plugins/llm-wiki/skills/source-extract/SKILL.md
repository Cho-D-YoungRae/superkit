---
name: source-extract
description: 소스를 LLM 위키의 raw/ 원본으로 변환할 때 반드시 사용 — 유튜브 URL 자막 추출, 장문 PDF 분할, 웹 페이지 본문 저장, 로컬 md·txt 복사. /llm-wiki:wiki-ingest 실행 중이거나 사용자가 위키에 영상·문서·링크·파일을 추가하려 할 때 항상 이 레시피를 따른다.
user-invocable: false
---

# source-extract — 소스 유형별 추출 레시피

## 공통 규칙

- 결과 원본은 `raw/sources/YYYY-MM-DD-slug.ext` — 날짜는 오늘, slug는 내용 기반 kebab-case 영어.
- 스크립트는 **stdout 또는 `raw/.cache/`에만** 출력한다. 원본 저장과 위키 반영은 에이전트가 한다.
- 스크립트 경로: 이 스킬의 `scripts/` — 이 스킬 본문에서는 `${CLAUDE_SKILL_DIR}/scripts/`, 다른 스킬(wiki-lint·wiki-status 등)에서는 `${CLAUDE_PLUGIN_ROOT}/skills/source-extract/scripts/`.
- exit code: 0 성공 / 1 일반 오류·사용법 오류(stderr 확인) / 2 도메인 특수 상황(유형별 폴백 참조).
- uv가 없으면: 설치 안내(macOS `brew install uv`, 기타 https://docs.astral.sh/uv/getting-started/installation/) 후 중단.

## 유형 판별

| 입력 | 레시피 |
|------|--------|
| youtube.com / youtu.be URL | 유튜브 URL |
| 경로가 `.pdf`로 끝나거나 응답 `Content-Type`이 `application/pdf`인 URL(`curl -sIL <URL>`로 확인), arXiv `abs/` 페이지(→ `pdf/` URL) | 원격 PDF |
| 그 밖의 http(s) URL | 일반 웹 URL |
| 로컬 `.md`·`.txt` | 로컬 md / txt |
| 로컬 `.pdf` | 로컬 PDF |
| 그 밖의 로컬 파일(docx·epub·html·이미지 등) | 지원 범위 외 — md나 PDF로 변환해 다시 넣으라고 안내한다 |

## 유튜브 URL (youtube.com / youtu.be)

1. config의 `ingest.youtube_sub_langs`(기본 ko,en)를 `--langs`로 전달해 실행:

   ```bash
   uv run "${CLAUDE_SKILL_DIR}/scripts/yt_transcript.py" "<URL>" --langs ko,en
   ```

2. stdout(frontmatter + `[mm:ss]` 문단 트랜스크립트)을 `raw/sources/YYYY-MM-DD-<제목-slug>.md`로 저장한다. 자막 선택은 원어 우선이다 — 수동 자막(langs → 원어) → 원어 자동 자막 → 기계 번역(최후). frontmatter `kind`가 `auto-translated`면 기계 번역 자막이므로 분석 노트에 그 사실을 밝힌다.
3. **exit 2 = 자막 없음**: stderr 안내를 사용자에게 그대로 전달하고, 수동 대안(영상 설명란·발표 자료·관련 블로그를 대신 인제스트)을 제안한다. Whisper 등 음성 인식은 이 플러그인 범위 외다.
4. **exit 1 = 추출 오류**: 유튜브 쪽 변경으로 yt-dlp가 낡았을 수 있다 — `uv run --upgrade-package yt-dlp "${CLAUDE_SKILL_DIR}/scripts/yt_transcript.py" …`로 한 번만 재시도하고, 그래도 실패하면 stderr를 전달한다. 재생목록 URL 자체(`/playlist?list=…`)는 지원 범위 외(exit 1) — 영상 URL을 하나씩 넘기게 한다.

## 일반 웹 URL

1. 내장 웹 조회 도구(WebFetch 등)로 본문을 가져와 **본문 위주 마크다운**으로 정리한다 — 내비게이션·광고·푸터·사이드바 제거.
2. frontmatter를 붙인다: `url`, `title`, `retrieved: YYYY-MM-DD` (+ 확인되면 `author`, `published`).
3. `raw/sources/YYYY-MM-DD-<slug>.md`로 저장한다.
4. **fetch 실패**(페이월·봇 차단 등): config `obsidian: true`면 "옵시디언 Web Clipper 확장으로 페이지를 저장한 뒤 그 파일을 인제스트하세요" 폴백을 안내하고, 아니면 브라우저에서 본문을 복사해 md로 저장하는 방법을 안내한다.

## 로컬 md / txt

- `raw/sources/YYYY-MM-DD-<원본이름-slug>.md`로 **복사**한다(원본 이동 금지). 이미 `raw/sources/` 안의 파일이면 복사를 생략한다.

## 원격 PDF

1. `curl -fsSL -o raw/.cache/download.pdf "<URL>"`로 내려받는다(arXiv `abs/…`는 같은 번호의 `pdf/…` URL). 중복 확인은 wiki-ingest가 이 파일의 sha로 한다.
2. 새 소스면 `raw/sources/YYYY-MM-DD-<slug>.pdf`로 **옮기고**, 아래 로컬 PDF 레시피를 그 파일로 이어간다(2단계 복사는 생략).

## 로컬 PDF

1. 쪽수 확인:

   ```bash
   uv run "${CLAUDE_SKILL_DIR}/scripts/pdf_chunk.py" "<PATH>" --info
   ```

   → `{"pages": N, "toc": true|false, "toc_top_entries": M}`
2. PDF를 `raw/sources/YYYY-MM-DD-<slug>.pdf`로 복사한다.
3. **N ≤ config `ingest.pdf_direct_max_pages`(기본 30)**: 복사본을 직접 읽어(Read, 필요 시 pages 지정) 인제스트한다.
4. **N 초과**: 청킹한다 —

   ```bash
   uv run "${CLAUDE_SKILL_DIR}/scripts/pdf_chunk.py" "raw/sources/YYYY-MM-DD-<slug>.pdf" --chunk-pages 20 --cache-dir raw/.cache
   ```

   (`--chunk-pages`는 config `ingest.pdf_chunk_pages` 값 사용.) stdout manifest의 `parts` 배열이 pass 계획이다: **청크당 1 pass**로 인제스트하고, 각 pass 후 log에 `part n/m (pages a-b)`를 기록한다(중단 후 재개 가능 — 재개 규칙은 wiki-ingest). 분할은 목차 경계를 따르고 작은 챕터는 `--chunk-pages`까지 묶는다. 캐시는 같은 설정이면 재사용되고, `--chunk-pages`나 분할 규칙이 바뀌면 자동으로 다시 만들어진다(`--force`는 강제 재생성).
5. **exit 2 = 텍스트 추출 불가**(암호화·스캔본): stderr 안내를 전달한다 — 암호 해제 사본 또는 OCR된 사본으로 재시도(OCR 자체는 범위 외).

## 이미지 포함 소스

- 이미지는 `raw/assets/`에 저장하고 원본 md에서 상대 경로로 참조한다. 텍스트를 먼저 읽고, 참조된 이미지는 필요한 것만 열람한다(위키 AGENTS.md의 이미지 규칙을 따른다).
