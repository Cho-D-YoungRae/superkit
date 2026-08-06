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
        joined = "\n".join(failures)
        self.assertNotIn("AKIA", joined)          # 추종 안 함(리크 없음)
        self.assertIn("dlink", joined)            # 심링크 디렉터리도 정책 위반으로 보고
        self.assertIn("심볼릭 링크", joined)


class TestAuditStructure(unittest.TestCase):
    def test_conflict_copy_filename_flagged(self):
        import tempfile, datetime
        d = tempfile.mkdtemp(); root = Path(d)
        (root / "harness.yaml").write_text("sharing: shared-drive\nsecrets_mode: none\nenvironments: [prod]\npolicies:\n  mutating:\n    prod: confirm\nhooks:\n  change_reminder: true\n", encoding="utf-8")
        (root / "inventory").mkdir()
        (root / "inventory" / "prod-db-01 (1).md").write_text("---\nid: prod-db-01\ntype: server\nenv: prod\nprovider: p\nruntime: ec2\npurpose: x\naccess: y\nmanaged_by: manual\n---\n", encoding="utf-8")
        import audit
        failures, _ = audit.run_audit(root, datetime.date(2026,7,22))
        self.assertTrue(any("conflict" in f.lower() or "충돌 사본" in f for f in failures))

    def test_duplicate_id_flagged(self):
        import tempfile, datetime
        d = tempfile.mkdtemp(); root = Path(d)
        (root / "harness.yaml").write_text("sharing: local\nsecrets_mode: none\nenvironments: [prod]\npolicies:\n  mutating:\n    prod: confirm\nhooks:\n  change_reminder: true\n", encoding="utf-8")
        (root / "inventory").mkdir(); (root / "providers").mkdir()
        body = "---\nid: dup\ntype: server\nenv: prod\nprovider: p\nruntime: ec2\npurpose: x\naccess: y\nmanaged_by: manual\n---\n"
        (root / "inventory" / "dup.md").write_text(body, encoding="utf-8")
        (root / "providers" / "dup.md").write_text("---\nid: dup\ntype: provider\nkind: aws\n---\n", encoding="utf-8")
        import audit
        failures, _ = audit.run_audit(root, datetime.date(2026,7,22))
        self.assertTrue(any("중복" in f and "dup" in f for f in failures))


