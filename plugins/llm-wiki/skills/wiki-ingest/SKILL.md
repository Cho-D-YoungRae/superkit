---
name: wiki-ingest
description: 소스(유튜브·웹·PDF·로컬 파일)를 위키에 인제스트 — 유형 판별 → 추출 → 2단계 인제스트
argument-hint: "<url|경로> [--batch] [--force]"
---

# /llm-wiki:wiki-ingest

## 1. 위키 루트와 설정

- 현재 디렉토리에서 상위로 `.llm-wiki/config.yaml`을 탐색해 위키 루트를 찾는다. 없으면 "이 디렉토리는 llm-wiki 위키가 아닙니다. `/llm-wiki:wiki-init`으로 먼저 위키를 만드세요."를 출력하고 **종료**한다.
- 세션 시작 절차: config → `purpose.md` → `wiki/log.md` 최근 항목(`grep '^## \[' wiki/log.md | tail -n 10`) 순으로 읽는다. 위키의 `AGENTS.md`도 읽는다.
- `$ARGUMENTS`에서 소스 인자와 플래그(`--batch`, `--force`)를 해석한다. 소스 인자가 없으면 사용법을 안내하고 종료한다.

## 2. 원본 확보

`llm-wiki:source-extract` 스킬을 로드해 소스 유형별 레시피를 따른다(유튜브 URL / 일반 웹 URL / 로컬 md·txt / 로컬 PDF — 각 절차·스크립트 호출법·폴백은 스킬이 단일 소스다). 결과 원본은 반드시 `raw/sources/YYYY-MM-DD-slug.ext`로 저장한다. PDF 청킹 캐시는 `raw/.cache/`에 둔다.

## 3. 중복 확인 (재인제스트 스킵)

- 원본 파일의 sha256을 계산한다: macOS는 `shasum -a 256 <파일>`, Linux는 `sha256sum <파일>` — 앞 12자리를 취한다.
- `grep <sha12> wiki/log.md`로 기존 인제스트 여부를 확인한다. 이미 있으면: 해당 log 항목을 인용해 "이미 인제스트된 소스입니다. 다시 하려면 `--force`를 붙이세요."를 안내하고, `--force`가 없으면 **종료**한다(이미 저장된 원본 파일은 그대로 둔다).
- 장문 PDF의 경우 log에서 `part n/m` 진행 기록이 m 미만에서 끝났다면 중단된 인제스트다 — 이어하기를 제안한다.

## 4. 2단계 인제스트

**위키 `AGENTS.md`의 Ingest 워크플로 섹션을 그대로 수행한다.** 요점만 재확인:

- 1단계 분석 노트 작성 → 사용자에게 보여주고 확인(대화형 기본). `--batch`면 확인을 생략하되 분석 요약을 log 항목에 포함한다.
- 2단계 생성·갱신: 페이지 생성/편집 + `wiki/sources/` 요약 1페이지 + `wiki/index.md`·`wiki/log.md` 갱신을 한 pass로. log 항목에 `sha: <sha12>`와 갱신 페이지 목록을 남긴다.
- 청킹된 장문 PDF: 청크당 1 pass. 각 pass 종료 시 log에 `part n/m` 진행을 기록해 중단 후 재개할 수 있게 한다.

## 5. 종료 요약

신규/수정된 페이지 목록, 소스 요약 페이지 경로, log 항목 제목을 표로 출력한다.
