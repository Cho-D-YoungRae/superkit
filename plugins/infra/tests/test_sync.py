import json
import sys
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import sync_snapshot  # noqa: E402

OK = PLUGIN_ROOT / "tests" / "fixtures" / "harness-ok"
MOCK = PLUGIN_ROOT / "tests" / "fixtures" / "mock-actual.json"
ONPREM = PLUGIN_ROOT / "tests" / "fixtures" / "harness-onprem"


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


class TestProviderSkipReason(unittest.TestCase):
    """자동 수집 불가 사유가 명시되어야 한다 (검토 P1-4)."""

    def test_onprem_has_no_collector(self):
        reason = sync_snapshot.provider_skip_reason({"kind": "onprem"})
        self.assertIsNotNone(reason)
        self.assertIn("자동 수집기가 없습니다", reason)

    def test_aws_without_regions(self):
        reason = sync_snapshot.provider_skip_reason({"kind": "aws", "cli_profile": "main"})
        self.assertIsNotNone(reason)
        self.assertIn("regions", reason)

    def test_aws_without_profile(self):
        reason = sync_snapshot.provider_skip_reason(
            {"kind": "aws", "regions": ["ap-northeast-2"]})
        self.assertIsNotNone(reason)
        self.assertIn("cli_profile", reason)

    def test_complete_aws_is_collectable(self):
        self.assertIsNone(sync_snapshot.provider_skip_reason(
            {"kind": "aws", "cli_profile": "main", "regions": ["ap-northeast-2"]}))

    def test_complete_gcp_is_collectable(self):
        self.assertIsNone(sync_snapshot.provider_skip_reason(
            {"kind": "gcp", "cli_profile": "gcp-prod"}))


class TestOnpremNotSilent(unittest.TestCase):
    """온프렘 하네스가 '전부 0건'으로 보고되면 안 된다 (검토 P1-4)."""

    def setUp(self):
        self.expected = sync_snapshot.build_expected(ONPREM)
        self.report = sync_snapshot.diff_state(
            self.expected, {"clusters": {}, "providers": {}})

    def test_onprem_reported_as_unverifiable(self):
        joined = "\n".join(self.report["unverifiable"])
        self.assertIn("onprem-idc", joined)
        self.assertIn("자동 수집기가 없습니다", joined)

    def test_report_is_not_all_zero(self):
        total = sum(len(v) for v in self.report.values())
        self.assertGreater(total, 0,
                           "온프렘 하네스가 4구획 전부 0건이면 조용한 거짓 안심이다")

    def test_onprem_server_is_not_reported_as_ghost(self):
        joined = "\n".join(self.report["ghost_in_docs"])
        self.assertNotIn("prod-web-01", joined,
                         "대조하지 않은 서버를 유령으로 단정하면 안 된다")


class TestRegionExplicit(unittest.TestCase):
    """aws 수집 명령이 --region까지 명시해야 한다 (원칙 6, 검토 P2-2)."""

    def test_aws_command_includes_region(self):
        cmds = sync_snapshot.build_collect_commands(OK)
        aws = [" ".join(c["cmd"]) for c in cmds if c["cmd"][0] == "aws"]
        self.assertTrue(aws, "aws 수집 명령이 생성되지 않았다")
        for c in aws:
            self.assertIn("--profile main", c)
            self.assertIn("--region ap-northeast-2", c)

    def test_multi_region_emits_one_command_per_region(self):
        import shutil
        import tempfile
        root = Path(tempfile.mkdtemp()) / "h"
        shutil.copytree(OK, root)
        (root / "providers" / "aws-main.md").write_text(
            "---\nid: aws-main\ntype: provider\nkind: aws\ncli_profile: main\n"
            "regions: [ap-northeast-2, us-east-1]\n"
            'console: "https://console.aws.amazon.com"\n---\n\n# aws-main\n',
            encoding="utf-8")
        cmds = sync_snapshot.build_collect_commands(root)
        aws = [" ".join(c["cmd"]) for c in cmds if c["cmd"][0] == "aws"]
        self.assertEqual(len(aws), 2, aws)
        self.assertTrue(any("--region ap-northeast-2" in c for c in aws))
        self.assertTrue(any("--region us-east-1" in c for c in aws))


