---
name: wiki-ingest
description: 소스(유튜브·웹·PDF·로컬 파일)를 위키에 인제스트 — 유형 판별 → 중복 확인 → 추출 → 2단계 인제스트
argument-hint: "[<url|경로> ...] [--batch] [--force]  (인자 없으면 미인제스트 원본 목록)"
---

# /llm-wiki:wiki-ingest

## 1. 위키 루트와 설정

- 현재 디렉토리에서 상위로 `.llm-wiki/config.yaml`을 탐색해 위키 루트를 찾는다. 없으면 "이 디렉토리는 llm-wiki 위키가 아닙니다. `/llm-wiki:wiki-init`으로 먼저 위키를 만드세요."를 출력하고 **종료**한다.
- 이후 모든 Bash 명령은 `cd "<위키 루트>" && …` 형태로 실행하고 파일 경로는 위키 루트 기준으로 쓴다 — 하위 폴더에서 호출돼도 `wiki/log.md`·`raw/.cache` 같은 상대 경로가 깨지지 않게.
- 세션 시작 절차: config → `purpose.md` → `wiki/log.md` 최근 항목(`grep '^## \[' wiki/log.md | tail -n 10`) 순으로 읽는다. 위키의 `AGENTS.md`도 읽는다.
- `$ARGUMENTS`에서 소스 인자와 플래그(`--batch`, `--force`)를 해석한다. 소스가 여러 개면 **하나씩 차례로** §2~§4 전체를 수행한다.
- **소스 인자가 없으면 — 인제스트 대기 목록**: `raw/sources/`에 있지만 log에 sha가 없는 원본(Web Clipper로 저장한 파일 등)을 찾는다:

  ```bash
  uv run "${CLAUDE_PLUGIN_ROOT}/skills/source-extract/scripts/wiki_check.py" --pending --format json
  ```

  목록이 비었으면 사용법을 안내하고 종료한다. 있으면 목록을 보여주고 인제스트할 것을 고르게 한다(`--batch`면 전부). 고른 파일은 이미 `raw/sources/` 안에 있으므로 §2의 중복 확인과 §3의 저장은 건너뛰고 §4부터 한 파일씩 수행한다(log에는 그 파일의 sha12를 남긴다).

## 2. 유형 판별과 중복 확인 — 원본을 저장하기 **전에**

`llm-wiki:source-extract` 스킬을 로드해 소스 유형을 판별한다(판별표·레시피·폴백은 그 스킬이 단일 소스다). 그다음 원본을 `raw/sources/`에 저장하기 **전에** 중복을 확인한다 — 저장부터 하면 중복일 때 새 날짜 사본만 남는다.

- **로컬 파일**: 그 파일 자체의 sha256 앞 12자리(macOS `shasum -a 256 <파일>`, Linux `sha256sum <파일>`).
- **URL**: 이미 저장된 원본을 frontmatter `url`로 찾는다 — 유튜브는 영상 ID로(`grep -l "<영상ID>" raw/sources/*.md`), 웹은 쿼리·`#조각`을 뗀 URL로. 찾으면 그 파일의 sha12를 계산한다. URL 원본은 추출 날짜·가공 결과가 매번 달라 sha가 바뀌므로 sha로는 중복을 못 찾는다.
- **원격 PDF**: 레시피대로 `raw/.cache/`에 내려받은 파일의 sha12.
- **로컬 HTML**: 저장된 원본의 frontmatter `source_file`(원래 파일명)로 찾는다 — 저장되는 원본은 변환된 md라 sha가 원래 파일과 다르다. 같은 이름의 다른 파일일 수 있으니 title·url로 한 번 더 확인한다.

`grep <sha12> wiki/log.md`로 판정한다:

- 기록 없음 → 새 소스. §3으로.
- 그 sha의 마지막 기록이 `part n/m`(n < m)인 장문 PDF → **중단된 인제스트**. 이어하기를 제안한다(재개 규칙은 §4).
- 완료 기록 있음 → 해당 log 항목을 인용해 "이미 인제스트된 소스입니다. 다시 하려면 `--force`를 붙이세요."를 안내한다. `--force`가 없으면 이 소스는 **아무것도 저장하지 않고** 끝낸다(다음 소스가 있으면 계속).

## 3. 원본 확보

source-extract 레시피대로 원본을 `raw/sources/YYYY-MM-DD-slug.ext`로 저장한다. PDF 청킹 캐시는 `raw/.cache/`에 둔다.

- `--force` 재인제스트는 이미 저장된 원본을 그대로 쓴다(새 날짜 사본을 만들지 않는다). 원문이 바뀌어 새로 받아야 한다면 새 원본으로 저장하고, 이전 원본은 사용자 확인 후 AGENTS.md의 Retire 절차를 따른다.

## 4. 2단계 인제스트

**위키 `AGENTS.md`의 Ingest 워크플로 섹션을 그대로 수행한다.** 요점만 재확인:

- 1단계 분석 노트 작성 → 사용자에게 보여주고 확인(대화형 기본). `--batch`면 확인을 생략하되 분석 요약을 log 항목에 포함한다.
- 2단계 생성·갱신: 페이지 생성/편집 + `wiki/sources/` 요약 1페이지 + `wiki/index.md`·`wiki/log.md` 갱신을 한 pass로. log 항목에 `sha: <sha12>`와 갱신 페이지 목록을 남긴다.
- 청킹된 장문 PDF: 청크당 1 pass. 각 pass가 끝날 때마다 log 항목에 `sha: <sha12>`와 `part n/m (pages a-b)`를 남긴다.
- **재개**: manifest의 `parts`를 log의 마지막 `part n/m (pages a-b)`와 대조해 다음 청크부터 이어간다. 청크 수나 쪽 범위가 log와 다르면(`pdf_chunk_pages` 설정이나 플러그인의 분할 규칙이 바뀐 경우) 사용자에게 알리고, 이미 다룬 쪽 범위를 건너뛰어 이어갈지 `--force`로 처음부터 다시 할지 묻는다.

## 5. 종료 요약

소스마다 신규/수정된 페이지 목록, 소스 요약 페이지 경로, log 항목 제목을 표로 출력한다. 건너뛴 중복 소스도 표에 표시한다.
