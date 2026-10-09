"""Test observable snapshot/diff behavior without changing real plugins."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "tree_state.py"


class TreeStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "plugin"
        self.root.mkdir()

    def run_cli(self, *args, code=0):
        proc = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, code, proc.stderr)
        if code == 2:
            self.assertIn("error:", proc.stderr)
        return json.loads(proc.stdout) if code == 0 else proc

    def write(self, path, text):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def baseline(self):
        path = self.base / "before.json"
        path.write_text(json.dumps(self.run_cli("snapshot", self.root)))
        return path

    def test_snapshot_is_deterministic_and_keeps_hidden_components(self):
        self.write(".claude-plugin/plugin.json", "{}")
        self.write("skills/check/SKILL.md", "check")
        self.write(".git/HEAD", "ignored")
        self.write("__pycache__/cache.pyc", "ignored")
        first = self.run_cli("snapshot", self.root)
        self.assertEqual(first, self.run_cli("snapshot", self.root))
        self.assertEqual(set(first["files"]),
                         {".claude-plugin/plugin.json", "skills/check/SKILL.md"})

    def test_detects_content_addition_deletion_and_executable_changes(self):
        self.write("modified.txt", "before")
        self.write("removed.txt", "before")
        executable = self.write("bin/tool", "#!/bin/sh\n")
        executable.chmod(0o644)
        before = self.baseline()
        self.write("modified.txt", "after")
        self.write("added.txt", "new")
        (self.root / "removed.txt").unlink()
        executable.chmod(0o755)
        diff = self.run_cli("compare", before, self.root)
        self.assertEqual(diff, {"added": ["added.txt"],
                                "modified": ["bin/tool", "modified.txt"],
                                "removed": ["removed.txt"]})
        self.assertEqual((self.root / "modified.txt").read_text(), "after")

    def test_symlinks_are_recorded_without_reading_external_targets(self):
        outside = self.base / "outside"
        outside.mkdir()
        (outside / "private.txt").write_text("do not traverse")
        (self.root / "linked").symlink_to(outside, target_is_directory=True)
        (self.root / "dangling").symlink_to("missing")
        state = self.run_cli("snapshot", self.root)
        self.assertEqual(set(state["files"]), {"linked", "dangling"})
        self.assertEqual(state["files"]["linked"],
                         {"type": "symlink", "target": str(outside)})

    def test_owned_paths_exclude_user_files_and_reject_escape(self):
        self.write("owned.txt", "generated")
        self.write("personal.txt", "custom")
        paths = self.base / "paths.json"
        paths.write_text('["owned.txt"]')
        state = self.run_cli("snapshot", self.root, "--paths-file", paths)
        self.assertEqual(set(state["files"]), {"owned.txt"})
        paths.write_text('["../outside"]')
        self.run_cli("snapshot", self.root, "--paths-file", paths, code=2)

    def test_explicit_paths_do_not_follow_symlink_ancestors(self):
        outside = self.base / "outside"
        outside.mkdir()
        (outside / "private.txt").write_text("do not read")
        (self.root / "linked").symlink_to(outside, target_is_directory=True)
        paths = self.base / "paths.json"
        paths.write_text('["linked/private.txt"]')
        self.run_cli("snapshot", self.root, "--paths-file", paths, code=2)

    def test_bad_baseline_and_missing_roots_are_errors(self):
        bad = self.base / "bad.json"
        bad.write_text('{"schema_version": 99, "files": {}}')
        self.run_cli("compare", bad, self.root, code=2)
        self.run_cli("snapshot", self.base / "missing", code=2)


if __name__ == "__main__":
    unittest.main()
