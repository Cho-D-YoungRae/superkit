# llm-wiki 플러그인 설계 스펙

- 날짜: 2026-07-27
- 상태: 승인됨 (사용자 "계속실행해줘" 지시로 일괄 진행)
- 기준 문서: 사용자가 제공한 구현 프롬프트(부록 A). 이 설계 문서는 그 프롬프트를 **베이스 스펙**으로 삼고, 프롬프트가 열어둔 결정을 확정하며, 구현 시점 공식 문서 조사 결과를 반영한다. 충돌 시 부록 A가 우선하고, 부록 A가 침묵하는 지점은 이 문서가 확정한다.

> **개정 메모 (2026-09-28)** — 이 문서는 초판 설계 스냅숏이다. 이후 변경은 `ARCHITECTURE.md`의 ADR과 커밋 이력이 기준이다: 커맨드를 `skills/wiki-*/SKILL.md`로 이전(ADR-5), 웹 원본 추출을 포크된 서브에이전트 `web-extract` + `html_to_md.py`로(ADR-6), `wiki_check`는 log·reports를 링크 검사와 고아 인바운드에서 제외(§5.3 ② 정교화)하고 옵시디언식 위키링크 해석·`raw-unreferenced`·`log-sha` 검사·`--pending`을 더했다. `yt_transcript`는 원어 우선 자막 선택(§5.1 대체), `pdf_chunk`는 목차 레벨 선택·작은 챕터 병합·`plan_version` 캐시 무효화(§5.2 대체). 인제스트 중복 확인은 원본 저장 전에, URL 소스는 URL로 한다.

## 1. 요약

`llm-wiki`는 Karpathy의 llm-wiki 패턴(LLM이 유지보수하는 개인 위키)을 Claude Code 플러그인으로 구현한다. 플러그인 = 부트스트래퍼 + 소스 추출 툴벨트이고, 위키 = 자립형 마크다운 저장소다. `/llm-wiki:wiki-init`이 생성한 위키는 플러그인 없는 머신·다른 에이전트(Codex 등)에서도 위키 안의 `AGENTS.md`만으로 동작한다.

베이스 스펙의 7개 불변 원칙(파일시스템+스크립트+스킬만 / 위키 자립성 / 판단은 LLM·기계 작업은 스크립트 / Core-Obsidian-qmd 3단 옵션 / 압축 원칙 / lint 필수 / 양 런타임 호환)과 비목표(MCP·벡터DB·지식그래프 UI·브라우저 확장·커맨드 5개 이상 금지)를 그대로 따른다.

## 2. 이번 설계에서 확정한 결정 (베이스 스펙 대비 추가)

