import datetime
import subprocess
import sys
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import audit  # noqa: E402

OK = PLUGIN_ROOT / "tests" / "fixtures" / "harness-ok"
BAD = PLUGIN_ROOT / "tests" / "fixtures" / "harness-bad"
TODAY = datetime.date(2026, 7, 19)


class TestAuditOk(unittest.TestCase):
    def test_ok_harness_passes(self):
        failures, warnings = audit.run_audit(OK, TODAY)
        self.assertEqual(failures, [])


class TestAuditBad(unittest.TestCase):
    def setUp(self):
        self.failures, self.warnings = audit.run_audit(BAD, TODAY)
        self.joined = "\n".join(self.failures)
        self.warn_joined = "\n".join(self.warnings)

    def test_secret_pattern_detected(self):
        self.assertIn("AKIA", self.joined)
        self.assertIn("notes.md", self.joined)

    def test_invalid_policy_combo(self):
        self.assertIn("plaintext", self.joined)
        self.assertIn("shared-drive", self.joined)

    def test_broken_reference(self):
        self.assertIn("no-such-provider", self.joined)
        self.assertIn("no-such-key", self.joined)

    def test_id_mismatch_and_missing_field(self):
        self.assertIn("ghost", self.joined)   # id-파일명 불일치
        self.assertIn("runtime", self.joined)  # 필수 필드 누락

    def test_expiry_warning(self):
        self.assertIn("old-cert", self.warn_joined)


class TestAuditCli(unittest.TestCase):
    def test_exit_codes(self):
        script = str(PLUGIN_ROOT / "scripts" / "audit.py")
        ok = subprocess.run([sys.executable, script, "--root", str(OK), "--today", "2026-07-19"],
                            capture_output=True, text=True)
        bad = subprocess.run([sys.executable, script, "--root", str(BAD), "--today", "2026-07-19"],
                             capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        self.assertEqual(bad.returncode, 1, bad.stdout + bad.stderr)


if __name__ == "__main__":
    unittest.main()
