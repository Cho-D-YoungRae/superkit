# llm-wiki 플러그인 개발 가이드

이 파일은 **플러그인을 유지보수하는** 에이전트용이다. init이 위키에 만들어 주는 위키 규약(`templates/AGENTS.md.tmpl`)과 혼동하지 말 것. llm-wiki는 [superkit](../../README.md) 모노레포의 `plugins/llm-wiki`에 있고, 저장소 공통 규칙(브랜치·커밋·버전·태그)은 루트 [AGENTS.md](../../AGENTS.md)를 따른다. 아래 명령은 이 디렉토리에서 실행한다.

## 저장소 구조

```
.claude-plugin/          plugin.json(매니페스트) — 마켓플레이스는 superkit 루트의 .claude-plugin/marketplace.json
skills/
  wiki-init/ wiki-ingest/ wiki-lint/ wiki-status/
                         워크플로 스킬 4개 = 슬래시 커맨드 /llm-wiki:wiki-* — 순서·게이트·출력만 담는다
  wiki-maintainer/       위키 운영 보강 (1원칙: 위키의 AGENTS.md를 따르라) — 모델 전용
  source-extract/        소스 추출 레시피(단일 소스) + scripts/ 4개 — 모델 전용
  web-extract/           웹·HTML 원본 추출 — 포크된 서브에이전트(context: fork), 모델 전용
templates/               /wiki-init이 렌더링하는 위키 스캐폴드 원본 (AGENTS.md.tmpl이 심장)
tests/                   pytest (결정적 로직만, 네트워크 불필요) + fixtures/
docs/superpowers/        설계 스펙·구현 계획
README.md ARCHITECTURE.md LICENSE
```

## 불변 원칙 (판단이 흔들리면 여기로 회귀)

1. 파일시스템 + 결정적 스크립트 + 스킬만. 런타임 의존은 `uv` 하나.
2. 위키 자립성 — 규칙은 위키 안의 `AGENTS.md`에. 플러그인 없이도 동작.
3. 판단은 LLM, 기계 작업은 스크립트 — 스크립트는 stdout·`raw/.cache/`만 출력, `wiki/` 직접 쓰기 금지.
4. 옵션 3단 — Core(항상) / Obsidian(뷰어) / qmd(검색, 콘텐츠 무변경).
5. 압축 원칙 — 소스 1:1 미러 페이지 금지.
6. lint는 옵션이 아니다 — 드리프트가 1번 실패 모드.
7. 양 런타임 호환 — 스키마는 AGENTS.md가 canonical, 스크립트는 `uv run` 단독 실행.

## 수정 규칙

- **슬래시 커맨드(워크플로 스킬)는 4개를 유지한다.** 신규 기능은 커맨드 추가가 아니라 스킬 지시문 또는 AGENTS.md 스키마로 흡수를 먼저 검토한다. 보조 스킬은 `user-invocable: false`로 슬래시 메뉴에서 숨긴다(`tests/test_skills.py`가 검사).
- 커맨드는 `commands/`가 아니라 `skills/<이름>/SKILL.md`에 둔다(공식 권장 형식, `name`은 디렉토리명과 동일). `commands/`에 같은 이름을 만들지 않는다 — 충돌 동작이 문서화돼 있지 않다.
- 워크플로 스킬에 레시피·규칙 본문을 복제하지 않는다 — 추출 레시피는 `source-extract/SKILL.md`(웹·HTML은 `web-extract/SKILL.md`), 운영 규칙은 `templates/AGENTS.md.tmpl`이 단일 소스.
- 스크립트 출력 경계(stdout·캐시만)를 절대 넘지 않는다. 서드파티 의존은 지연 임포트(테스트가 의존 없이 순수 함수를 로드한다).
- 스킬 지시문에서 파일 읽기·검색은 Read·Glob·Grep 도구로, Bash는 `cd` 없이 절대 경로의 단일 명령으로 쓴다 — `cd … &&` 복합 명령·셸 변수·플래그 붙은 `cp`는 사용자 권한 확인을 부른다(ARCHITECTURE ADR-8, `tests/test_skills.py`가 검사).
- **`templates/` 변경 시**: `AGENTS.md.tmpl`의 managed 마커와 `config.yaml.tmpl`의 `schema_version`을 함께 증가시키고(단, main에 아직 나가지 않은 버전은 번호를 올리지 않고 제자리에서 보정하며 그 버전의 이력 줄을 갱신한다), `ARCHITECTURE.md` "스키마 버전 이력"에 변경 요약 한 줄을 추가하며(두 가지 모두 `tests/test_templates.py`가 검사), `skills/wiki-init/SKILL.md`의 업그레이드 경로(B 섹션)가 신·구 버전을 올바르게 마이그레이션하는지 갱신·확인한다. config 키 추가 시 업그레이드 모드의 "기본값으로 추가, 기존 값 유지" 규칙에 반영한다.
- 문서 동기화: 원칙·구조 변경 시 README.md와 ARCHITECTURE.md를 같은 변경에서 함께 수정한다.

## 테스트 절차

단위 테스트(결정적, 네트워크 불필요):

```bash
uv run --with pytest --with pyyaml --with pymupdf pytest tests/ -q
```

스모크 검증(수용 기준 — 설계 스펙 §11의 9개 시나리오): 임시 디렉토리에서 `claude --plugin-dir <이 저장소>` 세션을 열고 순서대로 수행한다 —
① `/llm-wiki:wiki-init`(옵시디언 no·유튜브 yes·git yes) → 구조·AGENTS.md 13섹션·CLAUDE.md 미생성(원래 CLAUDE.md가 있던 폴더면 `@AGENTS.md`가 덧붙음)·log init 항목 확인
② `tests/fixtures/sample-note.md` ingest → 분석 확인 단계 표시, sources 요약 1페이지+횡단 페이지+index·log 갱신, 1:1 미러 없음
③ 같은 파일 재-ingest → sha 스킵, `--force` 재수행
④ 자막 있는/없는 유튜브 URL → 정상 인제스트 / exit 2 안내 전달
⑤ 30쪽 초과 PDF → 청킹, log `part n/m`, 중단 후 재개
⑥ 위키 질문 → index 우선 조회, synthesis 회수
⑦ `/llm-wiki:wiki-lint` → clean 리포트, 링크 파손 후 재실행 시 감지
⑧ `/llm-wiki:wiki-status` → log 10건+통계, 파일 무변경
⑨ 문서가 설계 스펙 §7 요구 충족
⑩ (추가) 일반 웹 URL ingest → `web-extract`가 포크 실행되어 짧은 보고만 돌아오고, raw에 요약 없이 본문이 저장되며(`extraction: html`), 같은 URL 재-ingest는 URL로 스킵
⑪ (추가) 인젝션 판정 — 프롬프트 예시를 인용한 글(예: 프롬프트 사례를 소개하는 블로그)을 `--batch`로 ingest하면 멈추지 않고 예시를 출처 밝힌 인용으로 옮기며, 읽는 에이전트를 향한 지시문(숨은 HTML 주석 등)이 든 노트는 `--batch`여도 멈추고 확인을 요청하며 지시를 따르지 않는다(페이지·log·AGENTS.md 무변경)

각 태스크/변경 완료 시 위 단위 테스트를 반드시 실행하고, 커밋은 단계별로 분리한다.