class TestAuditStagedFlag(unittest.TestCase):
    def test_staged_non_git_falls_back(self):
        import subprocess, sys, tempfile
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "harness.yaml").write_text(
                "sharing: local\nsecrets_mode: none\nenvironments: [prod]\npolicies:\n  mutating:\n    prod: confirm\nhooks:\n  change_reminder: true\n",
                encoding="utf-8")
            script = str(PLUGIN_ROOT / "scripts" / "audit.py")
            r = subprocess.run([sys.executable, script, "--root", str(root), "--staged"],
                               capture_output=True, text=True)
        self.assertIn("git 저장소가 아니라", r.stdout)   # 폴백 분기 실제 진입
        self.assertIn(r.returncode, (0, 1))
        self.assertNotIn("Traceback", r.stderr)

    def test_staged_parses_zsep_non_ascii(self):
        # -z NUL 출력의 비-ASCII 파일명이 따옴표/이스케이프 없이 파싱돼 스캔 대상에 포함되는가
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory() as d:
            # resolve()로 고정 — macOS에서 tempdir가 /var -> /private/var 심링크라
            # 미resolve 경로를 섞어 쓰면 이 테스트 자체의 mock 왕복에서 relative_to가
            # 어긋난다(운영 코드 경로가 아니라 테스트 결정론화를 위한 조정).
            root = Path(d).resolve()
            (root / "runbooks").mkdir()
            f = root / "runbooks" / "한글-런북.md"
            f.write_text("AKIAIOSFODNN7EXAMPLE\n", encoding="utf-8")

            class R:
                def __init__(self, rc, out=b"", outs=""):
                    self.returncode = rc; self.stdout = out if out else outs

            def fake_run(cmd, **kw):
                if "rev-parse" in cmd:
                    return R(0, outs=str(root) + "\n")     # git 저장소로 인식
                if "diff" in cmd:
                    return R(0, out=("runbooks/한글-런북.md".encode("utf-8") + b"\0"))  # -z 출력
                return R(0)
            import audit
            with mock.patch.object(audit.subprocess, "run", side_effect=fake_run):
                staged = audit._staged_files_in_harness(root)
            self.assertTrue(any(p.name == "한글-런북.md" for p in staged))
            # 그리고 그 파일을 스캔하면 시크릿을 잡는다(미탐 아님)
            failures = []
            audit.check_staged_secret_scan(root, staged, failures)
            self.assertTrue(any("한글-런북.md" in f for f in failures))
            # 값(매치된 전체 키)은 미출력 — 패턴 라벨 "AWS Access Key ID(AKIA...)" 자체는
            # 정적 설명 문자열이라 "AKIA"를 포함하는 게 정상(test_secret_pattern_detected와 동일 전제).
            # 그래서 부분 문자열 "AKIA"가 아니라 실제 매치된 전체 값이 없는지로 검증한다.
            self.assertNotIn("AKIAIOSFODNN7EXAMPLE", "\n".join(failures))

    def test_staged_symlinked_root_no_crash(self):
        # check_staged_secret_scan을 심링크 root + resolve된 staged 경로로 직접 호출한다.
        # root를 resolve하지 않으면 fp.relative_to(root)가 ValueError로 크래시한다(D13 회귀 가드).
        import tempfile
        import os
        with tempfile.TemporaryDirectory() as d:
            real = (Path(d) / "real").resolve()
            (real / "inventory").mkdir(parents=True)
            leak = real / "inventory" / "leak.md"
            leak.write_text("AKIAIOSFODNN7EXAMPLE\n", encoding="utf-8")
            link = Path(d) / "link"
            os.symlink(real, link, target_is_directory=True)   # 심링크 root
            failures = []
            import audit
            # staged는 _staged_files_in_harness가 돌려주는 형태(=이미 resolve된 절대경로)
            audit.check_staged_secret_scan(link, [leak.resolve()], failures)
        joined = "\n".join(failures)
        self.assertTrue(any("leak.md" in f for f in failures))   # 크래시 없이 스캔·검출
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", joined)         # 매치 값은 미출력


class TestCredentialSchema(unittest.TestCase):
    def test_ok_keys_pass(self):
        import datetime
        failures, _ = audit.run_audit(OK, datetime.date(2026, 7, 22))
        self.assertEqual([f for f in failures if "[키]" in f], [])

    def test_bad_kind_flagged(self):
        import datetime
        failures, _ = audit.run_audit(BAD, datetime.date(2026, 7, 22))
        self.assertTrue(any("superkey" in f for f in failures))

    def test_expiry_still_detected_new_schema(self):
        import datetime
        _, warnings = audit.run_audit(BAD, datetime.date(2026, 7, 22))
        self.assertTrue(any("old-cert" in w for w in warnings))


class TestRecipients(unittest.TestCase):
    def _root(self, harness):
        import tempfile
        d = tempfile.mkdtemp(); root = Path(d)
        (root / "harness.yaml").write_text(harness, encoding="utf-8")
        return root

    def test_encrypted_requires_recovery_recipient(self):
        import datetime
        h = "sharing: git\nsecrets_mode: encrypted\nsecrets_format: sops-age\nsecrets_recipients:\n  alice: age1aaa\nenvironments: [prod]\npolicies:\n  mutating:\n    prod: confirm\nhooks:\n  change_reminder: true\n"
        failures, _ = audit.run_audit(self._root(h), datetime.date(2026,7,22))
        self.assertTrue(any("recovery" in f for f in failures))

    def test_encrypted_with_recovery_passes_recipient_check(self):
        import datetime
        h = "sharing: git\nsecrets_mode: encrypted\nsecrets_format: sops-age\nsecrets_recipients:\n  alice: age1aaa\n  recovery: age1rec\nenvironments: [prod]\npolicies:\n  mutating:\n    prod: confirm\nhooks:\n  change_reminder: true\n"
        failures, _ = audit.run_audit(self._root(h), datetime.date(2026,7,22))
        self.assertEqual([f for f in failures if "recovery" in f or "recipient" in f], [])


