#!/usr/bin/env python3
"""PostToolUse(Bash) hook — mutating 인프라 명령 실행 후 변경 기록 리마인드.

독립 실행형(다른 모듈 import 없음). 어떤 경우에도 exit 0 (비차단 — 스펙 D6).
"""
import json
import re
import sys
from pathlib import Path

MUTATING = [
    r"(?<!\S)terraform(?!\S).*(?<!\S)(apply|destroy|import|taint|untaint)(?!\S)",
    r"(?<!\S)terraform(?!\S).*(?<!\S)state(?!\S)\s+(mv|rm|push)(?!\S)",
    r"(?<!\S)kubectl(?!\S).*(?<!\S)(apply|create|delete|patch|replace|scale|edit|label|annotate|cordon|uncordon|drain|taint)(?!\S)",
    r"(?<!\S)kubectl(?!\S).*(?<!\S)rollout(?!\S)\s+(restart|undo|pause|resume)(?!\S)",
    r"(?<!\S)helm(?!\S).*(?<!\S)(install|upgrade|uninstall|rollback|delete)(?!\S)",
    r"(?<!\S)argocd(?!\S).*(?<!\S)app(?!\S)\s+(sync|delete|set|patch|rollback)(?!\S)",
    # --- 서버 계열 (C5) ---
    # 경계가 위 6개와 다르다. `(?<!\S)`는 앞 문자가 공백이어야 하는데,
    # `ssh host 'systemctl restart nginx'`에서는 앞 문자가 따옴표라 매치되지 않는다.
    # ssh 경유 작업을 덮는 것이 이 확장의 핵심이므로 단어 문자·점·하이픈만 배제해
    # 따옴표와 경로 구분자(`/usr/bin/systemctl`)를 허용한다. 하이픈을 배제한 덕분에
    # `--installed` 안의 `install`은 여전히 걸리지 않는다.
    r"(?<![\w.-])systemctl(?![\w.-]).*(?<![\w.-])(restart|stop|start|enable|disable|mask|unmask|daemon-reload)(?![\w.-])",
    r"(?<![\w.-])(apt|apt-get|yum|dnf|apk)(?![\w.-]).*(?<![\w.-])(install|remove|purge|upgrade|autoremove)(?![\w.-])",
    r"(?<![\w.-])docker(?![\w.-]).*(?<![\w.-])(run|rm|stop|start|restart|kill|exec)(?![\w.-])",
    r"(?<![\w.-])docker(?![\w.-]).*(?<![\w.-])compose(?![\w.-])\s+(up|down|restart)(?![\w.-])",
    r"(?<![\w.-])aws(?![\w.-]).*(?<![\w.-])(create|delete|update|put|modify|terminate|reboot)-[a-z-]+(?![\w.-])",
]

# DB 클라이언트는 "psql/mysql이 있고 + SQL 쓰기 키워드가 있을 때"만 매치한다.
# 하나의 정규식으로 대소문자를 섞어 처리하려면 인라인 플래그가 필요해 가독성이
# 나빠지므로 두 갈래로 나눈다. 경계는 위 서버 계열과 같은 이유로 완화한다.
DB_CLIENT_RE = re.compile(r"(?<![\w.-])(psql|mysql|mariadb)(?![\w.-])")
DB_WRITE_RE = re.compile(
    r"\b(INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|GRANT|REVOKE|TRUNCATE)\b", re.IGNORECASE)

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


def is_mutating(command):
    """이 명령이 변경 기록 리마인드 대상인가.

    PostToolUse는 어떤 경우에도 차단하지 않으므로(D6) 오탐 비용은 알림 한 줄이고,
    미탐(기록 누락)이 더 비싸다. 그래도 read-only 명령까지 매번 울리면 알림이
    무시되므로 제외 어휘는 지킨다.
    """
    if "--dry-run" in command:
        return False
    if DB_CLIENT_RE.search(command) and DB_WRITE_RE.search(command):
        return True
    return any(re.search(p, command) for p in MUTATING)


def main():
    try:
        data = json.load(sys.stdin)
        command = str(data.get("tool_input", {}).get("command", ""))
        cwd = data.get("cwd") or "."
        if not is_mutating(command):
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
