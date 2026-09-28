"""layout.py — 산출물 배치와 옛 배치 감지의 계약 테스트."""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from layout import (BASELINE_RELATIVE, CHANGELOG, DOMAIN_RELATIVE, Layout, LayoutError,
                    from_domain_path, legacy_leftovers)

MARKED = "# 샘플 — Domain\n<!-- superdomain:template v1 -->\n"


class LayoutTestCase(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="superdomain-")).resolve()
        self.addCleanup(shutil.rmtree, self.root, True)

    def write(self, relpath, text=""):
        path = self.root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def raises(self, path):
        with self.assertRaises(LayoutError) as caught:
            from_domain_path(path)
        return str(caught.exception)


class TestNewLayout(LayoutTestCase):
    def test_root_is_three_levels_above_the_declaration(self):
        layout = from_domain_path(self.write(DOMAIN_RELATIVE, MARKED))
        self.assertEqual(layout.root, self.root)
        self.assertEqual(layout.domain, self.root / "docs/superdomain/DOMAIN.md")
        self.assertEqual(layout.summary, self.root / "docs/superdomain/summary.md")
        self.assertEqual(layout.contexts_dir, self.root / "docs/superdomain/contexts")
        self.assertEqual(layout.adr_dir, self.root / "docs/superdomain/adr")
        self.assertEqual(layout.conventions_dir, self.root / "docs/superdomain/conventions")
        self.assertEqual(layout.baseline, self.root / "docs/superdomain/state/baseline.jsonl")
        self.assertEqual(layout.review_log, self.root / "docs/superdomain/state/review-log.jsonl")

    def test_missing_file_in_the_right_place_is_not_a_layout_error(self):
        # 읽기 실패는 파서가 자기 오류(exit 1/2)로 보고한다 — 배치 오류로 뭉뚱그리지 않는다.
        layout = from_domain_path(self.root / DOMAIN_RELATIVE)
        self.assertEqual(layout.root, self.root)

    def test_display_is_root_relative_posix(self):
        layout = Layout(self.root)
        self.assertEqual(layout.display(self.root / "a" / "b.kt"), "a/b.kt")
        outside = Path("/elsewhere/x.kt")
        self.assertEqual(layout.display(outside), "/elsewhere/x.kt")

    def test_team_decisions_folder_alone_is_not_a_leftover(self):
        # docs/decisions/는 팀이 따로 쓰는 폴더일 수 있다 — 옛 선언이 없으면 잔여물이 아니다.
        self.write(DOMAIN_RELATIVE, MARKED)
        self.write("docs/decisions/2026-01-01-team.md", "# 팀 결정\n")
        self.assertEqual(legacy_leftovers(self.root), [])
        from_domain_path(self.root / DOMAIN_RELATIVE)

    def test_team_owned_domain_folder_without_heading_is_not_a_leftover(self):
        # 마커 있는 옛 root DOMAIN.md가 없고 docs/domain/ 문서에도 소유 신호(## 불변식)가
        # 없으면 팀이 따로 쓰는 폴더로 본다 — superdomain 소유가 확실한 것만 잔여물이다.
        self.write(DOMAIN_RELATIVE, MARKED)
        self.write("docs/domain/team-notes.md", "# 팀 노트\n")
        self.assertEqual(legacy_leftovers(self.root), [])
        from_domain_path(self.root / DOMAIN_RELATIVE)

    def test_domain_summary_without_generated_header_is_not_a_leftover(self):
        # docs/domain-summary.md도 마찬가지 — 생성 헤더가 없으면 팀 문서로 본다.
        self.write(DOMAIN_RELATIVE, MARKED)
        self.write("docs/domain-summary.md", "# 우리 팀 요약\n")
        self.assertEqual(legacy_leftovers(self.root), [])
        from_domain_path(self.root / DOMAIN_RELATIVE)

    def test_no_declaration_anywhere_with_team_owned_domain_folder_creates_layout(self):
        # 루트 DOMAIN.md 자체가 없고 docs/domain/에 소유 신호 없는 문서만 있으면 옛 배치
        # 안내 없이 새 배치가 그대로 선다.
        self.write("docs/domain/team-notes.md", "# 팀 노트\n")
        layout = from_domain_path(self.root / DOMAIN_RELATIVE)
        self.assertEqual(layout.root, self.root)


