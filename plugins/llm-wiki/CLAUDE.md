# CLAUDE.md — llm-wiki 플러그인 개발 가이드

이 파일은 **플러그인 저장소를 유지보수하는** 에이전트용이다. init이 위키에 생성해 주는 포인터 파일(`templates/CLAUDE.md.tmpl`)과 혼동하지 말 것.

## 저장소 구조

```
.claude-plugin/          plugin.json(매니페스트) · marketplace.json(이 저장소 = 마켓플레이스)
commands/                커맨드 4개 — 워크플로의 순서·게이트·출력만 담는다
skills/
  wiki-maintainer/       위키 운영 보강 (1원칙: 위키의 AGENTS.md를 따르라)
  source-extract/        소스 추출 레시피(단일 소스) + scripts/ 3개
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

- **커맨드는 4개를 유지한다.** 신규 기능은 커맨드 추가가 아니라 스킬 지시문 또는 AGENTS.md 스키마로 흡수를 먼저 검토한다.
- 커맨드에 레시피·규칙 본문을 복제하지 않는다 — 추출 레시피는 `source-extract/SKILL.md`, 운영 규칙은 `templates/AGENTS.md.tmpl`이 단일 소스.
- 스크립트 출력 경계(stdout·캐시만)를 절대 넘지 않는다. 서드파티 의존은 지연 임포트(테스트가 의존 없이 순수 함수를 로드한다).
- **`templates/` 변경 시**: `AGENTS.md.tmpl`의 managed 마커 `schema_version`을 증가시키고, `commands/wiki-init.md`의 업그레이드 경로(B 섹션)가 신·구 버전을 올바르게 마이그레이션하는지 갱신·확인한다. config 키 추가 시 업그레이드 모드의 "기본값으로 추가, 기존 값 유지" 규칙에 반영한다.
- 문서 동기화: 원칙·구조 변경 시 README.md와 ARCHITECTURE.md를 같은 변경에서 함께 수정한다.

## 테스트 절차

단위 테스트(결정적, 네트워크 불필요):

```bash
uv run --with pytest --with pyyaml --with pymupdf pytest tests/ -q
```

스모크 검증(수용 기준 — 설계 스펙 §11의 9개 시나리오): 임시 디렉토리에서 `claude --plugin-dir <이 저장소>` 세션을 열고 순서대로 수행한다 —
① `/llm-wiki:wiki-init`(옵시디언 no·유튜브 yes·git yes) → 구조·AGENTS.md 13섹션·CLAUDE.md 포인터·log init 항목 확인
② `tests/fixtures/sample-note.md` ingest → 분석 확인 단계 표시, sources 요약 1페이지+횡단 페이지+index·log 갱신, 1:1 미러 없음
③ 같은 파일 재-ingest → sha 스킵, `--force` 재수행
④ 자막 있는/없는 유튜브 URL → 정상 인제스트 / exit 2 안내 전달
⑤ 30쪽 초과 PDF → 청킹, log `part n/m`, 중단 후 재개
⑥ 위키 질문 → index 우선 조회, synthesis 회수
⑦ `/llm-wiki:wiki-lint` → clean 리포트, 링크 파손 후 재실행 시 감지
⑧ `/llm-wiki:wiki-status` → log 10건+통계, 파일 무변경
⑨ 문서가 설계 스펙 §7 요구 충족

각 태스크/변경 완료 시 위 단위 테스트를 반드시 실행하고, 커밋은 단계별로 분리한다.