| # | 결정 | 내용 | 근거 |
|---|------|------|------|
| D1 | 배포 = 저장소 자체가 마켓플레이스 | `.claude-plugin/marketplace.json` 추가. 설치: `/plugin marketplace add <owner>/llm-wiki` → `/plugin install llm-wiki@llm-wiki`. 로컬 개발 설치(`claude --plugin-dir .`)도 README에 병기 | 사용자 선택 |
| D2 | 라이선스 = MIT | `LICENSE` 파일 + `plugin.json`의 `license: "MIT"` | 사용자 선택 |
| D3 | 자동 테스트 = pytest | `tests/`에 결정적 로직 대상 pytest 추가(네트워크 불필요). 실행: `uv run --with pytest --with pyyaml --with pymupdf pytest tests/ -q` | 사용자 선택 |
| D4 | 커맨드-스킬 계층 = 얇은 커맨드 + 스킬 단일 소스 | 커맨드 md는 워크플로 골격(인자, 위키 루트 탐색, 단계 순서, 확인 게이트, 종료 출력)만. 추출 레시피는 `source-extract` 스킬에만, 위키 운영 규칙은 위키의 `AGENTS.md`에만 존재. 커맨드는 이를 참조하도록 지시 | 드리프트 방지 원칙(§1-6)을 플러그인 저장소에도 적용 |
| D5 | 커맨드 호출 표기 = 네임스페이스 형식 | 플러그인 커맨드는 `/llm-wiki:wiki-init` 형태로 호출됨(공식 문서 확인). README·안내 문구 전부 이 표기 사용 | 공식 문서 조사 |
| D6 | 번들 스크립트 참조 = `${CLAUDE_PLUGIN_ROOT}` | 커맨드 본문에서 `uv run "${CLAUDE_PLUGIN_ROOT}/skills/source-extract/scripts/x.py"` 형태. 스킬 본문에서는 `${CLAUDE_SKILL_DIR}/scripts/x.py`도 사용 가능 | 공식 문서 조사 |
| D7 | `pdf_chunk.py --info` 계약 확장 | 쪽수·목차 유무만 JSON으로 출력하고 캐시를 쓰지 않는 플래그. `pdf_direct_max_pages` 판정에 필요(에이전트가 쪽수를 알 방법이 계약에 없었음) | 베이스 스펙 §4.2의 "쪽수 확인" 실행 수단 |
| D8 | 스크립트 지연 임포트 | 서드파티 의존(yt_dlp, pymupdf)은 사용 함수 안에서 임포트. 순수 파싱 함수는 의존 없이 임포트 가능 → pytest가 네트워크·무거운 의존 없이 검증 | D3 실현 |
| D9 | 빈 디렉토리 = `.gitkeep` | init에서 git 사용 시 `raw/sources/` 등 빈 디렉토리에 `.gitkeep` 생성(디렉토리 소실 방지) | git 동작 특성 |
| D10 | managed 마커에 버전 표기 | `<!-- llm-wiki:managed:start schema_version=1 -->` 형태. 업그레이드 모드가 이 값과 템플릿 버전을 비교 | §4.1 업그레이드 모드 구현 수단 |
| D11 | plugin.json 스키마 확정 | `name` 필수, `author`는 객체 `{name, url}`. `version: 0.1.0`, `description`, `license`, `keywords`, `repository`, `homepage` 포함 | 공식 문서 조사(추측 금지 조항 이행) |
| D12 | 특수 파일 frontmatter 면제 | `wiki/index.md`·`log.md`·`overview.md`·`reports/*`는 페이지 frontmatter 스펙 적용 대상이 아님. `wiki_check.py` 검증 대상은 4개 타입 디렉토리의 페이지만 | frontmatter 스펙의 적용 범위 명확화 |

## 3. 저장소 파일 청사진

```
llm-wiki/
├── .claude-plugin/
│   ├── plugin.json              # D11 스키마
│   └── marketplace.json         # D1: name=llm-wiki, owner, plugins=[{name: llm-wiki, source: "./"}]
├── commands/
│   ├── wiki-init.md             # 인터뷰 4문항 → 템플릿 렌더링 → 사전요건 체크 (+업그레이드 모드)
│   ├── wiki-ingest.md           # 위키 루트 탐색 → source-extract 스킬로 추출 → sha 중복 확인 → 2단계 인제스트
│   ├── wiki-lint.md             # wiki_check.py 실행 → LLM 판단 검사(표본) → 리포트 → qmd/스키마 개정 제안
│   └── wiki-status.md           # 읽기 전용: log tail 10 + --stats + purpose 핵심 질문
├── skills/
│   ├── wiki-maintainer/
│   │   └── SKILL.md             # 1원칙: 위키의 AGENTS.md를 읽고 따르라 + 플러그인 보강(스크립트 경로, 커맨드 연계)
│   └── source-extract/
│       ├── SKILL.md             # 유형별 추출 레시피 + 폴백 안내 (유일한 레시피 소스, D4)
│       └── scripts/
│           ├── yt_transcript.py
│           ├── pdf_chunk.py
│           └── wiki_check.py
├── templates/
│   ├── AGENTS.md.tmpl           # 13개 섹션, managed 마커(D10), 링크 규칙 조건 블록
│   ├── CLAUDE.md.tmpl           # "@AGENTS.md" 임포트 + 폴백 한 줄
│   ├── purpose.md.tmpl          # {{PURPOSE}}, {{KEY_QUESTIONS}}
│   ├── config.yaml.tmpl         # §3.1 스키마 + 플레이스홀더
│   ├── index.md.tmpl            # 타입별 빈 섹션
│   ├── log.md.tmpl              # 헤더 + 규약 안내(항목은 init이 append)
│   └── overview.md.tmpl         # 빈 전역 요약 스켈레톤
├── tests/
│   ├── fixtures/
│   │   ├── sample-note.md       # 스모크용: 엔티티 2~3, 개념 2 이상 포함한 학습 노트
│   │   └── sample-captions.vtt  # 롤링 캡션 중복 포함 VTT (yt 파서 테스트)
│   ├── conftest.py              # scripts/ 모듈 로더 (importlib)
│   ├── test_yt_transcript.py    # VTT 파싱·중복 정리·문단화·frontmatter 조립
│   ├── test_pdf_chunk.py        # TOC/고정 분할 경계, manifest, idempotent (pymupdf로 임시 PDF 생성)
│   └── test_wiki_check.py       # 7개 검사 항목 각각 + --stats (tmp_path에 미니 위키 구성)
├── docs/superpowers/            # 설계·계획 문서 (이 파일 포함)
├── .gitignore                   # __pycache__, .pytest_cache, .venv 등
├── LICENSE                      # MIT (D2)
├── README.md                    # §7.1 — 크레딧, 설치(D1·D5), Quickstart, 커맨드 레퍼런스, 유즈케이스 3개, FAQ
├── ARCHITECTURE.md              # §7.2 — mermaid 2개, 경계 표, 옵션 매트릭스, ADR 4건
└── CLAUDE.md                    # §7.3 — 개발 가이드 (테스트 절차 = D3 명령 + §8 스모크 절차)
```

