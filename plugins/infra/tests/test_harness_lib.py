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

    def test_inline_list(self):
        fm = harness_lib.parse_frontmatter((OK / "providers" / "aws-main.md").read_text(encoding="utf-8"))
        self.assertEqual(fm["regions"], ["ap-northeast-2"])

    def test_rejects_missing_delim(self):
        with self.assertRaises(harness_lib.FrontmatterError):
            harness_lib.parse_frontmatter("id: x\n")

    def test_rejects_nested(self):
        with self.assertRaises(harness_lib.FrontmatterError):
            harness_lib.parse_frontmatter("---\nparent:\n  child: 1\n---\n")


class TestParseYamlSubset(unittest.TestCase):
    def test_harness_yaml(self):
        data = harness_lib.load_harness_yaml(OK / "harness.yaml")
        self.assertEqual(data["sharing"], "local")
        self.assertEqual(data["environments"], ["prod", "dev"])
        self.assertEqual(data["iac"]["repos"], ["terraform://github.com/example/infra-tf"])
        self.assertEqual(data["policies"]["mutating"]["prod"], "confirm")
        self.assertIs(data["hooks"]["change_reminder"], True)


class TestIterEntities(unittest.TestCase):
    def test_collects_all(self):
        ents = harness_lib.iter_entities(OK)
        ids = sorted(e["_stem"] for e in ents)
        self.assertEqual(ids, ["aws-main", "prod-db-01", "prod-k8s", "victoria-metrics"])
        for e in ents:
            self.assertNotIn("_error", e)


if __name__ == "__main__":
    unittest.main()
