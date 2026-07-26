import json
import sys
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import sync_snapshot  # noqa: E402

OK = PLUGIN_ROOT / "tests" / "fixtures" / "harness-ok"
MOCK = PLUGIN_ROOT / "tests" / "fixtures" / "mock-actual.json"


class TestParseInstalledBy(unittest.TestCase):
    def test_helm(self):
        self.assertEqual(sync_snapshot.parse_installed_by("helm://vm/victoria-metrics-single@0.x"),
                         ("helm", "vm/victoria-metrics-single", "0.x"))

    def test_non_helm(self):
        self.assertEqual(sync_snapshot.parse_installed_by("apt"), ("apt", "", None))


class TestCollectCommands(unittest.TestCase):
    def test_context_profile_explicit(self):
        cmds = sync_snapshot.build_collect_commands(OK)
        flat = [" ".join(c["cmd"]) for c in cmds]
        self.assertTrue(any("--kube-context prod-k8s" in c for c in flat))
        self.assertTrue(any("--context prod-k8s" in c for c in flat))
        self.assertTrue(any("--profile main" in c for c in flat))
        for c in cmds:  # read-only 보증: mutating 동사가 없어야 한다
            joined = " ".join(c["cmd"])
            for bad in ("apply", "delete", "upgrade", "install", "scale"):
                self.assertNotIn(bad, joined)


class TestDiff(unittest.TestCase):
    def setUp(self):
        expected = sync_snapshot.build_expected(OK)
        actual = json.loads(MOCK.read_text(encoding="utf-8"))
        self.report = sync_snapshot.diff_state(expected, actual)

    def test_missing_in_docs(self):
        self.assertTrue(any("argocd" in x for x in self.report["missing_in_docs"]))
        self.assertTrue(any("prod-app-01" in x for x in self.report["missing_in_docs"]))

    def test_ghost_in_docs(self):
        self.assertTrue(any("prod-db-01" in x for x in self.report["ghost_in_docs"]))

    def test_version_mismatch(self):
        self.assertTrue(any("victoria-metrics" in x for x in self.report["version_mismatch"]))

    def test_no_unverifiable_when_reachable(self):
        self.assertEqual(self.report["unverifiable"], [])


class TestUnverifiable(unittest.TestCase):
    def test_unreachable_reported(self):
        expected = sync_snapshot.build_expected(OK)
        report = sync_snapshot.diff_state(expected, {"clusters": {}, "providers": {}})
        self.assertTrue(any("prod-k8s" in x for x in report["unverifiable"]))
        self.assertTrue(any("aws-main" in x for x in report["unverifiable"]))


class TestCollectReachability(unittest.TestCase):
    def test_helm_failure_marks_cluster_unverifiable(self):
        from unittest import mock

        class R:
            def __init__(self, rc, out=""):
                self.returncode = rc
                self.stdout = out

        def fake_run(cmd, **kw):
            if "nodes" in cmd:            # kubectl get nodes → 성공
                return R(0, "node/ip-1\n")
            if "list" in cmd:            # helm list → 실패
                return R(1, "")
            return R(0, "")              # aws describe-instances 등 → 성공(빈 결과)

        with mock.patch.object(sync_snapshot.subprocess, "run", side_effect=fake_run):
            actual = sync_snapshot.collect(OK)
        self.assertFalse(actual["clusters"]["prod-k8s"]["reachable"])
        report = sync_snapshot.diff_state(sync_snapshot.build_expected(OK), actual)
        self.assertTrue(any("prod-k8s" in x for x in report["unverifiable"]))
        # 유령 오분류가 없어야 한다: prod-k8s 컴포넌트가 ghost로 안 나와야 함
        self.assertFalse(any("victoria-metrics" in x for x in report["ghost_in_docs"]))


class TestDryMode(unittest.TestCase):
    def test_dry_prints_snapshot_and_commands(self):
        import io
        import contextlib
        from unittest import mock

        buf = io.StringIO()
        with mock.patch.object(sys, "argv", ["sync_snapshot.py", "--root", str(OK)]):
            with contextlib.redirect_stdout(buf):
                rc = sync_snapshot.main()
        out = buf.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("기대 스냅샷", out)
        self.assertIn("prod-k8s", out)
        self.assertIn("수집 명령", out)
        self.assertIn("--kube-context prod-k8s", out)


class TestSyncRobustness(unittest.TestCase):
    def test_missing_id_entity_skipped_not_crash(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "inventory").mkdir()
            (root / "inventory" / "noid.md").write_text(
                "---\ntype: server\nenv: prod\n---\n", encoding="utf-8")
            exp = sync_snapshot.build_expected(root)  # 크래시하면 안 됨
            self.assertEqual(exp["servers"], {})


if __name__ == "__main__":
    unittest.main()
