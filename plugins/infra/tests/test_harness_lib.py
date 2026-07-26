import sys
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import harness_lib  # noqa: E402

OK = PLUGIN_ROOT / "tests" / "fixtures" / "harness-ok"


class TestFindHarnessRoot(unittest.TestCase):
    def test_finds_from_subdir(self):
        self.assertEqual(harness_lib.find_harness_root(OK / "inventory" / "components"), OK)

    def test_none_outside(self):
        self.assertIsNone(harness_lib.find_harness_root("/"))


class TestParseFrontmatter(unittest.TestCase):
    def test_parses_server(self):
        fm = harness_lib.parse_frontmatter((OK / "inventory" / "prod-db-01.md").read_text(encoding="utf-8"))
        self.assertEqual(fm["id"], "prod-db-01")
        self.assertEqual(fm["type"], "server")
        self.assertEqual(fm["depends_on"], [])
        self.assertEqual(fm["purpose"], "PostgreSQL 단독 DB 서버")

    def test_body_is_ignored(self):
        # 본문에 콜론 줄·리스트·--- 수평선이 있어도 frontmatter만 파싱된다 (스펙 D10)
        fm = harness_lib.parse_frontmatter((OK / "inventory" / "prod-db-01.md").read_text(encoding="utf-8"))
        self.assertEqual(set(fm), {"id", "type", "env", "provider", "runtime",
                                   "purpose", "access", "managed_by", "depends_on"})
        self.assertNotIn("사설 IP", fm)
        self.assertNotIn("arch", fm)

    def test_inline_list(self):
        fm = harness_lib.parse_frontmatter((OK / "providers" / "aws-main.md").read_text(encoding="utf-8"))
        self.assertEqual(fm["regions"], ["ap-northeast-2"])

    def test_rejects_missing_delim(self):
        with self.assertRaises(harness_lib.FrontmatterError):
            harness_lib.parse_frontmatter("id: x\n")

    def test_rejects_nested(self):
        with self.assertRaises(harness_lib.FrontmatterError):
            harness_lib.parse_frontmatter("---\nparent:\n  child: 1\n---\n")

    def test_strips_comment_after_value(self):
        fm = harness_lib.parse_frontmatter("---\nid: x  # 코멘트\n---\n")
        self.assertEqual(fm, {"id": "x"})

    def test_rejects_line_without_colon(self):
        with self.assertRaises(harness_lib.FrontmatterError):
            harness_lib.parse_frontmatter("---\nid: x\nnocolonline\n---\n")


class TestParseYamlSubset(unittest.TestCase):
    def test_harness_yaml(self):
        data = harness_lib.load_harness_yaml(OK / "harness.yaml")
        self.assertEqual(data["sharing"], "local")
        self.assertEqual(data["environments"], ["prod", "dev"])
        self.assertEqual(data["iac"]["repos"], ["terraform://github.com/example/infra-tf"])
        self.assertEqual(data["policies"]["mutating"]["prod"], "confirm")
        self.assertIs(data["hooks"]["change_reminder"], True)

    def test_rejects_list_in_populated_map(self):
        with self.assertRaises(harness_lib.HarnessYamlError):
            harness_lib.parse_yaml_subset("a: 1\n- x\n")

    def test_rejects_bare_line(self):
        with self.assertRaises(harness_lib.HarnessYamlError):
            harness_lib.parse_yaml_subset("just-a-bare-word\n")

    def test_strips_comments(self):
        data = harness_lib.parse_yaml_subset(
            "sharing: local  # 주석\n# 전체 주석 줄\nhooks:\n  change_reminder: true\n"
        )
        self.assertEqual(data, {"sharing": "local", "hooks": {"change_reminder": True}})


class TestIterEntities(unittest.TestCase):
    def test_collects_all(self):
        ents = harness_lib.iter_entities(OK)
        ids = sorted(e["_stem"] for e in ents)
        self.assertEqual(ids, ["aws-main", "prod-db-01", "prod-k8s", "victoria-metrics"])
        for e in ents:
            self.assertNotIn("_error", e)


if __name__ == "__main__":
    unittest.main()
