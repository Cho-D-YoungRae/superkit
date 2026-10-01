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


DOCS = ((CLAUDE_MD, "CLAUDE.md"), (README, "README.md"))
"""D16의 검사 대상 문서 — 스펙이 `CLAUDE.md`·`README.md` 양쪽을 지목한다.

한쪽만 검사하면 규약이 자기모순이 된다: 실제로 README가 'D1~D14'와 plan 4건 중 2건만
열거한 채로 통과했다. 새 항목을 추가할 때도 반드시 두 문서를 함께 돌린다.
"""


class TestDecisionRange(unittest.TestCase):
    def test_docs_d_range_matches_spec(self):
        nums = [int(x) for x in re.findall(
            r"^\| D(\d+) \|", SPEC.read_text(encoding="utf-8"), re.MULTILINE)]
        self.assertTrue(nums, "스펙에서 D 결정표 행을 찾지 못했다")
        for path, label in DOCS:
            with self.subTest(doc=label):
                m = re.search(r"결정\s*D1~D(\d+)", path.read_text(encoding="utf-8"))
                self.assertIsNotNone(m, f"{label}에 '결정 D1~DN' 표기가 없다")
                self.assertEqual(int(m.group(1)), max(nums),
                                 f"{label}의 D 범위가 스펙의 최대 D{max(nums)}와 다르다")


class TestPlanList(unittest.TestCase):
    def test_docs_list_every_plan(self):
        actual = {p.name for p in PLANS_DIR.glob("*.md")}
        for path, label in DOCS:
            with self.subTest(doc=label):
                listed = set(re.findall(r"docs/superpowers/plans/([\w.-]+\.md)",
                                        path.read_text(encoding="utf-8")))
                self.assertEqual(listed, actual,
                                 f"{label}가 열거한 plan {listed}이 실제 {actual}와 다르다")


def actual_template_count():
    return len([p for p in (PLUGIN_ROOT / "templates").iterdir() if p.is_file()])


class TestTemplateCount(unittest.TestCase):
    """'골격 N종' 표기가 templates/ 실제 파일 수와 같아야 한다."""

    def test_claude_md_matches_reality(self):
        found = [int(x) for x in re.findall(r"골격\s*(\d+)종",
                                            CLAUDE_MD.read_text(encoding="utf-8"))]
        self.assertTrue(found, "CLAUDE.md에 '골격 N종' 표기가 없다")
        actual = actual_template_count()
        self.assertEqual(set(found), {actual},
                         f"CLAUDE.md의 표기 {found}가 실제 {actual}종과 다르다")


def actual_fixture_names():
    return {p.name for p in (PLUGIN_ROOT / "tests" / "fixtures").iterdir() if p.is_dir()}


class TestFixtureList(unittest.TestCase):
    """CLAUDE.md·README.md가 언급하는 harness-* fixture 이름이 **모두** 실제와
    일치해야 한다. 일부만 열거해도 실패한다 — fixture를 언급하는 이상 전부
    열거해야 새 fixture 추가나 이름 변경 같은 드리프트를 놓치지 않는다.
    """

    def test_docs_list_every_fixture(self):
        actual = actual_fixture_names()
        for path, label in ((CLAUDE_MD, "CLAUDE.md"), (README, "README.md")):
            with self.subTest(doc=label):
                found = set(re.findall(r"(harness-\w+)`?\(",
                                       path.read_text(encoding="utf-8")))
                self.assertTrue(found, f"{label}에 'harness-*(...)' fixture 언급이 없다")
                self.assertEqual(found, actual,
                                 f"{label}가 언급하는 fixture {found}가 실제 {actual}와 다르다")


def actual_test_method_count():
    # 정규식을 "공백 네 칸 그대로 + def test_" 리터럴로 적으면 이 줄 자신이 grep
    # 측정 명령의 검색 대상 부분 문자열과 겹쳐서 스스로를 메서드로 오탐한다
    # (실측으로 발견: 리터럴로 쓰면 130, 실제 unittest discover 결과는 129).
    # `{4}` 수량자로 공백 반복을 표현해 그 부분 문자열이 소스에 나타나지 않게
    # 한다 — 매치 의미는 동일하다.
    total = 0
    for path in (PLUGIN_ROOT / "tests").glob("test_*.py"):
        total += len(re.findall(r"^ {4}def test_", path.read_text(encoding="utf-8"),
                                re.MULTILINE))
    return total


class TestTotalTestCount(unittest.TestCase):
    """CLAUDE.md의 '전체 테스트(N개)' 표기가 실제 테스트 메서드 수와 같아야
    한다. 스위트를 실행해 세면 이 테스트 자신의 존재가 카운트에 영향을 주는
    재귀 문제가 생긴다 — 대신 tests/test_*.py의 'def test_' 메서드를 정적으로
    센다(unittest가 discover하는 개수와 일치).
    """

    def test_claude_md_matches_reality(self):
        found = [int(x) for x in re.findall(r"전체\s*테스트\((\d+)개\)",
                                            CLAUDE_MD.read_text(encoding="utf-8"))]
        self.assertTrue(found, "CLAUDE.md에 '전체 테스트(N개)' 표기가 없다")
        actual = actual_test_method_count()
        self.assertEqual(set(found), {actual},
                         f"CLAUDE.md의 표기 {found}가 실제 {actual}개와 다르다")


if __name__ == "__main__":
    unittest.main()
