"""스킬과 레퍼런스의 구조를 검사한다.

플러그인 디렉터리에서: python3 -m unittest discover -s tests -q
"""
import re
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
SKILL_DIR = PLUGIN / "skills" / "apply"
REVIEW_DIR = PLUGIN / "skills" / "review"
REVIEWER = PLUGIN / "agents" / "clean-code-reviewer.md"
REFS = SKILL_DIR / "references"
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
CHAPTER_SECTIONS = ("## 핵심", "## 체크리스트", "## 관련")


def chapter_files():
    return sorted(REFS.glob("chapter_*.md"))


def frontmatter(path):
    match = re.match(r"^---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.S)
    assert match, f"{path.name} 앞머리가 없다"
    return match.group(1)


def local_links(text):
    for target in LINK.findall(text):
        if re.match(r"^[a-z]+:", target) or target.startswith("#"):
            continue
        yield target.split("#", 1)[0]


class SkillTest(unittest.TestCase):
    def test_frontmatter(self):
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        self.assertIsNotNone(match, "SKILL.md 앞머리가 없다")
        front = match.group(1)
        self.assertRegex(front, r"(?m)^name: apply$")
        self.assertRegex(front, r"(?m)^description: \S")

    def test_mentioned_reference_files_exist(self):
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        for name in set(re.findall(r"`((?:index|chapter_\d+_\w+)\.md)`", text)):
            with self.subTest(name=name):
                self.assertTrue((REFS / name).is_file(), f"SKILL.md가 없는 파일 {name}을 가리킨다")
        for name in set(re.findall(r"references/([\w.]+\.md)", text)):
            with self.subTest(name=name):
                self.assertTrue((REFS / name).is_file(), f"SKILL.md가 없는 파일 {name}을 가리킨다")


class ReviewTest(unittest.TestCase):
    def test_review_skill_frontmatter(self):
        front = frontmatter(REVIEW_DIR / "SKILL.md")
        self.assertRegex(front, r"(?m)^name: review$")
        self.assertRegex(front, r"(?m)^description: \S")
        self.assertNotRegex(front, r"(?m)^model:", "모델은 에이전트 파일에서만 정한다")

    def test_review_skill_calls_reviewer(self):
        text = (REVIEW_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("clean-code:clean-code-reviewer", text)
        self.assertIn("${CLAUDE_PLUGIN_ROOT}/skills/apply/references/", text)

    def test_reviewer_frontmatter(self):
        front = frontmatter(REVIEWER)
        self.assertRegex(front, r"(?m)^name: clean-code-reviewer$")
        self.assertRegex(front, r"(?m)^model: \S")
        tools = re.search(r"(?m)^tools: (.+)$", front).group(1)
        for write_tool in ("Edit", "Write", "NotebookEdit"):
            self.assertNotIn(write_tool, tools, "리뷰어는 읽기 전용이다")
        self.assertRegex(front, r"(?m)^disallowedTools: .*\bAgent\b")

    def test_reviewer_reference_paths_exist(self):
        text = REVIEWER.read_text(encoding="utf-8")
        for rel in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]+)", text):
            with self.subTest(path=rel):
                self.assertTrue((PLUGIN / rel).exists(), f"리뷰어가 없는 경로 {rel}을 가리킨다")
        for name in set(re.findall(r"`?(chapter_\d+_\w+\.md)`?", text)):
            with self.subTest(file=name):
                self.assertTrue((REFS / name).is_file(), f"리뷰어가 없는 파일 {name}을 가리킨다")


class ReferencesTest(unittest.TestCase):
    def test_index_links_every_chapter_file(self):
        index = (REFS / "index.md").read_text(encoding="utf-8")
        linked = {Path(t).name for t in local_links(index)}
        for path in chapter_files():
            with self.subTest(file=path.name):
                self.assertIn(path.name, linked, "index.md가 이 챕터 파일을 가리키지 않는다")

    def test_local_links_resolve(self):
        for path in [REFS / "index.md", *chapter_files()]:
            text = path.read_text(encoding="utf-8")
            for target in local_links(text):
                with self.subTest(file=path.name, link=target):
                    self.assertTrue((path.parent / target).is_file(), f"{path.name}의 링크 {target}가 깨졌다")

    def test_chapter_shape(self):
        for path in chapter_files():
            text = path.read_text(encoding="utf-8")
            with self.subTest(file=path.name):
                number = int(re.match(r"chapter_(\d+)_", path.name).group(1))
                self.assertRegex(text.splitlines()[0], rf"^# Chapter {number}: ")
                self.assertIn("> 원서: *Clean Code*", text)
                for section in CHAPTER_SECTIONS:
                    self.assertRegex(text, rf"(?m)^{re.escape(section)}\s*$", f"{section} 절이 없다")

    def test_code_fences_closed(self):
        for path in [REFS / "index.md", *chapter_files()]:
            fences = re.findall(r"(?m)^\s*```", path.read_text(encoding="utf-8"))
            with self.subTest(file=path.name):
                self.assertEqual(len(fences) % 2, 0, "닫히지 않은 코드 블록이 있다")


if __name__ == "__main__":
    unittest.main()
