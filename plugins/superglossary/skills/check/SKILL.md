---
name: check
description: 작업 완료 후나 커밋 전에 코드 네이밍을 프로젝트 용어사전과 대조해 위반·누락 용어를 검토할 때 사용한다. "용어 검사", "사전이랑 맞는지 확인", "네이밍 점검" 같은 요청에 트리거.
allowed-tools: Bash(superglossary:*), Bash(python3 .claude/superglossary/glossary.py:*), Bash(git diff:*), Bash(git ls-files:*), Task
---

# 용어사전 검토

1. **사전 확인**: `.claude/superglossary/`가 없으면 `/superglossary:init` 실행을 제안하고 종료한다.
2. **대상 결정**: 인자가 없으면 `git diff --name-only --diff-filter=d`(unstaged) + `git diff --cached --name-only --diff-filter=d`(staged) + `git ls-files --others --exclude-standard`(신규 untracked)의 합집합, 경로가 주어지면 그 범위. 삭제된 파일은 넘기지 않는다(lint는 없는 경로를 경고한다). `.claude/`(용어사전·CLAUDE.md)는 lint가 스스로 제외하므로 따로 거르지 않아도 된다. **대상이 하나도 없으면** "검사할 변경 파일이 없습니다"로 보고하고 종료한다(빈 목록으로 lint를 호출하지 않는다).
3. **후보 추출(결정론)**: `superglossary lint <paths...>` 실행(디렉토리를 주면 재귀 탐색한다). `superglossary`를 찾지 못하면 `python3 .claude/superglossary/glossary.py lint <paths...>`로 대체한다. 출력은 두 섹션 — `[위반]`(금지 변형 사용: `토큰	표준영문(한글)	빈도	파일`)과 `[후보]`(미등록 토큰: `토큰	빈도	파일`).
4. **위반 처리**: `[위반]`은 사전이 결정론적으로 확정한 결과다. 그대로 보고 표에 올린다.
5. **후보 처리(하이브리드)**:
   - `[후보]`가 **10개 이하**면 이 세션에서 직접 의미 확정한다. 판단 기준: ① 사전 등록 개념을 다른 영문으로 쓴 동의어(빈도·문맥 확인) ② 미등록 축약어 ③ 반복 등장하는 미등록 단일어는 추가 후보 ④ 일반 영어·라이브러리 식별자는 노이즈로 제외 ⑤ 기존 모듈 컨벤션 존중.
   - **10개 초과**면 `[후보]` 목록(파일 위치 포함)과 `superglossary list` 결과를 `check-analyzer` 서브에이전트에 넘겨(Task) 확정을 받는다.
6. **보고**: 위반(금지 변형 + 의미 위반)과 추가 후보(add 스킬로 등록할 대상)를 표로 보고한다. **자동 수정은 하지 않는다** — 적용은 사용자 판단.
7. **노이즈가 반복되면**: 사내 접두사처럼 후보로 계속 올라오는 무의미한 토큰이 있으면, `glossary.json`의 `stopwords.add`에 넣자고 제안한다(반대로 도메인 핵심어가 기본 스톱워드에 걸려 누락되면 `stopwords.remove`).

작업 완료 후 커밋 전에 실행하기를 권장한다.
