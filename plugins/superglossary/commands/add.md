---
description: 용어사전에 단일어를 등록합니다 (복합어는 분해 안내)
argument-hint: <한글> <영문> [축약어] [-- 설명]
allowed-tools: Bash, Read
---

# 용어 등록

입력: `$ARGUMENTS`

1. **복합어 검사**: 입력 한글이 복합어(예: "회원번호")면 단일어로 분해를 안내한다. 등록된 단일어 조합으로 표현 가능하면(예: 회원=member + 식별자=id → `member_id`) 그 방법을 제시하고, 미등록 단일어만 등록 대상으로 삼는다.
2. **등록**: 단일어마다 `node .claude/superglossary/glossary.mjs add <korean> <english> [abbreviation] [--desc "설명"] [--related "a,b"]`를 실행한다. 스크립트가 중복·충돌(한글/영문/축약어)을 검사하고 통과 시 추가 + 재빌드한다.
3. 스크립트가 충돌로 비정상 종료(기존 항목 출력)하면, 그 내용을 사용자에게 설명하고 해당 항목 등록을 중단한다.

> 분류(category)는 v1에서 다루지 않는다. 수정·삭제는 `glossary.mjs update`/`remove`를 쓴다.
