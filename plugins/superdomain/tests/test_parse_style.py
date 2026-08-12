import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from parse_style import parse_style

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures" / "styles"
PRESET_STYLES_DIR = ROOT / "references" / "knowledge" / "styles"

DEFAULT_LAYERS = "domain, application, adapter"


def load(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


def doc(rows, layers=DEFAULT_LAYERS):
    """규칙 행 목록으로 최소 스타일 문서를 만든다. rows: [(규칙 id, primitive, 파라미터)].

    행 i는 1-기준 라인 ROW_LINE + i 에 놓인다(라인 번호 단언에 사용).
    """
    lines = ["## 선언", f"- 레이어: {layers}", "", "| 규칙 id | primitive | 파라미터 |", "|---|---|---|"]
    lines += [f"| {rid} | {primitive} | {params} |" for rid, primitive, params in rows]
    return "\n".join(lines) + "\n"


ROW_LINE = 6  # doc()이 만든 문서에서 첫 규칙 행의 1-기준 라인 번호


class StyleTestCase(unittest.TestCase):
    def parse(self, text, style_name="hexagonal"):
        return parse_style(text, style_name)

    def assert_one_error(self, text, needle, line=None):
        """오류가 정확히 1건이고 그 메시지에 needle이 들어 있는지 확인하고 그 오류를 돌려준다."""
        _decl, errors = self.parse(text)
        self.assertEqual(len(errors), 1, f"오류 1건을 기대했지만 {[e.message for e in errors]}")
        self.assertIn(needle, errors[0].message)
        if line is not None:
            self.assertEqual(errors[0].line, line)
        return errors[0]

    def assert_no_error(self, text):
        decl, errors = self.parse(text)
        self.assertEqual([e.message for e in errors], [])
        return decl


class TestValidDeclaration(StyleTestCase):
    def test_hexagonal_fixture(self):
        text = load("valid-hexagonal.md")
        decl, errors = parse_style(text, "hexagonal")
        self.assertEqual([e.message for e in errors], [])
        self.assertEqual(decl.name, "hexagonal")
        self.assertEqual(decl.layers, ["domain", "application", "adapter"])
        self.assertEqual([r.rule_id for r in decl.rules],
                         ["hex.deps-inward", "hex.domain-pure",
                          "hex.domain-no-framework", "hex.ports-owned-inside"])
        self.assertEqual([r.primitive for r in decl.rules],
                         ["layer-order", "confine-type", "forbid-import", "naming-suffix"])
        self.assertEqual([r.params for r in decl.rules], [
            {"layers": ["domain", "application", "adapter"]},
            {"type": ["jpa-entity"], "allowed_layer": ["adapter"]},
            {"from": ["domain"], "to": ["org.springframework..", "jakarta.persistence.."]},
            {"scope": ["application"], "suffixes": ["Port", "UseCase"]},
        ])
        # 라인 번호는 픽스처 본문에서 직접 찾아 대조한다(픽스처가 바뀌어도 따라간다).
        body = text.split("\n")
        first_row = next(i for i, l in enumerate(body) if l.startswith("| hex.deps-inward ")) + 1
        self.assertEqual([r.line for r in decl.rules],
                         [first_row, first_row + 1, first_row + 2, first_row + 3])

    def test_layer_label_trailing_comment_stripped(self):
        # 픽스처의 '- 레이어: ... (안 → 밖 순서)'에서 괄호 주석이 레이어 이름에 섞이면 안 된다
        decl = self.assert_no_error(load("valid-hexagonal.md"))
        self.assertNotIn("(안", "".join(decl.layers))

    def test_preset_styles_parse_without_error(self):
        # 정본 프리셋 4종은 이 파서가 오류 없이 읽어야 한다(실제 코퍼스 회귀 방지)
        preset_files = sorted(PRESET_STYLES_DIR.glob("*.md"))
        self.assertEqual(len(preset_files), 4)
        for path in preset_files:
            with self.subTest(style=path.stem):
                decl, errors = parse_style(path.read_text(encoding="utf-8"), path.stem, str(path))
                self.assertEqual([e.message for e in errors], [])
                self.assertTrue(decl.layers)
                self.assertTrue(decl.rules)

    def test_all_five_primitives_accepted(self):
        decl = self.assert_no_error(doc([
            ("x.order", "layer-order", "layers=domain,application; strict=true"),
            ("x.import", "forbid-import", "from=domain; to=org.springframework.."),
            ("x.confine", "confine-type", "type=jpa-entity; allowed_layer=adapter"),
            ("x.naming", "naming-suffix", "scope=application; suffixes=Port,UseCase"),
            ("x.sibling", "forbid-sibling-dependency", "layer=application; suffix=Service"),
        ]))
        self.assertEqual(len(decl.rules), 5)
        self.assertEqual(decl.rules[0].params["strict"], ["true"])


class TestParamGrammar(StyleTestCase):
    def test_list_value_split(self):
        decl = self.assert_no_error(doc([
            ("x.import", "forbid-import", "from=domain; to=org.springframework..,jakarta.persistence.."),
        ]))
        self.assertEqual(decl.rules[0].params["to"],
                         ["org.springframework..", "jakarta.persistence.."])
        self.assertEqual(decl.rules[0].params["from"], ["domain"])  # 항목 1개도 목록이다

    def test_key_order_irrelevant(self):
        forward = self.assert_no_error(doc([("x.import", "forbid-import", "from=domain; to=adapter")]))
        reverse = self.assert_no_error(doc([("x.import", "forbid-import", "to=adapter; from=domain")]))
        self.assertEqual(forward.rules[0].params, reverse.rules[0].params)

    def test_duplicate_key_error(self):
        self.assert_one_error(
            doc([("x.import", "forbid-import", "from=domain; to=adapter; from=application")]),
            "중복", line=ROW_LINE)

    def test_unknown_key_error(self):
        self.assert_one_error(
            doc([("x.import", "forbid-import", "from=domain; to=adapter; suffix=Service")]),
            "알 수 없는 키", line=ROW_LINE)

    def test_trailing_semicolon_error(self):
        self.assert_one_error(
            doc([("x.import", "forbid-import", "from=domain; to=adapter;")]),
            "빈 파라미터", line=ROW_LINE)

    def test_internal_space_error(self):
        self.assert_one_error(
            doc([("x.naming", "naming-suffix", "scope=application; suffixes=Use Case")]),
            "공백", line=ROW_LINE)

    def test_internal_space_in_key_error(self):
        self.assert_one_error(
            doc([("x.naming", "naming-suffix", "sco pe=application; suffixes=Port")]),
            "공백", line=ROW_LINE)

    def test_nonlist_key_multiple_items_error(self):
        self.assert_one_error(
            doc([("x.sibling", "forbid-sibling-dependency", "layer=application; suffix=Service,Component")]),
            "목록", line=ROW_LINE)

    def test_equals_count_error(self):
        self.assert_one_error(doc([("x.order", "layer-order", "layers")]), "'='", line=ROW_LINE)
        self.assert_one_error(doc([("x.order", "layer-order", "layers=domain=application")]), "'='",
                              line=ROW_LINE)

    def test_empty_key_error(self):
        self.assert_one_error(doc([("x.order", "layer-order", "=domain")]), "빈 키", line=ROW_LINE)

    def test_empty_value_error(self):
        self.assert_one_error(doc([("x.import", "forbid-import", "from=domain; to=")]),
                              "빈 값", line=ROW_LINE)

    def test_empty_item_error(self):
        self.assert_one_error(
            doc([("x.import", "forbid-import", "from=domain; to=adapter,,application")]),
            "빈 항목", line=ROW_LINE)

    def test_empty_param_cell_error(self):
        self.assert_one_error(doc([("x.order", "layer-order", "")]), "비어", line=ROW_LINE)

    def test_case_sensitive_values(self):
        decl = self.assert_no_error(doc([("x.naming", "naming-suffix", "scope=application; suffixes=Controller")]))
        self.assertEqual(decl.rules[0].params["suffixes"], ["Controller"])


class TestRequiredAndValueChecks(StyleTestCase):
    def test_missing_required_key_error(self):
        self.assert_one_error(doc([("x.order", "layer-order", "strict=true")]),
                              "필수 키", line=ROW_LINE)

    def test_strict_value_error(self):
        self.assert_one_error(doc([("x.order", "layer-order", "layers=domain; strict=yes")]),
                              "strict", line=ROW_LINE)

    def test_strict_false_accepted(self):
        decl = self.assert_no_error(doc([("x.order", "layer-order", "layers=domain; strict=false")]))
        self.assertEqual(decl.rules[0].params["strict"], ["false"])


class TestLayerResolution(StyleTestCase):
    def test_na_param_unknown_layer_error(self):
        error = self.assert_one_error(doc([("x.order", "layer-order", "layers=domain,typo")]),
                                      "typo", line=ROW_LINE)
        self.assertIn("레이어", error.message)

    def test_na_param_package_pattern_rejected(self):
        # (나)에는 패키지 패턴으로 넘어가는 대체 해석이 없다
        self.assert_one_error(
            doc([("x.confine", "confine-type", "type=jpa-entity; allowed_layer=com.acme.adapter..")]),
            "com.acme.adapter..", line=ROW_LINE)

    def test_na_param_sibling_layer_error(self):
        self.assert_one_error(
            doc([("x.sibling", "forbid-sibling-dependency", "layer=typo; suffix=Service")]),
            "typo", line=ROW_LINE)

    def test_ga_param_bare_word_not_layer_error(self):
        # from=kotlinx — 점이 없고 레이어도 아니다(§2.1(가)의 조용한 실패 차단)
        self.assert_one_error(doc([("x.import", "forbid-import", "from=kotlinx; to=adapter")]),
                              "kotlinx", line=ROW_LINE)

    def test_ga_param_layer_name_accepted(self):
        decl = self.assert_no_error(doc([("x.import", "forbid-import", "from=domain; to=adapter")]))
        self.assertEqual(decl.rules[0].params["to"], ["adapter"])

    def test_ga_param_package_pattern_accepted(self):
        decl = self.assert_no_error(
            doc([("x.import", "forbid-import", "from=domain; to=org.springframework..")]))
        self.assertEqual(decl.rules[0].params["to"], ["org.springframework.."])

    def test_ga_param_scope_bare_word_error(self):
        self.assert_one_error(
            doc([("x.naming", "naming-suffix", "scope=kotlinx; suffixes=Port")]),
            "kotlinx", line=ROW_LINE)

    def test_suffixes_not_layer_checked(self):
        # suffixes는 (가)도 (나)도 아니다 — 점 없는 단어여도 레이어 판별을 받지 않는다
        self.assert_no_error(doc([("x.naming", "naming-suffix", "scope=application; suffixes=Port")]))


class TestConfineType(StyleTestCase):
    def test_xor_both_error(self):
        self.assert_one_error(
            doc([("x.confine", "confine-type", "type=jpa-entity; allowed_layer=adapter; allowed_package=com.acme..")]),
            "allowed_layer", line=ROW_LINE)

    def test_xor_neither_error(self):
        self.assert_one_error(doc([("x.confine", "confine-type", "type=jpa-entity")]),
                              "allowed_layer", line=ROW_LINE)

    def test_unknown_selector_error(self):
        self.assert_one_error(
            doc([("x.confine", "confine-type", "type=jpa-entities; allowed_layer=adapter")]),
            "jpa-entities", line=ROW_LINE)

    def test_allowed_package_not_layer_checked(self):
        # allowed_package는 순수 패키지 패턴 필드다 — 점 없는 값도 레이어 판별을 받지 않는다(어휘 §2)
        decl = self.assert_no_error(
            doc([("x.confine", "confine-type", "type=jpa-entity; allowed_package=kotlinx")]))
        self.assertEqual(decl.rules[0].params["allowed_package"], ["kotlinx"])


class TestSection(StyleTestCase):
    def test_missing_declaration_section_error(self):
        decl, errors = parse_style(load("broken-no-declaration.md"), "hexagonal")
        self.assertIsNone(decl)
        self.assertEqual(len(errors), 1)
        self.assertIn("'## 선언' 섹션이 없습니다", errors[0].message)
        self.assertEqual(errors[0].line, 0)

    def test_level3_heading_not_matched(self):
        decl, errors = parse_style(load("broken-level3-declaration.md"), "hexagonal")
        self.assertIsNone(decl)
        self.assertIn("'## 선언' 섹션이 없습니다", errors[0].message)

    def test_section_ends_at_next_h2(self):
        # valid 픽스처의 '## 규칙' 아래 표(hex.bogus / layers=nope)는 읽히지 않는다
        decl = self.assert_no_error(load("valid-hexagonal.md"))
        self.assertNotIn("hex.bogus", [r.rule_id for r in decl.rules])

    def test_table_before_section_not_read(self):
        decl = self.assert_no_error(load("valid-hexagonal.md"))
        self.assertEqual(len(decl.rules), 4)

    def test_duplicate_rule_id_error(self):
        decl, errors = parse_style(load("broken-duplicate-rule-id.md"), "hexagonal")
        self.assertEqual(len(errors), 1)
        self.assertIn("hex.deps-inward", errors[0].message)
        self.assertIn("중복", errors[0].message)
        self.assertEqual(errors[0].line, 7)          # 두 번째로 등장한 행
        self.assertEqual(len(decl.rules), 2)          # 파싱 가능한 부분은 채운다

    def test_unknown_primitive_error(self):
        decl, errors = parse_style(load("broken-unknown-primitive.md"), "hexagonal")
        self.assertEqual(len(errors), 1)
        self.assertIn("forbid-cycle", errors[0].message)
        self.assertEqual(errors[0].line, 6)
        self.assertEqual(decl.rules[0].primitive, "forbid-cycle")

    def test_missing_layer_label_error(self):
        decl, errors = parse_style(load("broken-no-layer-label.md"), "hexagonal")
        self.assertEqual(len(errors), 1)             # 레이어 판별 오류가 연쇄되지 않는다
        self.assertIn("레이어", errors[0].message)
        self.assertEqual(decl.layers, [])
        self.assertEqual(len(decl.rules), 1)

    def test_empty_layer_list_error(self):
        text = "## 선언\n- 레이어:\n\n| 규칙 id | primitive | 파라미터 |\n|---|---|---|\n" \
               "| x.order | layer-order | layers=domain |\n"
        _decl, errors = self.parse(text)
        self.assertEqual(len(errors), 1)
        self.assertIn("레이어", errors[0].message)
        self.assertEqual(errors[0].line, 2)

    def test_duplicate_layer_name_error(self):
        self.assert_one_error(doc([("x.order", "layer-order", "layers=domain")],
                                  layers="domain, application, domain"),
                              "domain", line=2)

    def test_missing_rule_table_error(self):
        text = "## 선언\n- 레이어: domain, application\n\n산문만 있고 규칙 표가 없다.\n"
        _decl, errors = self.parse(text)
        self.assertEqual(len(errors), 1)
        self.assertIn("표", errors[0].message)
        self.assertEqual(errors[0].line, 1)

    def test_empty_rule_table_error(self):
        text = "## 선언\n- 레이어: domain, application\n\n| 규칙 id | primitive | 파라미터 |\n|---|---|---|\n"
        _decl, errors = self.parse(text)
        self.assertEqual(len(errors), 1)
        self.assertIn("규칙", errors[0].message)

    def test_partial_parse_with_multiple_errors(self):
        decl, errors = parse_style(load("broken-params.md"), "hexagonal")
        messages = sorted(e.message for e in errors)
        self.assertEqual(len(errors), 3, messages)
        self.assertEqual(len(decl.rules), 3)
        self.assertEqual(decl.rules[0].params, {"layers": ["domain", "application", "adapter"]})
        self.assertTrue(any("빈 파라미터" in m for m in messages))
        self.assertTrue(any("알 수 없는 키" in m for m in messages))
        self.assertTrue(any("필수 키" in m for m in messages))


if __name__ == "__main__":
    unittest.main()
