---
name: wiki-status
description: 위키 현황 — 최근 로그 10건 + 통계 + 핵심 질문 (읽기 전용)
disallowed-tools: ["Write", "Edit", "NotebookEdit"]
---

# /llm-wiki:wiki-status — 읽기 전용

**어떤 파일도 만들거나 수정하지 않는다. log 기록도 하지 않는다.**

1. 현재 디렉토리에서 상위로 `.llm-wiki/config.yaml`을 탐색해 위키 루트를 찾는다. 없으면 "이 디렉토리는 llm-wiki 위키가 아닙니다. `/llm-wiki:wiki-init`으로 먼저 위키를 만드세요."를 출력하고 종료한다. 이후 모든 Bash 명령은 `cd "<위키 루트>" && …` 형태로 실행한다.
2. 최근 활동: `grep '^## \[' wiki/log.md | tail -n 10`
3. 통계:

   ```bash
   uv run "${CLAUDE_PLUGIN_ROOT}/skills/source-extract/scripts/wiki_check.py" --stats --format json
   ```

   (uv가 없으면 `ls wiki/entities wiki/concepts wiki/sources wiki/synthesis raw/sources` 수준의 디렉토리 나열로 대체한다.)
   같은 스크립트를 `--pending --format json`으로 한 번 더 돌려 미인제스트 원본 수를 센다(uv가 없으면 생략).
4. `purpose.md`의 핵심 질문을 다시 보여준다.
5. 한 화면으로 요약 출력: 최근 활동 / 타입별 페이지 수·소스 수 표 / 핵심 질문. 미인제스트 원본이 있으면 그 수와 함께 인자 없는 `/llm-wiki:wiki-ingest`를 권장하고, 통계의 `last_lint`가 7일 이상 지났거나 없으면 마지막 줄에 `/llm-wiki:wiki-lint` 실행을 권장한다.
