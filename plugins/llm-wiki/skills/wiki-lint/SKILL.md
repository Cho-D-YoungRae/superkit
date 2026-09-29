---
name: wiki-lint
description: 위키 정합성 점검 — 기계 검사(wiki_check) + LLM 판단 검사 → 리포트
---

# /llm-wiki:wiki-lint

## 1. 위키 루트

현재 디렉토리부터 상위로 `.llm-wiki/config.yaml`을 Read 도구로 확인해 위키 루트를 찾는다. 없으면 "이 디렉토리는 llm-wiki 위키가 아닙니다. `/llm-wiki:wiki-init`으로 먼저 위키를 만드세요."를 출력하고 종료한다. 위키의 `AGENTS.md`와 `purpose.md`를 읽는다. 파일 읽기·찾기는 Read·Glob·Grep 도구로 하고, Bash는 `cd` 없이 명령 하나에 절대 경로로 쓴다 — `cd`·`&&`로 이은 복합 명령은 사용자 권한 확인을 부른다.

## 2. 기계 검사

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/source-extract/scripts/wiki_check.py" --root "<위키 루트>" --format json
```

- exit 0 = clean, exit 1 = findings(JSON의 `findings` 배열). 결과를 검사 항목별로 요약한다.
- `raw-unreferenced` 중 "미인제스트 원본"은 인자 없는 `/llm-wiki:wiki-ingest`로 처리하도록 권고하고, "인제스트 기록은 있으나 참조 없음"은 페이지 `sources[]` 누락(드리프트)이나 retire 미완료로 보고 수정 후보에 넣는다. `log-sha`(sha 없는 ingest 항목)는 재인제스트 중복 검사가 그 소스를 못 찾는다는 뜻이다 — log는 append-only이므로 고치지 말고 리포트에 알린다.
- uv가 없으면 설치 안내(`brew install uv` 등)를 출력하고, 기계 검사 없이 §3만으로 진행하되 리포트에 그 사실을 명시한다.

## 3. LLM 판단 검사 — 전수 조사 금지

- 범위: `wiki/log.md` 최근 항목들이 언급한 변경 페이지 + `wiki/index.md`에서 무작위 표본 약 10페이지.
- 검사 항목: (a) 페이지 간 **모순** (b) **낡은 주장**(stale — updated가 오래됐고 이후 소스와 어긋나는 서술) (c) 여러 페이지에서 언급되는데 **존재하지 않는 페이지**(있어야 할 누락 페이지).

## 4. 리포트와 log

- `wiki/reports/YYYY-MM-DD-lint.md`를 작성한다: 기계 검사 결과 표(항목별 건수·상세) + 판단 검사 발견 + 권고 조치 목록.
- `wiki/log.md`에 `## [날짜] lint | <요약>` 항목을 append한다.
- 발견된 문제의 수정은 목록으로 제안하고 **사용자가 승인한 것만** 고친다(자동 일괄 수정 금지).

## 5. 규모와 스키마 공진화

- `wiki_check.py --stats`의 총 페이지 수(또는 index 항목 수)가 **200을 초과**하면: index만으로는 검색이 버거워지는 시점이므로 qmd 같은 마크다운 검색 CLI 도입을 제안한다 — 현재 설치·사용 방법을 조사해 **안내만** 하고, 자동 설치는 하지 않는다. 도입 시 config의 `search: qmd`로 기록하도록 안내한다(위키 콘텐츠는 무변경).
- 반복 관찰된 패턴(예: 특정 규칙이 계속 어겨짐, 자주 필요한데 없는 규칙)이 있으면 리포트에 **"AGENTS.md 개정 제안"** 섹션을 포함한다. 적용은 사용자 승인 후에만 한다 — 스키마는 사용자와 LLM이 공진화한다.
