"""패키지 레이아웃 불변식 — 같은 폴더(plugins/superglossary)를 Claude Code와 Codex가 함께 쓴다.

개발용 검사라 설치 패키지 밖에 둔다. 저장소 루트에서:
python3 -m unittest discover -s evals/superglossary/tests -q
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PLUGIN = ROOT / "plugins" / "superglossary"
SKILLS = sorted((PLUGIN / "skills").glob("*/SKILL.md"))
AGENTS = sorted((PLUGIN / "agents").glob("*.md"))
GUIDE = PLUGIN / "skills" / "glossary" / "glossary-guide.md"
DISPATCH = PLUGIN / "skills" / "glossary" / "references" / "scanner-dispatch.md"
GLOSSARY_SKILL = PLUGIN / "skills" / "glossary" / "SKILL.md"
CHECK_SKILL = PLUGIN / "skills" / "check" / "SKILL.md"
README = PLUGIN / "README.md"
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
RUNTIME_NOTE = "**런타임 메모**"
# Claude Code만 치환하는 자리표시자 — Codex에서는 그대로 보인다
CLAUDE_PLACEHOLDER = re.compile(r"\$\{CLAUDE_[A-Z_]+\}|\$ARGUMENTS")
# Claude Code가 본문에서 치환하는 표기 — 런타임 메모 자체에 있으면 Claude에서 뜻이 망가진다
SUBSTITUTABLE = re.compile(r"\$[\w{]")
# 런타임마다 다른 스킬 호출 표기
INVOCATION = re.compile(r"[/$]superglossary:")
POINTER = re.compile(r"^\s*- 용어 사전: docs/superglossary/glossary\.md .*$", re.M)
RG_EXAMPLE = re.compile(r"`rg ")
GREP_FALLBACK = "Grep 도구가 없는"


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

    def test_scanner_role_document_carries_runtime_note(self):
        # Codex는 에이전트 정의를 역할 문서로 읽는다 — 머리의 tools·model이 적용되지 않음을 알려야 한다
        for path in AGENTS:
            with self.subTest(agent=path.stem):
                self.assertIn(RUNTIME_NOTE, text(path))
                self.assertIn("scanner-dispatch.md", text(path))

    def test_runtime_note_survives_claude_substitution(self):
        for path in [*SKILLS, *AGENTS]:
            for line in text(path).splitlines():
                if RUNTIME_NOTE in line:
                    with self.subTest(path=path.relative_to(PLUGIN)):
                        self.assertIsNone(SUBSTITUTABLE.search(line), "런타임 메모에 치환되는 표기가 있다")

    def test_guide_names_no_runtime(self):
        # guide는 두 런타임이 같은 파일을 읽는다
        body = text(GUIDE)
        self.assertNotIn("Claude", body)
        self.assertNotIn("Codex", body)


class Scanner(unittest.TestCase):
    def test_scanner_keeps_claude_enforcement(self):
        # 공용 폴더로 합쳐도 Claude Code에서는 도구 제한·모델이 그대로 강제된다(0.9.0)
        self.assertEqual({p.stem for p in AGENTS}, {"glossary-scanner"})
        fm = frontmatter(PLUGIN / "agents" / "glossary-scanner.md")
        self.assertEqual(fm.get("name"), "glossary-scanner")
        self.assertEqual(fm.get("model"), "sonnet")
        tools = {tool.strip() for tool in fm.get("tools", "").split(",")}
        self.assertEqual(tools, {"Read", "Grep", "Glob"}, "스캐너는 읽기·검색 도구만 쓴다")

    def test_glossary_has_a_path_without_the_agent_tool(self):
        body = text(GLOSSARY_SKILL)
        self.assertIn("Agent 도구", body)
        self.assertIn("references/scanner-dispatch.md", body, "Agent 도구가 없는 런타임의 실행 계약 링크가 없다")
        self.assertIn("미완료", body, "스캐너를 못 띄우거나 실패하면 미완료로 알려야 한다")

    def test_dispatch_uses_the_agent_definition_as_role_document(self):
        self.assertIn("../../../agents/glossary-scanner.md", text(DISPATCH))

    def test_shell_search_examples_are_fallbacks(self):
        # Claude Code에서 스캐너는 셸이 없고, check의 allowed-tools에는 rg가 없다
        for path in [CHECK_SKILL, *AGENTS]:
            for line in text(path).splitlines():
                if RG_EXAMPLE.search(line):
                    with self.subTest(path=path.relative_to(PLUGIN), line=line[:60]):
                        self.assertIn(GREP_FALLBACK, line, "rg 예시는 Grep 도구가 없을 때의 대안으로만 둔다")


class ProjectOutput(unittest.TestCase):
    def test_files_written_to_user_projects_are_runtime_neutral(self):
        # 포인터 줄과 용어집 머리말은 사용자 프로젝트에 남고 두 런타임이 같은 파일을 읽는다
        pointers = [m.group(0).strip() for m in POINTER.finditer(text(GLOSSARY_SKILL))]
        self.assertEqual(len(pointers), 1)
        self.assertIsNone(INVOCATION.search(pointers[0]))
        self.assertIsNone(INVOCATION.search(text(GUIDE)), "용어집 템플릿에 런타임 호출 표기가 있다")
        self.assertIn(pointers[0], text(README), "README의 포인터 예시가 스킬과 다르다")

    def test_existing_pointers_are_matched_by_glossary_path(self):
        # 옛 호출 표기(/superglossary:·$superglossary:)의 포인터가 있는 프로젝트에 줄을 또 넣지 않는다
        self.assertIn("같은 용어집을 가리키는", text(GLOSSARY_SKILL))


class Package(unittest.TestCase):
    def test_relative_links_resolve(self):
        for path in [*SKILLS, *AGENTS, DISPATCH, README]:
            for target in LINK.findall(text(path)):
                if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                    continue
                with self.subTest(path=path.relative_to(PLUGIN), link=target):
                    self.assertTrue((path.parent / target.split("#")[0]).exists())

    def test_skills_have_codex_display_metadata(self):
        for path in SKILLS:
            with self.subTest(skill=path.parent.name):
                self.assertTrue((path.parent / "agents" / "openai.yaml").is_file())

    def test_manifest_names_both_runtimes(self):
        manifest = text(PLUGIN / ".claude-plugin" / "plugin.json")
        self.assertIn("Codex", manifest)


if __name__ == "__main__":
    unittest.main()