class TestLegacyLayout(LayoutTestCase):
    def test_legacy_root_declaration_is_refused_with_commands(self):
        path = self.write("DOMAIN.md", MARKED)
        self.write("docs/domain-summary.md", "요약\n")
        self.write("docs/domain/claim.md", "# claim\n")
        self.write("docs/domain/baseline.jsonl", "{}\n")
        self.write("docs/decisions/2026-08-21-first.md", "# ADR\n")
        message = self.raises(path)
        self.assertIn("옛 배치", message)
        self.assertIn("mkdir -p docs/superdomain docs/superdomain/contexts docs/superdomain/state",
                      message)
        for line in ("git mv DOMAIN.md docs/superdomain/DOMAIN.md",
                     "git mv docs/domain-summary.md docs/superdomain/summary.md",
                     "git mv docs/domain/claim.md docs/superdomain/contexts/claim.md",
                     "git mv docs/domain/baseline.jsonl docs/superdomain/state/baseline.jsonl",
                     "git mv docs/decisions docs/superdomain/adr"):
            self.assertIn(line, message)
        self.assertIn(str(CHANGELOG), message)

    def test_only_existing_files_are_listed(self):
        path = self.write("DOMAIN.md", MARKED)
        message = self.raises(path)
        self.assertIn("git mv DOMAIN.md docs/superdomain/DOMAIN.md", message)
        self.assertNotIn("domain-summary", message)
        self.assertNotIn("docs/decisions", message)

    def test_new_path_missing_but_legacy_present_is_refused(self):
        self.write("DOMAIN.md", MARKED)
        message = self.raises(self.root / DOMAIN_RELATIVE)
        self.assertIn("git mv DOMAIN.md docs/superdomain/DOMAIN.md", message)

    def test_consolidated_document_gets_a_placeholder_target(self):
        self.write("DOMAIN.md", MARKED)
        self.write("docs/domain.md", "# 단일 컨텍스트\n")
        message = self.raises(self.root / "DOMAIN.md")
        self.assertIn("git mv docs/domain.md docs/superdomain/contexts/<컨텍스트 이름>.md",
                      message)

    def test_root_file_without_marker_is_not_legacy(self):
        path = self.write("DOMAIN.md", "# 우리 팀 도메인 메모\n")
        message = self.raises(path)
        self.assertNotIn("git mv", message)
        self.assertIn(DOMAIN_RELATIVE, message)

    def test_leftover_after_partial_migration_is_refused(self):
        # 옛 자리에 남은 컨텍스트 문서를 조용히 무시하면 check_invariants가 confirmed 불변식을 놓친다.
        self.write(DOMAIN_RELATIVE, MARKED)
        self.write("docs/domain/claim.md", "# claim\n\n## 불변식\n")
        self.write("docs/domain/baseline.jsonl", "{}\n")
        message = self.raises(self.root / DOMAIN_RELATIVE)
        self.assertIn("이행이 끝나지 않았습니다", message)
        self.assertIn("docs/domain/claim.md", message)
        self.assertIn("docs/domain/baseline.jsonl", message)

    def test_domain_summary_with_generated_header_is_refused(self):
        # 생성 헤더가 있으면 소유가 확실하므로 잔여물로 본다 — 이행 미완료로 거부한다.
        self.write(DOMAIN_RELATIVE, MARKED)
        self.write("docs/domain-summary.md",
                   "<!-- GENERATED by superdomain from DOMAIN.md — 직접 수정 금지 -->\n요약\n")
        message = self.raises(self.root / DOMAIN_RELATIVE)
        self.assertIn("이행이 끝나지 않았습니다", message)
        self.assertIn("docs/domain-summary.md", message)

    def test_leftovers_are_listed_in_a_stable_order(self):
        self.write("DOMAIN.md", MARKED)
        self.write("docs/domain/b.md")
        self.write("docs/domain/a.md")
        self.write("docs/domain/review-log.jsonl")
        self.assertEqual(legacy_leftovers(self.root), [
            ("DOMAIN.md", "docs/superdomain/DOMAIN.md"),
            ("docs/domain/a.md", "docs/superdomain/contexts/a.md"),
            ("docs/domain/b.md", "docs/superdomain/contexts/b.md"),
            ("docs/domain/review-log.jsonl", "docs/superdomain/state/review-log.jsonl"),
        ])


class TestWrongPlace(LayoutTestCase):
    def test_arbitrary_path_is_a_usage_error(self):
        # 마커가 있으면 옛 배치로 판정되므로(TestLegacyLayout) 여기서는 마커 없는 파일로 본다.
        message = self.raises(self.write("notes/DOMAIN.md", "# 메모\n"))
        self.assertIn(DOMAIN_RELATIVE, message)
        self.assertNotIn("git mv", message)

    def test_other_file_name_is_a_usage_error(self):
        message = self.raises(self.write("docs/superdomain/domain.md", MARKED))
        self.assertIn(DOMAIN_RELATIVE, message)


if __name__ == "__main__":
    unittest.main()
