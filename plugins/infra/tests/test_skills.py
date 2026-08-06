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


class TestAuditSkillCategories(unittest.TestCase):
    def test_audit_skill_documents_new_categories(self):
        body = (PLUGIN_ROOT / "skills" / "audit" / "SKILL.md").read_text(encoding="utf-8")
        for token in ("[구조]", "[키]", "recovery", "[보호]", "[내부오류]", "secrets_format"):
            self.assertIn(token, body, f"audit SKILL.md에 {token} 카테고리 설명 없음")


class TestHandoffPathsResolve(unittest.TestCase):
    """문서가 가리키는 곳에 실제로 그 절이 있어야 한다 (검토 P1-6)."""

    def _read(self, rel):
        import subprocess
        p = PLUGIN_ROOT / rel
        try:
            return p.read_text(encoding="utf-8")
        except (OSError, PermissionError):
            out = subprocess.run(["git", "-C", str(PLUGIN_ROOT), "show", f"HEAD:{rel}"],
                                 capture_output=True, text=True, check=True)
            return out.stdout

    def test_secrets_skill_has_initial_encryption_section(self):
        body = self._read("skills/secrets/SKILL.md")
        self.assertIn("신규 시크릿 생성", body,
                      "init이 인계하는 초기 암호화 절이 secrets 스킬에 없다")
        self.assertIn(".sops.yaml", body)

    def test_init_handoff_names_the_section(self):
        body = self._read("skills/init/SKILL.md")
        self.assertIn("신규 시크릿 생성", body,
                      "init의 인계 문구가 실재하는 절 이름을 가리키지 않는다")


if __name__ == "__main__":
    unittest.main()
