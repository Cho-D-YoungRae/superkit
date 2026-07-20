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


class TestEncryptedSecretPolicy(unittest.TestCase):
    def _run(self, files):
        import tempfile
        failures = []
        with tempfile.TemporaryDirectory() as d:
            sdir = Path(d) / "secrets"
            sdir.mkdir()
            for name, content in files.items():
                (sdir / name).write_bytes(content)
            audit.check_secret_policy(Path(d), {"sharing": "git", "secrets_mode": "encrypted"}, failures)
        return failures

    def test_plaintext_file_flagged(self):
        failures = self._run({"leak.txt": b"this is plaintext, not encrypted\n"})
        joined = "\n".join(failures)
        self.assertIn("leak.txt", joined)
        self.assertIn("암호문 형식이 아님", joined)
        # 파일 내용(값)이 리포트에 새어나오지 않는지 확인
        self.assertNotIn("plaintext, not encrypted", joined)

    def test_age_headered_file_passes(self):
        failures = self._run({"ok.age": b"age-encryption.org/v1\n-> X25519 ...\n"})
        self.assertEqual(failures, [])

    def test_gitkeep_ignored(self):
        failures = self._run({".gitkeep": b""})
        self.assertEqual(failures, [])


class TestAuditRobustness(unittest.TestCase):
    def test_missing_id_reported_not_crash(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "inventory").mkdir()
            (root / "inventory" / "noid.md").write_text(
                "---\ntype: server\nenv: prod\nprovider: p\nruntime: ec2\n"
                "purpose: x\naccess: y\nmanaged_by: manual\n---\n", encoding="utf-8")
            failures = []
            audit.check_schema_and_refs(root, failures)  # 크래시하면 안 됨
            self.assertTrue(any("누락 — id" in f for f in failures))

    def test_invalid_expiry_date_no_crash(self):
        import datetime
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "access").mkdir()
            (root / "access" / "keys.md").write_text(
                "# keys\n\n| 이름 | 종류 | fingerprint | 위치 참조 | 소유자 | 생성일 | 만료/로테이션 |\n"
                "|--|--|--|--|--|--|--|\n"
                "| badcert | tls-cert | - | secrets/x | o | 2025-01-01 | 2026-13-45 |\n",
                encoding="utf-8")
            warnings = []
            audit.check_expiry(root, datetime.date(2026, 7, 20), warnings)  # 크래시하면 안 됨
            self.assertTrue(any("badcert" in w for w in warnings))


if __name__ == "__main__":
    unittest.main()
