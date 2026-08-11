import json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from check_invariants import LIMITATION_NOTE, check, render

ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = Path(__file__).resolve().parent
SCRIPT = ROOT / "scripts" / "check_invariants.py"
TEMPLATE = ROOT / "references" / "governance" / "domain-doc-template.md"

HEAD = """# 샘플 — Architecture
<!-- superarchitect:template v1 -->

## 프로젝트: backend
- 경로: .
- 프로파일: kotlin-spring
- 기본 패키지: com.acme
- 아키텍처 테스트 위치: architecture-test/src/test/kotlin
"""


def context_section(name, path=None):
    """단일 모듈 컨텍스트 하나. 모듈 표가 없으면 parse_architecture가 오류를 낸다."""
    return f"""
## 컨텍스트: {name}
- 분류: core
- 스타일: layered-simple
- 모듈 구성: single-module

| 모듈 | 경로 | 레이어 |
|---|---|---|
| {name}-app | {path or name} | all |
"""


MONO_ARCH = HEAD + context_section("claim")
# `core`와 `core-api`가 함께 선언된 트리 — 최장 일치가 아니면 `INV-CORE-API-001`이
# 컨텍스트 `core` + 번호 `API-001`로 잘못 읽힌다(정본 §4.2).
HYPHEN_ARCH = HEAD + context_section("core") + context_section("core-api")
# 이름에 `test` 세그먼트가 없는 테스트 위치 — 선언을 읽지 않으면 스캔되지 않는다(P3-D4).
ITEST_ARCH = HEAD.replace("architecture-test/src/test/kotlin", "itest/kotlin") \
    + context_section("claim")
# 첫 프로젝트의 경로는 아직 없고 태그는 둘째 프로젝트에만 있다 — 스캔이 프로젝트를 다 돌아야 한다.
TWO_PROJECT_ARCH = """# 샘플 — Architecture
<!-- superarchitect:template v1 -->

## 프로젝트: absent
- 경로: absent
- 프로파일: kotlin-spring
- 기본 패키지: com.acme.absent
- 아키텍처 테스트 위치: src/test/kotlin

## 프로젝트: second
- 경로: second
- 프로파일: kotlin-spring
- 기본 패키지: com.acme
- 아키텍처 테스트 위치: src/test/kotlin
""" + context_section("claim").replace("- 분류: core", "- 분류: core\n- 프로젝트: second")
# 모노레포에서 흔한 겹치는 경로 — 같은 파일을 두 번 세면 관측 건수가 부풀고 경고가 중복된다.
OVERLAP_ARCH = TWO_PROJECT_ARCH.replace("## 프로젝트: absent\n- 경로: absent",
                                        "## 프로젝트: root\n- 경로: .")


def row(inv_id, status, description="검증 가능한 서술이다"):
    return f"| {inv_id} | {description} | {status} |"


# 아래 조립에서 첫 데이터 행은 언제나 7행이다 — 위반의 행 번호 단언이 이 상수에 걸린다.
FIRST_ROW_LINE = 7


def domain_doc(*rows, title="claim", tail=""):
    head = [f"# {title} — Domain", "", "## 불변식", "", "| ID | 서술 | 상태 |", "|---|---|---|"]
    return "\n".join(head + list(rows)) + "\n" + tail


def skeleton():
    """정본 §3의 4-백틱 스켈레톤을 그대로 떼어 온다 — 픽스처를 손으로 베끼지 않는다."""
    lines = TEMPLATE.read_text(encoding="utf-8").split("\n")
    start = lines.index("````markdown") + 1
    return "\n".join(lines[start:lines.index("````", start)]) + "\n"


class InvariantTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(dir=TESTS_DIR, prefix="tmp"))
        self.arch_path = self.tmpdir / "ARCHITECTURE.md"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ---- 트리 구성 -------------------------------------------------------

    def arch(self, text=MONO_ARCH):
        self.arch_path.write_text(text, encoding="utf-8")
        return self.arch_path

    def src(self, relpath, text):
        path = self.tmpdir / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def doc(self, name, body):
        return self.src(f"docs/architecture/domain/{name}.md", body)

    def consolidated(self, body):
        return self.src("docs/architecture/DOMAIN.md", body)

    def tagged(self, *ids, relpath="src/test/kotlin/com/acme/ClaimTest.kt",
              form='@Tag("{id}")'):
        """테스트 소스 한 개. 첫 태그가 5행에 오도록 머리를 고정한다."""
        lines = ["package com.acme", "", "import org.junit.jupiter.api.Tag", ""]
        for index, inv_id in enumerate(ids):
            lines.append(form.format(id=inv_id))
            lines.append(f"fun test{index}() {{}}")
        return self.src(relpath, "\n".join(lines) + "\n")

    def empty_tests(self):
        """태그 없는 테스트 소스 — '테스트 소스 0건' 검사 불능을 피하기 위한 최소 트리."""
        return self.src("src/test/kotlin/com/acme/SmokeTest.kt",
                        "package com.acme\n\nclass SmokeTest\n")

    # ---- 관측 도우미 ------------------------------------------------------

    def check(self, context=None):
        return check(self.arch_path, context)

    def messages(self, report):
        return [f"{e.path}:{e.line}: {e.message}" for e in report.errors]

    def assert_error(self, report, needle, count=None):
        found = [m for m in self.messages(report) if needle in m]
        self.assertTrue(found, f"'{needle}'을(를) 기대했지만 {self.messages(report)}")
        if count is not None:
            self.assertEqual(len(found), count, found)
        return found[0]

    def assert_clean(self, report):
        self.assertEqual(self.messages(report), [])
        self.assertEqual([f"{v.path}:{v.line}: {v.message}" for v in report.violations], [])
        self.assertEqual(report.blocked, "")

    def warnings(self, report):
        """사람이 보는 줄에서 경고만 골라낸다 — 푸터의 '경고 N건'에는 콜론이 없다."""
        return [line for line in render(report) if "경고: " in line]

    def assert_warning(self, report, needle, count=None):
        found = [w for w in self.warnings(report) if needle in w]
        self.assertTrue(found, f"'{needle}' 경고를 기대했지만 {self.warnings(report)}")
        if count is not None:
            self.assertEqual(len(found), count, found)
        return found[0]


# ---------------------------------------------------------------------------
# 정본 스켈레톤 — 템플릿 §3이 그대로 파싱을 통과해야 한다
# ---------------------------------------------------------------------------

class TestCanonicalSkeleton(InvariantTestCase):
    def test_skeleton_extraction_is_not_empty(self):
        body = skeleton()
        self.assertIn("## 불변식", body)
        self.assertIn("INV-CLAIM-001", body)

    def test_skeleton_parses_without_error(self):
        self.arch()
        self.doc("claim", skeleton())
        self.empty_tests()
        report = self.check()
        self.assertEqual(self.messages(report), [])
        self.assertEqual([i.id for i in report.invariants],
                         ["INV-CLAIM-001", "INV-CLAIM-002", "INV-CLAIM-003"])
        self.assertEqual([i.status for i in report.invariants],
                         ["confirmed", "confirmed", "proposed"])
        self.assertEqual({i.context for i in report.invariants}, {"claim"})

    def test_skeleton_aggregate_table_is_not_read_as_invariants(self):
        """`## 애그리거트`의 표가 창을 넘어 불변식으로 읽히면 4건 이상이 나온다."""
        self.arch()
        self.doc("claim", skeleton())
        self.empty_tests()
        self.assertEqual(len(self.check().invariants), 3)

    def test_skeleton_confirmed_without_tags_is_violation(self):
        self.arch()
        self.doc("claim", skeleton())
        self.empty_tests()
        report = self.check()
        self.assertEqual(sorted(v.invariant_id for v in report.violations),
                         ["INV-CLAIM-001", "INV-CLAIM-002"])


# ---------------------------------------------------------------------------
# 표 파싱 계약 (정본 §4.1)
# ---------------------------------------------------------------------------

