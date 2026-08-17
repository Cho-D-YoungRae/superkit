#!/usr/bin/env bash
# SessionStart 훅: cwd에서 git 루트까지 상향 탐색하며 docs/domain/summary.md를
# 찾아 그대로 출력한다(파싱하지 않는다). 없으면 조용히 종료한다.
set -euo pipefail
dir="$(pwd)"
while :; do
  if [ -f "$dir/docs/domain/summary.md" ]; then
    cat "$dir/docs/domain/summary.md"
    exit 0
  fi
  # git 루트(일반 저장소 디렉터리 또는 worktree 파일) 또는 파일시스템 루트에 도달하면 중단
  if [ -e "$dir/.git" ] || [ "$dir" = "/" ]; then
    exit 0
  fi
  dir="$(dirname "$dir")"
done
