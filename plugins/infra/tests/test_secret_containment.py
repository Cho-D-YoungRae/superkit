"""시크릿 값이 스크립트 출력으로 새지 않음을 카나리로 강제한다 (원칙 1, 검토 P0-4).

왜 이 테스트가 필요한가: `.claude/settings.json`의 deny 규칙은 Read 도구와 클로드가
인식하는 파일 명령(`cat`·`head`·`tail`·`sed`)에만 걸리고, **파이썬 스크립트처럼 스스로
파일을 여는 임의 서브프로세스에는 걸리지 않는다**(공식 문서 Warning). 이 플러그인의
`scripts/*.py`가 바로 거기 해당한다 — `audit`이 `secrets/`를 재귀 스캔할 수 있는 이유이자,
동시에 스크립트가 값을 한 줄만 출력해도 방어선이 무력화되는 이유다.

그 규율을 코드 리뷰 관행에만 맡기지 않고 여기서 기계적으로 고정한다. 카나리를 심은
하네스에 스크립트를 돌리고, 그 값이 stdout·stderr 어디에도 나타나지 않아야 한다.
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
OK = PLUGIN_ROOT / "tests" / "fixtures" / "harness-ok"

# 합성 카나리 — 실제 자격증명이 아니다. 스크립트 출력에 이 문자열이 보이면 유출이다.
CANARY = "CANARY-SECRET-VALUE-DO-NOT-PRINT-9f3a7c2e"
# audit의 시크릿 패턴에 걸리는 형태로도 심어, "검출은 하되 값은 안 찍는지"까지 본다.
CANARY_AKIA = "AKIAIOSFODNN7EXAMPLE"


class SecretContainmentTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = Path(self.tmp) / "h"
        shutil.copytree(OK, self.root)
        secrets = self.root / "secrets"
        secrets.mkdir(exist_ok=True)
        # secrets/ 안 — 여러 형태로 심는다
        (secrets / "canary-token.txt").write_text(CANARY + "\n", encoding="utf-8")
        (secrets / "canary-db.env").write_text(
            f"user=postgres\npassword={CANARY}\n", encoding="utf-8")
        (secrets / "canary-key").write_text(
            f"-----BEGIN OPENSSH PRIVATE KEY-----\n{CANARY}\n"
            "-----END OPENSSH PRIVATE KEY-----\n", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, script, *args):
        proc = subprocess.run(
            [sys.executable, str(PLUGIN_ROOT / "scripts" / script),
             "--root", str(self.root), *args],
            capture_output=True, text=True, timeout=60,
        )
        return (proc.stdout or "") + (proc.stderr or "")

    def assertNoCanary(self, output, where):
        self.assertNotIn(CANARY, output, f"{where} 출력에 시크릿 값이 실렸다")

    def test_audit_does_not_print_secret_values(self):
        self.assertNoCanary(self._run("audit.py", "--today", "2026-07-19"), "audit")

    def test_audit_debug_mode_does_not_print_secret_values(self):
        """--debug는 트레이스백을 띄우지만 그 경로로도 값이 새면 안 된다."""
        self.assertNoCanary(
            self._run("audit.py", "--today", "2026-07-19", "--debug"), "audit --debug")

    def test_audit_detects_planted_pattern_without_echoing_it(self):
        """secrets/ 밖 오염은 검출하되 매치된 값 자체는 출력하지 않는다."""
        (self.root / "leak-notes.md").write_text(
            f"aws_access_key_id = {CANARY_AKIA}\n", encoding="utf-8")
        out = self._run("audit.py", "--today", "2026-07-19")
        self.assertIn("[시크릿]", out, f"오염을 검출하지 못했다:\n{out}")
        self.assertNotIn(CANARY_AKIA, out, "검출은 했으나 매치 값을 그대로 출력했다")

    def test_sync_does_not_print_secret_values(self):
        self.assertNoCanary(self._run("sync_snapshot.py"), "sync_snapshot")

    def test_encrypted_policy_path_does_not_print_file_contents(self):
        """secrets_mode: encrypted에서 평문 파일을 만나도 내용은 출력하지 않는다."""
        hy = self.root / "harness.yaml"
        hy.write_text(
            hy.read_text(encoding="utf-8")
              .replace("secrets_mode: plaintext", "secrets_mode: encrypted"),
            encoding="utf-8")
        out = self._run("audit.py", "--today", "2026-07-19")
        self.assertIn("[정책]", out, f"암호문 형식 위반을 검출하지 못했다:\n{out}")
        self.assertNoCanary(out, "audit(encrypted 위반 경로)")

    def test_hook_does_not_print_secret_values(self):
        """PostToolUse hook의 additionalContext에도 값이 실리면 안 된다."""
        payload = (
            '{"cwd": "%s", "tool_name": "Bash", '
            '"tool_input": {"command": "kubectl --context c apply -f x.yaml"}, '
            '"tool_response": {"stdout": "ok"}}' % self.root
        )
        proc = subprocess.run(
            [sys.executable, str(PLUGIN_ROOT / "hooks" / "scripts" / "change_reminder.py")],
            input=payload, capture_output=True, text=True, timeout=30,
        )
        self.assertNoCanary((proc.stdout or "") + (proc.stderr or ""), "change_reminder hook")


if __name__ == "__main__":
    unittest.main()
