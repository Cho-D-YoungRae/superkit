#!/usr/bin/env python3
"""
Test suite for scripts/session_summary.sh — SessionStart hook

Verifies upward directory traversal from cwd to git root (directory or worktree file),
and that repository boundaries are correctly enforced.
"""

import sys
import unittest
import tempfile
import shutil
import subprocess
import json
import os
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "session_summary.sh"


class TestSessionSummary(unittest.TestCase):
    """Test session_summary.sh upward traversal and git boundary detection."""

    def setUp(self):
        """Create isolated temp directory for each test."""
        self.tmpdir = Path(tempfile.mkdtemp(prefix="superdomain-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmpdir, True)

    def _run_script(self, cwd, env=None):
        """Run session_summary.sh from specified directory, return (stdout, returncode)."""
        result = subprocess.run(
            [str(SCRIPT_PATH)],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            env=env,
        )
        return result.stdout, result.returncode

    def test_finds_summary_from_subdirectory(self):
        """Test upward search from subdirectory to git root."""
        # Setup: repo/.git (directory) + repo/docs/superdomain/summary.md
        repo = self.tmpdir / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / "docs" / "superdomain").mkdir(parents=True)
        summary_file = repo / "docs" / "superdomain" / "summary.md"
        summary_file.write_text("SUMMARY-OK")

        # Run from repo/backend (subdirectory)
        backend = repo / "backend"
        backend.mkdir()
        stdout, returncode = self._run_script(backend)

        self.assertEqual(returncode, 0, "Script should exit with code 0")
        self.assertEqual(stdout, "SUMMARY-OK", "Script should output summary content")

    def test_silent_when_no_summary(self):
        """Test silent exit when summary.md not found."""
        # Setup: directory with no summary
        repo = self.tmpdir / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()

        stdout, returncode = self._run_script(repo)

        self.assertEqual(returncode, 0, "Script should exit silently with code 0")
        self.assertEqual(stdout, "", "Script should output nothing when summary not found")

    def test_finds_summary_at_repo_root(self):
        """Test summary detection at git root itself."""
        # Setup: repo root is the git root
        repo = self.tmpdir / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / "docs" / "superdomain").mkdir(parents=True)
        (repo / "docs" / "superdomain" / "summary.md").write_text("SUMMARY-AT-ROOT")

        stdout, returncode = self._run_script(repo)

        self.assertEqual(returncode, 0)
        self.assertEqual(stdout, "SUMMARY-AT-ROOT")

    def test_stops_at_worktree_root(self):
        """Test that worktree boundary is correctly enforced.

        Verifies that .git as a file (worktree marker) is detected and traversal stops,
        preventing "poison" file from outer directory from being included.
        """
        # Setup: outer/docs/superdomain/summary.md (poison — should NOT be found)
        outer = self.tmpdir / "outer"
        outer.mkdir()
        (outer / "docs" / "superdomain").mkdir(parents=True)
        (outer / "docs" / "superdomain" / "summary.md").write_text("POISON-MUST-NOT-APPEAR")

        # Setup: outer/wt/.git as FILE (worktree) with no summary of its own
        wt = outer / "wt"
        wt.mkdir()
        (wt / ".git").write_text("gitdir: /somewhere/.git/worktrees/wt")
        (wt / "sub").mkdir()

        # Run from deep inside worktree
        stdout, returncode = self._run_script(wt / "sub")

        self.assertEqual(returncode, 0, "Worktree should exit cleanly")
        self.assertEqual(
            stdout, "",
            "Worktree boundary should be enforced; poison file must NOT leak"
        )

    def test_worktree_fix_is_load_bearing(self):
        """Prove that the -e fix actually prevents poison file injection.

        Creates a copy of the script with -d (old buggy version) and verifies
        that it incorrectly outputs the poison file from the outer directory.
        This demonstrates that the -e → -d change is load-bearing.
        """
        # Setup: Same tree as test_stops_at_worktree_root
        outer = self.tmpdir / "outer"
        outer.mkdir()
        (outer / "docs" / "superdomain").mkdir(parents=True)
        poison_file = outer / "docs" / "superdomain" / "summary.md"
        poison_file.write_text("POISON-MUST-NOT-APPEAR")

        wt = outer / "wt"
        wt.mkdir()
        (wt / ".git").write_text("gitdir: /somewhere/.git/worktrees/wt")
        (wt / "sub").mkdir()

        # Create buggy version: replace [ -e with [ -d
        original_script = SCRIPT_PATH.read_text()
        self.assertIn(
            '[ -e "$dir/.git" ]',
            original_script,
            "Current script must use -e test"
        )

        buggy_script = original_script.replace('[ -e "$dir/.git" ]', '[ -d "$dir/.git" ]')
        self.assertNotEqual(
            original_script, buggy_script,
            "Substitution must change the script (sanity check)"
        )
        self.assertIn(
            '[ -d "$dir/.git" ]',
            buggy_script,
            "Buggy version must have -d test"
        )

        # Write buggy version to temp file
        buggy_path = self.tmpdir / "old_session_summary.sh"
        buggy_path.write_text(buggy_script)
        buggy_path.chmod(0o755)

        # Run buggy version from same cwd
        result_buggy = subprocess.run(
            [str(buggy_path)],
            cwd=str(wt / "sub"),
            capture_output=True,
            text=True
        )

        # CRITICAL: Buggy version MUST leak the poison
        self.assertEqual(
            result_buggy.stdout,
            "POISON-MUST-NOT-APPEAR",
            "Buggy version (-d) must incorrectly output poison file from outer dir"
        )

        # CRITICAL: Current version MUST NOT leak the poison
        result_fixed = subprocess.run(
            [str(SCRIPT_PATH)],
            cwd=str(wt / "sub"),
            capture_output=True,
            text=True
        )
        self.assertEqual(
            result_fixed.stdout,
            "",
            "Fixed version (-e) must NOT output poison file"
        )

        # Prove the differential: they must be different
        self.assertNotEqual(
            result_buggy.stdout,
            result_fixed.stdout,
            "Buggy vs fixed versions must produce different output (proving fix is real)"
        )

    def _repo(self):
        repo = self.tmpdir / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        return repo

    def test_legacy_summary_prints_one_migration_line(self):
        repo = self._repo()
        (repo / "docs").mkdir()
        (repo / "docs" / "domain-summary.md").write_text(
            "<!-- GENERATED by superdomain from DOMAIN.md "
            "— 직접 수정 금지, 결정 템플릿 또는 SSOT 문서를 수정할 것 -->\n"
            "OLD-SUMMARY"
        )
        env = dict(os.environ, CLAUDE_PLUGIN_ROOT="/plugins/superdomain")
        stdout, returncode = self._run_script(repo, env=env)
        self.assertEqual(returncode, 0)
        self.assertNotIn("OLD-SUMMARY", stdout)
        self.assertTrue(stdout.startswith("[superdomain] "), stdout)
        self.assertIn("/plugins/superdomain/CHANGELOG.md", stdout)
        self.assertEqual(stdout.count("\n"), 1)

    def test_legacy_summary_without_generated_header_is_silent(self):
        repo = self._repo()
        (repo / "docs").mkdir()
        (repo / "docs" / "domain-summary.md").write_text("팀 요약")
        stdout, returncode = self._run_script(repo)
        self.assertEqual((stdout, returncode), ("", 0))

    def test_legacy_root_declaration_prints_the_line(self):
        repo = self._repo()
        (repo / "DOMAIN.md").write_text("# x\n<!-- superdomain:template v1 -->\n")
        stdout, returncode = self._run_script(repo)
        self.assertEqual(returncode, 0)
        self.assertTrue(stdout.startswith("[superdomain] "), stdout)

    def test_root_file_without_marker_is_silent(self):
        repo = self._repo()
        (repo / "DOMAIN.md").write_text("# 팀 메모\n")
        stdout, returncode = self._run_script(repo)
        self.assertEqual((stdout, returncode), ("", 0))

    def test_unreadable_summary_is_silent(self):
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            self.skipTest("root는 권한과 무관하게 읽는다")
        repo = self._repo()
        summary = repo / "docs" / "superdomain" / "summary.md"
        summary.parent.mkdir(parents=True)
        summary.write_text("SECRET")
        summary.chmod(0)
        self.addCleanup(summary.chmod, 0o644)
        stdout, returncode = self._run_script(repo)
        self.assertEqual((stdout, returncode), ("", 0))

    def test_hook_command_path_is_quoted(self):
        hooks = json.loads((SCRIPT_PATH.parent.parent / "hooks" / "hooks.json").read_text())
        command = hooks["hooks"]["SessionStart"][0]["hooks"][0]["command"]
        self.assertEqual(command, '"${CLAUDE_PLUGIN_ROOT}/scripts/session_summary.sh"')


if __name__ == "__main__":
    unittest.main()