## 4. 지식의 단일 소스 매트릭스 (D4)

| 지식 | 유일한 위치 | 참조하는 곳 |
|------|------------|------------|
| 위키 운영 규칙 전체(페이지 타입, frontmatter, ingest/query/lint/retire 워크플로, log 규약) | 위키의 `AGENTS.md` (templates/AGENTS.md.tmpl이 원본) | wiki-maintainer 스킬, 커맨드 4개 |
| 소스 유형별 추출 레시피(스크립트 사용법, 폴백) | `skills/source-extract/SKILL.md` | wiki-ingest 커맨드, wiki-maintainer 스킬 |
| 스크립트 계약(usage, exit code) | 각 스크립트의 `--help`/docstring + ARCHITECTURE.md | source-extract SKILL.md |
| 위키의 "왜"(목적·핵심 질문·논지) | 위키의 `purpose.md` | 세션 시작 절차(AGENTS.md §2) |
| 플러그인 개발 규칙 | 루트 `CLAUDE.md` | — |

커맨드 본문 규칙: 절차의 **순서와 게이트**는 커맨드에 쓰되, 절차의 **내용**이 위 표의 소스에 있으면 "X를 읽고 따르라"로 위임한다. 커맨드에 레시피·규칙 본문을 복제하지 않는다.

## 5. 스크립트 계약 상세 (§6 구체화)

공통: PEP 723 인라인 메타데이터(`requires-python = ">=3.12"`), `uv run scripts/x.py` 단독 실행. stdout 또는 캐시 디렉토리에만 출력, `wiki/` 파일 직접 쓰기 금지. 사람이 읽을 에러는 stderr(한국어). exit 0 성공 / 1 일반 오류 / 2 도메인 특수 상황. 서드파티 임포트는 지연 임포트(D8).

### 5.1 yt_transcript.py

- `usage: uv run yt_transcript.py URL [--langs ko,en]` / deps: `yt-dlp>=2025.1.1` (하한만, 상한 핀 금지)
- 동작: yt-dlp Python API로 메타데이터+자막 목록 조회(영상 다운로드 금지). 자막 선택 우선순위: langs 순서로 수동 자막 전부 → langs 순서로 자동 자막. VTT를 받아 파싱.
- 자동 자막 VTT 정리(핵심): 태그(`<c>`, 인라인 타임스탬프) 제거 → 연속 중복 라인 제거·병합(롤링 캡션) → 시간 간격(기본 4초 초과) 또는 누적 길이(~600자) 기준 문단화, 문단 시작에 `[mm:ss]` 마커.
- stdout: frontmatter(`title, channel, url, upload_date(YYYY-MM-DD), duration, lang, retrieved`) + 정리된 트랜스크립트.
- exit 2 = 자막 없음(stderr: "자막이 없는 영상 — 지원 범위 외. 영상 설명란·관련 블로그 등 수동 대안을 사용하세요.").
- 테스트 가능 함수 분리: `parse_vtt(text) -> list[Cue]`, `dedupe_cues(cues)`, `to_paragraphs(cues, gap, max_chars)`, `render_markdown(meta, paragraphs)`.