class TestTableContract(InvariantTestCase):
    def setUp(self):
        super().setUp()
        self.arch()
        self.empty_tests()

    def test_missing_table_is_zero_not_error(self):
        self.doc("claim", "# claim — Domain\n\n본문뿐인 새 문서다.\n")
        report = self.check()
        self.assertEqual(self.messages(report), [])
        self.assertEqual(report.invariants, [])
        self.assertTrue(any("불변식 0건" in n for n in report.notices), report.notices)

    def test_wrong_heading_name_yields_zero_invariants(self):
        self.doc("claim", "# claim — Domain\n\n## 불변 조건\n\n| ID | 서술 | 상태 |\n"
                          "|---|---|---|\n| INV-CLAIM-001 | 서술 | confirmed |\n")
        report = self.check()
        self.assertEqual(self.messages(report), [])
        self.assertEqual(report.invariants, [])

    def test_second_table_in_section_is_ignored(self):
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "confirmed"),
                                     tail="\n| ID | 서술 | 상태 |\n|---|---|---|\n"
                                          "| INV-CLAIM-002 | 서술 | confirmed |\n"))
        self.assertEqual([i.id for i in self.check().invariants], ["INV-CLAIM-001"])

    def test_level_three_heading_does_not_close_the_window(self):
        body = ("# claim — Domain\n\n## 불변식\n\n### 핵심\n\n| ID | 서술 | 상태 |\n"
                "|---|---|---|\n| INV-CLAIM-001 | 서술 | confirmed |\n")
        self.doc("claim", body)
        self.assertEqual([i.id for i in self.check().invariants], ["INV-CLAIM-001"])

    def test_level_two_heading_closes_the_window(self):
        body = ("# claim — Domain\n\n## 불변식\n\n표를 아직 쓰지 않았다.\n\n## 애그리거트\n\n"
                "| 애그리거트 | 루트 | 포함 |\n|---|---|---|\n| Claim | Claim | ClaimItem |\n")
        self.doc("claim", body)
        report = self.check()
        self.assertEqual(report.invariants, [])
        self.assertEqual(self.messages(report), [])

    def test_last_section_runs_to_end_of_file(self):
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "confirmed")))
        self.assertEqual([i.id for i in self.check().invariants], ["INV-CLAIM-001"])

    def test_header_names_are_not_read(self):
        body = ("# claim — Domain\n\n## 불변식\n\n| 상태 | ID | 서술 |\n|---|---|---|\n"
                "| INV-CLAIM-001 | 서술 | confirmed |\n")
        self.doc("claim", body)
        report = self.check()
        self.assertEqual([i.id for i in report.invariants], ["INV-CLAIM-001"])
        self.assertEqual(self.messages(report), [])

    def test_fourth_cell_is_discarded(self):
        self.doc("claim", domain_doc("| INV-CLAIM-001 | 서술 | confirmed | 메모 |"))
        report = self.check()
        self.assertEqual(self.messages(report), [])
        self.assertEqual([i.status for i in report.invariants], ["confirmed"])

    def test_undecodable_document_is_error_not_silence(self):
        """읽지 못한 문서를 '불변식 0건'으로 넘기면 그 컨텍스트가 검사에서 통째로 사라진다."""
        path = self.tmpdir / "docs/architecture/domain/claim.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"# claim \xff\xfe Domain\n")
        report = self.check()
        message = self.assert_error(report, "claim.md:0:")
        self.assertIn("읽지 못했습니다", message)
        self.assertEqual(report.invariants, [])

    def test_pipe_in_description_splits_the_row_loudly(self):
        """서술 칸의 `|`는 열을 가른다 — 조용히 통과하지 않고 상태 칸에서 걸린다(§4.1)."""
        self.doc("claim", domain_doc("| INV-CLAIM-001 | 금액 | 수량은 0보다 크다 | confirmed |"))
        report = self.check()
        self.assert_error(report, "정규 값")
        self.assertEqual(report.invariants, [])

    def test_row_with_two_cells_is_error(self):
        self.doc("claim", domain_doc("| INV-CLAIM-001 | 서술 |"))
        report = self.check()
        self.assert_error(report, f"claim.md:{FIRST_ROW_LINE}:")
        self.assert_error(report, "칸")
        self.assertEqual(report.invariants, [])

    def test_empty_status_cell_is_non_canonical_not_missing_cell(self):
        self.doc("claim", domain_doc("| INV-CLAIM-001 | 서술 |  |"))
        report = self.check()
        message = self.assert_error(report, f"claim.md:{FIRST_ROW_LINE}:")
        self.assertIn("정규 값", message)
        self.assertNotIn("데이터 행에 칸이", message)     # 결손 행으로 뭉개지면 안 된다

    def test_missing_separator_drops_the_first_data_row(self):
        body = ("# claim — Domain\n\n## 불변식\n\n| ID | 서술 | 상태 |\n"
                + row("INV-CLAIM-001", "confirmed") + "\n"
                + row("INV-CLAIM-002", "confirmed") + "\n")
        self.doc("claim", body)
        self.assertEqual([i.id for i in self.check().invariants], ["INV-CLAIM-002"])

    def test_blank_line_ends_the_table(self):
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "confirmed"),
                                     tail="\n" + row("INV-CLAIM-002", "confirmed") + "\n"))
        self.assertEqual([i.id for i in self.check().invariants], ["INV-CLAIM-001"])

    def test_row_line_numbers_are_document_lines(self):
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "confirmed"),
                                     row("INV-CLAIM-002", "proposed")))
        lines = [i.line for i in self.check().invariants]
        self.assertEqual(lines, [FIRST_ROW_LINE, FIRST_ROW_LINE + 1])


