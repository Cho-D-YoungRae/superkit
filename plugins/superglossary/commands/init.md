---
description: 프로젝트 용어사전을 초기화하고 .claude/CLAUDE.md에 연결합니다
argument-hint: ""
allowed-tools: Bash, Read, Write, Edit, Task, AskUserQuestion
---

# 용어사전 초기화

다음을 순서대로 수행한다.

1. `.claude/superglossary/` 디렉토리를 만들고 `${CLAUDE_PLUGIN_ROOT}/templates/glossary.mjs`를 `.claude/superglossary/glossary.mjs`로 복사한다.
2. `node .claude/superglossary/glossary.mjs init`을 실행한다 → 초기 `glossary.json`(없을 때) · `core.md` · `terms.md` 생성 + `.claude/CLAUDE.md`에 `## 용어 사전` 블록 삽입(이미 있으면 건너뜀).
3. 생성·연결 결과를 사용자에게 보고한다.

## 기존 코드베이스(brownfield)라면

코드가 이미 존재하면, **용어 후보·혼용 스캔 여부를 먼저 사용자에게 묻는다**(AskUserQuestion).

- 동의하면 `glossary-scanner` 서브에이전트를 Task로 dispatch한다.
- scanner가 반환한 **(a) 단일어 후보**와 **(b) 혼용 리포트(영문 변형·빈도)**를 사용자에게 제시한다.
- 사용자가 후보를 선별하고, 혼용 건은 **표준 1개**를 고르면, 각 항목을 `node .claude/superglossary/glossary.mjs add <korean> <english> [abbreviation] [--desc "..."]`로 등록한다.
- **자동 리네이밍은 하지 않는다.** 비표준 사용처는 이후 `glossary-check`가 보고한다.

분류(category)는 v1에서 다루지 않는다.
