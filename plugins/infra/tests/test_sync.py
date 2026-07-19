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


if __name__ == "__main__":
    unittest.main()