### 5.2 pdf_chunk.py

- `usage: uv run pdf_chunk.py PATH [--chunk-pages 20] [--cache-dir raw/.cache] [--force] [--info]` / deps: `pymupdf>=1.24`
- `--info`(D7): `{"pages": N, "toc": true|false, "toc_top_entries": M}` JSON만 stdout, 캐시 미생성.
- 분할: sha256 → `<cache-dir>/<sha12>/`에 `manifest.json` + `part-NN.md`. 캐시 존재 시 재사용(idempotent, manifest 요약만 출력), `--force`로 재생성. TOC 있으면 최상위 챕터 경계 우선(챕터가 chunk-pages의 1.5배 초과 시 고정 쪽수로 재분할), 없으면 고정 쪽수 분할.
- part frontmatter: `source, part: n/m, pages: a-b, toc_title(있을 때)`. 본문에 쪽 경계 `[p.N]` 마커.
- stdout: manifest 요약 JSON(`{sha12, pages, parts: [{file, pages, title}]}`).
- exit 2 = 암호화 등으로 텍스트 추출 불가(stderr 안내).
- 테스트 가능 함수 분리: `plan_chunks(page_count, toc, chunk_pages) -> list[Chunk]` (순수 로직).

### 5.3 wiki_check.py

- `usage: uv run wiki_check.py [--format md|json] [--stats]` / deps: `pyyaml` (그 외 표준 라이브러리)
- 위키 루트: cwd에서 상위로 `.llm-wiki/config.yaml` 탐색(커맨드와 동일 규칙). 없으면 exit 1 + 안내.
- 검사 7종: ① 깨진 링크(markdown 상대 경로 해석 + wikilink는 wiki/ 내 파일명 stem 매칭, 두 스타일 모두 항상 검사, http/anchor/mailto 제외) ② 고아 페이지(4개 타입 디렉토리 페이지 중 index.md를 제외한 페이지들로부터 인바운드 0) ③ index↔실제 파일 정합(누락/유령) ④ frontmatter 필수 필드·type enum·날짜 형식(대상: 4개 타입 디렉토리만, D12) ⑤ `sources[]` 경로 실존 ⑥ 제목·별칭·파일명 stem 충돌 ⑦ log 규약 위반(`^## \[YYYY-MM-DD\] op \| 제목`, op ∈ init·ingest·query·lint·retire 외 형식의 `## ` 헤딩)
- `--stats`: 타입별 페이지 수, raw 소스 수, 아카이브 수, log 항목 수, 마지막 lint 날짜(reports/ 파일명 기준). 검사 없이 통계만.
- exit 0 clean / 1 findings. 파일을 절대 쓰지 않는다(읽기 전용).
- 테스트 가능: 검사 로직을 `check_*` 함수로 분리, tmp_path 미니 위키로 각 검사를 단독 검증.

## 6. 템플릿 렌더링 규약 (§3.3 구체화)

- 엔진 없음. init 커맨드의 지시에 따라 에이전트가 직접 치환·제거한다.
- 플레이스홀더: `{{PURPOSE}}`, `{{KEY_QUESTIONS}}`(purpose.md), `{{LANGUAGE}}`, `{{OBSIDIAN}}`, `{{LINK_STYLE}}`, `{{YT_LANGS}}`(config.yaml). AGENTS.md.tmpl은 플레이스홀더 없이 조건 블록만 사용(정적 유지 → 업그레이드 diff 최소화).
- 조건 블록 키 3종: `<!-- if:obsidian -->…<!-- endif:obsidian -->`, `<!-- if:wikilink -->…<!-- endif:wikilink -->`, `<!-- if:markdown -->…<!-- endif:markdown -->`. 채택 블록은 마커만 벗기고, 미채택 블록은 통째로 삭제.
- managed 영역: AGENTS.md 스키마 본문 전체를 `<!-- llm-wiki:managed:start schema_version=1 -->` / `<!-- llm-wiki:managed:end -->`로 감싼다. 마커 밖(파일 하단 "사용자 확장 영역")은 업그레이드 시 보존.
- 업그레이드 판정: 위키 AGENTS.md의 마커 `schema_version` vs 플러그인 템플릿의 `schema_version`. 다르면 현재 config(link_style 등)로 새 managed 블록을 렌더링해 diff 제시 → 승인 후 마커 사이만 교체, config의 `schema_version` 갱신, log에 init 항목 기록. config에 새 키가 생겼으면 기본값으로 추가(기존 값 보존).

