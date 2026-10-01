---
name: init
description: 프로젝트 용어사전을 초기화하고 .claude/CLAUDE.md에 연결합니다. 재실행하면 CLI 복사본과 CLAUDE.md 블록을 최신으로 갱신합니다(데이터 보존).
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Agent, AskUserQuestion
---

# 용어사전 초기화

다음을 순서대로 수행한다.

1. 프로젝트 루트에서 `superglossary init`을 실행한다. `superglossary`를 찾지 못하면 `python3 "${CLAUDE_PLUGIN_ROOT}/templates/glossary.py" init`으로 대체한다(같은 CLI다). 이 한 번으로 다음이 처리된다.
   - `.claude/superglossary/`에 초기 `glossary.json`(없을 때) · `core.md` · `terms.md` 생성. 기존 `glossary.json`은 보존되며 구 스키마면 자동으로 올라간다.
   - CLI 복사본 `.claude/superglossary/glossary.py` 배치 — 플러그인이 없는 팀원과 CI를 위한 것이다. 재실행이 곧 CLI 업그레이드이며, 복사본이 플러그인보다 새 버전이면 덮어쓰지 않고 경고한다.
   - `.claude/CLAUDE.md`에 `## 용어 사전` 블록을 마커(`<!-- superglossary:begin -->`…`<!-- superglossary:end -->`)로 감싸 넣거나 최신 문구로 갱신한다. 마커 없는 구버전 블록도 손대지 않은 것이면 자동으로 바뀐다.
2. 방금 배치된 복사본이 도는지 `python3 .claude/superglossary/glossary.py version`으로 확인한다.
3. 출력의 **경고(⚠)**를 그대로 사용자에게 전달하고 필요한 조치를 확인한다.
   - `.gitignore` 경고: 안내된 패턴으로 `.gitignore`를 수정할지 묻는다(동의 시 수정). 용어사전은 팀과 공유되어야 가치가 있다.
   - 남은 `glossary.mjs`(0.4.0 이전 복사본) 경고: 삭제할지 묻는다(동의 시 삭제).
   - CLAUDE.md의 `## 용어 사전` 섹션이 직접 수정되어 갱신하지 않았다는 경고: 섹션을 지우고 init을 다시 실행할지 묻는다.
4. 생성·연결 결과와 CLI 버전을 사용자에게 보고한다.

## 기존 코드베이스(brownfield)라면

코드가 이미 존재하면, **용어 후보·혼용 스캔 여부를 먼저 사용자에게 묻는다**(AskUserQuestion).

- 동의하면 `glossary-scanner` 서브에이전트를 Agent 도구로 dispatch한다.
- scanner가 반환한 **(a) 단일어 후보**와 **(b) 혼용 리포트(영문 변형·빈도)**를 사용자에게 제시한다.
- 사용자가 후보를 선별하고, 혼용 건은 **표준 1개**를 고르면 — 탈락 변형을 금지 목록에 보존하며 등록한다(금지 변형도 단일어만 가능):
  `superglossary add <korean> <english> [abbreviation] [--desc "..."] --avoid "탈락변형1,탈락변형2"`
- **자동 리네이밍은 하지 않는다.** 비표준 사용처는 이후 check 스킬의 lint가 `[위반]`으로 보고한다.

분류(category)는 다루지 않는다.