class TestListValuedRefFields(unittest.TestCase):
    """참조 필드에 리스트가 와도 크래시하지 않고 스키마 오류로 보고한다.

    회귀 방지 대상: `runs_on: [a, b]` 하나가 unhashable TypeError를 내며 audit
    전체를 죽여서 시크릿 스캔까지 통째로 건너뛰던 문제(검토 P0-1). 크래시하면
    `실패 0건`조차 못 내므로 사용자는 오염을 발견할 기회를 잃는다.
    """

    def _harness_with(self, entity_rel, body):
        import shutil
        import tempfile
        d = tempfile.mkdtemp()
        root = Path(d) / "h"
        shutil.copytree(OK, root)
        target = root / entity_rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        return root

    def test_list_runs_on_reports_schema_error_not_crash(self):
        body = ("---\nid: multi\ntype: component\ncategory: monitoring\n"
                "runs_on: [prod-k8s, prod-db-01]\nnamespace: monitoring\n"
                "endpoint: https://x.invalid\ninstalled_by: helm://x/y@1\n"
                'access: "API"\n---\n본문\n')
        root = self._harness_with("inventory/components/multi.md", body)
        failures, _ = audit.run_audit(root, TODAY)   # 크래시하면 여기서 터진다
        self.assertTrue(any("runs_on" in f and "단일 id" in f for f in failures), failures)

    def test_list_provider_reports_schema_error_not_crash(self):
        body = ("---\nid: multi-srv\ntype: server\nenv: prod\n"
                "provider: [aws-main, onprem-idc]\nruntime: vm\npurpose: 검증용\n"
                'access: "ssh"\nmanaged_by: manual\ndepends_on: []\n---\n본문\n')
        root = self._harness_with("inventory/multi-srv.md", body)
        failures, _ = audit.run_audit(root, TODAY)
        self.assertTrue(any("provider" in f and "단일 id" in f for f in failures), failures)

    def test_secret_scan_still_runs_when_a_ref_field_is_a_list(self):
        """핵심 회귀: 리스트 필드가 있어도 시크릿 스캔이 수행되어야 한다."""
        body = ("---\nid: multi\ntype: component\ncategory: monitoring\n"
                "runs_on: [prod-k8s, prod-db-01]\nnamespace: monitoring\n"
                "endpoint: https://x.invalid\ninstalled_by: helm://x/y@1\n"
                'access: "API"\n---\n본문\n')
        root = self._harness_with("inventory/components/multi.md", body)
        (root / "notes-leak.md").write_text(
            "aws_access_key_id = AKIAIOSFODNN7EXAMPLE\n", encoding="utf-8")
        failures, _ = audit.run_audit(root, TODAY)
        self.assertTrue(any("[시크릿]" in f for f in failures),
                        f"리스트 필드 때문에 시크릿 스캔이 건너뛰어졌다: {failures}")

    def test_scalar_depends_on_is_not_iterated_per_character(self):
        """`depends_on: prod-k8s`(스칼라)를 글자 단위로 순회하면 안 된다."""
        body = ("---\nid: solo\ntype: server\nenv: prod\nprovider: aws-main\n"
                "runtime: vm\npurpose: 검증용\n"
                'access: "ssh"\nmanaged_by: manual\ndepends_on: prod-k8s\n---\n본문\n')
        root = self._harness_with("inventory/solo.md", body)
        failures, _ = audit.run_audit(root, TODAY)
        bogus = [f for f in failures if "depends_on 'p'" in f or "depends_on 'r'" in f]
        self.assertEqual(bogus, [], f"스칼라가 글자 단위로 쪼개졌다: {failures}")