## 7. AGENTS.md.tmpl 13개 섹션 (§3.2 그대로)

1 개요와 3계층·에이전트 역할 / 2 세션 시작 절차 / 3 페이지 타입 4종 / 4 frontmatter 스펙 / 5 링크 규칙(조건 블록) / 6 네이밍 / 7 Ingest 워크플로(2단계, new-vs-edit 휴리스틱, 3회 언급 승격, sha 중복 스킵) / 8 Query 워크플로(index 우선, 본문 전체 스캔 금지, synthesis 회수) / 9 Lint 워크플로(기계+판단, 리포트 경로, qmd 200 기준, 스키마 공진화) / 10 Retire 절차(계단식) / 11 log 규약 / 12 이미지 / 13 overview.md. — 플러그인 의존 문구(`wiki_check.py` 등)는 "플러그인 환경이면"으로 조건화해 위키 자립성 유지.

## 8. 커맨드 공통 규약

- 위키 루트 탐색: cwd에서 상위로 `.llm-wiki/config.yaml` 탐색. 없으면 "위키가 아님 — `/llm-wiki:wiki-init`으로 생성" 안내 후 종료(wiki-init 제외).
- frontmatter: `description`(트리거 요약), `argument-hint`. 인자는 `$ARGUMENTS`로 수신.
- wiki-status는 읽기 전용 선언(파일 수정 도구 사용 금지 명시).
- sha256: macOS `shasum -a 256` / Linux `sha256sum` 중 가용한 것 사용(커맨드에 명시), 12자리 축약을 log에 기록.

## 9. 테스트 전략 (D3 + §8)

pytest(결정적, 네트워크 불필요): VTT 파싱·중복 정리·문단화 / 청킹 계획(TOC 유·무·재분할 경계) / manifest 캐시 idempotent / wiki_check 7개 검사 각각의 양성·음성 케이스 / --stats. 실행: `uv run --with pytest --with pyyaml --with pymupdf pytest tests/ -q`.

§8 스모크 9종: 임시 디렉토리에서 커맨드 지시문을 에이전트가 그대로 수행해 검증(유튜브 실 URL 건은 네트워크 가용 시 실행, 불가 시 픽스처 기반 테스트 결과로 대체하고 문서에 명시). 절차는 루트 CLAUDE.md에 기록.

## 10. 에러 처리 원칙

- 스크립트: 위 exit code 계약. 커맨드·스킬은 exit 2를 "지원 범위 외/특수 상황" 폴백 안내로 변환해 사용자에게 전달(자막 없음 → 수동 대안, 암호화 PDF → 해제 후 재시도 안내).
- uv 부재: init 사전요건 체크에서 설치 안내(`brew install uv` 등) 출력하되 스캐폴드는 계속.
- 웹 fetch 실패: obsidian 사용자면 Web Clipper 폴백 안내, 아니면 수동 저장 안내(source-extract 스킬에 기재).
- 인제스트 중단: PDF 청크는 log의 `part n/m` 기록으로 재개 지점 판별.

## 11. 수용 기준 매핑 (§8 → 검증 방법)

