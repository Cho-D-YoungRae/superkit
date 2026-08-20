---
name: init
description: 프로젝트 용어사전을 초기화하고 .claude/CLAUDE.md에 연결합니다. 재실행하면 CLI 복사본을 최신으로 갱신합니다(데이터 보존).
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Task, AskUserQuestion
---

# 용어사전 초기화

다음을 순서대로 수행한다.

1. `.claude/superglossary/` 디렉토리를 만들고 `${CLAUDE_PLUGIN_ROOT}/templates/glossary.py`를 `.claude/superglossary/glossary.py`로 복사한다. **기존 복사본이 있어도 덮어쓴다** — 재실행이 곧 CLI 업그레이드이며, `glossary.json`과 기존 CLAUDE.md 블록은 보존된다.
   (플러그인은 같은 CLI를 `superglossary` 명령으로도 노출한다. 복사본은 플러그인이 없는 팀원과 CI를 위한 것이므로 생략하지 않는다.)
2. 프로젝트 루트에서 `python3 .claude/superglossary/glossary.py init`을 실행한다(방금 복사한 사본이 도는지 함께 확인하기 위해 짧은 이름 대신 경로를 쓴다) → 초기 `glossary.json`(없을 때) · `core.md` · `terms.md` 생성 + `.claude/CLAUDE.md`에 `## 용어 사전` 블록 삽입(이미 있으면 건너뜀). 기존 `glossary.json`이 구 스키마면 이 단계에서 자동으로 올라간다(데이터 보존).
3. 출력에 **`.gitignore` 경고**가 있으면 그대로 사용자에게 전달하고, 안내된 패턴으로 `.gitignore`를 수정할지 확인한다(동의 시 수정). 용어사전은 팀과 공유되어야 가치가 있다.
4. 생성·연결 결과(및 CLI 버전: `python3 .claude/superglossary/glossary.py version`)를 사용자에게 보고한다.

## 기존 코드베이스(brownfield)라면

코드가 이미 존재하면, **용어 후보·혼용 스캔 여부를 먼저 사용자에게 묻는다**(AskUserQuestion).

- 동의하면 `glossary-scanner` 서브에이전트를 Task로 dispatch한다.
- scanner가 반환한 **(a) 단일어 후보**와 **(b) 혼용 리포트(영문 변형·빈도)**를 사용자에게 제시한다.
- 사용자가 후보를 선별하고, 혼용 건은 **표준 1개**를 고르면 — 탈락 변형을 금지 목록에 보존하며 등록한다:
  `python3 .claude/superglossary/glossary.py add <korean> <english> [abbreviation] [--desc "..."] --avoid "탈락변형1,탈락변형2"`
- **자동 리네이밍은 하지 않는다.** 비표준 사용처는 이후 check 스킬의 lint가 `[위반]`으로 보고한다.

분류(category)는 다루지 않는다.
