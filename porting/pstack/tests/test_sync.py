import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sync  # noqa: E402

PLUGIN_JSON = b'{"name": "pstack", "version": "1.2.3", "homepage": "https://example.com/up"}\n'


def skill(name: str, *, adapter: bool = False, explicit_only: bool = True, body: str = "") -> bytes:
    flag = "disable-model-invocation: true\n" if explicit_only else ""
    line = f"{sync.CLAUDE_LINE}\n\n" if adapter else ""
    return f"---\nname: {name}\ndescription: d\n{flag}---\n\n# {name}\n\n{line}{body}\n".encode()


def upstream(**extra: bytes) -> sync.Tree:
    tree = {
        "plugin.json": (PLUGIN_JSON, False),
        ".claude-plugin/plugin.json": (PLUGIN_JSON, False),
        "docs/harness/claude-code.md": (b"# adapter\n", False),
        "skills/wrapped/SKILL.md": (skill("wrapped", adapter=True), False),
        "skills/plain/SKILL.md": (skill("plain", body="See [wrapped](../wrapped/SKILL.md)."), False),
        "skills/setup/SKILL.md": (skill("setup", adapter=True, explicit_only=False), False),
        "skills/plain/scripts/run.sh": (b"#!/bin/sh\n", True),
    }
    tree.update({path: (data, False) for path, data in extra.items()})
    return tree


OVERLAY = {"docs/harness/codex.md": (b"# codex\n", False)}


def table_keys(text: str) -> dict[str, list[str]]:
    """## 절마다 표 첫 칸의 값을 모은다."""
    keys: dict[str, list[str]] = {}
    section = ""
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            keys.setdefault(section, [])
        elif line.startswith("| ") and not re.match(r"\| (-+|Cursor) \|", line):
            keys.setdefault(section, []).append(line.split(" | ")[0][2:].strip())
    return keys


class RenderTest(unittest.TestCase):
    def test_appends_codex_line_only_where_claude_line_is(self):
        files = sync.render(upstream(), OVERLAY)
        wrapped = files["skills/wrapped/SKILL.md"][0].decode()
        self.assertIn(sync.CLAUDE_LINE + sync.CODEX_LINE, wrapped)
        self.assertEqual(wrapped.count("docs/harness/codex.md"), 1)
        self.assertEqual(files["skills/plain/SKILL.md"], upstream()["skills/plain/SKILL.md"])

    def test_turns_off_implicit_invocation_for_explicit_only_skills(self):
        files = sync.render(upstream(), OVERLAY)
        self.assertEqual(files["skills/wrapped/agents/openai.yaml"][0], sync.OPENAI_YAML)
        self.assertEqual(files["skills/plain/agents/openai.yaml"][0], sync.OPENAI_YAML)
        self.assertNotIn("skills/setup/agents/openai.yaml", files)

    def test_keeps_one_manifest_with_superkit_links_and_upstream_version(self):
        files = sync.render(upstream(), OVERLAY)
        self.assertNotIn("plugin.json", files)
        manifest = sync.json.loads(files[".claude-plugin/plugin.json"][0])
        self.assertEqual(manifest["version"], "1.2.3")
        self.assertEqual(manifest["homepage"], sync.PLUGIN_JSON_OVERRIDES["homepage"])

    def test_keeps_executable_bit_and_adds_overlay(self):
        files = sync.render(upstream(), OVERLAY)
        self.assertTrue(files["skills/plain/scripts/run.sh"][1])
        self.assertEqual(files["docs/harness/codex.md"], OVERLAY["docs/harness/codex.md"])

    def test_fails_when_upstream_rewords_the_adapter_line(self):
        reworded = skill("wrapped", body="Read [the adapter](../../docs/harness/claude-code.md) first.")
        with self.assertRaises(sync.SyncError) as error:
            sync.render(upstream(**{"skills/wrapped/SKILL.md": reworded}), OVERLAY)
        self.assertIn("어댑터 문장", error.exception.problems[0])

    def test_fails_when_upstream_ships_a_path_superkit_owns(self):
        for path in ("docs/harness/codex.md", "skills/plain/agents/openai.yaml"):
            with self.subTest(path=path), self.assertRaises(sync.SyncError):
                sync.render(upstream(**{path: b"upstream\n"}), OVERLAY)

    def test_fails_on_links_that_leave_or_miss_the_tree(self):
        for href in ("../../../outside.md", "../missing/SKILL.md"):
            with self.subTest(href=href), self.assertRaises(sync.SyncError):
                sync.render(upstream(**{"skills/plain/SKILL.md": skill("plain", body=f"[x]({href})")}), OVERLAY)

    def test_fails_on_claude_md(self):
        with self.assertRaises(sync.SyncError):
            sync.render(upstream(**{"docs/CLAUDE.md": b"x\n"}), OVERLAY)

    def test_reconstruct_undoes_render(self):
        files = sync.render(upstream(), OVERLAY)
        want = {path: entry for path, entry in upstream().items() if path not in sync.DROPPED}
        want[".claude-plugin/plugin.json"] = files[".claude-plugin/plugin.json"]
        self.assertEqual(sync.reconstruct(files, OVERLAY), want)
        self.assertEqual(sync.render(sync.reconstruct(files, OVERLAY), OVERLAY), files)


class InstalledTreeTest(unittest.TestCase):
    def test_plugin_matches_pinned_upstream(self):
        self.assertEqual(sync.verify(), [])

    def test_codex_adapter_covers_every_claude_adapter_row(self):
        adapters = sync.PLUGIN / "docs" / "harness"
        claude = table_keys((adapters / "claude-code.md").read_text(encoding="utf-8"))
        codex = table_keys((adapters / "codex.md").read_text(encoding="utf-8"))
        for section, keys in claude.items():
            self.assertIn(section, codex, f"Codex 어댑터에 '## {section}' 절이 없다")
            for key in keys:
                self.assertIn(key, codex[section], f"Codex 어댑터 '{section}'에 '{key}' 행이 없다")

    def test_every_adapter_line_points_at_both_adapters(self):
        for path in sorted(sync.PLUGIN.glob("skills/*/SKILL.md")):
            text = path.read_text(encoding="utf-8")
            if "docs/harness/claude-code.md" in text:
                self.assertIn(sync.CLAUDE_LINE + sync.CODEX_LINE, text, path)


if __name__ == "__main__":
    unittest.main()