| §8 | 검증 방법 |
|----|----------|
| 1 init | 임시 디렉토리에서 init 지시문 수행(옵시디언 no·유튜브 yes·git yes) → 구조·13섹션·CLAUDE.md 포인터·log 항목 확인 |
| 2 첫 ingest | fixtures/sample-note.md → 분석 노트 표시 → sources 1페이지+개념/엔티티 페이지+index·log 갱신, 1:1 미러 부재 확인 |
| 3 재-ingest | sha grep 스킵 → `--force` 재수행 |
| 4 유튜브 | 자막 있는 실 URL 1건 + 없는 URL 1건(exit 2 안내 전달). 네트워크 불가 시 pytest 결과로 대체 명시 |
| 5 장문 PDF | pymupdf로 40쪽 테스트 PDF 생성 → 청킹 경로·part 진행 log·중단 후 재개 |
| 6 질의 | index 우선 조회로 답변 → synthesis 회수 |
| 7 lint | clean 리포트 → 링크 고의 파손 → wiki_check 감지(exit 1) |
| 8 status | log 10건+통계 출력, 파일 mtime 무변경 확인 |
| 9 문서 | §7.1~7.3 체크리스트 대조 |

## 12. 구현 순서 (§9 그대로, 단계별 커밋)

templates → scripts(+tests) → commands → skills → docs(README·ARCHITECTURE·CLAUDE.md·LICENSE·plugin.json·marketplace.json은 구조상 첫 단계에 골격 생성 가능) → §8 스모크 검증. 각 단계 완료 시 커밋 분리.

---

## 부록 A. 베이스 스펙 (사용자 제공 프롬프트 — 규범 내용 보존 요약)

> 아래는 사용자가 제공한 구현 프롬프트의 규범 내용을 보존한 요약이다(§0·§1·§3·§3.1은 원문 그대로, 나머지는 요구사항 손실 없이 압축). 이 설계 문서와 충돌 시 아래가 우선한다.

LLM Wiki — Claude Code 플러그인 구현 프롬프트
너는 이 저장소에서 `llm-wiki`라는 Claude Code 플러그인을 처음부터 구현한다. 이 문서가 유일한 사양(spec)이다. 아래 참고 링크를 fetch할 수 있으면 참고하되, §10 요약만으로도 구현에 충분하도록 작성되어 있다. 사양과 충돌하는 내용은 이 문서가 우선한다.

* 원전(패턴): https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f — LLM이 유지보수하는 개인 위키 패턴
* 참고 구현(아이디어 차용만): https://github.com/nashsu/llm_wiki — 데스크톱 앱. 개념 일부만 차용하고 아키텍처는 차용 금지

0. 포지셔닝과 비목표
포지셔닝: 플러그인 = 부트스트래퍼 + 소스 추출 툴벨트. 위키 = 자립형 마크다운 저장소. `/wiki-init`이 생성한 위키는 이 플러그인이 없는 머신, 다른 에이전트(Codex 등)에서도 스키마 파일(AGENTS.md)만으로 동작해야 한다. 플러그인은 세팅·업그레이드·소스 추출만 담당한다.
비목표 — 구현 금지 (오버엔지니어링 방지):

* MCP 서버, 상주 프로세스, HTTP API
* 벡터 DB·임베딩·자체 검색 엔진 (검색은 선택적 qmd 안내로 대체)
* 지식그래프 엔진·시각화 UI (옵시디언 graph view가 대체)
* 브라우저 확장, Whisper(자막 없는 영상), Notion 백엔드, 리뷰 큐, Marp 등 출력 툴링
* 커맨드 5개 이상 (신규 기능은 스키마/스킬 지시문으로 흡수 우선)

1. 불변 설계 원칙
구현 중 모든 판단은 이 7개 원칙으로 회귀한다.

1. 파일시스템 + 결정적 스크립트 + 스킬만 사용한다. 런타임 의존은 `uv` 하나다.
2. 위키 자립성: 위키의 모든 규칙은 위키 안의 AGENTS.md에 있다. 플러그인 없이도 동작한다.
3. 판단은 LLM, 기계 작업은 스크립트: 추출 스크립트는 stdout 또는 캐시 디렉토리에만 출력하고 `wiki/` 파일을 직접 쓰지 않는다. 어디에 어떻게 반영할지는 항상 에이전트가 결정한다.
4. 옵션 3단 구조: Core(항상) / Obsidian(뷰어 옵션 — 링크 문법·`.obsidian/`·클리퍼 안내에만 영향) / qmd(검색 옵션 — 콘텐츠 무변경, 언제든 attach 가능).
5. 압축 원칙: 위키는 여러 소스에 흩어진 사실을 압축할 때만 가치가 있다. 소스당 요약 1페이지 + 횡단 개념/엔티티 페이지가 기본이며, 소스를 1:1로 미러링하는 페이지는 금지한다.
6. lint는 옵션이 아니다: 드리프트(교차 참조가 조용히 낡는 것)가 이 패턴의 1번 실패 모드다.
7. 양 런타임 호환: Claude Code + Codex. 스키마는 AGENTS.md가 canonical, 스크립트는 `uv run`으로 단독 실행.

