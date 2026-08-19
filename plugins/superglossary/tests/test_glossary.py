"""templates/glossary.py 테스트 스위트 (표준 라이브러리 unittest)."""
import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location("glossary", os.path.join(ROOT, "templates", "glossary.py"))
g = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(g)


def load_file(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write_file(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


class TempDirCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="glossary-")
        self.addCleanup(shutil.rmtree, self.dir, True)


class DataTest(TempDirCase):
    def test_save_load_roundtrip(self):
        terms = [{"korean": "회원", "english": "member", "abbreviation": None,
                  "description": "", "relatedElements": [], "avoid": []}]
        g.save_glossary(self.dir, {"schemaVersion": g.SCHEMA_VERSION, "terms": terms})
        loaded = g.load_glossary(self.dir)
        self.assertEqual(loaded["terms"], terms)
        self.assertEqual(loaded["schemaVersion"], g.SCHEMA_VERSION)

    def test_save_puts_schema_version_first(self):
        g.save_glossary(self.dir, {"terms": []})
        raw = load_file(os.path.join(self.dir, "glossary.json"))
        self.assertTrue(raw.startswith('{\n  "schemaVersion":'), raw[:40])

    def test_initial_data_carries_schema_version(self):
        self.assertEqual(g.INITIAL_DATA["schemaVersion"], g.SCHEMA_VERSION)

    def test_save_writes_hangul_unescaped(self):
        g.save_glossary(self.dir, {"terms": [{"korean": "회원", "english": "member"}]})
        self.assertIn("회원", load_file(os.path.join(self.dir, "glossary.json")))

    def test_load_missing_file_gives_guidance(self):
        with self.assertRaisesRegex(g.GlossaryError, "용어사전이 없습니다"):
            g.load_glossary(self.dir)


class TermTest(unittest.TestCase):
    def test_sorted_terms_is_korean_alphabetical(self):
        data = {"terms": [{"korean": "주문", "english": "order"},
                          {"korean": "가격", "english": "price"},
                          {"korean": "회원", "english": "member"}]}
        self.assertEqual([t["korean"] for t in g.sorted_terms(data)], ["가격", "주문", "회원"])

    def test_add_term_normalizes_fields(self):
        data = {"terms": []}
        g.add_term(data, "회원", "member")
        self.assertEqual(data["terms"][0], {
            "korean": "회원", "english": "member", "abbreviation": None,
            "description": "", "relatedElements": [], "avoid": [],
        })

    def test_add_term_returns_data(self):
        data = {"terms": []}
        self.assertIs(g.add_term(data, "주문", "order"), data)

    def test_add_term_requires_korean_and_english(self):
        with self.assertRaisesRegex(g.GlossaryError, "필수입니다"):
            g.add_term({"terms": []}, "회원", None)

    def test_add_term_rejects_duplicate_korean(self):
        data = {"terms": [{"korean": "회원", "english": "member", "abbreviation": None}]}
        with self.assertRaisesRegex(g.GlossaryError, "이미 등록된 한글"):
            g.add_term(data, "회원", "customer")

    def test_add_term_rejects_duplicate_english_case_insensitive(self):
        data = {"terms": [{"korean": "회원", "english": "member", "abbreviation": None}]}
        with self.assertRaisesRegex(g.GlossaryError, "이미 등록된 영문"):
            g.add_term(data, "고객", "Member")

    def test_add_term_rejects_duplicate_abbreviation(self):
        data = {"terms": [{"korean": "식별자", "english": "identifier", "abbreviation": "id"}]}
        with self.assertRaisesRegex(g.GlossaryError, "이미 등록된 축약어"):
            g.add_term(data, "지수", "index", "ID")

    def test_update_term_updates_only_given_fields(self):
        data = {"terms": [{"korean": "청구", "english": "claim", "abbreviation": None,
                           "description": "", "relatedElements": []}]}
        g.update_term(data, "청구", {"english": "billing", "description": "요금 청구"})
        self.assertEqual(g.find_term(data, "청구")["english"], "billing")
        self.assertEqual(g.find_term(data, "청구")["description"], "요금 청구")

    def test_update_term_unknown_raises(self):
        with self.assertRaisesRegex(g.GlossaryError, "등록되지 않은 용어"):
            g.update_term({"terms": []}, "없음", {"english": "x"})

    def test_remove_term(self):
        data = {"terms": [{"korean": "청구", "english": "claim"}]}
        g.remove_term(data, "청구")
        self.assertEqual(len(data["terms"]), 0)

    def test_remove_term_unknown_raises(self):
        with self.assertRaisesRegex(g.GlossaryError, "등록되지 않은 용어"):
            g.remove_term({"terms": []}, "없음")

    def test_lookup_matches_korean_english_abbreviation(self):
        data = {"terms": [{"korean": "회원", "english": "member", "abbreviation": None},
                          {"korean": "식별자", "english": "identifier", "abbreviation": "id"}]}
        self.assertEqual([t["korean"] for t in g.lookup(data, "mem")], ["회원"])
        self.assertEqual([t["korean"] for t in g.lookup(data, "ID")], ["식별자"])

    def test_list_terms_is_sorted(self):
        data = {"terms": [{"korean": "회원", "english": "member"}, {"korean": "가격", "english": "price"}]}
        self.assertEqual([t["korean"] for t in g.list_terms(data)], ["가격", "회원"])

    def test_format_term_detail(self):
        full = g.format_term_detail({"korean": "회원", "english": "member", "abbreviation": "mbr",
                                     "description": "가입 사용자", "relatedElements": ["member_id"],
                                     "avoid": ["customer"]})
        self.assertEqual(full, "회원 → member (축약: mbr)\n  설명: 가입 사용자\n  관련: member_id\n  금지: customer")
        minimal = g.format_term_detail({"korean": "주문", "english": "order", "abbreviation": None,
                                        "description": "", "relatedElements": [], "avoid": []})
        self.assertEqual(minimal, "주문 → order")


class ConflictTest(unittest.TestCase):
    def test_no_conflict_returns_none(self):
        self.assertIsNone(g.find_conflict([], "회원", "member", None, []))

    def test_add_term_stores_avoid_list(self):
        data = {"terms": []}
        g.add_term(data, "회원", "member", avoid=["customer", "user"])
        self.assertEqual(data["terms"][0]["avoid"], ["customer", "user"])

    def test_english_matching_existing_avoid_points_to_standard(self):
        data = {"terms": [{"korean": "회원", "english": "member", "abbreviation": None, "avoid": ["customer"]}]}
        with self.assertRaisesRegex(g.GlossaryError, "금지 변형입니다. 표준: member"):
            g.add_term(data, "고객", "Customer")

    def test_avoid_colliding_with_existing_english(self):
        data = {"terms": [{"korean": "회원", "english": "member", "abbreviation": None}]}
        with self.assertRaisesRegex(g.GlossaryError, r"금지 변형 'member'이\(가\) 등록 용어 회원\(member\)과\(와\) 충돌합니다"):
            g.add_term(data, "고객", "client", avoid=["member"])

    def test_avoid_colliding_with_existing_abbreviation(self):
        data = {"terms": [{"korean": "식별자", "english": "identifier", "abbreviation": "id"}]}
        with self.assertRaisesRegex(g.GlossaryError, r"등록 용어 식별자\(identifier\)과\(와\) 충돌합니다"):
            g.add_term(data, "지표", "metric", avoid=["ID"])

    def test_avoid_is_globally_unique(self):
        data = {"terms": [{"korean": "회원", "english": "member", "abbreviation": None, "avoid": ["customer"]}]}
        with self.assertRaisesRegex(g.GlossaryError, r"이미 회원\(member\)의 금지 목록에 있습니다"):
            g.add_term(data, "고객", "client", avoid=["customer"])

    def test_avoid_cannot_equal_own_english_or_abbreviation(self):
        with self.assertRaisesRegex(g.GlossaryError, "자신의 영문"):
            g.add_term({"terms": []}, "고객", "client", avoid=["client"])
        with self.assertRaisesRegex(g.GlossaryError, "자신의 축약어"):
            g.add_term({"terms": []}, "고객", "client", "cl", avoid=["cl"])

    def test_cross_collision_between_english_and_abbreviation(self):
        data = {"terms": [{"korean": "식별자", "english": "identifier", "abbreviation": "id"},
                          {"korean": "회원", "english": "member", "abbreviation": None}]}
        with self.assertRaisesRegex(g.GlossaryError, "이미 등록된 축약어와 충돌"):
            g.add_term(data, "지표", "id")
        with self.assertRaisesRegex(g.GlossaryError, "이미 등록된 영문과 충돌"):
            g.add_term(data, "고객", "client", "member")

    def test_update_term_avoid_and_conflict_check(self):
        data = {"terms": [
            {"korean": "회원", "english": "member", "abbreviation": None, "description": "", "relatedElements": [], "avoid": []},
            {"korean": "주문", "english": "order", "abbreviation": None, "description": "", "relatedElements": [], "avoid": []},
        ]}
        g.update_term(data, "회원", {"avoid": ["customer", "user"]})
        self.assertEqual(g.find_term(data, "회원")["avoid"], ["customer", "user"])
        with self.assertRaisesRegex(g.GlossaryError, r"등록 용어 주문\(order\)과\(와\) 충돌합니다"):
            g.update_term(data, "회원", {"avoid": ["order"]})
        self.assertEqual(g.find_term(data, "회원")["avoid"], ["customer", "user"], "실패 시 원본 불변")


class RenderTest(TempDirCase):
    def test_render_core_sorted_blank_abbreviation_and_header(self):
        data = {"terms": [{"korean": "회원", "english": "member", "abbreviation": None},
                          {"korean": "식별자", "english": "identifier", "abbreviation": "id"}]}
        out = g.render_core(data)
        self.assertTrue(out.startswith(g.AUTOGEN))
        self.assertLess(out.index("식별자"), out.index("회원"), "가나다순(식별자<회원)")
        self.assertIn("| 회원 | member |  |", out)

    def test_render_terms_joins_related_elements(self):
        data = {"terms": [{"korean": "식별자", "english": "identifier", "abbreviation": "id",
                           "description": "고유 식별", "relatedElements": ["member_id", "product_id"]}]}
        self.assertIn("| member_id, product_id |", g.render_terms(data))

    def test_escape_cell(self):
        self.assertEqual(g.escape_cell("현재가|주문시점가"), "현재가\\|주문시점가")
        self.assertEqual(g.escape_cell("첫줄\n둘째줄"), "첫줄<br>둘째줄")
        self.assertEqual(g.escape_cell(None), "")

    def test_render_terms_escapes_pipe_in_description(self):
        data = {"terms": [{"korean": "가격", "english": "price", "abbreviation": None,
                           "description": "현재가|주문시점가 구분", "relatedElements": [], "avoid": []}]}
        self.assertIn("현재가\\|주문시점가 구분", g.render_terms(data))

    def test_render_core_avoid_summary(self):
        with_avoid = {"terms": [
            {"korean": "회원", "english": "member", "abbreviation": None, "avoid": ["customer", "user"]},
            {"korean": "주문", "english": "order", "abbreviation": None, "avoid": []},
        ]}
        out = g.render_core(with_avoid)
        self.assertIn("금지 변형(대신 표준 사용):", out)
        self.assertIn("- customer, user → member(회원)", out)
        self.assertNotIn("order(주문)", out, "avoid 없는 용어는 요약에 없음")
        without = g.render_core({"terms": [{"korean": "주문", "english": "order", "abbreviation": None}]})
        self.assertNotIn("금지 변형", without)

    def test_render_terms_has_avoid_column(self):
        data = {"terms": [{"korean": "회원", "english": "member", "abbreviation": None,
                           "description": "", "relatedElements": [], "avoid": ["customer"]}]}
        out = g.render_terms(data)
        self.assertIn("| 한글 | 영문 | 축약 | 설명 | 관련 요소 | 금지 |", out)
        self.assertIn("| customer |", out)

    def test_build_is_idempotent(self):
        g.save_glossary(self.dir, {"terms": [{"korean": "회원", "english": "member", "abbreviation": None,
                                              "description": "", "relatedElements": []}]})
        g.build(self.dir)
        core1 = load_file(os.path.join(self.dir, "core.md"))
        terms1 = load_file(os.path.join(self.dir, "terms.md"))
        g.build(self.dir)
        self.assertEqual(load_file(os.path.join(self.dir, "core.md")), core1)
        self.assertEqual(load_file(os.path.join(self.dir, "terms.md")), terms1)

    def test_build_warns_when_core_exceeds_threshold(self):
        many = [{"korean": f"용어{i:03d}", "english": f"term{i}", "abbreviation": None,
                 "description": "", "relatedElements": [], "avoid": []}
                for i in range(g.CORE_SPLIT_THRESHOLD)]
        g.save_glossary(self.dir, {"terms": many})
        self.assertRegex(g.build(self.dir), r"core\.md가 \d+줄입니다")
        g.save_glossary(self.dir, {"terms": many[:3]})
        self.assertIsNone(g.build(self.dir))

    def test_is_stale(self):
        g.save_glossary(self.dir, {"terms": [{"korean": "회원", "english": "member", "abbreviation": None,
                                              "description": "", "relatedElements": [], "avoid": []}]})
        self.assertTrue(g.is_stale(self.dir, g.load_glossary(self.dir)), "생성물 없음 = stale")
        g.build(self.dir)
        self.assertFalse(g.is_stale(self.dir, g.load_glossary(self.dir)))
        data = g.load_glossary(self.dir)
        data["terms"].append({"korean": "주문", "english": "order", "abbreviation": None,
                              "description": "", "relatedElements": [], "avoid": []})
        g.save_glossary(self.dir, data)
        self.assertTrue(g.is_stale(self.dir, g.load_glossary(self.dir)))


class LintTest(TempDirCase):
    def test_tokenize(self):
        self.assertEqual(g.tokenize("memberId"), ["member", "id"])
        self.assertEqual(g.tokenize("reg_dt"), ["reg", "dt"])
        self.assertEqual(g.tokenize("ship_address"), ["ship", "address"])

    def test_unregistered_tokens_become_candidates(self):
        f = os.path.join(self.dir, "sample.js")
        write_file(f, "const customer = 1; const customerName = 2; const memberId = 3;")
        data = {"terms": [{"korean": "회원", "english": "member", "abbreviation": None},
                          {"korean": "식별자", "english": "identifier", "abbreviation": "id"},
                          {"korean": "이름", "english": "name", "abbreviation": None}]}
        candidates = g.lint_files(data, [f])["candidates"]
        customer = next((c for c in candidates if c["token"] == "customer"), None)
        self.assertIsNotNone(customer)
        self.assertEqual(customer["count"], 2, "customer 2회 미등록")
        self.assertEqual(customer["files"], [f])
        self.assertIsNone(next((c for c in candidates if c["token"] == "member"), None), "member는 등록되어 제외")
        self.assertIsNone(next((c for c in candidates if c["token"] == "const"), None), "const는 스톱워드로 제외")

    def test_stopwords_membership(self):
        for w in ["const", "public", "import", "string", "repository", "service"]:
            self.assertIn(w, g.STOPWORDS, f"{w}는 스톱워드여야 함")
        for w in ["user", "order", "member", "customer", "item", "price", "product", "address", "status", "state"]:
            self.assertNotIn(w, g.STOPWORDS, f"{w}는 스톱워드가 아니어야 함")

    def test_avoid_matches_become_violations_and_beat_stopwords(self):
        f = os.path.join(self.dir, "sample.js")
        # 'repository'는 스톱워드지만 avoid로 등록되면 위반으로 잡혀야 한다(결정 #10)
        write_file(f, "class MemberStore {} class MemberRepository {} const customerId = 1;")
        data = {"terms": [
            {"korean": "저장소", "english": "store", "abbreviation": None, "avoid": ["repository"]},
            {"korean": "회원", "english": "member", "abbreviation": None, "avoid": ["customer"]},
            {"korean": "식별자", "english": "identifier", "abbreviation": "id"},
        ]}
        report = g.lint_files(data, [f])
        repo = next((v for v in report["violations"] if v["token"] == "repository"), None)
        self.assertIsNotNone(repo)
        self.assertEqual((repo["standard"], repo["korean"]), ("store", "저장소"))
        cust = next((v for v in report["violations"] if v["token"] == "customer"), None)
        self.assertIsNotNone(cust)
        self.assertEqual(cust["standard"], "member")
        self.assertIsNone(next((c for c in report["candidates"] if c["token"] == "customer"), None),
                          "위반은 후보에 중복되지 않음")

    def test_all_flag_disables_stopwords(self):
        f = os.path.join(self.dir, "sample.js")
        write_file(f, "const value = 1;")
        data = {"terms": []}
        self.assertIsNone(next((c for c in g.lint_files(data, [f])["candidates"] if c["token"] == "const"), None))
        with_all = g.lint_files(data, [f], all_tokens=True)["candidates"]
        self.assertIsNotNone(next((c for c in with_all if c["token"] == "const"), None))

    def test_multiword_english_matches_by_word(self):
        f = os.path.join(self.dir, "sample.js")
        write_file(f, "const stockKeepingUnit = 1;")
        data = {"terms": [{"korean": "재고관리단위", "english": "Stock Keeping Unit", "abbreviation": "SKU"}]}
        self.assertEqual(g.lint_files(data, [f])["candidates"], [])

    def test_directory_paths_are_walked_recursively(self):
        src = os.path.join(self.dir, "src", "nested")
        os.makedirs(src)
        write_file(os.path.join(src, "OrderService.java"), "class OrderService { String customerName; }")
        data = {"terms": [{"korean": "회원", "english": "member", "abbreviation": None, "avoid": ["customer"]}]}
        report = g.lint_files(data, [os.path.join(self.dir, "src")])
        self.assertIsNotNone(next((v for v in report["violations"] if v["token"] == "customer"), None),
                             "디렉토리를 재귀 탐색해야 한다")

    def test_ignored_directories_are_skipped(self):
        vendor = os.path.join(self.dir, "node_modules")
        os.makedirs(vendor)
        write_file(os.path.join(vendor, "dep.js"), "const customerName = 1;")
        data = {"terms": [{"korean": "회원", "english": "member", "abbreviation": None, "avoid": ["customer"]}]}
        self.assertEqual(g.lint_files(data, [self.dir])["violations"], [])

    def test_binary_files_are_skipped(self):
        binary = os.path.join(self.dir, "logo.png")
        with open(binary, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n\xff\xfe customer")
        data = {"terms": [{"korean": "회원", "english": "member", "abbreviation": None, "avoid": ["customer"]}]}
        self.assertEqual(g.lint_files(data, [self.dir])["violations"], [])

    def test_duplicate_paths_are_counted_once(self):
        f = os.path.join(self.dir, "sample.js")
        write_file(f, "const customerName = 1;")
        data = {"terms": [{"korean": "회원", "english": "member", "abbreviation": None, "avoid": ["customer"]}]}
        report = g.lint_files(data, [f, f])
        self.assertEqual(report["violations"][0]["count"], 1)

    def test_format_file_list(self):
        self.assertEqual(g.format_file_list(["a", "b"]), "a, b")
        self.assertEqual(g.format_file_list(["a", "b", "c", "d", "e"]), "a, b, c 외 2")


class ArgsTest(unittest.TestCase):
    def test_positional_and_options(self):
        positional, options = g.parse_args(["청구", "claim", "--desc", "요금", "--related=a,b"])
        self.assertEqual(positional, ["청구", "claim"])
        self.assertEqual(options["desc"], "요금")
        self.assertEqual(options["related"], "a,b")

    def test_boolean_option_has_no_value(self):
        positional, options = g.parse_args(["--all", "a.js", "b.js"])
        self.assertIs(options["all"], True)
        self.assertEqual(positional, ["a.js", "b.js"])

    def test_trailing_option_without_value(self):
        _, options = g.parse_args(["--desc"])
        self.assertIsNone(options["desc"])


class RunTest(TempDirCase):
    def test_add_then_list_rebuilds(self):
        g.save_glossary(self.dir, {"terms": []})
        g.run(["add", "회원", "member"], self.dir)
        g.run(["add", "식별자", "identifier", "id", "--desc", "고유값"], self.dir)
        listed = g.run(["list"], self.dir)
        self.assertIn("회원", listed)
        self.assertIn("member", listed)
        self.assertIn("identifier", load_file(os.path.join(self.dir, "core.md")), "add가 재빌드한다")

    def test_remove(self):
        g.save_glossary(self.dir, {"terms": [{"korean": "회원", "english": "member", "abbreviation": None,
                                              "description": "", "relatedElements": []}]})
        g.run(["remove", "회원"], self.dir)
        self.assertEqual(len(g.load_glossary(self.dir)["terms"]), 0)

    def test_add_with_avoid_persists_and_rebuilds(self):
        g.save_glossary(self.dir, {"terms": []})
        g.run(["add", "회원", "member", "--avoid", "customer,user"], self.dir)
        self.assertEqual(g.load_glossary(self.dir)["terms"][0]["avoid"], ["customer", "user"])
        self.assertIn("- customer, user → member(회원)", load_file(os.path.join(self.dir, "core.md")))

    def test_update_avoid(self):
        g.save_glossary(self.dir, {"terms": [{"korean": "회원", "english": "member", "abbreviation": None,
                                              "description": "", "relatedElements": [], "avoid": []}]})
        g.run(["update", "회원", "--avoid", "customer"], self.dir)
        self.assertEqual(g.load_glossary(self.dir)["terms"][0]["avoid"], ["customer"])

    def test_lint_sections_and_clean_output(self):
        # 식별자(id)를 등록해 두어 clean.js의 memberId가 전부 등록어로 매칭되게 한다
        g.save_glossary(self.dir, {"terms": [
            {"korean": "회원", "english": "member", "abbreviation": None, "description": "",
             "relatedElements": [], "avoid": ["customer"]},
            {"korean": "식별자", "english": "identifier", "abbreviation": "id", "description": "",
             "relatedElements": [], "avoid": []},
        ]})
        g.build(self.dir)
        f = os.path.join(self.dir, "sample.js")
        write_file(f, "const customerId = 1; const deliveryFee = 2;")
        out = g.run(["lint", f], self.dir)
        self.assertIn("[위반]", out)
        self.assertIn("customer\tmember(회원)", out)
        self.assertIn("[후보]", out)
        self.assertIn("delivery", out)
        clean = os.path.join(self.dir, "clean.js")
        write_file(clean, "const memberId = 1;")
        self.assertEqual(g.run(["lint", clean], self.dir), "이상 없음")

    def test_lint_without_paths_is_an_error(self):
        g.save_glossary(self.dir, {"terms": []})
        g.build(self.dir)
        with self.assertRaisesRegex(g.GlossaryError, "검사할 파일이나 디렉토리를 지정하세요"):
            g.run(["lint"], self.dir)

    def test_lookup_detail_and_miss(self):
        g.save_glossary(self.dir, {"terms": [{"korean": "청구", "english": "claim", "abbreviation": None,
                                              "description": "요금 청구", "relatedElements": [], "avoid": []}]})
        g.build(self.dir)
        out = g.run(["lookup", "청구"], self.dir)
        self.assertIn("청구 → claim", out)
        self.assertIn("설명: 요금 청구", out)
        self.assertEqual(g.run(["lookup", "없는말"], self.dir), "일치하는 용어 없음")

    def test_version_help_and_unknown_command(self):
        self.assertRegex(g.run(["version"], self.dir), r"^superglossary CLI v\d+\.\d+\.\d+")
        self.assertIn("사용법", g.run(["help"], self.dir))
        with self.assertRaisesRegex(g.GlossaryError, r"알 수 없는 커맨드[\s\S]*사용법"):
            g.run(["nope"], self.dir)
        with self.assertRaisesRegex(g.GlossaryError, r"커맨드를 지정하세요[\s\S]*사용법"):
            g.run([], self.dir)

    def test_version_matches_plugin_manifest(self):
        with open(os.path.join(ROOT, ".claude-plugin", "plugin.json"), encoding="utf-8") as f:
            manifest = json.load(f)
        self.assertEqual(g.VERSION, manifest["version"])


class ScaffoldTest(TempDirCase):
    def data_dir(self):
        return os.path.join(self.dir, ".claude", "superglossary")

    def test_assert_data_dir_placement(self):
        with self.assertRaisesRegex(g.GlossaryError, "\\.claude/superglossary/ 여야 합니다"):
            g.assert_data_dir_placement(os.path.join("/tmp", "plugin", "templates"))
        g.assert_data_dir_placement(os.path.join("/tmp", "proj", ".claude", "superglossary"))

    def test_initial_data_generated_products_and_claude_block(self):
        g.scaffold(self.data_dir())
        data = g.load_glossary(self.data_dir())
        self.assertTrue(any(t["korean"] == "일시" and t["abbreviation"] == "at" for t in data["terms"]), "일시=at")
        self.assertFalse(any(t["korean"] == "주소" for t in data["terms"]), "주소 없음")
        self.assertIn("identifier", load_file(os.path.join(self.data_dir(), "core.md")))
        claude = load_file(os.path.join(self.dir, ".claude", "CLAUDE.md"))
        self.assertIn("## 용어 사전", claude)
        self.assertIn("@superglossary/core.md", claude)

    def test_existing_claude_md_is_not_duplicated(self):
        os.makedirs(os.path.join(self.dir, ".claude"), exist_ok=True)
        write_file(os.path.join(self.dir, ".claude", "CLAUDE.md"), "# 기존\n\n## 용어 사전\n기존 내용\n")
        g.scaffold(self.data_dir())
        claude = load_file(os.path.join(self.dir, ".claude", "CLAUDE.md"))
        self.assertEqual(claude.count("## 용어 사전"), 1, "섹션 1개 유지")
        self.assertIn("# 기존", claude, "기존 내용 보존")

    def test_claude_block_mentions_add_skill_and_lookup(self):
        g.scaffold(self.data_dir())
        claude = load_file(os.path.join(self.dir, ".claude", "CLAUDE.md"))
        self.assertIn("add 스킬", claude)
        self.assertIn("lookup", claude)
        self.assertIn("@superglossary/core.md", claude)
        self.assertIn("python3 .claude/superglossary/glossary.py", claude)

    def test_no_gitignore_warning_outside_git_repo(self):
        self.assertEqual(g.scaffold(self.data_dir()), [])

    def test_gitignore_warning_when_claude_dir_is_ignored(self):
        if shutil.which("git") is None:
            self.skipTest("git 없는 환경")
        subprocess.run(["git", "init", "-q"], cwd=self.dir, check=True)
        write_file(os.path.join(self.dir, ".gitignore"), ".claude/\n")
        warnings = g.scaffold(self.data_dir())
        self.assertTrue(any("무시되어" in w for w in warnings), "무시 경고 포함")
        self.assertTrue(any("!.claude/superglossary/" in w for w in warnings), "해법 안내 포함")


class SchemaMigrationTest(TempDirCase):
    def test_v0_file_is_migrated_on_load(self):
        # 0.4.0 이전 파일: schemaVersion 없음, 일부 필드 누락
        write_file(os.path.join(self.dir, "glossary.json"),
                   json.dumps({"terms": [{"korean": "회원", "english": "member"}]}, ensure_ascii=False))
        data = g.load_glossary(self.dir)
        self.assertEqual(data["schemaVersion"], g.SCHEMA_VERSION)
        self.assertEqual(data["terms"][0]["avoid"], [])
        self.assertEqual(data["terms"][0]["relatedElements"], [])
        self.assertIsNone(data["terms"][0]["abbreviation"])
        self.assertEqual(data["terms"][0]["description"], "")

    def test_migrate_reports_whether_it_changed_anything(self):
        self.assertTrue(g.migrate({"terms": []}))
        self.assertFalse(g.migrate({"schemaVersion": g.SCHEMA_VERSION, "terms": []}))

    def test_future_schema_version_is_rejected(self):
        write_file(os.path.join(self.dir, "glossary.json"),
                   json.dumps({"schemaVersion": g.SCHEMA_VERSION + 1, "terms": []}))
        with self.assertRaisesRegex(g.GlossaryError, "CLI가 오래됐습니다"):
            g.load_glossary(self.dir)

    def test_init_rerun_upgrades_old_file_in_place(self):
        data_dir = os.path.join(self.dir, ".claude", "superglossary")
        os.makedirs(data_dir)
        write_file(os.path.join(data_dir, "glossary.json"),
                   json.dumps({"terms": [{"korean": "회원", "english": "member"}]}, ensure_ascii=False))
        g.scaffold(data_dir)
        raw = json.loads(load_file(os.path.join(data_dir, "glossary.json")))
        self.assertEqual(raw["schemaVersion"], g.SCHEMA_VERSION, "init 재실행이 스키마를 올린다")
        self.assertEqual(raw["terms"][0]["korean"], "회원", "기존 용어는 보존된다")


class StopwordsConfigTest(TempDirCase):
    def test_effective_stopwords_adds_and_removes(self):
        data = {"terms": [], "stopwords": {"add": ["Acme", "svc"], "remove": ["repository"]}}
        words = g.effective_stopwords(data)
        self.assertIn("acme", words, "add는 소문자로 정규화된다")
        self.assertIn("svc", words)
        self.assertNotIn("repository", words)
        self.assertIn("const", words, "기본 스톱워드는 유지된다")

    def test_effective_stopwords_defaults_to_builtin(self):
        self.assertEqual(g.effective_stopwords({"terms": []}), set(g.STOPWORDS))

    def test_lint_honors_project_stopwords(self):
        f = os.path.join(self.dir, "sample.js")
        write_file(f, "const acmeWidget = 1; const repositoryUrl = 2;")
        base = {"terms": []}
        tokens = {c["token"] for c in g.lint_files(base, [f])["candidates"]}
        self.assertIn("acme", tokens)
        self.assertNotIn("repository", tokens)

        tuned = {"terms": [], "stopwords": {"add": ["acme"], "remove": ["repository"]}}
        tokens = {c["token"] for c in g.lint_files(tuned, [f])["candidates"]}
        self.assertNotIn("acme", tokens, "add된 단어는 후보에서 빠진다")
        self.assertIn("repository", tokens, "remove된 단어는 후보로 올라온다")

    def test_avoid_still_beats_custom_stopwords(self):
        f = os.path.join(self.dir, "sample.js")
        write_file(f, "const acmeWidget = 1;")
        data = {"terms": [{"korean": "위젯", "english": "widget", "abbreviation": None, "avoid": ["acme"]}],
                "stopwords": {"add": ["acme"]}}
        violations = g.lint_files(data, [f])["violations"]
        self.assertEqual([v["token"] for v in violations], ["acme"], "금지 변형은 스톱워드보다 우선한다")


class ResolveDataDirTest(TempDirCase):
    def test_env_override_wins(self):
        target = os.path.join(self.dir, "elsewhere")
        resolved = g.resolve_data_dir(script_path=None, cwd=self.dir, env={"SUPERGLOSSARY_DIR": target})
        self.assertEqual(resolved, os.path.abspath(target))

    def test_script_inside_data_dir_uses_its_own_directory(self):
        # 프로젝트 복사본 모드 — 스크립트가 .claude/superglossary 안에 있다
        data_dir = os.path.join(self.dir, ".claude", "superglossary")
        os.makedirs(data_dir)
        script = os.path.join(data_dir, "glossary.py")
        write_file(script, "")
        self.assertEqual(g.resolve_data_dir(script, cwd="/", env={}), data_dir)

    def test_walks_up_from_cwd(self):
        # bin/ 모드 — 스크립트는 플러그인 안에 있고, 하위 디렉토리에서 실행한다
        data_dir = os.path.join(self.dir, ".claude", "superglossary")
        os.makedirs(data_dir)
        nested = os.path.join(self.dir, "src", "main", "java")
        os.makedirs(nested)
        plugin_script = os.path.join(self.dir, "plugin", "templates", "glossary.py")
        os.makedirs(os.path.dirname(plugin_script))
        write_file(plugin_script, "")
        self.assertEqual(g.resolve_data_dir(plugin_script, cwd=nested, env={}), data_dir)

    def test_falls_back_to_cwd_when_not_found(self):
        nested = os.path.join(self.dir, "fresh")
        os.makedirs(nested)
        self.assertEqual(g.resolve_data_dir(None, cwd=nested, env={}),
                         os.path.join(nested, ".claude", "superglossary"))

    def test_is_data_dir(self):
        self.assertTrue(g.is_data_dir(os.path.join("/proj", ".claude", "superglossary")))
        self.assertTrue(g.is_data_dir(os.path.join("/proj", ".claude", "superglossary") + os.sep))
        self.assertFalse(g.is_data_dir(os.path.join("/proj", "superglossary")))
        self.assertFalse(g.is_data_dir(os.path.join("/proj", ".claude")))


class BinEntryPointTest(unittest.TestCase):
    def test_bin_executable_runs_the_bundled_cli(self):
        script = os.path.join(ROOT, "bin", "superglossary")
        self.assertTrue(os.access(script, os.X_OK), "bin/superglossary는 실행 권한이 있어야 한다")
        done = subprocess.run([sys.executable, script, "version"], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn(g.VERSION, done.stdout)


class MainTest(TempDirCase):
    def test_main_returns_exit_code_on_error(self):
        with contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(g.main(["nope"]), 1)
        self.assertIn("알 수 없는 커맨드", err.getvalue())


if __name__ == "__main__":
    unittest.main()