# ---------------------------------------------------------------------------
# ID 형식과 최장 일치 (정본 §4.2)
# ---------------------------------------------------------------------------

class TestIdFormat(InvariantTestCase):
    def test_longest_match_picks_the_hyphenated_context(self):
        self.arch(HYPHEN_ARCH)
        self.empty_tests()
        self.doc("core-api", domain_doc(row("INV-CORE-API-001", "proposed"), title="core-api"))
        report = self.check()
        self.assertEqual(self.messages(report), [])
        self.assertEqual([(i.id, i.context) for i in report.invariants],
                         [("INV-CORE-API-001", "core-api")])

    def test_shorter_context_still_resolves(self):
        self.arch(HYPHEN_ARCH)
        self.empty_tests()
        self.doc("core", domain_doc(row("INV-CORE-001", "proposed"), title="core"))
        self.assertEqual([(i.id, i.context) for i in self.check().invariants],
                         [("INV-CORE-001", "core")])

    def test_unknown_context_id_is_error(self):
        self.arch()
        self.empty_tests()
        self.doc("claim", domain_doc(row("INV-BILLING-001", "confirmed")))
        report = self.check()
        self.assert_error(report, "INV-BILLING-001")
        self.assertEqual(report.invariants, [])

    def test_number_must_be_three_digits(self):
        self.arch()
        self.empty_tests()
        self.doc("claim", domain_doc(row("INV-CLAIM-1", "confirmed")))
        self.assert_error(self.check(), "INV-CLAIM-1")

    def test_missing_prefix_is_error(self):
        self.arch()
        self.empty_tests()
        self.doc("claim", domain_doc(row("CLAIM-001", "confirmed")))
        self.assert_error(self.check(), "CLAIM-001")

    def test_lowercase_id_is_error(self):
        self.arch()
        self.empty_tests()
        self.doc("claim", domain_doc(row("inv-claim-001", "confirmed")))
        self.assert_error(self.check(), "inv-claim-001")

    def test_lowercase_context_in_id_is_error(self):
        """ID는 `@Tag` 리터럴과 문자 그대로 같아야 한다 — 대소문자를 관대하게 보면 안 된다."""
        self.arch()
        self.empty_tests()
        self.doc("claim", domain_doc(row("INV-claim-001", "confirmed")))
        self.assert_error(self.check(), "INV-claim-001")

    def test_duplicate_id_in_one_document_is_error(self):
        self.arch()
        self.empty_tests()
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "confirmed"),
                                     row("INV-CLAIM-001", "proposed")))
        report = self.check()
        message = self.assert_error(report, f"claim.md:{FIRST_ROW_LINE + 1}:")
        self.assertIn("INV-CLAIM-001", message)
        self.assertEqual(len(report.invariants), 1)

    def test_filename_context_mismatch_is_error(self):
        self.arch(HYPHEN_ARCH)
        self.empty_tests()
        self.doc("core", domain_doc(row("INV-CORE-API-001", "confirmed"), title="core"))
        report = self.check()
        message = self.assert_error(report, "INV-CORE-API-001")
        self.assertIn("core-api", message)


# ---------------------------------------------------------------------------
# 상태 (정본 §4.3)
# ---------------------------------------------------------------------------

class TestStatus(InvariantTestCase):
    def setUp(self):
        super().setUp()
        self.arch()
        self.empty_tests()

    def test_third_status_is_error(self):
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "deprecated")))
        message = self.assert_error(self.check(), f"claim.md:{FIRST_ROW_LINE}:")
        self.assertIn("deprecated", message)

    def test_uppercase_status_is_error(self):
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "Confirmed")))
        self.assert_error(self.check(), "Confirmed")

    def test_both_canonical_statuses_are_accepted(self):
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "proposed"),
                                     row("INV-CLAIM-002", "confirmed")))
        report = self.check()
        self.assertEqual(self.messages(report), [])
        self.assertEqual([i.status for i in report.invariants], ["proposed", "confirmed"])


