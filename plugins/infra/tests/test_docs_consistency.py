"""문서가 코드 구조를 수치로 언급하면 그 정합성을 강제한다 (D16).

손으로 고치는 것만으로는 재발한다 — 실제로 P0 작업 중에 테스트 수와 D 범위가
다시 어긋나 사람이 고쳤다. 사람 규율에 맡기지 않고 테스트로 고정한다.
"""
import re
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_MD = PLUGIN_ROOT / "CLAUDE.md"
README = PLUGIN_ROOT / "README.md"
SPEC = PLUGIN_ROOT / "docs" / "superpowers" / "specs" / "2026-07-19-infra-plugin-design.md"
PLANS_DIR = PLUGIN_ROOT / "docs" / "superpowers" / "plans"


def actual_skill_count():
    return len([p for p in (PLUGIN_ROOT / "skills").iterdir() if (p / "SKILL.md").is_file()])


class TestSkillCount(unittest.TestCase):
    """'스킬 N종' 표기가 **모두** 실제 수와 같아야 한다.

    첫 등장만 검사하면 뒤쪽에 다른 수치가 남아도 통과한다 — 드리프트를 막는 게
    목적이므로 findall로 전부 본다.
    """

    def _assert_all_match(self, path, label):
        found = [int(x) for x in re.findall(r"스킬\s*(\d+)종",
                                            path.read_text(encoding="utf-8"))]
        self.assertTrue(found, f"{label}에 '스킬 N종' 표기가 없다")
        actual = actual_skill_count()
        self.assertEqual(set(found), {actual},
                         f"{label}의 표기 {found}가 실제 {actual}종과 다르다")

    def test_claude_md_matches_reality(self):
        self._assert_all_match(CLAUDE_MD, "CLAUDE.md")

    def test_readme_matches_reality(self):
        self._assert_all_match(README, "README.md")


class TestDecisionRange(unittest.TestCase):
    def test_claude_md_d_range_matches_spec(self):
        nums = [int(x) for x in re.findall(
            r"^\| D(\d+) \|", SPEC.read_text(encoding="utf-8"), re.MULTILINE)]
        self.assertTrue(nums, "스펙에서 D 결정표 행을 찾지 못했다")
        m = re.search(r"결정\s*D1~D(\d+)", CLAUDE_MD.read_text(encoding="utf-8"))
        self.assertIsNotNone(m, "CLAUDE.md에 '결정 D1~DN' 표기가 없다")
        self.assertEqual(int(m.group(1)), max(nums))


class TestPlanList(unittest.TestCase):
    def test_claude_md_lists_every_plan(self):
        listed = set(re.findall(r"docs/superpowers/plans/([\w.-]+\.md)",
                                CLAUDE_MD.read_text(encoding="utf-8")))
        actual = {p.name for p in PLANS_DIR.glob("*.md")}
        self.assertEqual(listed, actual)


if __name__ == "__main__":
    unittest.main()