class TestSecretScanFileIsolation(unittest.TestCase):
    """읽을 수 없는 파일 하나가 시크릿 스캔 **전체**를 중단시키면 안 된다.

    `check_secret_scan`은 os.walk를 정렬 순서로 도는데, 앞쪽 파일의 read_bytes()가
    예외를 올리면 `_run_check`가 이 검사를 통째로 `[내부오류]`로 끝낸다 — 그 뒤 파일의
    실제 오염은 검출조차 되지 않는다. 여기서 단언하는 것은 "크래시하지 않는다"가 아니라
    **읽지 못한 파일 뒤의 오염이 여전히 검출된다**는 것이다.
    """

    def setUp(self):
        import os
        import shutil
        import tempfile
        self.tmp = tempfile.mkdtemp()
        self.root = Path(self.tmp) / "h"
        shutil.copytree(OK, self.root)
        # 정렬 순서상 오염 파일보다 **앞**에 오도록 이름을 정한다
        self.unreadable = self.root / "aaa-unreadable.md"
        self.unreadable.write_text("표시용 더미 내용\n", encoding="utf-8")
        os.chmod(self.unreadable, 0)
        if os.access(self.unreadable, os.R_OK):
            self.skipTest("이 환경에서는 chmod 0으로 읽기를 막을 수 없다(root 등)")
        (self.root / "zzz-leak.md").write_text(
            "aws_access_key_id = AKIAIOSFODNN7EXAMPLE\n", encoding="utf-8")

    def tearDown(self):
        import os
        import shutil
        try:
            os.chmod(self.unreadable, 0o644)
        except OSError:
            pass
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_unreadable_file_does_not_hide_later_contamination(self):
        failures, _ = audit.run_audit(self.root, TODAY)
        joined = "\n".join(failures)
        self.assertTrue(
            any("zzz-leak.md" in f and "[시크릿]" in f for f in failures),
            f"읽을 수 없는 파일 때문에 뒤 파일의 오염을 놓쳤다: {failures}")
        self.assertNotIn("[내부오류]", joined,
                         f"검사 전체가 중단됐다(파일 단위 격리 실패): {failures}")

    def test_unreadable_file_is_reported_as_not_scanned(self):
        """읽지 못한 파일은 조용히 넘기지 않고 **경로만** 보고한다(내용 없음)."""
        failures, _ = audit.run_audit(self.root, TODAY)
        self.assertTrue(
            any("aaa-unreadable.md" in f and "읽을 수 없어" in f for f in failures),
            f"읽지 못한 파일이 보고되지 않았다: {failures}")


class TestDenyRuleProtection(unittest.TestCase):
    """secrets/ 차단 설정의 드리프트와 하위 디렉터리 구멍을 잡는다(검토 P0-3).

    `.claude/settings.json`은 cwd의 `.claude/`에서만 부모 폴백 없이 로드되는데
    하네스 발견은 상향 탐색이라(D1), 하위 디렉터리 세션은 스킬만 동작하고 차단은
    없는 상태가 된다. `.claude/settings.local.json`이 git 저장소 루트에서 로드되어
    그 구멍을 메우므로, git 하네스라면 두 파일이 모두 있어야 한다.
    """

    DENY = {"permissions": {"deny": ["Read(/secrets/**)", "Read(./secrets/**)"]}}

    def _harness(self, secrets_mode="plaintext", settings=None, local=None, git=False):
        import json as _json
        import tempfile
        root = Path(tempfile.mkdtemp())
        (root / "harness.yaml").write_text(
            f"sharing: local\nsecrets_mode: {secrets_mode}\nenvironments: [prod]\n"
            "policies:\n  mutating:\n    prod: confirm\nhooks:\n  change_reminder: true\n",
            encoding="utf-8")
        if settings is not None or local is not None:
            (root / ".claude").mkdir()
        if settings is not None:
            (root / ".claude" / "settings.json").write_text(_json.dumps(settings), encoding="utf-8")
        if local is not None:
            (root / ".claude" / "settings.local.json").write_text(_json.dumps(local), encoding="utf-8")
        if git:
            (root / ".git").mkdir()
        return root

    def _run(self, root):
        failures, warnings = [], []
        cfg = __import__("harness_lib").load_harness_yaml(root / "harness.yaml")
        audit.check_deny_rules(root, cfg, failures, warnings)
        return failures, warnings

    def test_missing_settings_is_failure_when_secrets_are_local(self):
        failures, _ = self._run(self._harness(secrets_mode="plaintext"))
        self.assertTrue(any("settings.json" in f for f in failures), failures)

    def test_missing_settings_is_only_warning_when_mode_none(self):
        failures, warnings = self._run(self._harness(secrets_mode="none"))
        self.assertEqual(failures, [])
        self.assertTrue(any("settings.json" in w for w in warnings), warnings)

    def test_incomplete_deny_list_is_reported(self):
        partial = {"permissions": {"deny": ["Read(/secrets/**)"]}}   # ./ 형태 누락
        failures, _ = self._run(self._harness(settings=partial))
        self.assertTrue(any("Read(./secrets/**)" in f for f in failures), failures)

    def test_git_harness_without_local_settings_is_reported(self):
        failures, _ = self._run(self._harness(settings=self.DENY, git=True))
        self.assertTrue(any("settings.local.json" in f for f in failures), failures)
        self.assertTrue(any("하위 디렉터리" in f for f in failures), failures)

    def test_git_harness_with_both_files_passes(self):
        failures, _ = self._run(
            self._harness(settings=self.DENY, local=self.DENY, git=True))
        self.assertEqual(failures, [])

    def test_non_git_harness_warns_to_open_at_root(self):
        failures, warnings = self._run(self._harness(settings=self.DENY))
        self.assertEqual(failures, [])
        self.assertTrue(any("하네스 루트에서 여세요" in w for w in warnings), warnings)

    def test_malformed_settings_json_does_not_crash(self):
        import tempfile
        root = Path(tempfile.mkdtemp())
        (root / "harness.yaml").write_text(
            "sharing: local\nsecrets_mode: plaintext\nenvironments: [prod]\n"
            "policies:\n  mutating:\n    prod: confirm\nhooks:\n  change_reminder: true\n",
            encoding="utf-8")
        (root / ".claude").mkdir()
        (root / ".claude" / "settings.json").write_text("{ not json", encoding="utf-8")
        failures, _ = self._run(root)
        self.assertTrue(any("settings.json" in f for f in failures), failures)


