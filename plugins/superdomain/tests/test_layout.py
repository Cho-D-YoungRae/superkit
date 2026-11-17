"""플러그인 레이아웃 불변식 — 같은 폴더를 Claude Code와 Codex가 함께 쓴다.

플러그인 디렉터리에서: python3 -m unittest discover -s tests -q
"""
import re
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
SKILLS = sorted((PLUGIN / "skills").glob("*/SKILL.md"))
AGENTS = sorted((PLUGIN / "agents").glob("*.md"))
DISPATCH = PLUGIN / "skills" / "review" / "references" / "dispatch.md"
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
RUNTIME_NOTE = "**런타임 메모**"
# Claude Code만 치환하는 자리표시자 — Codex에서는 그대로 보인다
CLAUDE_PLACEHOLDER = re.compile(r"\$\{CLAUDE_[A-Z_]+\}|\$ARGUMENTS")
# Claude Code가 본문에서 치환하는 표기 — 런타임 메모 자체에 있으면 Claude에서 뜻이 망가진다
SUBSTITUTABLE = re.compile(r"\$[\w{]")
POINTER = re.compile(r"^\s*- (도메인 정의|결정 기록): docs/superdomain/.*$", re.M)


def text(path):
    return path.read_text(encoding="utf-8")


def frontmatter(path):
    match = re.match(r"^---\n(.*?)\n---\n", text(path), re.S)
    assert match, f"{path.name}: 앞머리가 없다"
    return dict(line.split(": ", 1) for line in match.group(1).splitlines() if ": " in line)


class RuntimeNote(unittest.TestCase):
    def test_files_with_claude_placeholders_carry_runtime_note(self):
        for path in [*SKILLS, *AGENTS]:
            with self.subTest(path=path.relative_to(PLUGIN)):
                if CLAUDE_PLACEHOLDER.search(text(path)):
                    self.assertIn(RUNTIME_NOTE, text(path), "Codex에서 자리표시자를 푸는 런타임 메모가 없다")

    def test_runtime_note_survives_claude_substitution(self):
        for path in [*SKILLS, *AGENTS]:
            for line in text(path).splitlines():
                if RUNTIME_NOTE in line:
                    with self.subTest(path=path.relative_to(PLUGIN)):
                        self.assertIsNone(SUBSTITUTABLE.search(line), "런타임 메모에 치환되는 표기가 있다")


class Reviewers(unittest.TestCase):
    def test_agents_keep_claude_enforcement(self):
        # 공용 폴더로 합쳐도 Claude Code에서는 도구 제한·모델이 그대로 강제된다(ADR: 0.10.0)
        self.assertEqual({p.stem for p in AGENTS}, {"domain-reviewer", "convention-reviewer"})
        for path in AGENTS:
            with self.subTest(agent=path.stem):
                fm = frontmatter(path)
                self.assertEqual(fm.get("name"), path.stem)
                self.assertIn(fm.get("model"), {"opus", "sonnet"})
                self.assertEqual(fm.get("disallowedTools"), "Agent")
                tools = {tool.strip() for tool in fm.get("tools", "").split(",")}
                self.assertEqual(tools, {"Read", "Grep", "Glob", "Bash"}, "리뷰어는 읽기 도구만 쓴다")

    def test_callers_have_a_path_without_the_agent_tool(self):
        for name in ("review", "domain"):
            with self.subTest(skill=name):
                body = text(PLUGIN / "skills" / name / "SKILL.md")
                self.assertIn("Agent 도구", body)
                self.assertIn("references/dispatch.md", body, "Agent 도구가 없는 런타임의 실행 계약 링크가 없다")
                self.assertIn("미검토", body, "리뷰어를 못 띄우거나 실패하면 미검토로 보고해야 한다")

    def test_dispatch_uses_the_agent_definitions_as_role_documents(self):
        body = text(DISPATCH)
        for agent in AGENTS:
            self.assertIn(f"../../../agents/{agent.name}", body)

    def test_reviewers_read_commit_ranges_from_the_end_commit(self):
        self.assertIn("git show", text(PLUGIN / "skills" / "review" / "SKILL.md"))
        for path in [*AGENTS, DISPATCH, PLUGIN / "skills" / "review" / "SKILL.md"]:
            with self.subTest(path=path.relative_to(PLUGIN)):
                body = text(path)
                if path in AGENTS:
                    self.assertIn("git show <B>:<경로>", body)
                # B 안의 파일을 찾고 검색하려면 작업 트리 검색 대신 ls-tree·grep이 필요하다(시험에서 확인)
                self.assertIn("ls-tree", body, "커밋 범위에서 B를 검색할 git 명령이 허용 목록에 없다")


class ProjectOutput(unittest.TestCase):
    def test_pointer_lines_are_runtime_neutral_and_identical(self):
        # 사용자 프로젝트의 지침 파일에 쓰는 줄 — 두 런타임이 같은 줄을 읽는다
        domain = POINTER.findall(text(PLUGIN / "skills" / "domain" / "SKILL.md"))
        self.assertEqual(domain, ["도메인 정의", "결정 기록"])
        lines = {
            path.parent.name: [m.group(0).strip() for m in POINTER.finditer(text(path))]
            for path in (PLUGIN / "skills" / "domain" / "SKILL.md", PLUGIN / "skills" / "adr" / "SKILL.md")
        }
        self.assertEqual(lines["adr"], [lines["domain"][1]], "결정 기록 줄이 domain과 adr에서 다르다")
        for line in lines["domain"]:
            self.assertNotIn("/superdomain:", line)


class Package(unittest.TestCase):
    def test_relative_links_resolve(self):
        for path in [*SKILLS, *AGENTS, DISPATCH]:
            for target in LINK.findall(text(path)):
                if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                    continue
                with self.subTest(path=path.relative_to(PLUGIN), link=target):
                    self.assertTrue((path.parent / target.split("#")[0]).exists())

    def test_skills_have_codex_display_metadata(self):
        for path in SKILLS:
            with self.subTest(skill=path.parent.name):
                self.assertTrue((path.parent / "agents" / "openai.yaml").is_file())


if __name__ == "__main__":
    unittest.main()