# ---------------------------------------------------------------------------
# 문서 위치와 배치 (정본 §2 · §4.4)
# ---------------------------------------------------------------------------

class TestPlacement(InvariantTestCase):
    def test_consolidated_domain_md_is_read_for_single_context(self):
        self.arch()
        self.empty_tests()
        self.consolidated(domain_doc(row("INV-CLAIM-001", "proposed")))
        report = self.check()
        self.assertEqual(self.messages(report), [])
        self.assertEqual([i.id for i in report.invariants], ["INV-CLAIM-001"])
        self.assertTrue(report.invariants[0].path.endswith("DOMAIN.md"),
                        report.invariants[0].path)

    def test_same_context_in_both_places_is_error(self):
        self.arch()
        self.empty_tests()
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "proposed")))
        self.consolidated(domain_doc(row("INV-CLAIM-002", "proposed")))
        report = self.check()
        self.assert_error(report, "중복 배치")
        self.assertEqual(report.invariants, [])

    def test_consolidated_with_two_contexts_is_error(self):
        self.arch(HYPHEN_ARCH)
        self.empty_tests()
        self.consolidated(domain_doc(row("INV-CORE-001", "proposed"), title="core"))
        report = self.check()
        self.assert_error(report, "DOMAIN.md")
        self.assertEqual(report.invariants, [])

    def test_undeclared_domain_file_is_warning_and_is_not_collected(self):
        self.arch()
        self.empty_tests()
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "proposed")))
        self.doc("billing", domain_doc(row("INV-CLAIM-002", "confirmed"), title="billing"))
        report = self.check()
        self.assertEqual(self.messages(report), [])
        self.assert_warning(report, "billing.md")
        self.assertEqual([i.id for i in report.invariants], ["INV-CLAIM-001"])

    def test_undeclared_domain_file_without_table_still_warns(self):
        self.arch()
        self.empty_tests()
        self.doc("billing", "# billing — Domain\n\n본문뿐이다.\n")
        self.assert_warning(self.check(), "billing.md")

    def test_declared_context_without_document_is_notice_not_error(self):
        self.arch()
        self.empty_tests()
        report = self.check()
        self.assertEqual(self.messages(report), [])
        self.assertEqual(report.warnings, [])
        self.assertTrue(any("claim" in n for n in report.notices), report.notices)


# ---------------------------------------------------------------------------
# 판정 — 위반과 경고 (정본 §4.4)
# ---------------------------------------------------------------------------

class TestVerdict(InvariantTestCase):
    def setUp(self):
        super().setUp()
        self.arch()

    def test_confirmed_with_tag_is_clean(self):
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "confirmed")))
        self.tagged("INV-CLAIM-001")
        report = self.check()
        self.assert_clean(report)
        self.assertEqual(report.warnings, [])
        self.assertEqual(report.checked, 1)

    def test_confirmed_without_tag_is_violation_at_document_line(self):
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "confirmed"),
                                     row("INV-CLAIM-002", "confirmed")))
        self.tagged("INV-CLAIM-001")
        report = self.check()
        self.assertEqual(len(report.violations), 1, report.violations)
        violation = report.violations[0]
        self.assertEqual(violation.invariant_id, "INV-CLAIM-002")
        self.assertEqual(violation.line, FIRST_ROW_LINE + 1)
        self.assertTrue(violation.path.endswith("domain/claim.md"), violation.path)
        self.assertIn("confirmed", violation.message)

    def test_orphan_tag_is_warning_at_tag_line(self):
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "confirmed")))
        self.tagged("INV-CLAIM-001", "INV-CLAIM-009")
        report = self.check()
        self.assertEqual(report.violations, [])
        warning = self.assert_warning(report, "INV-CLAIM-009", count=1)
        self.assertIn("ClaimTest.kt:7", warning)

    def test_orphan_tag_of_unknown_context_is_warning(self):
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "confirmed")))
        self.tagged("INV-CLAIM-001", "INV-BILLING-001")
        self.assert_warning(self.check(), "INV-BILLING-001")

    def test_proposed_with_tag_is_warning(self):
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "proposed")))
        self.tagged("INV-CLAIM-001")
        report = self.check()
        self.assertEqual(report.violations, [])
        warning = self.assert_warning(report, "INV-CLAIM-001", count=1)
        self.assertIn("proposed", warning)

    def test_warnings_do_not_become_violations(self):
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "proposed")))
        self.tagged("INV-CLAIM-001", "INV-CLAIM-009")
        report = self.check()
        self.assertEqual(report.violations, [])
        self.assertEqual(len(report.warnings), 2, self.warnings(report))