class TestCheckIsolation(unittest.TestCase):
    """한 검사가 죽어도 나머지 검사는 계속 수행되어야 한다(검토 P0-1)."""

    def test_failing_check_does_not_block_others(self):
        def boom():
            raise RuntimeError("의도적 실패")

        failures = []
        audit._run_check("테스트", boom, failures)
        self.assertTrue(any("[내부오류]" in f for f in failures), failures)
        self.assertTrue(any("RuntimeError" in f for f in failures), failures)

    def test_isolated_error_does_not_leak_exception_message(self):
        """예외 메시지에 파일 내용이 실릴 수 있으므로 타입만 보고한다(원칙 1)."""
        def boom():
            raise ValueError("CANARY-SHOULD-NOT-APPEAR-IN-REPORT")

        failures = []
        audit._run_check("테스트", boom, failures)
        self.assertNotIn("CANARY-SHOULD-NOT-APPEAR-IN-REPORT", "\n".join(failures))

    def test_debug_reraises(self):
        def boom():
            raise RuntimeError("의도적 실패")

        with self.assertRaises(RuntimeError):
            audit._run_check("테스트", boom, [], debug=True)


class TestSecretsFormat(unittest.TestCase):
    """스펙이 정의한 secrets_format이 실제로 검증되어야 한다 (검토 P2-3)."""

    BASE = ("sharing: git\nsecrets_mode: {mode}\n{fmt}"
            "secrets_recipients:\n  alice: age1aaa\n  recovery: age1rec\n"
            "environments: [prod]\npolicies:\n  mutating:\n    prod: confirm\n"
            "hooks:\n  change_reminder: true\n")

    def _run(self, mode, fmt_line):
        import tempfile
        root = Path(tempfile.mkdtemp())
        (root / "harness.yaml").write_text(
            self.BASE.format(mode=mode, fmt=fmt_line), encoding="utf-8")
        return audit.run_audit(root, TODAY)

    def test_unknown_format_fails(self):
        failures, _ = self._run("encrypted", "secrets_format: pgp\n")
        self.assertTrue(any("secrets_format" in f for f in failures), failures)

    def test_valid_format_passes(self):
        failures, _ = self._run("encrypted", "secrets_format: sops-age\n")
        self.assertEqual([f for f in failures if "secrets_format" in f], [])

    def test_missing_format_on_encrypted_warns(self):
        failures, warnings = self._run("encrypted", "")
        self.assertEqual([f for f in failures if "secrets_format" in f], [])
        self.assertTrue(any("secrets_format" in w for w in warnings), warnings)

    def test_format_on_non_encrypted_warns(self):
        failures, warnings = self._run("none", "secrets_format: sops-age\n")
        self.assertEqual([f for f in failures if "secrets_format" in f], [])
        self.assertTrue(any("secrets_format" in w for w in warnings), warnings)


if __name__ == "__main__":
    unittest.main()
