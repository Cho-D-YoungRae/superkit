"""parse_domain.py — DOMAIN.md 단층 파서의 계약 테스트.

이 파서가 이후 모든 스크립트(check_imports·check_invariants·collect_signals)의 유일한
해석기이므로, 여기서 고정하는 것은 "파싱이 된다"가 아니라 **계약**이다: 공개 시그니처,
기본 패키지 규약, 격리 allow-list의 방향 의미, 그리고 침묵하지 않아야 할 오류 목록.
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import parse_domain as pd
from parse_domain import (LocatedError, Relation, context_packages, format_error,
                          isolation_allowlist, parse_domain)

ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = Path(__file__).resolve().parent
FIXTURES = TESTS_DIR / "fixtures" / "domain"
SCRIPT = ROOT / "scripts" / "parse_domain.py"

MINIMAL = (FIXTURES / "minimal.md").read_text(encoding="utf-8")


class DomainTextCase(unittest.TestCase):
    """문서 텍스트를 임시 파일에 써서 파싱하는 공통 도우미.

    임시 디렉터리는 시스템 temp에 만들고 addCleanup으로 지운다 — 실패한 테스트도 흔적을
    남기지 않는다.
    """

    def _write(self, text, name="DOMAIN.md"):
        tmpdir = Path(tempfile.mkdtemp(prefix="superdomain-")).resolve()
        self.addCleanup(shutil.rmtree, tmpdir, True)
        path = tmpdir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def _parse_text(self, text):
        return parse_domain(self._write(text))

    def _messages(self, domain):
        return [error.message for error in domain.errors]

    def assertHasError(self, domain, needle):
        messages = self._messages(domain)
        self.assertTrue(any(needle in message for message in messages),
                        f"'{needle}'을(를) 담은 오류가 없습니다: {messages}")


class TestParseDomainMinimal(DomainTextCase):
    """가장 작은 완본 — 프로젝트 1·컨텍스트 1, 선택 라벨 전무."""

    def test_minimal_parses_without_errors(self):
        d = parse_domain(FIXTURES / "minimal.md")
        self.assertEqual(d.errors, [])
        self.assertEqual([c.name for c in d.contexts], ["claim"])

    def test_minimal_project_fields(self):
        d = parse_domain(FIXTURES / "minimal.md")
        project = d.projects[0]
        self.assertEqual((project.name, project.path, project.base_package),
                         ("backend", ".", "com.acme"))
        self.assertEqual(project.line, 4)

    def test_single_project_is_auto_attributed(self):
        # 프로젝트가 하나뿐이면 '- 프로젝트:' 라벨 없이도 그 프로젝트에 귀속된다.
        d = parse_domain(FIXTURES / "minimal.md")
        self.assertEqual(d.contexts[0].project, "backend")
        self.assertEqual(d.contexts[0].classification, "core")
        self.assertEqual(d.contexts[0].packages, [])
        self.assertEqual(d.contexts[0].patterns, [])
        self.assertEqual(d.contexts[0].relations, [])

    def test_default_package_convention(self):
        d = parse_domain(FIXTURES / "minimal.md")
        self.assertEqual(context_packages(d, d.contexts[0]), ["com.acme.claim.."])

    def test_missing_file_is_error_not_exception(self):
        d = parse_domain(TESTS_DIR / "없는파일-DOMAIN.md")
        self.assertHasError(d, "읽을 수 없습니다")
        self.assertEqual(d.projects, [])


class TestParseDomainFull(DomainTextCase):
    """프로젝트 2·컨텍스트 3, 명시 패키지·복수 위치·관계 표·생성 구역이 있는 완본."""

    def setUp(self):
        self.domain = parse_domain(FIXTURES / "full.md")
        self.by_name = {c.name: c for c in self.domain.contexts}

    def test_full_parses_without_errors(self):
        self.assertEqual(self.domain.errors, [])
        self.assertEqual([p.name for p in self.domain.projects], ["backend", "batch"])
        self.assertEqual([c.name for c in self.domain.contexts], ["claim", "admin", "billing"])

    def test_context_project_attribution(self):
        self.assertEqual(self.by_name["claim"].project, "backend")
        self.assertEqual(self.by_name["billing"].project, "batch")

    def test_patterns_label_is_a_comma_list(self):
        self.assertEqual(self.by_name["claim"].patterns, ["cqrs", "outbox"])

    def test_explicit_and_multi_packages(self):
        self.assertEqual(context_packages(self.domain, self.by_name["claim"]),
                         ["com.acme.claiming.."])
        self.assertEqual(len(context_packages(self.domain, self.by_name["billing"])), 2)
        self.assertEqual(context_packages(self.domain, self.by_name["billing"]),
                         ["com.acme.web.billing..", "com.acme.batch.billing.."])

    def test_default_convention_uses_owning_project_base_package(self):
        # admin은 '- 패키지:'가 없으므로 귀속 프로젝트(backend)의 기본 패키지를 쓴다.
        self.assertEqual(context_packages(self.domain, self.by_name["admin"]),
                         ["com.acme.admin.."])

    def test_relation_row_is_parsed_with_line_number(self):
        relations = self.by_name["claim"].relations
        self.assertEqual(len(relations), 1)
        relation = relations[0]
        self.assertEqual((relation.partner, relation.kind, relation.contract),
                         ("admin", "customer-supplier", "claim-events-v1"))
        lines = (FIXTURES / "full.md").read_text(encoding="utf-8").split("\n")
        self.assertIn("admin", lines[relation.line - 1])
        self.assertTrue(lines[relation.line - 1].startswith("|"))

    def test_isolation_allowlist_from_relations(self):
        self.assertIn("admin", isolation_allowlist(self.domain)["claim"])

    def test_generated_zone_does_not_change_the_parse(self):
        # 생성 구역(마커 2줄 + mermaid)을 통째로 들어내고 파싱한 결과와 같아야 한다.
        text = (FIXTURES / "full.md").read_text(encoding="utf-8")
        without = text[:text.index("## 컨텍스트 맵")] + text[text.index("## 컨텍스트: claim"):]
        stripped = self._parse_text(without)
        self.assertEqual(stripped.errors, [])
        shape = lambda d: [(c.name, c.project, c.classification, c.packages,
                            [(r.partner, r.kind, r.contract) for r in c.relations])
                           for c in d.contexts]
        self.assertEqual(shape(stripped), shape(self.domain))
        self.assertEqual([(p.name, p.path, p.base_package) for p in stripped.projects],
                         [(p.name, p.path, p.base_package) for p in self.domain.projects])


class TestGeneratedZoneInsideSection(DomainTextCase):
    """생성 구역 마커는 섹션 상태를 건드리지 않는다 — 그 뒤의 라벨이 여전히 같은 컨텍스트에 붙는다."""

    ZONE = ("<!-- superdomain:generated:structure:claim -->\n"
            "```mermaid\ngraph LR\n  a --> b\n```\n"
            "<!-- /superdomain:generated -->\n")

    def test_label_after_zone_still_binds_to_the_same_context(self):
        d = self._parse_text(MINIMAL + self.ZONE + "- 패키지: com.acme.claiming..\n")
        self.assertEqual(d.errors, [])
        self.assertEqual(len(d.contexts), 1)
        self.assertEqual(d.contexts[0].packages, ["com.acme.claiming.."])

    def test_relation_table_after_zone_still_binds_to_the_same_context(self):
        text = (MINIMAL + "\n## 컨텍스트: admin\n- 분류: generic\n\n### 관계\n"
                + self.ZONE
                + "| 상대 | 유형 | 계약 |\n|---|---|---|\n| claim | conformist | - |\n")
        d = self._parse_text(text)
        self.assertEqual(d.errors, [])
        self.assertEqual([r.partner for r in d.contexts[1].relations], ["claim"])


class TestParenComments(DomainTextCase):
    """라벨 값 뒤의 괄호 주석은 값에서 제거된다(기존 파서에서 이관한 동작)."""

    def test_classification_comment_stripped(self):
        text = MINIMAL.replace("- 분류: core", "- 분류: core   (core | supporting | generic)")
        d = self._parse_text(text)
        self.assertEqual(d.errors, [])
        self.assertEqual(d.contexts[0].classification, "core")

    def test_fixture_comment_stripped(self):
        # full.md의 '- 분류: core (core | supporting | generic)'도 같은 경로를 탄다.
        d = parse_domain(FIXTURES / "full.md")
        self.assertEqual(d.contexts[0].classification, "core")

    def test_project_label_comment_stripped(self):
        text = MINIMAL.replace("- 기본 패키지: com.acme", "- 기본 패키지: com.acme  (루트 패키지)")
        d = self._parse_text(text)
        self.assertEqual(d.errors, [])
        self.assertEqual(d.projects[0].base_package, "com.acme")

    def test_package_label_comment_stripped(self):
        text = MINIMAL + "- 패키지: com.acme.claiming..   (역사적 이름)\n"
        d = self._parse_text(text)
        self.assertEqual(d.errors, [])
        self.assertEqual(d.contexts[0].packages, ["com.acme.claiming.."])


class TestPackageLabel(DomainTextCase):
    """`- 패키지:` 값은 쉼표 목록이고 언제나 `..` 접미 접두 패턴으로 정규화된다."""

    def test_missing_dotdot_suffix_is_added(self):
        d = self._parse_text(MINIMAL + "- 패키지: com.acme.claiming\n")
        self.assertEqual(d.errors, [])
        self.assertEqual(d.contexts[0].packages, ["com.acme.claiming.."])

    def test_trailing_single_dot_is_normalized(self):
        d = self._parse_text(MINIMAL + "- 패키지: com.acme.claiming.\n")
        self.assertEqual(d.errors, [])
        self.assertEqual(d.contexts[0].packages, ["com.acme.claiming.."])

    def test_multiple_packages_keep_document_order(self):
        d = self._parse_text(MINIMAL + "- 패키지: com.acme.web.claim, com.acme.batch.claim..\n")
        self.assertEqual(d.errors, [])
        self.assertEqual(d.contexts[0].packages,
                         ["com.acme.web.claim..", "com.acme.batch.claim.."])

    def test_empty_item_is_error(self):
        d = self._parse_text(MINIMAL + "- 패키지: com.acme.claim.., , com.acme.other..\n")
        self.assertHasError(d, "빈 항목")

    def test_duplicate_item_is_error(self):
        d = self._parse_text(MINIMAL + "- 패키지: com.acme.claim.., com.acme.claim\n")
        self.assertHasError(d, "중복")

    def test_context_packages_without_base_package_raises(self):
        # '기본 패키지'가 없으면 기본 규약을 만들 수 없다 — 조용히 빈 목록을 주지 않는다.
        text = MINIMAL.replace("- 기본 패키지: com.acme\n", "")
        d = self._parse_text(text)
        self.assertHasError(d, "기본 패키지")
        with self.assertRaises(LocatedError):
            context_packages(d, d.contexts[0])


class TestPackageOverlap(DomainTextCase):
    """컨텍스트 패키지가 서로 접두로 겹치면 소스의 귀속이 모호해진다 — 오류다."""

    HEAD = ("# 샘플 — Domain\n<!-- superdomain:template v1 -->\n\n"
            "## 프로젝트: backend\n- 경로: .\n- 기본 패키지: com.acme\n")

    def _two_contexts(self, first, second):
        return (self.HEAD
                + f"\n## 컨텍스트: {first[0]}\n- 분류: core\n"
                + (f"- 패키지: {first[1]}\n" if first[1] else "")
                + f"\n## 컨텍스트: {second[0]}\n- 분류: supporting\n"
                + (f"- 패키지: {second[1]}\n" if second[1] else ""))

    def test_nested_prefix_is_error(self):
        d = self._parse_text(self._two_contexts(("claim", "com.acme.claim.."),
                                                ("sub", "com.acme.claim.sub..")))
        self.assertHasError(d, "겹칩니다")

    def test_identical_package_is_error(self):
        d = self._parse_text(self._two_contexts(("claim", "com.acme.shared.."),
                                                ("admin", "com.acme.shared..")))
        self.assertHasError(d, "겹칩니다")

    def test_default_convention_against_explicit_overlap_is_error(self):
        # claim은 기본 규약으로 com.acme.claim.., admin은 그 안쪽을 명시 — 겹친다.
        d = self._parse_text(self._two_contexts(("claim", None),
                                                ("admin", "com.acme.claim.inner..")))
        self.assertHasError(d, "겹칩니다")

    def test_sibling_name_sharing_a_prefix_is_not_overlap(self):
        # 'claim'과 'claiming'은 문자열 접두는 겹치지만 패키지 세그먼트 경계가 다르다.
        d = self._parse_text(self._two_contexts(("claim", None), ("claiming", None)))
        self.assertEqual(d.errors, [])

    def test_overlap_across_projects_is_caught(self):
        # 겹침 판정은 프로젝트 경계를 가리지 않는다 — 귀속은 패키지 접두로만 이뤄지기 때문이다.
        text = (self.HEAD
                + "\n## 프로젝트: batch\n- 경로: batch\n- 기본 패키지: com.acme.batch\n"
                + "\n## 컨텍스트: claim\n- 프로젝트: backend\n- 분류: core\n"
                + "- 패키지: com.acme.batch.claim.inner..\n"
                + "\n## 컨텍스트: work\n- 프로젝트: batch\n- 분류: supporting\n"
                + "- 패키지: com.acme.batch.claim..\n")
        d = self._parse_text(text)
        self.assertHasError(d, "겹칩니다")


class TestIsolationAllowlist(DomainTextCase):
    """관계 표가 여는 것은 **쌍**이다 — 방향을 구분하지 않는다(구 `_derive_context_isolation` 의미)."""

    def _two_related(self):
        return (MINIMAL
                + "\n## 컨텍스트: admin\n- 분류: generic\n"
                + "\n### 관계\n| 상대 | 유형 | 계약 |\n|---|---|---|\n"
                + "| claim | conformist | - |\n")

    def test_declared_direction_is_open(self):
        d = self._parse_text(self._two_related())
        self.assertEqual(d.errors, [])
        self.assertIn("claim", isolation_allowlist(d)["admin"])

    def test_reverse_direction_is_also_open(self):
        # 허용 단위가 쌍이므로 한쪽 선언이 양쪽을 연다.
        d = self._parse_text(self._two_related())
        self.assertIn("admin", isolation_allowlist(d)["claim"])

    def test_keys_are_exactly_the_declared_contexts(self):
        d = parse_domain(FIXTURES / "full.md")
        allowlist = isolation_allowlist(d)
        self.assertEqual(set(allowlist), {"claim", "admin", "billing"})
        self.assertEqual(allowlist["billing"], frozenset())

    def test_undeclared_partner_does_not_become_a_key(self):
        # 오타 난 상대는 validate가 오류로 잡는다. allowlist까지 유령 키를 만들면
        # 소비자가 그것을 컨텍스트 목록으로 착각한다.
        text = MINIMAL + "\n### 관계\n| 상대 | 유형 | 계약 |\n|---|---|---|\n| ghost | conformist | - |\n"
        d = self._parse_text(text)
        allowlist = isolation_allowlist(d)
        self.assertEqual(set(allowlist), {"claim"})
        self.assertEqual(allowlist["claim"], frozenset())

    def test_values_are_frozensets(self):
        d = parse_domain(FIXTURES / "full.md")
        for value in isolation_allowlist(d).values():
            self.assertIsInstance(value, frozenset)


class TestValidationRequiredLabels(DomainTextCase):
    """필수 라벨은 프로젝트 `경로`·`기본 패키지`, 컨텍스트 `분류` 셋뿐이다."""

    def test_project_missing_path_is_error(self):
        d = self._parse_text(MINIMAL.replace("- 경로: .\n", ""))
        self.assertHasError(d, "'경로'")

    def test_project_missing_base_package_is_error(self):
        d = self._parse_text(MINIMAL.replace("- 기본 패키지: com.acme\n", ""))
        self.assertHasError(d, "'기본 패키지'")

    def test_context_missing_classification_is_error(self):
        d = self._parse_text(MINIMAL.replace("- 분류: core\n", ""))
        self.assertHasError(d, "'분류'")

    def test_no_project_section_is_error(self):
        text = "# 샘플 — Domain\n<!-- superdomain:template v1 -->\n\n## 컨텍스트: claim\n- 분류: core\n"
        d = self._parse_text(text)
        self.assertHasError(d, "프로젝트 섹션이 없습니다")

    def test_multiple_projects_require_explicit_attribution(self):
        text = MINIMAL + "\n## 프로젝트: batch\n- 경로: batch\n- 기본 패키지: com.acme.batch\n"
        d = self._parse_text(text)
        self.assertHasError(d, "프로젝트가 여러 개")

    def test_unknown_project_reference_is_error(self):
        d = self._parse_text(MINIMAL.replace("- 분류: core", "- 프로젝트: 없는프로젝트\n- 분류: core"))
        self.assertHasError(d, "없는프로젝트")


class TestValidationValues(DomainTextCase):
    """정규 값 라벨과 상호 참조 무결성."""

    def test_bad_classification_is_error(self):
        d = self._parse_text(MINIMAL.replace("- 분류: core", "- 분류: kernel"))
        self.assertHasError(d, "kernel")

    def test_classification_error_points_at_its_own_line(self):
        d = self._parse_text(MINIMAL.replace("- 분류: core", "- 분류: kernel"))
        error = next(e for e in d.errors if "kernel" in e.message)
        self.assertEqual(error.line, 9)

    def test_all_canonical_classifications_accepted(self):
        for value in pd.CLASSIFICATIONS:
            d = self._parse_text(MINIMAL.replace("- 분류: core", f"- 분류: {value}"))
            self.assertEqual(d.errors, [], value)

    def test_unknown_relation_partner_is_error(self):
        text = MINIMAL + "\n### 관계\n| 상대 | 유형 | 계약 |\n|---|---|---|\n| ghost | conformist | - |\n"
        d = self._parse_text(text)
        self.assertTrue(any("ghost" in e.message for e in d.errors), self._messages(d))

    def test_unknown_relation_kind_is_error(self):
        text = (MINIMAL + "\n## 컨텍스트: admin\n- 분류: generic\n"
                + "\n### 관계\n| 상대 | 유형 | 계약 |\n|---|---|---|\n| claim | 친하게지냄 | - |\n")
        d = self._parse_text(text)
        self.assertHasError(d, "친하게지냄")

    def test_duplicate_project_name_is_error(self):
        text = MINIMAL + "\n## 프로젝트: backend\n- 경로: other\n- 기본 패키지: com.other\n"
        d = self._parse_text(text)
        self.assertHasError(d, "프로젝트 이름 'backend'")

    def test_duplicate_context_name_is_error(self):
        text = MINIMAL + "\n## 컨텍스트: claim\n- 분류: generic\n"
        d = self._parse_text(text)
        self.assertHasError(d, "컨텍스트 이름 'claim'")


class TestRetiredLabels(DomainTextCase):
    """구 템플릿의 라벨 6종은 침묵으로 무시하지 않고 명시적으로 거부한다."""

    RETIRED = ["스타일", "모듈 구성", "규칙 예외", "이행", "프로파일", "아키텍처 테스트 위치"]

    def test_style_label_is_rejected(self):
        d = self._parse_text(MINIMAL + "- 스타일: hexagonal\n")
        self.assertTrue(any("스타일" in e.message for e in d.errors), self._messages(d))

    def test_every_retired_label_is_rejected(self):
        for label in self.RETIRED:
            d = self._parse_text(MINIMAL + f"- {label}: 아무값\n")
            self.assertHasError(d, f"'{label}'")

    def test_retired_project_label_is_rejected_in_project_section(self):
        text = MINIMAL.replace("- 기본 패키지: com.acme",
                               "- 프로파일: kotlin-spring\n- 기본 패키지: com.acme")
        d = self._parse_text(text)
        self.assertHasError(d, "'프로파일'")

    def test_rejection_message_points_at_the_new_template(self):
        d = self._parse_text(MINIMAL + "- 이행: layered-simple → hexagonal\n")
        self.assertHasError(d, "domain-template.md")

    def test_other_unknown_labels_are_still_ignored(self):
        d = self._parse_text(MINIMAL + "- 담당팀: 청구스쿼드\n")
        self.assertEqual(d.errors, [])


class TestTemplateMarker(DomainTextCase):
    """마커가 없으면 거부하고, 파서가 아는 것보다 높은 버전도 거부한다(침묵 금지)."""

    def test_marker_constants(self):
        self.assertEqual(pd.MARKER_TEMPLATE, "superdomain:template")
        self.assertEqual(pd.TEMPLATE_VERSION, "v1")

    def test_missing_marker_is_error(self):
        d = self._parse_text(MINIMAL.replace("<!-- superdomain:template v1 -->\n", ""))
        self.assertHasError(d, "템플릿 마커")
        self.assertHasError(d, "없습니다")

    def test_marker_without_version_is_a_format_error_not_a_missing_error(self):
        # 마커가 '깨진 것'과 '아예 없는 것'은 고칠 자리가 다르다.
        d = self._parse_text(MINIMAL.replace("<!-- superdomain:template v1 -->",
                                             "<!-- superdomain:template -->"))
        self.assertHasError(d, "형식이 올바르지 않습니다")
        self.assertFalse(any("없습니다" in e.message and "템플릿 마커" in e.message
                             for e in d.errors), self._messages(d))

    def test_malformed_marker_error_points_at_that_line(self):
        d = self._parse_text(MINIMAL.replace("<!-- superdomain:template v1 -->",
                                             "<!-- superdomain:template v1 --> 초안"))
        error = next(e for e in d.errors if "형식이 올바르지 않습니다" in e.message)
        self.assertEqual(error.line, 2)

    def test_future_version_is_rejected(self):
        d = self._parse_text(MINIMAL.replace("template v1", "template v2"))
        self.assertHasError(d, "v2")

    def test_future_version_error_points_at_the_marker_line(self):
        d = self._parse_text(MINIMAL.replace("template v1", "template v9"))
        error = next(e for e in d.errors if "v9" in e.message)
        self.assertEqual(error.line, 2)

    def test_current_version_is_accepted(self):
        self.assertEqual(self._parse_text(MINIMAL).errors, [])


class TestContextNameSegment(DomainTextCase):
    """컨텍스트 이름은 기본 규약의 패키지 세그먼트 자리에 그대로 들어간다(구 `_check_context_segment`).

    성립하지 않는 세그먼트를 통과시키면 그 컨텍스트의 격리 규칙이 0건을 검사한 채 조용히 통과한다.
    """

    def _with_name(self, name, package=None):
        text = MINIMAL.replace("## 컨텍스트: claim", f"## 컨텍스트: {name}")
        return self._parse_text(text + (f"- 패키지: {package}\n" if package else ""))

    def test_hyphenated_name_is_error(self):
        d = self._with_name("order-mgmt")
        self.assertHasError(d, "order-mgmt")
        self.assertHasError(d, "패키지 세그먼트")

    def test_dotted_name_is_error(self):
        self.assertHasError(self._with_name("order.mgmt"), "패키지 세그먼트")

    def test_name_starting_with_digit_is_error(self):
        self.assertHasError(self._with_name("2fa"), "패키지 세그먼트")

    def test_non_ascii_name_is_error(self):
        self.assertHasError(self._with_name("청구"), "패키지 세그먼트")

    def test_explicit_package_skips_the_check(self):
        # 명시 패키지가 있으면 이름은 패턴에 전혀 들어가지 않는다 — 검사하지 않는다.
        d = self._with_name("order-mgmt", "com.acme.order.management..")
        self.assertEqual(d.errors, [])

    def test_valid_names_pass(self):
        for name in ("claim", "claim2", "_internal", "orderMgmt"):
            self.assertEqual(self._with_name(name).errors, [], name)

    def test_broken_name_would_otherwise_produce_a_dead_pattern(self):
        # 검사가 없으면 이 패턴이 조용히 만들어진다 — 그것이 이 오류가 막는 상태다.
        d = self._with_name("order-mgmt")
        self.assertEqual(context_packages(d, d.contexts[0]), ["com.acme.order-mgmt.."])


class TestBasePackage(DomainTextCase):
    """`기본 패키지`도 패키지 접두다 — `- 패키지:`와 같은 규칙으로 정규화하고 검증한다."""

    def _with_base(self, value):
        return self._parse_text(MINIMAL.replace("- 기본 패키지: com.acme",
                                                f"- 기본 패키지: {value}"))

    def test_trailing_dot_is_normalized(self):
        d = self._with_base("com.acme.")
        self.assertEqual(d.errors, [])
        self.assertEqual(d.projects[0].base_package, "com.acme")
        self.assertEqual(context_packages(d, d.contexts[0]), ["com.acme.claim.."])

    def test_trailing_double_dot_is_normalized(self):
        d = self._with_base("com.acme..")
        self.assertEqual(d.errors, [])
        self.assertEqual(context_packages(d, d.contexts[0]), ["com.acme.claim.."])

    def test_inner_empty_segment_is_error(self):
        self.assertHasError(self._with_base("com..acme"), "유효한 패키지가 아닙니다")

    def test_leading_dot_is_error(self):
        self.assertHasError(self._with_base(".com.acme"), "유효한 패키지가 아닙니다")

    def test_hyphenated_segment_is_error(self):
        self.assertHasError(self._with_base("com.acme-corp"), "유효한 패키지가 아닙니다")

    def test_error_points_at_the_label_line(self):
        error = next(e for e in self._with_base("com..acme").errors
                     if "유효한 패키지가 아닙니다" in e.message)
        self.assertEqual(error.line, 6)


class TestDuplicateLabelLines(DomainTextCase):
    """한 섹션에 같은 라벨이 두 줄이면 뒤가 앞을 조용히 덮어쓴다 — 오류로 막는다."""

    def test_duplicate_package_label_is_error(self):
        d = self._parse_text(MINIMAL + "- 패키지: com.acme.web.claim..\n"
                                       "- 패키지: com.acme.batch.claim..\n")
        self.assertHasError(d, "두 번 나타납니다")

    def test_first_value_is_kept_not_the_last(self):
        d = self._parse_text(MINIMAL + "- 패키지: com.acme.web.claim..\n"
                                       "- 패키지: com.acme.batch.claim..\n")
        self.assertEqual(d.contexts[0].packages, ["com.acme.web.claim.."])

    def test_duplicate_classification_is_error(self):
        d = self._parse_text(MINIMAL + "- 분류: generic\n")
        self.assertHasError(d, "두 번 나타납니다")

    def test_duplicate_project_label_is_error(self):
        text = MINIMAL.replace("- 경로: .", "- 경로: .\n- 경로: backend")
        self.assertHasError(self._parse_text(text), "두 번 나타납니다")

    def test_same_label_in_different_sections_is_fine(self):
        text = (MINIMAL + "\n## 컨텍스트: admin\n- 분류: generic\n")
        self.assertEqual(self._parse_text(text).errors, [])


class TestRelationTableShape(DomainTextCase):
    """표는 칸 순서로 읽는다 — 헤더·구분선이 어긋나면 값이 조용히 어긋나거나 사라진다."""

    def _with_table(self, table):
        return self._parse_text(MINIMAL + "\n## 컨텍스트: admin\n- 분류: generic\n"
                                          "\n### 관계\n" + table)

    def test_missing_divider_is_error(self):
        d = self._with_table("| 상대 | 유형 | 계약 |\n| claim | conformist | - |\n")
        self.assertHasError(d, "구분선")

    def test_missing_divider_does_not_silently_drop_the_row(self):
        # 검사가 없으면 첫 행이 구분선 자리에 놓여 통째로 사라진다.
        d = self._with_table("| 상대 | 유형 | 계약 |\n| claim | conformist | - |\n")
        self.assertEqual(d.contexts[1].relations, [])
        self.assertNotEqual(d.errors, [])

    def test_header_only_table_is_error(self):
        self.assertHasError(self._with_table("| 상대 | 유형 | 계약 |\n"), "구분선")

    def test_wrong_header_order_is_error(self):
        d = self._with_table("| 유형 | 상대 | 계약 |\n|---|---|---|\n| conformist | claim | - |\n")
        self.assertHasError(d, "헤더")

    def test_wrong_header_names_are_error(self):
        d = self._with_table("| 대상 | 종류 | 계약 |\n|---|---|---|\n| claim | conformist | - |\n")
        self.assertHasError(d, "헤더")

    def test_wrong_column_count_is_error(self):
        d = self._with_table("| 상대 | 유형 |\n|---|---|\n| claim | conformist |\n")
        self.assertHasError(d, "헤더")

    def test_aligned_divider_is_accepted(self):
        d = self._with_table("| 상대 | 유형 | 계약 |\n|:---|:---:|---:|\n| claim | conformist | - |\n")
        self.assertEqual(d.errors, [])

    def test_divider_with_trailing_whitespace_is_accepted(self):
        # 마크다운은 줄 끝 공백을 허용하고(2칸은 hard line break 관례) 에디터가 트림하지도 않는다.
        # 헤더 검사는 _header_cells의 strip()으로 이미 관대하므로 구분선만 엄격하면 비대칭이다.
        d = self._with_table("| 상대 | 유형 | 계약 |\n|---|---|---|  \n| claim | conformist | - |\n")
        self.assertEqual(d.errors, [])
        self.assertEqual([(r.partner, r.kind, r.contract) for r in d.contexts[1].relations],
                         [("claim", "conformist", "-")])

    def test_aligned_divider_with_trailing_whitespace_is_accepted(self):
        d = self._with_table("| 상대 | 유형 | 계약 |\n|:---|:---:|---:| \n| claim | conformist | - |\n")
        self.assertEqual(d.errors, [])
        self.assertEqual([r.partner for r in d.contexts[1].relations], ["claim"])

    def test_spaced_divider_is_accepted(self):
        d = self._with_table("| 상대 | 유형 | 계약 |\n| --- | --- | --- |\n| claim | conformist | - |\n")
        self.assertEqual(d.errors, [])
        self.assertEqual([r.partner for r in d.contexts[1].relations], ["claim"])

    def test_data_row_is_still_not_mistaken_for_a_divider(self):
        # 관용도를 넓혀도 데이터 행이 구분선으로 읽히면 안 된다 — 그러면 첫 행이 사라진다.
        d = self._with_table("| 상대 | 유형 | 계약 |\n| claim | conformist | - |  \n")
        self.assertHasError(d, "구분선")

    def test_correct_table_passes(self):
        d = self._with_table("| 상대 | 유형 | 계약 |\n|---|---|---|\n| claim | conformist | v1 |\n")
        self.assertEqual(d.errors, [])


class TestDividerIsNotADataRow(DomainTextCase):
    """구분선 판정은 **칸당 대시 3개 이상**이다.

    '대시·콜론·공백이면 아무거나'로 넓히면 `| - | - | - |` 같은 데이터 행이 구분선 자리에서
    구분선으로 읽혀, 그 행이 오류 없이 통째로 사라진다. 후행 공백 유무로 갈라지지 않도록
    두 변종을 모두 고정한다.
    """

    def _divider(self, line):
        return self._parse_text(
            MINIMAL + "\n## 컨텍스트: admin\n- 분류: generic\n\n### 관계\n"
            + "| 상대 | 유형 | 계약 |\n" + line + "\n| claim | conformist | - |\n")

    def assertAcceptedAsDivider(self, line):
        d = self._divider(line)
        self.assertEqual(d.errors, [], f"{line!r}이(가) 구분선으로 받아들여지지 않았습니다")
        self.assertEqual([r.partner for r in d.contexts[1].relations], ["claim"], repr(line))

    def assertRejectedAsDivider(self, line):
        d = self._divider(line)
        self.assertHasError(d, "구분선")

    def test_dash_only_row_is_not_a_divider(self):
        self.assertRejectedAsDivider("| - | - | - |")

    def test_dash_only_row_with_trailing_space_is_not_a_divider(self):
        # 후행 공백 변종을 빼면 같은 실수가 한쪽 경로로 재발한다.
        self.assertRejectedAsDivider("| - | - | - |  ")

    def test_two_dash_row_is_not_a_divider(self):
        self.assertRejectedAsDivider("| -- | -- | -- |")

    def test_word_row_is_not_a_divider(self):
        self.assertRejectedAsDivider("| claim | conformist | - |")

    def test_canonical_divider_variants_are_accepted(self):
        for line in ("|---|---|---|", "|---|---|---|  ",
                     "|:---|:---:|---:|", "|:---|:---:|---:| ",
                     "| --- | --- | --- |"):
            self.assertAcceptedAsDivider(line)

    def test_dash_only_row_would_otherwise_vanish(self):
        # 이 오류가 막는 상태: 구분선으로 오인되면 그 행이 relations에서 사라진다.
        d = self._divider("| - | - | - |")
        self.assertEqual([r.partner for r in d.contexts[1].relations], [])
        self.assertNotEqual(d.errors, [])


class TestRelationEmptyCells(DomainTextCase):
    """`상대`·`유형` 빈 칸은 아무 쌍도 열지 않는다 — 사용자는 열었다고 믿으므로 오류다."""

    def _with_row(self, row):
        return self._parse_text(MINIMAL + "\n## 컨텍스트: admin\n- 분류: generic\n"
                                          "\n### 관계\n| 상대 | 유형 | 계약 |\n|---|---|---|\n"
                                + row + "\n")

    def test_empty_partner_is_error(self):
        d = self._with_row("|  | conformist | - |")
        self.assertHasError(d, "'상대' 칸이 비어")

    def test_empty_kind_is_error(self):
        d = self._with_row("| claim |  | - |")
        self.assertHasError(d, "'유형' 칸이 비어")

    def test_empty_contract_is_allowed(self):
        # '계약'은 자유 문자열이므로 빈 값을 허용한다(구 템플릿 §4 라벨 사전).
        d = self._with_row("| claim | conformist |  |")
        self.assertEqual(d.errors, [])
        self.assertEqual(d.contexts[1].relations[0].contract, "")

    def test_empty_partner_opens_no_pair(self):
        d = self._with_row("|  | conformist | - |")
        self.assertEqual(isolation_allowlist(d)["claim"], frozenset())


class TestPublicSurface(unittest.TestCase):
    """이후 태스크가 그대로 import하는 공개 시그니처."""

    def test_exported_names(self):
        for name in ("MARKER_TEMPLATE", "TEMPLATE_VERSION", "CLASSIFICATIONS", "Relation",
                     "Project", "Context", "ParseError", "Domain", "LocatedError",
                     "format_error", "parse_domain", "context_packages", "isolation_allowlist"):
            self.assertTrue(hasattr(pd, name), name)

    def test_classifications_is_the_canonical_tuple(self):
        self.assertEqual(pd.CLASSIFICATIONS, ("core", "supporting", "generic"))

    def test_relation_field_order(self):
        relation = Relation("admin", "conformist", "-", 12)
        self.assertEqual((relation.partner, relation.kind, relation.contract, relation.line),
                         ("admin", "conformist", "-", 12))

    def test_located_error_keeps_parse_error_shape(self):
        error = LocatedError(3, "메시지", "DOMAIN.md")
        self.assertEqual((error.line, error.message, error.path), (3, "메시지", "DOMAIN.md"))
        self.assertEqual(format_error(error, "기본.md"), "DOMAIN.md:3: 메시지")

    def test_format_error_falls_back_to_default_path(self):
        self.assertEqual(format_error(pd.ParseError(0, "메시지"), "DOMAIN.md"),
                         "DOMAIN.md:0: 메시지")

    def test_located_error_str_is_readable_not_a_tuple(self):
        # 소비자가 `except LocatedError as e: print(e)`를 써도 사용자에게 튜플이 보이면 안 된다.
        self.assertEqual(str(LocatedError(3, "메시지", "DOMAIN.md")), "DOMAIN.md:3: 메시지")
        self.assertEqual(str(LocatedError(3, "메시지")), "3: 메시지")


class TestCli(DomainTextCase):
    """exit 규약: 0=OK, 1=해석 오류, 2=사용법 오류."""

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args],
                              capture_output=True, text=True)

    def test_exit_zero_on_valid_document(self):
        result = self.run_cli(str(FIXTURES / "full.md"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "OK: 프로젝트 2, 컨텍스트 3")

    def test_exit_one_on_parse_error(self):
        path = self._write(MINIMAL.replace("- 분류: core", "- 분류: kernel"))
        result = self.run_cli(str(path))
        self.assertEqual(result.returncode, 1)
        self.assertIn("kernel", result.stderr)
        self.assertIn(f"{path}:", result.stderr)

    def test_exit_one_on_missing_file(self):
        result = self.run_cli(str(TESTS_DIR / "없는파일-DOMAIN.md"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("읽을 수 없습니다", result.stderr)

    def test_exit_two_on_no_argument(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn("사용법", result.stderr)

    def test_exit_two_on_extra_argument(self):
        result = self.run_cli(str(FIXTURES / "full.md"), str(FIXTURES / "minimal.md"))
        self.assertEqual(result.returncode, 2)

    def test_exit_two_on_unknown_flag(self):
        result = self.run_cli("--json")
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
