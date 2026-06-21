---
name: glossary-check
description: 작업 완료 후나 커밋 전에 코드 네이밍을 프로젝트 용어사전과 대조해 위반·누락 용어를 검토할 때 사용한다. "용어 검사", "사전이랑 맞는지 확인", "네이밍 점검" 같은 요청에 트리거.
---

# 용어사전 검토

`.claude/superglossary/`가 있는 프로젝트에서 코드 네이밍을 사전과 대조한다.

1. **대상 결정**: 인자가 없으면 `git diff`(staged + unstaged)의 변경 파일, 경로가 주어지면 그 범위.
2. **후보 추출(결정론)**: `node .claude/superglossary/glossary.mjs lint <files...>`로 미매칭 토큰·미등록 축약어 후보를 빈도와 함께 얻는다.
3. **의미 확정(서브에이전트)**: 위 후보와 `node .claude/superglossary/glossary.mjs list` 결과를 `check-analyzer` 서브에이전트에 넘겨(Task) 의미 기반 확정을 받는다.
4. **보고**: 위반(코드→사전 다른 영문/미등록 축약어)과 추가 후보(사전→코드 미등록 용어)를 표로 보고한다. **자동 수정은 하지 않는다** — 적용은 사용자 판단.

작업 완료 후 커밋 전에 실행하기를 권장한다.
