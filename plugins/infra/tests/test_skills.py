import sys
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import harness_lib  # noqa: E402

# 태스크 진행에 따라 스킬 이름을 추가한다 (Task 8: register, lookup / Task 9: change, decide
# / Task 10: connect, ops / Task 11: sync, audit / Task A2-2: secrets)
SKILLS = ["init", "register", "lookup", "change", "decide", "connect", "ops", "sync", "audit", "secrets"]


class TestSkills(unittest.TestCase):
    def _skill_path(self, name):
        return PLUGIN_ROOT / "skills" / name / "SKILL.md"

    def test_skill_files_exist(self):
        for name in SKILLS:
            self.assertTrue(self._skill_path(name).is_file(), f"{name}: SKILL.md 없음")

    def test_frontmatter_name_and_description(self):
        for name in SKILLS:
            fm = harness_lib.parse_frontmatter(self._skill_path(name).read_text(encoding="utf-8"))
            self.assertEqual(fm.get("name"), name)
            desc = str(fm.get("description", ""))
            self.assertGreaterEqual(len(desc), 80, f"{name}: description이 3요소를 담기에 너무 짧음")

    def test_principles_and_harness_discovery_mentioned(self):
        for name in SKILLS:
            body = self._skill_path(name).read_text(encoding="utf-8")
            self.assertIn("원칙", body, f"{name}: 적용 원칙 명시 없음")
            self.assertIn("harness.yaml", body, f"{name}: 하네스 발견 규약 언급 없음")


class TestOpsReferences(unittest.TestCase):
    def test_references_exist_when_ops_added(self):
        if "ops" not in SKILLS:
            self.skipTest("ops 미구현")
        for ref in ("kubectl", "argocd", "prometheus", "helm"):
            p = PLUGIN_ROOT / "skills" / "ops" / "references" / f"{ref}.md"
            self.assertTrue(p.is_file(), f"references/{ref}.md 없음")


if __name__ == "__main__":
    unittest.main()
