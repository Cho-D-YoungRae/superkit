#!/usr/bin/env python3
"""PostToolUse(Bash) hook — mutating 인프라 명령 실행 후 변경 기록 리마인드.

독립 실행형(다른 모듈 import 없음). 어떤 경우에도 exit 0 (비차단 — 스펙 D6).
"""
import json
import re
import sys
from pathlib import Path

MUTATING = [
    r"\bterraform\s+.*\b(apply|destroy|import|taint|untaint)\b",
    r"\bterraform\s+.*\bstate\s+(mv|rm|push)\b",
    r"\bkubectl\b.*\b(apply|create|delete|patch|replace|scale|edit|label|annotate|cordon|uncordon|drain|taint)\b",
    r"\bkubectl\b.*\brollout\s+(restart|undo|pause|resume)\b",
    r"\bhelm\b.*\b(install|upgrade|uninstall|rollback)\b",
    r"\bhelm\s+delete\b",
    r"\bargocd\s+app\s+(sync|delete|set|patch|rollback)\b",
]
REMINDER = ("방금 mutating 인프라 명령이 실행되었습니다. "
            "changes/에 변경 기록을 남기세요 — change 스킬 (/infra:change). 롤백 방법 필수.")


def find_harness_root(start):
    cur = Path(start).resolve()
    for p in [cur, *cur.parents]:
        if (p / "harness.yaml").is_file():
            return p
    return None


def reminder_enabled(root):
    # 간이 판독: harness.yaml 전체에서 change_reminder 값만 읽는다 (독립 실행형 유지)
    try:
        text = (root / "harness.yaml").read_text(encoding="utf-8")
    except OSError:
        return True
    m = re.search(r"^\s*change_reminder\s*:\s*(true|false)\b", text, re.MULTILINE)
    return m is None or m.group(1) == "true"


def main():
    try:
        data = json.load(sys.stdin)
        command = str(data.get("tool_input", {}).get("command", ""))
        cwd = data.get("cwd") or "."
        if "--dry-run" in command:
            return
        if not any(re.search(p, command) for p in MUTATING):
            return
        root = find_harness_root(cwd)
        if root is None or not reminder_enabled(root):
            return
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": REMINDER,
            }
        }, ensure_ascii=False))
    except Exception:
        pass  # 어떤 오류도 세션에 영향 주지 않는다


if __name__ == "__main__":
    main()
    sys.exit(0)