class TestPartialCollectIsUnverifiable(unittest.TestCase):
    """일부 리전만 본 것을 전부 본 것처럼 보고하면 안 된다 (검토 P1-4)."""

    def test_one_region_failure_marks_provider_unverifiable(self):
        expected = sync_snapshot.build_expected(OK)
        actual = {"clusters": {},
                  "providers": {"aws-main": {"reachable": False, "instances": ["prod-db-01"]}}}
        report = sync_snapshot.diff_state(expected, actual)
        self.assertTrue(any("aws-main" in u for u in report["unverifiable"]),
                        report["unverifiable"])


class TestCollectAccumulatesRegions(unittest.TestCase):
    """collect()가 리전별 명령 결과를 한 provider 엔트리로 누적하는지 검증한다 (검토 Important-1).

    이 가드가 없으면(예: instances 분기를 덮어쓰기 한 줄로 되돌리면) 다중 리전에서 마지막
    명령이 앞 결과를 덮어써, 앞 리전 실패+뒤 리전 성공 시 reachable: True + 부분 instances로
    오보된다 — 이 태스크가 없애려던 거짓 안심이 되살아난다.
    """

    def _multi_region_root(self):
        import shutil
        import tempfile
        root = Path(tempfile.mkdtemp()) / "h"
        shutil.copytree(OK, root)
        (root / "providers" / "aws-main.md").write_text(
            "---\nid: aws-main\ntype: provider\nkind: aws\ncli_profile: main\n"
            "regions: [ap-northeast-2, us-east-1]\n"
            'console: "https://console.aws.amazon.com"\n---\n\n# aws-main\n',
            encoding="utf-8")
        return root

    def test_both_regions_succeed_merge_into_one_entry(self):
        from unittest import mock

        class R:
            def __init__(self, rc, out=""):
                self.returncode = rc
                self.stdout = out

        def fake_run(cmd, **kw):
            if "nodes" in cmd:            # kubectl get nodes → 성공
                return R(0, "node/ip-1\n")
            if "list" in cmd:            # helm list → 성공(빈 결과)
                return R(0, "[]")
            if "ap-northeast-2" in cmd:  # 첫 리전 → 성공
                return R(0, "prod-db-01\n")
            if "us-east-1" in cmd:       # 둘째 리전 → 성공
                return R(0, "prod-app-01\n")
            return R(0, "")

        root = self._multi_region_root()
        with mock.patch.object(sync_snapshot.subprocess, "run", side_effect=fake_run):
            actual = sync_snapshot.collect(root)
        entry = actual["providers"]["aws-main"]
        self.assertTrue(entry["reachable"])
        self.assertEqual(set(entry["instances"]), {"prod-db-01", "prod-app-01"},
                         "두 리전의 instances가 한 엔트리로 누적되어야 한다(덮어쓰기 금지)")

    def test_first_region_failure_keeps_provider_unreachable(self):
        from unittest import mock

        class R:
            def __init__(self, rc, out=""):
                self.returncode = rc
                self.stdout = out

        def fake_run(cmd, **kw):
            if "nodes" in cmd:
                return R(0, "node/ip-1\n")
            if "list" in cmd:
                return R(0, "[]")
            if "ap-northeast-2" in cmd:  # 첫 리전 → 실패
                return R(1, "")
            if "us-east-1" in cmd:       # 둘째 리전 → 성공
                return R(0, "prod-app-01\n")
            return R(0, "")

        root = self._multi_region_root()
        with mock.patch.object(sync_snapshot.subprocess, "run", side_effect=fake_run):
            actual = sync_snapshot.collect(root)
        entry = actual["providers"]["aws-main"]
        self.assertFalse(entry["reachable"],
                         "한 리전이라도 실패하면 뒤 리전이 성공해도 확인 불가로 남아야 한다")


if __name__ == "__main__":
    unittest.main()