문서·커맨드·스킬 지시문은 한국어로 작성한다. 코드, 경로, frontmatter 키, config 키는 영어를 쓴다.

2. 플러그인 저장소 구조 — (설계 문서 §3의 청사진과 동일 구조 + marketplace.json·LICENSE·tests 확장. plugin.json·커맨드 frontmatter·SKILL.md frontmatter는 구현 시점 공식 문서 기준으로 정확히 작성, 스키마 추측 금지. 루트 CLAUDE.md는 개발 가이드, templates/CLAUDE.md.tmpl은 위키용 포인터 — 혼동 금지.)

3. 위키 스캐폴드 사양 (init 결과물)

```
my-wiki/
├── AGENTS.md                # canonical 스키마 — 이 위키의 헌법
├── CLAUDE.md                # 포인터: "@AGENTS.md" 임포트 한 줄 + 폴백 안내 한 줄
├── purpose.md               # 위키의 목적·핵심 질문·발전 중인 논지
├── .llm-wiki/
│   └── config.yaml
├── raw/
│   ├── sources/             # YYYY-MM-DD-slug.ext
│   ├── assets/
│   ├── archive/
│   └── .cache/              # gitignore 대상
└── wiki/
    ├── index.md
    ├── log.md
    ├── overview.md
    ├── reports/
    ├── entities/
    ├── concepts/
    ├── sources/
    └── synthesis/
```

단일 소스 규칙: 스키마 내용은 AGENTS.md 한 곳에만. CLAUDE.md는 `@AGENTS.md` 임포트 + 폴백 안내 한 줄. 방향을 뒤집지 않는 이유: Claude Code는 CLAUDE.md만 자동 로드하지만 `@path` 임포트가 있고, AGENTS.md 표준에는 임포트 문법이 없다. 심볼릭링크 금지(Windows core.symlinks=false에서 이식성 깨짐).

3.1 config.yaml 스키마

```yaml
schema_version: 1
language: ko
obsidian: false
link_style: markdown          # markdown | wikilink (obsidian: true면 기본 wikilink)
search: none                  # none | qmd
ingest:
  pdf_direct_max_pages: 30
  pdf_chunk_pages: 20
  youtube_sub_langs: [ko, en]
```

* 커맨드는 cwd에서 상위로 `.llm-wiki/config.yaml`을 탐색해 위키 루트를 찾는다. 없으면 "위키가 아님 — /wiki-init 안내"로 종료.
* 다중 위키 지원은 "해당 위키 저장소에서 실행"으로 단순화.

3.2 AGENTS.md 필수 13개 섹션: ① 개요와 3계층·에이전트 역할 ② 세션 시작 절차(config → purpose → log 최근 항목) ③ 페이지 타입 4종(entity/concept/source/synthesis — 정의·위치·예시) ④ frontmatter 스펙(type/title/sources/created/updated 필수, tags/aliases 선택) ⑤ 링크 규칙(config.link_style 따라 렌더링) ⑥ 네이밍(페이지 kebab-case, 원본 YYYY-MM-DD-slug.ext) ⑦ Ingest 워크플로(1단계 분석 → 사용자 확인(batch 생략, 분석 요약 log) → 2단계 생성·갱신 한 pass; new-vs-edit 휴리스틱; 3회 이상 언급 개념 승격; sha256 12자리 log 기록·grep 중복 확인) ⑧ Query 워크플로(index 먼저 → 후보 ~10 → 정독 → 출처와 합성; 본문 전체 스캔 금지; 가치 있는 답변 synthesis 회수·log 기록) ⑨ Lint 워크플로(기계 검사 + LLM 판단 검사; 리포트 wiki/reports/YYYY-MM-DD-lint.md; index 200 초과 시 qmd 제안; 스키마 공진화 조항) ⑩ Retire 절차(archive 이동 → sources[] 제거 → 유일 출처 페이지만 삭제 → 죽은 링크·index 정리 → log) ⑪ log 규약(`## [YYYY-MM-DD] <op> | <제목>`, op ∈ init·ingest·query·lint·retire, grep 파싱 가능, 본문에 sha·갱신 페이지) ⑫ 이미지(raw/assets/ 로컬 저장, 필요한 것만 열람) ⑬ overview.md(주요 pass 후 갱신, 형식 자유)

