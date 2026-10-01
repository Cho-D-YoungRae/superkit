"""시크릿 값이 스크립트 출력으로 새지 않음을 카나리로 강제한다 (원칙 1, 검토 P0-4).

왜 이 테스트가 필요한가: `.claude/settings.json`의 deny 규칙은 Read 도구와 클로드가
인식하는 파일 명령(`cat`·`head`·`tail`·`sed`)에만 걸리고, **파이썬 스크립트처럼 스스로
파일을 여는 임의 서브프로세스에는 걸리지 않는다**(공식 문서 Warning). 이 플러그인의
`scripts/*.py`가 바로 거기 해당한다 — `audit`이 `secrets/`를 재귀 스캔할 수 있는 이유이자,
동시에 스크립트가 값을 한 줄만 출력해도 방어선이 무력화되는 이유다.

그 규율을 코드 리뷰 관행에만 맡기지 않고 여기서 기계적으로 고정한다. 카나리를 심은
하네스에 스크립트를 돌리고, 그 값이 stdout·stderr 어디에도 나타나지 않아야 한다.
"""
import datetime
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import audit  # noqa: E402

OK = PLUGIN_ROOT / "tests" / "fixtures" / "harness-ok"
TODAY = datetime.date(2026, 7, 19)

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

    def test_internal_error_drops_message_without_debug_but_debug_reraises_it(self):
        """`_run_check`의 "메시지는 버리고 타입만" 규율을 두 모드 대조로 증명한다.

        이전 테스트는 예외가 나지 않는 정상 하네스에 `--debug`만 붙여 돌렸다 —
        재raise 경로에 한 번도 들어가지 않아서, `_run_check`가 debug에서 재raise하지
        않도록 바꿔도 그대로 통과하는 공허한 테스트였다. 여기서는 검사 하나가 카나리를
        담은 예외를 던지게 강제한다.

        `--debug`는 유출 규율을 **의도적으로 끄는 사용자용 모드**이므로, 올바른 단언은
        "어느 모드에서도 카나리가 없어야 한다"가 아니라 **기본 모드에는 없고 `--debug`
        에는 있다**는 대조다.
        """
        with mock.patch.object(audit, "check_secret_scan",
                               side_effect=RuntimeError(CANARY)):
            failures, _ = audit.run_audit(self.root, TODAY)
        joined = "\n".join(failures)
        self.assertIn("[내부오류]", joined, joined)
        self.assertIn("RuntimeError", joined, joined)   # 타입만 남는다
        self.assertNoCanary(joined, "audit(기본 모드 내부오류)")

        with mock.patch.object(audit, "check_secret_scan",
                               side_effect=RuntimeError(CANARY)):
            with self.assertRaises(RuntimeError) as ctx:
                audit.run_audit(self.root, TODAY, debug=True)
        self.assertIn(CANARY, str(ctx.exception),
                      "--debug가 원본 예외를 그대로 올리지 않는다 — 대조가 성립하지 않는다")

    def test_audit_does_not_print_broken_frontmatter_source_line(self):
        """파싱에 실패한 엔티티의 **원문 줄**이 리포트에 실리면 안 된다(원칙 1).

        `[시크릿]` 경로는 패턴 라벨만 찍는데 `[스키마]` 파싱 실패 경로가 문제된 줄
        전체를 인쇄하던 결함의 회귀 방지다. 이 경로는 `SECRET_PATTERNS`의 제약을 전혀
        받지 않으므로(패턴에 없는 내부 DB 비밀번호 등도 그대로 샌다) 여기 심는 카나리는
        일부러 어떤 시크릿 패턴에도 걸리지 않는 형태로 둔다.
        """
        (self.root / "inventory" / "broken.md").write_text(
            f"---\n  token: {CANARY}\n  id: broken\n---\n본문\n", encoding="utf-8")
        out = self._run("audit.py", "--today", "2026-07-19")
        self.assertIn("[스키마]", out, f"파싱 실패를 보고하지 않았다:\n{out}")
        self.assertIn("선행 공백", out, f"원인을 지목하지 않았다:\n{out}")
        self.assertNoCanary(out, "audit(frontmatter 파싱 실패 경로)")

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