# ---------------------------------------------------------------------------
# 태그 스캔 범위와 한계 (P3-D4 · 정본 §4.4)
# ---------------------------------------------------------------------------

class TestTagScan(InvariantTestCase):
    def setUp(self):
        super().setUp()
        self.arch()
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "confirmed")))

    def assert_seen(self, seen=True):
        """태그가 관측됐는가. 검사 불능이 '위반 없음'으로 보이는 것을 함께 막는다."""
        report = self.check()
        self.assertEqual(self.messages(report), [])
        self.assertEqual(report.blocked, "")
        self.assertGreater(report.test_sources, 0)
        if seen:
            self.assertEqual(report.violations, [], [v.message for v in report.violations])
            self.assertEqual([t.id for t in report.tags], ["INV-CLAIM-001"])
        else:
            self.assertEqual([v.invariant_id for v in report.violations], ["INV-CLAIM-001"])

    def test_src_test_directory_is_scanned(self):
        self.tagged("INV-CLAIM-001", relpath="src/test/kotlin/com/acme/ClaimTest.kt")
        self.assert_seen()

    def test_plain_test_directory_is_scanned(self):
        self.tagged("INV-CLAIM-001", relpath="test/com/acme/ClaimTest.java")
        self.assert_seen()

    def test_declared_test_location_is_scanned(self):
        """`itest/kotlin`에는 `test` 세그먼트가 없다 — 선언을 읽어야만 스캔된다."""
        self.arch(ITEST_ARCH)
        self.tagged("INV-CLAIM-001", relpath="itest/kotlin/com/acme/ArchTest.kt")
        self.assert_seen()

    def test_main_source_tag_is_not_a_test_tag(self):
        self.tagged("INV-CLAIM-001", relpath="src/main/kotlin/com/acme/Claim.kt")
        self.empty_tests()
        self.assert_seen(seen=False)

    def test_test_package_under_src_main_is_not_a_test_source(self):
        """`src/main/.../test/`는 프로덕션 소스다.

        여기 태그가 세어지면 프로덕션 코드의 리터럴이 confirmed를 충족시켜 exit 0이 난다 —
        결정적 검사의 침묵 통과 채널이다(P3-D4의 스캔 범위는 테스트 소스로 한정된다).
        """
        self.tagged("INV-CLAIM-001", relpath="src/main/kotlin/com/acme/test/Helper.kt")
        self.empty_tests()
        report = self.check()
        self.assertEqual(report.test_sources, 1)      # empty_tests의 것 하나뿐
        self.assertEqual(report.tags, [])
        self.assertEqual([v.invariant_id for v in report.violations], ["INV-CLAIM-001"])

    def test_build_output_is_not_scanned(self):
        self.tagged("INV-CLAIM-001", relpath="build/test/kotlin/com/acme/ClaimTest.kt")
        self.empty_tests()
        self.assert_seen(seen=False)

    def test_multiple_tags_on_one_line_are_seen(self):
        self.src("src/test/kotlin/com/acme/ClaimTest.kt",
                 'package com.acme\n\n@Tag("INV-CLAIM-001") @Tag("INV-CLAIM-009")\n'
                 "fun test() {}\n")
        report = self.check()
        self.assertEqual(report.violations, [])
        self.assert_warning(report, "INV-CLAIM-009")

    def test_named_value_argument_is_a_literal_tag(self):
        self.tagged("INV-CLAIM-001", form='@Tag(value = "{id}")')
        self.assert_seen()

    def test_constant_reference_is_invisible(self):
        """정본 §4.4 한계 — 상수 간접 참조는 보이지 않는다(그래서 위반이 남는다)."""
        self.tagged("INV-CLAIM-001", form="@Tag(INV_CLAIM_001)")
        self.assert_seen(seen=False)

    def test_fully_qualified_annotation_is_invisible(self):
        self.tagged("INV-CLAIM-001", form='@org.junit.jupiter.api.Tag("{id}")')
        self.assert_seen(seen=False)

    def test_unreadable_test_source_makes_a_false_violation_and_is_reported(self):
        """읽지 못한 테스트 파일의 태그는 안 보인다 — 그 결과가 거짓 위반이다.

        검사는 이 사각지대를 없애지 못하므로 render의 고지가 유일한 방어선이다. 고지가
        빠지면 사용자는 태그를 지운 적도 없는데 위반을 보고 문서를 고치게 된다.
        """
        path = self.tmpdir / "src/test/kotlin/com/acme/ClaimTest.kt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'@Tag("INV-CLAIM-001")\n\xff\xfe\n')
        report = self.check()
        self.assertEqual(report.test_sources, 1)
        self.assertEqual(report.tags, [])
        self.assertEqual([v.invariant_id for v in report.violations], ["INV-CLAIM-001"])
        self.assertEqual(report.unreadable, ["src/test/kotlin/com/acme/ClaimTest.kt"])
        self.assertTrue(any("읽지 못한 테스트 소스" in line for line in render(report)),
                        render(report))

    def test_limitation_note_is_always_rendered(self):
        self.tagged("INV-CLAIM-001")
        self.assertIn(LIMITATION_NOTE, render(self.check()))

    def test_overlapping_project_paths_do_not_double_count(self):
        self.arch(OVERLAP_ARCH)
        self.tagged("INV-CLAIM-001", relpath="second/src/test/kotlin/com/acme/ClaimTest.kt")
        report = self.check()
        self.assertEqual(report.test_sources, 1)
        self.assertEqual(len(report.tags), 1, report.tags)

    def test_every_declared_project_is_walked_and_missing_paths_are_skipped(self):
        """태그가 둘째 프로젝트에만 있어도 보여야 하고, 없는 경로가 스캔을 멈추면 안 된다."""
        self.arch(TWO_PROJECT_ARCH)
        self.tagged("INV-CLAIM-001", relpath="second/src/test/kotlin/com/acme/ClaimTest.kt")
        report = self.check()
        self.assertEqual(self.messages(report), [])
        self.assertEqual(report.violations, [])
        self.assertEqual(report.test_sources, 1)