3.3 템플릿 렌더링: 엔진 없음. `{{PLACEHOLDER}}` + 조건 블록 주석. managed 마커로 플러그인 관리 영역 구분, 마커 밖 사용자 영역 보존.

4. 커맨드 사양
4.1 /wiki-init: 업그레이드 모드(managed 블록만 갱신, diff 승인) / 신규 인터뷰 4문항(목적·핵심질문 → purpose.md / 옵시디언 → link_style·.obsidian/·클리퍼 안내 / 유튜브 → 사전요건 / git → init + .gitignore에 raw/.cache/) / uv 체크(없으면 안내하되 계속) / 렌더링 → log init 항목 → 다음 단계 안내.
4.2 /wiki-ingest <url|path> [--batch] [--force]: 루트 탐색·config 로드 → 유형 판별·원본 확보(유튜브=yt_transcript.py, 웹=내장 fetch로 마크다운 정리, md/txt=복사, PDF=쪽수 기준 직접/청킹) → sha256·log grep 중복 확인(--force 강제) → AGENTS.md 2단계 워크플로(기본 대화형, --batch 생략) → 갱신 요약 출력.
4.3 /wiki-lint: wiki_check.py --format json → LLM 판단 검사(전수 금지: 최근 변경 + 무작위 ~10) → 리포트·log → 200 초과 시 qmd 제안 → AGENTS.md 개정 제안 섹션(공진화).
4.4 /wiki-status: log tail 10 + wiki_check.py --stats + purpose 핵심 질문 재표시. 읽기 전용.

5. 스킬 사양: skill-creator 규약(트리거는 frontmatter description에 pushy하게, 본문 500줄 이하, progressive disclosure). wiki-maintainer(운영 판단 전반, "AGENTS.md를 읽고 따르라" 1원칙 + 플러그인 보강), source-extract(유형별 레시피 + 폴백 안내).

6. 스크립트 계약: PEP 723, `requires-python = ">=3.12"`, stdout/캐시만, stderr 에러, exit 0/1/2. yt_transcript.py(yt-dlp 하한만, 수동 우선 자막, VTT 롤링 중복 정리, frontmatter+[mm:ss], exit 2 자막 없음), pdf_chunk.py(pymupdf, sha 캐시 idempotent, TOC 우선 분할, part frontmatter, manifest 요약 stdout), wiki_check.py(pyyaml만, 검사 7종, --stats, exit 0/1).

7. 문서화: README(크레딧·설치·Quickstart·커맨드 레퍼런스·유즈케이스 3개·아키텍처 요약·요구사항·FAQ), ARCHITECTURE(3계층·3연산 mermaid, ingest 시퀀스, 경계 표, 옵션 매트릭스, ADR 4건), CLAUDE.md(구조 지도·원칙 요약·수정 규칙·문서 동기화·테스트 절차).

8. 수용 기준: 스모크 시나리오 9종(본 설계 문서 §11 표와 동일).

9. 구현 순서: templates → scripts → commands → skills → docs → 스모크. 단계별 커밋 분리.

10. 참조 요약: karpathy gist(3계층·3연산·index/log 특수 파일·모듈식 옵션·운영 교훈: 드리프트 1번 실패 모드, 압축일 때만 이득, 기계 작업 스크립트, 인덱스→선별→정독), nashsu 차용(purpose.md, 2단계 인제스트, sources[] 추적성·계단식 retire, overview.md, 해시 스킵) / 차용 금지(LanceDB, 지식그래프 엔진, HTTP API·MCP, Deep Research, 크롬 확장, Rust 파서).
