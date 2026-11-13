# superglossary 0.8.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 합의한 문맥·축약·선택 읽기·현재 사전 기준 검사를 두 플랫폼에 반영하고 0.8.0으로 검증한다.

**Architecture:** Markdown 업무 규칙은 glossary-guide에 모으고 두 스킬과 scanner가 이를 따른다. 평가 자료는 설치 패키지 밖에 두며 전환 기록과 CI로 플랫폼 간 반영 누락을 검사한다.

**Tech Stack:** Markdown/YAML/JSON, 기존 Python/Node 검증 도구, 모델 행동 평가.

**Spec:** `docs/superpowers/specs/2026-11-13-superglossary-0.8.0-design.md`

## Global Constraints

- 기존 5열 유지, 문맥은 설명에 짧게 기록한다.
- 영문과 축약 분리, Markdown 원문 검색, 현재 작업 트리 사전 사용.
- 런타임 파서·스크립트·구버전 호환·자동 마이그레이션을 추가하지 않는다.
- 평가 자료는 `evals/superglossary/`에만 두며 설치 패키지에서 참조하지 않는다.
- 버전은 두 패키지 모두 0.8.0. 기존 `.gitignore`와 다른 플러그인은 건드리지 않는다.
- 사용자에게 승인받은 범위를 실행한다. 설치·배포·사용 프로젝트 반영은 후속 단계다.

## Review Focus

- 같은 표기이지만 다른 의미인 용어와 불명확한 금지 범위 → 의미/금지 평가에서 검증.
- 영문·축약을 함께 허용하면서 설명의 선호 조건 보존 → 축약 평가에서 검증.
- 커밋 사전과 현재 사전이 다르거나 사전만 바뀐 경우 → Git fixture 및 영향 평가에서 검증.
- 큰 파일에서 동의어·활용형 누락, 잘림, 읽기 실패 → 도구 기록을 포함한 읽기 평가에서 검증.
- 설치 패키지의 바깥 파일 참조·평가 포함·원본 변경 CI 누락 → 독립 패키지/CI 검사에서 검증.

## Task 1: 평가 기준과 baseline

Files: `evals/superglossary/`.

- [x] 여섯 범주의 예제·요청·기대 행동을 작성한다.
- [x] 변경 전 0.7.0으로 핵심 사례를 실행하고 실제 실패·실행 한계를 기록한다. 의미 중복 거부와 사전만 변경 시 조기 종료를 재현했다.
- [x] 재실행 가능한 절차와 도구 기록 확인 방법을 남긴다.

## Task 2: Claude 원본

Files: `plugins/superglossary/skills/{glossary,check}/`, `agents/glossary-scanner.md`, `README.md`, `AGENTS.md`, `CHANGELOG.md`, `.claude-plugin/plugin.json`.

- [x] guide의 의미/금지/축약/읽기 계약을 수정하고 템플릿도 일치시킨다.
- [x] glossary 추가·수정·분리의 충돌/읽기/승인 절차를 일치시킨다.
- [x] check의 코드 범위·현재 사전·사전 변경 영향·결과 구분을 구현한다.
- [x] scanner와 안내·버전·변경 이력을 갱신한다.

## Task 3: Codex 및 저장소 검증

Files: `plugins/superglossary-codex/`, `porting/superglossary/`, `.github/workflows/superglossary-codex.yml`.

- [x] 변경 전 원본/대상 상태를 비교한다.
- [x] 현재 사전 기준과 사전만 변경된 사례의 Git 검증을 보완한다. 기존 문서에서 현재 사전 검색 계약 부재로 실패함을 확인했다.
- [x] 원본 업무 규칙을 전환하고 기존 Codex 실행 계약을 유지한다.
- [x] 원본 경로 CI 트리거와 0.8.0 전환 기록을 반영한다.

## Task 4: 검증·리뷰·기준 확정

- [x] 여섯 범주(9개 fixture)의 행동 평가를 양쪽 새 스킬로 실행했다. 원본 9/9·Codex 9/9 PASS. 실제 네이티브 실행은 인증 부재로 미검증이며 새 컨텍스트 대리 하네스임을 결과에 기록했다.
- [x] Claude manifest, Codex schema/독립 패키지, Git fixture, 기존 상태 도구 테스트를 실행한다.
- [x] 별도 리뷰어가 업무 규칙·범위·패키지 경계를 검토한다. final_review PASS, 수정 지적 없음.
- [x] 검토한 원본/대상 상태를 snapshot하고 repository/diff 검사를 통과시킨다.
- [x] 변경 내용·검증 결과·버전·후속 적용 단계를 정리했다. 사용자 프로젝트 반영·설치·배포는 수행하지 않았으며 작업 브랜치에 변경을 보존한다.