# ---------------------------------------------------------------------------
# 검사 불능 — 테스트 소스 0건 (P3-D3)
# ---------------------------------------------------------------------------

class TestBlocked(InvariantTestCase):
    def test_no_test_source_blocks_the_check(self):
        self.arch()
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "confirmed")))
        report = self.check()
        self.assertIn("검사 불능", report.blocked)
        self.assertEqual(report.violations, [])
        self.assertEqual(report.checked, 0)

    def test_blocked_reason_names_the_confirmed_count(self):
        self.arch()
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "confirmed"),
                                     row("INV-CLAIM-002", "confirmed"),
                                     row("INV-CLAIM-003", "proposed")))
        self.assertIn("2건", self.check().blocked)

    def test_blocked_is_rendered(self):
        self.arch()
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "confirmed")))
        self.assertTrue(any("검사 불능" in line for line in render(self.check())))

    def test_empty_test_source_tree_still_counts_as_sources(self):
        self.arch()
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "confirmed")))
        self.empty_tests()
        report = self.check()
        self.assertEqual(report.blocked, "")
        self.assertEqual(len(report.violations), 1)


# ---------------------------------------------------------------------------
# --context 필터
# ---------------------------------------------------------------------------

class TestContextFilter(InvariantTestCase):
    def setUp(self):
        super().setUp()
        self.arch(HYPHEN_ARCH)
        self.doc("core", domain_doc(row("INV-CORE-001", "confirmed"), title="core"))
        self.doc("core-api", domain_doc(row("INV-CORE-API-001", "confirmed"),
                                        title="core-api"))
        self.empty_tests()

    def test_filter_narrows_the_corpus(self):
        report = self.check(context="core-api")
        self.assertEqual([i.id for i in report.invariants], ["INV-CORE-API-001"])
        self.assertEqual([v.invariant_id for v in report.violations], ["INV-CORE-API-001"])

    def test_unfiltered_run_sees_both(self):
        self.assertEqual(sorted(i.id for i in self.check().invariants),
                         ["INV-CORE-001", "INV-CORE-API-001"])

    def test_other_context_tag_is_not_an_orphan_in_filtered_run(self):
        self.tagged("INV-CORE-001", "INV-CORE-API-001")
        report = self.check(context="core-api")
        self.assertEqual(report.violations, [])
        self.assertEqual(report.warnings, [], self.warnings(report))

    def test_unresolvable_tag_is_an_orphan_even_when_filtered(self):
        self.tagged("INV-CORE-API-001", "INV-BILLING-001")
        self.assert_warning(self.check(context="core-api"), "INV-BILLING-001")

    def test_undeclared_context_argument_is_error(self):
        report = self.check(context="billing")
        self.assert_error(report, "billing")


