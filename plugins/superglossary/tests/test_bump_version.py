"""scripts/bump_version.py 테스트 — 임시 저장소 사본에서 실행해 실제 파일을 건드리지 않는다."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class BumpVersionTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="bump-")
        self.addCleanup(shutil.rmtree, self.root, True)
        os.makedirs(os.path.join(self.root, "scripts"))
        os.makedirs(os.path.join(self.root, ".claude-plugin"))
        os.makedirs(os.path.join(self.root, "templates"))
        self.script = os.path.join(self.root, "scripts", "bump_version.py")
        shutil.copy(os.path.join(ROOT, "scripts", "bump_version.py"), self.script)
        self.manifest = os.path.join(self.root, ".claude-plugin", "plugin.json")
        self.cli = os.path.join(self.root, "templates", "glossary.py")
        self.write(self.manifest, '{\n  "name": "superglossary",\n  "version": "0.1.0"\n}\n')
        self.write(self.cli, 'import sys\n\nVERSION = "0.1.0"\n')

    def write(self, path, text):
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def read(self, path):
        with open(path, encoding="utf-8") as f:
            return f.read()

    def bump(self, *args):
        return subprocess.run([sys.executable, self.script, *args], capture_output=True, text=True)

    def test_bump_updates_manifest_and_cli_together(self):
        self.assertEqual(self.bump("0.2.0").returncode, 0)
        self.assertEqual(json.loads(self.read(self.manifest))["version"], "0.2.0")
        self.assertIn('VERSION = "0.2.0"', self.read(self.cli))
        self.assertEqual(self.bump("--check").returncode, 0)

    def test_missing_cli_version_leaves_manifest_untouched(self):
        # plugin.json만 바뀐 채 실패하면 저장소가 불일치 상태로 남는다
        self.write(self.cli, "import sys\n")
        before = self.read(self.manifest)
        done = self.bump("0.2.0")
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("VERSION", done.stderr)
        self.assertEqual(self.read(self.manifest), before)

    def test_invalid_semver_is_rejected_without_changes(self):
        before = (self.read(self.manifest), self.read(self.cli))
        self.assertNotEqual(self.bump("1.2").returncode, 0)
        self.assertEqual((self.read(self.manifest), self.read(self.cli)), before)

    def test_check_detects_mismatch(self):
        self.write(self.cli, 'VERSION = "0.0.9"\n')
        done = self.bump("--check")
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("불일치", done.stderr)


if __name__ == "__main__":
    unittest.main()
