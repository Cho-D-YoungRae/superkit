import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from parse_architecture import parse_architecture

FIXTURES = Path(__file__).resolve().parent / "fixtures"

def load(name):
    return (FIXTURES / name).read_text(encoding="utf-8")

class TestParseCore(unittest.TestCase):
    def test_minimal_project_and_context(self):
        arch, errors = parse_architecture(load("minimal.md"))
        self.assertEqual(errors, [])
        self.assertTrue(arch.has_template_marker)
        p = arch.projects[0]
        self.assertEqual((p.name, p.path, p.profile, p.base_package), ("backend", ".", "kotlin-spring", "com.acme"))
        c = arch.contexts[0]
        self.assertEqual((c.name, c.project, c.classification, c.style, c.module_layout),
                         ("claim", "backend", "core", "hexagonal", "multi-module"))
        self.assertEqual(len(c.modules), 4)
        self.assertEqual((c.modules[0].name, c.modules[0].path, c.modules[0].layer),
                         ("claim-domain", "claim/domain", "domain"))

    def test_full_app_embedded(self):
        arch, errors = parse_architecture(load("full.md"))
        self.assertEqual(errors, [])
        p = arch.projects[0]
        self.assertEqual(len(p.applications), 4)
        self.assertEqual(p.applications[3].contexts, ["all"])          # core-admin
        self.assertEqual(len(p.shared_modules), 4)
        self.assertEqual(p.shared_modules[0].role, "shared-kernel")     # core-enum
        self.assertIn("domain", p.package_conventions)
        self.assertEqual(p.package_conventions["domain"], "com.imstargg.core.domain.{컨텍스트}..")
        braw = next(c for c in arch.contexts if c.name == "brawlstars")
        self.assertEqual(braw.module_layout, "app-embedded")
        self.assertEqual(braw.modules, [])                              # app-embedded는 모듈 표 없음
        self.assertEqual(braw.relations[0].type, "customer-supplier")

    def test_label_comment_stripped(self):
        # "- 분류: core (설명 주석)" 처럼 후행 괄호 주석은 값에서 제거된다
        text = load("minimal.md").replace("- 분류: core", "- 분류: core   (core | supporting | generic)")
        arch, errors = parse_architecture(text)
        self.assertEqual(errors, [])
        self.assertEqual(arch.contexts[0].classification, "core")

    def test_unknown_sections_ignored(self):
        text = load("minimal.md") + "\n## 자유 섹션\n아무 내용.\n\n| 임의 | 표 |\n|---|---|\n| a | b |\n"
        arch, errors = parse_architecture(text)
        self.assertEqual(errors, [])
        self.assertEqual(len(arch.contexts), 1)

    def test_table_row_trailing_text_discarded(self):
        # "| presentation | com.imstargg.{앱}.. |    ← ... (core-api → core.api)" 처럼
        # 헤더보다 많은 파이프 구분 조각이 있는 행은 헤더가 선언한 칸 수만큼만 취하고 나머지는 버린다.
        arch, errors = parse_architecture(load("full.md"))
        self.assertEqual(errors, [])
        p = arch.projects[0]
        self.assertEqual(p.package_conventions["presentation"], "com.imstargg.{앱}..")

if __name__ == "__main__":
    unittest.main()