# ---------------------------------------------------------------------------
# 해석 불가 — ARCHITECTURE.md 자체의 오류
# ---------------------------------------------------------------------------

class TestUnparseable(InvariantTestCase):
    def test_architecture_parse_error_is_reported(self):
        self.arch(HEAD + "\n## 컨텍스트: claim\n- 분류: core\n")
        report = self.check()
        self.assertTrue(report.errors)
        self.assertTrue(all(e.path == str(self.arch_path) for e in report.errors),
                        self.messages(report))

    def test_missing_architecture_file_is_error(self):
        report = self.check()
        self.assertTrue(report.errors)


# ---------------------------------------------------------------------------
# CLI — exit 계약과 --json
# ---------------------------------------------------------------------------

class TestCli(InvariantTestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args],
                              capture_output=True, text=True)

    def test_exit_zero_when_clean(self):
        self.arch()
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "confirmed")))
        self.tagged("INV-CLAIM-001")
        result = self.run_cli(str(self.arch_path))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(LIMITATION_NOTE, result.stdout)

    def test_exit_one_when_violation(self):
        self.arch()
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "confirmed")))
        self.empty_tests()
        result = self.run_cli(str(self.arch_path))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("INV-CLAIM-001", result.stdout)

    def test_exit_one_when_blocked(self):
        self.arch()
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "confirmed")))
        result = self.run_cli(str(self.arch_path))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("검사 불능", result.stdout)

    def test_exit_two_when_document_error(self):
        self.arch()
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "wip")))
        self.empty_tests()
        result = self.run_cli(str(self.arch_path))
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("wip", result.stderr)

    def test_exit_two_when_architecture_error(self):
        self.arch(HEAD + "\n## 컨텍스트: claim\n- 분류: core\n")
        result = self.run_cli(str(self.arch_path))
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_exit_two_on_usage_error(self):
        self.assertEqual(self.run_cli().returncode, 2)
        self.assertEqual(self.run_cli(str(self.arch_path), "--context").returncode, 2)
        self.assertEqual(self.run_cli(str(self.arch_path), "--bogus").returncode, 2)

    def test_warnings_do_not_change_the_exit_code(self):
        self.arch()
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "proposed")))
        self.tagged("INV-CLAIM-001")
        result = self.run_cli(str(self.arch_path))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("경고", result.stdout)

    def test_context_option_is_accepted(self):
        self.arch(HYPHEN_ARCH)
        self.doc("core", domain_doc(row("INV-CORE-001", "confirmed"), title="core"))
        self.doc("core-api", domain_doc(row("INV-CORE-API-001", "confirmed"),
                                        title="core-api"))
        self.tagged("INV-CORE-API-001")
        result = self.run_cli(str(self.arch_path), "--context", "core-api")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_json_structure(self):
        self.arch()
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "confirmed"),
                                     row("INV-CLAIM-002", "proposed")))
        self.tagged("INV-CLAIM-002", "INV-CLAIM-009")
        result = self.run_cli(str(self.arch_path), "--json")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual([v["invariant_id"] for v in payload["violations"]], ["INV-CLAIM-001"])
        self.assertEqual(payload["checked"], 2)
        self.assertEqual(payload["confirmed"], 1)
        self.assertEqual(payload["proposed"], 1)
        self.assertEqual(len(payload["warnings"]), 2)
        self.assertEqual([i["id"] for i in payload["invariants"]],
                         ["INV-CLAIM-001", "INV-CLAIM-002"])
        self.assertEqual(payload["blocked"], "")
        self.assertEqual(payload["limitation"], LIMITATION_NOTE)

    def test_json_carries_the_description_for_apply(self):
        self.arch()
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "confirmed", "금액은 0보다 크다")))
        self.empty_tests()
        payload = json.loads(self.run_cli(str(self.arch_path), "--json").stdout)
        self.assertEqual(payload["invariants"][0]["description"], "금액은 0보다 크다")

    def test_json_reports_blocked(self):
        self.arch()
        self.doc("claim", domain_doc(row("INV-CLAIM-001", "confirmed")))
        result = self.run_cli(str(self.arch_path), "--json")
        self.assertEqual(result.returncode, 1)
        self.assertIn("검사 불능", json.loads(result.stdout)["blocked"])


if __name__ == "__main__":
    unittest.main()
