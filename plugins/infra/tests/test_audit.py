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


class TestAuditHardening(unittest.TestCase):
    def _root(self, files, harness="sharing: local\nsecrets_mode: encrypted\nenvironments: [prod]\npolicies:\n  mutating:\n    prod: confirm\nhooks:\n  change_reminder: true\n"):
        import tempfile
        d = tempfile.mkdtemp()
        root = Path(d)
        (root / "harness.yaml").write_text(harness, encoding="utf-8")
        (root / "secrets").mkdir()
        for rel, content in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                p.write_bytes(content)
            else:
                p.write_text(content, encoding="utf-8")
        return root

    def test_symlink_in_secrets_rejected_not_followed(self):
        root = self._root({})
        target = root.parent / "outside-secret.txt"
        target.write_text("AKIAIOSFODNN7EXAMPLE\n", encoding="utf-8")
        (root / "secrets" / "link.age").symlink_to(target)
        failures = []
        import audit
        audit.check_secret_policy(root, {"sharing": "local", "secrets_mode": "encrypted"}, failures)
        joined = "\n".join(failures)
        self.assertIn("link.age", joined)           # 심링크가 보고되고
        self.assertIn("심볼릭 링크", joined)          # 링크로 분류
        self.assertNotIn("AKIA", joined)             # 대상 내용은 절대 안 읽음

    def test_nested_encrypted_file_checked(self):
        # secrets/ 하위 디렉터리의 비암호문도 잡는다(재귀)
        root = self._root({"secrets/team/plain.txt": b"not encrypted at all\n"})
        failures = []
        import audit
        audit.check_secret_policy(root, {"sharing": "local", "secrets_mode": "encrypted"}, failures)
        self.assertTrue(any("plain.txt" in f and "암호문 형식이 아님" in f for f in failures))

    def test_strict_header_rejects_loose_substring(self):
        # 'sops'가 파일 중간에 있을 뿐 유효 암호문 아님 → 엄격 검사로 실패
        root = self._root({"secrets/fake.age": b"hello sops world not encrypted\n"})
        failures = []
        import audit
        audit.check_secret_policy(root, {"sharing": "local", "secrets_mode": "encrypted"}, failures)
        self.assertTrue(any("fake.age" in f for f in failures))

    def test_valid_age_and_sops_pass(self):
        root = self._root({
            "secrets/ok.age": b"age-encryption.org/v1\n-> X25519 abc\n--- def\n",
            "secrets/ok.sops.yaml": b"data: ENC[AES256_GCM,data:xx]\nsops:\n    mac: ENC[AES256_GCM,data:yy]\n",
        })
        failures = []
        import audit
        audit.check_secret_policy(root, {"sharing": "local", "secrets_mode": "encrypted"}, failures)
        self.assertEqual([f for f in failures if "ok.age" in f or "ok.sops.yaml" in f], [])

    def test_secrets_mode_none_forbids_payload(self):
        root = self._root({"secrets/leftover.age": b"age-encryption.org/v1\n"})
        failures = []
        import audit
        audit.check_secret_policy(root, {"sharing": "local", "secrets_mode": "none"}, failures)
        self.assertTrue(any("leftover.age" in f and "secrets_mode: none" in f for f in failures))

    def test_large_sops_file_with_tail_metadata_passes(self):
        # 실제 SOPS는 sops:/mac 메타데이터가 파일 끝에 온다. 4096B 초과도 통과해야 함
        filler = b"data: ENC[AES256_GCM,data:" + b"x" * 6000 + b"]\n"
        tail = b"sops:\n    mac: ENC[AES256_GCM,data:yy]\n    version: 3.7.3\n"
        root = self._root({"secrets/big.sops.yaml": filler + tail})
        failures = []
        import audit
        audit.check_secret_policy(root, {"sharing": "local", "secrets_mode": "encrypted"}, failures)
        self.assertEqual([f for f in failures if "big.sops.yaml" in f], [])

    def test_strict_header_message(self):
        root = self._root({"secrets/fake.age": b"hello sops world not encrypted\n"})
        failures = []
        import audit
        audit.check_secret_policy(root, {"sharing": "local", "secrets_mode": "encrypted"}, failures)
        self.assertTrue(any("fake.age" in f and "암호문 형식이 아님" in f for f in failures))

    def test_secret_scan_symlink_not_followed(self):
        root = self._root({}, harness="sharing: local\nsecrets_mode: none\nenvironments: [prod]\npolicies:\n  mutating:\n    prod: confirm\nhooks:\n  change_reminder: true\n")
        target = root.parent / "outside2.txt"
        target.write_text("AKIAIOSFODNN7EXAMPLE\n", encoding="utf-8")
        (root / "notes-link.md").symlink_to(target)
        failures = []
        import audit
        audit.check_secret_scan(root, failures)
        self.assertNotIn("AKIA", "\n".join(failures))

    def test_none_mode_symlink_not_followed(self):
        root = self._root({})
        target = root.parent / "outside3.txt"
        target.write_text("AKIAIOSFODNN7EXAMPLE\n", encoding="utf-8")
        (root / "secrets" / "l.age").symlink_to(target)
        failures = []
        import audit
        audit.check_secret_policy(root, {"sharing": "local", "secrets_mode": "none"}, failures)
        self.assertNotIn("AKIA", "\n".join(failures))

    def test_directory_symlink_in_secrets_not_recursed(self):
        root = self._root({})
        outside_dir = root.parent / "outside-dir"
        outside_dir.mkdir(exist_ok=True)  # 공유 임시 디렉터리 — 재실행 시에도 충돌 없이 멱등
        (outside_dir / "leak.txt").write_text("AKIAIOSFODNN7EXAMPLE\n", encoding="utf-8")
        (root / "secrets" / "dlink").symlink_to(outside_dir, target_is_directory=True)
        failures = []
        import audit
        audit.check_secret_policy(root, {"sharing": "local", "secrets_mode": "encrypted"}, failures)
        self.assertNotIn("AKIA", "\n".join(failures))


if __name__ == "__main__":
    unittest.main()
