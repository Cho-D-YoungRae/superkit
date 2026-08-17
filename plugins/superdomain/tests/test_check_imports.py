import json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from check_imports import (BASELINE_MATCH_NOTE, BASELINE_RELATIVE, LIMITATION_NOTE, RULE_ID,
                           SKIP_DIRS, SOURCE_SUFFIXES, SRC_DIR, ZERO_MATCH_REASON,
                           _owning_context, check, render)

ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = Path(__file__).resolve().parent
SCRIPT = ROOT / "scripts" / "check_imports.py"

HEAD = """# 샘플 — Domain
<!-- superarchitect:template v1 -->

## 프로젝트: backend
- 경로: .
- 기본 패키지: com.acme
"""

CLAIM = """
## 컨텍스트: claim
- 분류: core
"""

ADMIN = """
## 컨텍스트: admin
- 분류: generic
"""

# `### 관계`는 컨텍스트 섹션 안에 놓인다 — 붙이는 자리에 따라 소속 컨텍스트가 달라진다.
RELATION_TO_ADMIN = """
### 관계
| 상대 | 유형 | 계약 |
|---|---|---|
| admin | customer-supplier | claim-events-v1 |
"""

RELATION_TO_CLAIM = """
### 관계
| 상대 | 유형 | 계약 |
|---|---|---|
| claim | acl | claim-events-v1 |
"""

# 복수 위치 컨텍스트 — `- 패키지:`가 규약 기본값을 대체한다.
MULTI_PACKAGE = """
## 컨텍스트: billing
- 분류: supporting
- 패키지: com.acme.web.billing.., com.acme.batch.billing..
"""

# 프로젝트 2개 — 컨텍스트가 각 프로젝트에 하나씩 붙는다.
MULTI_PROJECT = """# 샘플 — Domain
<!-- superarchitect:template v1 -->

## 프로젝트: backend
- 경로: backend
- 기본 패키지: com.acme

## 프로젝트: batch
- 경로: batch
- 기본 패키지: com.acme.batch

## 컨텍스트: claim
- 프로젝트: backend
- 분류: core

## 컨텍스트: billing
- 프로젝트: batch
- 분류: supporting
"""

LEAKY = "app/src/main/kotlin/com/acme/claim/Leaky.kt"


class CheckTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(dir=TESTS_DIR, prefix="tmp"))
        self.domain_path = self.tmpdir / "DOMAIN.md"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def domain(self, text):
        self.domain_path.write_text(text, encoding="utf-8")
        return self.domain_path

    def src(self, relpath, text):
        path = self.tmpdir / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def kt(self, package, name, imports=(), module="app"):
        """`<module>/src/main/kotlin/<패키지 경로>/<이름>.kt`에 최소 Kotlin 파일을 쓴다.

        import이 있으면 첫 import는 언제나 3번째 줄이다(package, 빈 줄, import…).
        """
        lines = [f"package {package}", ""]
        lines += [f"import {i}" for i in imports]
        if imports:
            lines.append("")
        lines.append(f"class {name}")
        relpath = f"{module}/src/main/kotlin/{package.replace('.', '/')}/{name}.kt"
        return self.src(relpath, "\n".join(lines) + "\n")

    def baseline(self, *lines):
        """`docs/domain/baseline.jsonl`을 쓴다 — 플래그 없이 자동 감지되는 자리."""
        path = self.tmpdir / BASELINE_RELATIVE
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(line + "\n" for line in lines), encoding="utf-8")
        return path

    def entry(self, rule, path, **extra):
        return json.dumps({"rule": rule, "path": path, **extra}, ensure_ascii=False)

    # ---- 관측 도우미 ------------------------------------------------------

    def check(self):
        return check(self.domain_path)

    def messages(self, report):
        return [f"{v.path}:{v.line}: {v.message}" for v in report.violations]

    def assert_violation(self, report, needle=None, count=None):
        self.assertTrue(report.violations, f"위반을 기대했지만 0건 (경고: {report.zero_match})")
        self.assertEqual({v.rule_id for v in report.violations}, {RULE_ID})
        if count is not None:
            self.assertEqual(len(report.violations), count, self.messages(report))
        if needle is not None:
            self.assertTrue(any(needle in v.message for v in report.violations),
                            self.messages(report))
        return report.violations[0]

    def assert_no_violation(self, report):
        self.assertEqual(self.messages(report), [])
        self.assertEqual(report.errors, [])

    # ---- 시나리오 --------------------------------------------------------

    def two_contexts(self, claim_extra="", admin_extra=""):
        """claim·admin 두 컨텍스트에 각각 소스가 하나씩 있는 최소 트리."""
        self.domain(HEAD + CLAIM + claim_extra + ADMIN + admin_extra)
        self.kt("com.acme.claim", "Claim")
        self.kt("com.acme.admin", "AdminUser")

    def leaky_tree(self, *imports):
        """claim이 admin을 참조하는 트리 — 위반 1건(LEAKY의 3번째 줄)."""
        self.two_contexts()
        self.kt("com.acme.claim", "Leaky",
                imports=list(imports) or ["com.acme.admin.AdminUser"])


class TestOwningContext(unittest.TestCase):
    """귀속의 핵심 — 접두 최장 일치, 세그먼트 경계, 미귀속은 None."""

    SCOPES = [("claim", ["com.acme.claim.."]), ("admin", ["com.acme.admin.."])]

    def test_exact_package_is_owned(self):
        self.assertEqual(_owning_context("com.acme.claim", self.SCOPES), "claim")

    def test_subpackage_is_owned(self):
        self.assertEqual(_owning_context("com.acme.claim.domain", self.SCOPES), "claim")

    def test_type_fqn_is_owned(self):
        self.assertEqual(_owning_context("com.acme.claim.Claim", self.SCOPES), "claim")

    def test_outside_every_context_is_none(self):
        self.assertIsNone(_owning_context("java.util.List", self.SCOPES))
        self.assertIsNone(_owning_context("com.acme", self.SCOPES))
        self.assertIsNone(_owning_context("com.acme.Shared", self.SCOPES))

    def test_sibling_prefix_is_not_absorbed(self):
        # 문자열 접두로만 보면 `com.acme.claim`이 `com.acme.claiming`을 삼킨다.
        self.assertIsNone(_owning_context("com.acme.claiming.Policy", self.SCOPES))

    def test_prefers_the_longest_prefix(self):
        # parse_domain의 겹침 검사가 오늘은 이런 문서를 막지만, 귀속이 매칭 순서에 좌우되면
        # 안 된다 — 순서를 뒤집어도 같은 답이어야 한다.
        nested = [("outer", ["com.acme.."]), ("inner", ["com.acme.claim.."])]
        self.assertEqual(_owning_context("com.acme.claim.Claim", nested), "inner")
        self.assertEqual(_owning_context("com.acme.claim.Claim", nested[::-1]), "inner")
        self.assertEqual(_owning_context("com.acme.other.X", nested), "outer")

    def test_multi_package_context_owns_every_package(self):
        scopes = [("billing", ["com.acme.web.billing..", "com.acme.batch.billing.."])]
        self.assertEqual(_owning_context("com.acme.web.billing.Invoice", scopes), "billing")
        self.assertEqual(_owning_context("com.acme.batch.billing.Job", scopes), "billing")

    def test_no_context_declared(self):
        self.assertIsNone(_owning_context("com.acme.claim.Claim", []))


class TestClean(CheckTestCase):
    def test_clean_tree_has_no_violation(self):
        self.two_contexts()
        report = self.check()
        self.assert_no_violation(report)

    def test_clean_tree_counts_one_rule_per_context(self):
        self.two_contexts()
        report = self.check()
        self.assertEqual(report.checked, 2)
        self.assertEqual(report.skipped, [])
        self.assertEqual(report.zero_match, [])

    def test_build_output_is_not_walked(self):
        self.two_contexts()
        self.src("app/build/generated/com/acme/claim/Gen.kt",
                 "package com.acme.claim\n\nimport com.acme.admin.AdminUser\n")
        self.src("app/out/Gen2.kt",
                 "package com.acme.claim\n\nimport com.acme.admin.AdminUser\n")
        self.assert_no_violation(self.check())

    def test_test_sources_are_not_walked(self):
        self.two_contexts()
        self.src("app/src/test/kotlin/com/acme/claim/ClaimTest.kt",
                 "package com.acme.claim\n\nimport com.acme.admin.AdminUser\n")
        self.assert_no_violation(self.check())


class TestContextIsolation(CheckTestCase):
    def test_cross_context_import_without_relation_is_violation(self):
        self.leaky_tree()
        violation = self.assert_violation(self.check(), needle="admin", count=1)
        self.assertEqual(violation.rule_id, RULE_ID)
        self.assertEqual(violation.path, LEAKY)
        self.assertEqual(violation.line, 3)
        self.assertIn("claim", violation.message)
        self.assertIn("관계", violation.message)

    def test_cross_context_import_with_relation_passes(self):
        self.two_contexts(claim_extra=RELATION_TO_ADMIN)
        self.kt("com.acme.claim", "Leaky", imports=["com.acme.admin.AdminUser"])
        self.assert_no_violation(self.check())

    def test_relation_declared_on_the_partner_side_opens_the_pair(self):
        # 허용 단위는 쌍이다 — 어느 섹션에 적든 같은 선언이다(context-mapping R1).
        self.two_contexts(admin_extra=RELATION_TO_CLAIM)
        self.kt("com.acme.claim", "Leaky", imports=["com.acme.admin.AdminUser"])
        self.assert_no_violation(self.check())

    def test_relation_kind_does_not_restrict_direction(self):
        # claim이 admin을 customer-supplier로 선언해도 admin → claim 방향까지 함께 열린다.
        self.two_contexts(claim_extra=RELATION_TO_ADMIN)
        self.kt("com.acme.admin", "Reverse", imports=["com.acme.claim.Claim"])
        self.assert_no_violation(self.check())

    def test_same_context_import_passes(self):
        self.two_contexts()
        self.kt("com.acme.claim.domain", "Policy", imports=["com.acme.claim.Claim"])
        self.assert_no_violation(self.check())

    def test_import_outside_any_context_ignored(self):
        self.two_contexts()
        self.kt("com.acme.claim", "Util",
                imports=["java.util.List", "com.acme.Shared", "org.springframework.stereotype.Component"])
        self.assert_no_violation(self.check())

    def test_source_outside_any_context_is_not_checked(self):
        # 어느 컨텍스트에도 속하지 않는 코드(조립·설정 등)는 이 검사의 대상이 아니다.
        self.two_contexts()
        self.kt("com.acme.wiring", "App",
                imports=["com.acme.claim.Claim", "com.acme.admin.AdminUser"])
        self.assert_no_violation(self.check())

    def test_wildcard_import_matches_prefix(self):
        self.two_contexts()
        self.kt("com.acme.claim", "Wild", imports=["com.acme.admin.*"])
        violation = self.assert_violation(self.check(), needle="com.acme.admin.*", count=1)
        self.assertEqual(violation.line, 3)

    def test_wildcard_import_of_a_deeper_package_matches(self):
        self.two_contexts()
        self.kt("com.acme.claim", "Wild", imports=["com.acme.admin.internal.*"])
        self.assert_violation(self.check(), needle="com.acme.admin.internal.*", count=1)

    def test_wildcard_import_does_not_reach_subpackages(self):
        # `com.acme.*`는 그 패키지의 멤버만 들여온다 — 컨텍스트 패키지는 들어오지 않는다.
        self.two_contexts()
        self.kt("com.acme.claim", "Wild", imports=["com.acme.*"])
        self.assert_no_violation(self.check())

    def test_sibling_prefix_context_is_not_absorbed(self):
        # `claim`과 `claiming`은 형제다 — 접두가 겹쳐 보여도 세그먼트 경계에서 갈린다.
        self.domain(HEAD + CLAIM + """
## 컨텍스트: claiming
- 분류: supporting
""")
        self.kt("com.acme.claim", "Claim")
        self.kt("com.acme.claiming", "Legacy", imports=["com.acme.claim.Claim"])
        violation = self.assert_violation(self.check(), needle="claiming", count=1)
        self.assertIn("claim", violation.message)

    def test_explicit_package_replaces_the_convention_default(self):
        # `- 패키지:`를 적으면 규약 기본값(`com.acme.admin..`)은 쓰이지 않는다.
        self.domain(HEAD + CLAIM + """
## 컨텍스트: admin
- 분류: generic
- 패키지: com.acme.backoffice..
""")
        self.kt("com.acme.claim", "Leaky", imports=["com.acme.backoffice.AdminUser"])
        # 구 규약 자리(com.acme.admin)는 이제 어느 컨텍스트도 아니다.
        self.kt("com.acme.claim", "Legacy", imports=["com.acme.admin.Ghost"])
        report = self.check()
        violation = self.assert_violation(report, needle="com.acme.backoffice.AdminUser", count=1)
        self.assertTrue(violation.path.endswith("Leaky.kt"), violation.path)

    def test_explicit_multi_package_context(self):
        self.domain(HEAD + CLAIM + MULTI_PACKAGE)
        # 두 패키지 모두 billing에 귀속된다 — 서로 참조해도 같은 컨텍스트다.
        self.kt("com.acme.web.billing", "Controller",
                imports=["com.acme.batch.billing.Job"])
        self.kt("com.acme.batch.billing", "Job")
        self.assert_no_violation(self.check())

    def test_multi_package_context_still_guards_the_boundary(self):
        self.domain(HEAD + CLAIM + MULTI_PACKAGE)
        self.kt("com.acme.batch.billing", "Job")
        self.kt("com.acme.claim", "Leaky", imports=["com.acme.batch.billing.Job"])
        self.assert_violation(self.check(), needle="billing", count=1)

    def test_two_imports_in_one_file_are_two_violations(self):
        self.leaky_tree("com.acme.admin.AdminUser", "com.acme.admin.Role")
        report = self.check()
        self.assert_violation(report, count=2)
        self.assertEqual([v.line for v in report.violations], [3, 4])

    def test_cross_project_cross_context_is_a_violation(self):
        self.domain(MULTI_PROJECT)
        self.kt("com.acme.claim", "Claim", module="backend")
        self.kt("com.acme.batch.billing", "Invoice", module="batch")
        self.kt("com.acme.claim", "Leaky", module="backend",
                imports=["com.acme.batch.billing.Invoice"])
        self.assert_violation(self.check(), needle="billing", count=1)

    def test_attribution_follows_the_package_not_the_directory(self):
        # 파일이 어느 프로젝트 디렉터리에 놓였든 귀속은 package 선언이 정한다.
        self.domain(MULTI_PROJECT)
        self.kt("com.acme.claim", "Claim", module="backend")
        self.kt("com.acme.batch.billing", "Misplaced", module="backend",
                imports=["com.acme.claim.Claim"])
        (self.tmpdir / "batch").mkdir(exist_ok=True)
        report = self.check()
        self.assert_violation(report, needle="billing", count=1)
        # billing에 귀속된 소스가 있으므로 0건 경고도, 생략도 아니다.
        self.assertEqual(report.zero_match, [])
        self.assertEqual(report.skipped, [])


class TestSourceParsing(CheckTestCase):
    def test_kotlin_import_alias(self):
        self.two_contexts()
        self.kt("com.acme.claim", "Aliased", imports=["com.acme.admin.AdminUser as User"])
        self.assert_violation(self.check(), needle="com.acme.admin.AdminUser", count=1)

    def test_java_source_is_checked(self):
        self.two_contexts()
        self.src("app/src/main/java/com/acme/claim/Leaky.java",
                 "package com.acme.claim;\n\n"
                 "import com.acme.admin.AdminUser;\n\n"
                 "public class Leaky {}\n")
        violation = self.assert_violation(self.check(), needle="com.acme.admin.AdminUser", count=1)
        self.assertTrue(violation.path.endswith("Leaky.java"), violation.path)
        self.assertEqual(violation.line, 3)

    def test_java_static_import(self):
        self.two_contexts()
        self.src("app/src/main/java/com/acme/claim/Static.java",
                 "package com.acme.claim;\n\n"
                 "import static com.acme.admin.Roles.ADMIN;\n\n"
                 "public class Static {}\n")
        self.assert_violation(self.check(), needle="com.acme.admin.Roles.ADMIN", count=1)

    def test_source_without_a_package_declaration_is_ignored(self):
        self.two_contexts()
        self.src("app/src/main/kotlin/Loose.kt", "import com.acme.admin.AdminUser\n\nclass Loose\n")
        self.assert_no_violation(self.check())


class TestRawTextScanning(CheckTestCase):
    """주석·문자열을 지우지 않고 원문을 읽는 선택의 **특성화 테스트**.

    두 방향의 대가가 정반대다. `import` 쪽은 오탐(시끄러운 실패)이라 그대로 두고, `package`
    쪽은 미탐(조용한 실패)이라 고지로 막는다. 의식적 판단이므로 여기 못 박는다 — 다음 사람이
    한 방향만 보고 뒤집지 않도록.
    """

    def test_import_inside_a_block_comment_is_reported(self):
        # **의도된 오탐이다.** 주석 마스킹을 되살리면 그 함수의 결함 하나가 import를 통째로
        # 삼켜 검사가 조용해진다 — 오탐(시끄러움)이 미탐(조용함)보다 안전하다는 판단.
        self.two_contexts()
        self.src("app/src/main/kotlin/com/acme/claim/Commented.kt",
                 "package com.acme.claim\n"
                 "\n"
                 "/*\n"
                 "import com.acme.admin.AdminUser\n"
                 "*/\n"
                 "class Commented\n")
        violation = self.assert_violation(self.check(), needle="com.acme.admin.AdminUser", count=1)
        self.assertEqual(violation.line, 4)

    def test_import_inside_a_raw_string_is_reported(self):
        # 같은 판단의 다른 얼굴 — raw string 안의 코드 예시도 위반으로 보고된다.
        self.two_contexts()
        self.src("app/src/main/kotlin/com/acme/claim/Snippet.kt",
                 "package com.acme.claim\n"
                 "\n"
                 'val SAMPLE = """\n'
                 "import com.acme.admin.AdminUser\n"
                 '"""\n')
        self.assert_violation(self.check(), needle="com.acme.admin.AdminUser", count=1)

    def test_multiple_package_declarations_are_announced(self):
        # 주석 처리된 옛 선언이 앞에 있으면 귀속이 통째로 뒤집혀 위반이 사라진다 ✅ 실측.
        # 위반으로 만들 수는 없으므로(어느 선언이 진짜인지 이 검사기는 모른다) 그 사실을 고지한다.
        self.two_contexts()
        self.src("app/src/main/kotlin/com/acme/claim/Leaky.kt",
                 "/*\n"
                 "package com.acme.admin\n"
                 "*/\n"
                 "package com.acme.claim\n"
                 "\n"
                 "import com.acme.admin.AdminUser\n"
                 "\n"
                 "class Leaky\n")
        report = self.check()
        self.assertEqual(len(report.ambiguous_package), 1, report.ambiguous_package)
        notice = report.ambiguous_package[0]
        self.assertEqual(notice.path, LEAKY)
        self.assertEqual(notice.count, 2)
        self.assertEqual(notice.package, "com.acme.admin")   # 첫 매칭이 귀속을 정했다
        line = next(l for l in render(report) if l.startswith("package 선언이 여러 건인 소스"))
        self.assertIn(LEAKY, line)
        self.assertIn("믿을 수 없습니다", line)

    def test_the_announcement_does_not_change_the_exit_code(self):
        # 경고성 고지이므로 기존 규율대로 exit을 바꾸지 않는다.
        self.two_contexts()
        self.src("app/src/main/kotlin/com/acme/claim/Leaky.kt",
                 "/*\npackage com.acme.admin\n*/\npackage com.acme.claim\n\n"
                 "import com.acme.admin.AdminUser\n")
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.domain_path)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("package 선언이 여러 건인 소스 1건", result.stdout)

    def test_a_single_package_declaration_is_not_announced(self):
        self.two_contexts()
        self.assertEqual(self.check().ambiguous_package, [])

    def test_json_carries_the_announcement(self):
        self.two_contexts()
        self.src("app/src/main/kotlin/com/acme/claim/Leaky.kt",
                 "/*\npackage com.acme.admin\n*/\npackage com.acme.claim\n")
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.domain_path), "--json"],
                                capture_output=True, text=True)
        payload = json.loads(result.stdout)
        self.assertEqual(sorted(payload["ambiguous_package"][0]),
                         ["count", "package", "path"])
        self.assertEqual(payload["ambiguous_package"][0]["path"], LEAKY)


class TestSourceTreeContract(CheckTestCase):
    """`SKIP_DIRS`·`SOURCE_SUFFIXES`·`SRC_DIR`은 check_invariants와 공유하는 불변 계약이다."""

    def test_constants_are_unchanged(self):
        self.assertEqual(SOURCE_SUFFIXES, (".kt", ".java"))
        self.assertEqual(SRC_DIR, "src")
        self.assertEqual(sorted(SKIP_DIRS),
                         [".git", ".gradle", ".idea", ".kotlin", ".settings", ".venv",
                          "build", "node_modules", "out", "target"])

    def test_every_skip_dir_is_pruned(self):
        self.two_contexts()
        for index, name in enumerate(sorted(SKIP_DIRS)):
            self.src(f"app/{name}/Gen{index}.kt",
                     "package com.acme.claim\n\nimport com.acme.admin.AdminUser\n")
        self.assert_no_violation(self.check())

    def test_suffixed_test_source_set_is_not_walked(self):
        # `src/androidTest`는 `endswith("Test")` 갈래다 — `test*` 갈래와 함께 걷지 않는다.
        self.two_contexts()
        self.src("app/src/androidTest/kotlin/com/acme/claim/UiTest.kt",
                 "package com.acme.claim\n\nimport com.acme.admin.AdminUser\n")
        self.src("app/src/integrationTest/kotlin/com/acme/claim/ItTest.kt",
                 "package com.acme.claim\n\nimport com.acme.admin.AdminUser\n")
        self.assert_no_violation(self.check())

    def test_a_test_named_directory_outside_src_is_still_walked(self):
        # 제외는 `src/` 바로 아래의 소스셋 이름에만 걸린다 — 그 밖의 `testing` 패키지는
        # 프로덕션 코드일 수 있으므로 걷는다.
        self.two_contexts()
        self.src("app/src/main/kotlin/com/acme/claim/testkit/Fixture.kt",
                 "package com.acme.claim.testkit\n\nimport com.acme.admin.AdminUser\n")
        self.assert_violation(self.check(), needle="com.acme.admin.AdminUser", count=1)


class TestSilenceGuards(CheckTestCase):
    def test_context_with_zero_sources_warns(self):
        self.domain(HEAD + CLAIM + ADMIN)
        self.kt("com.acme.claim", "Claim")
        report = self.check()
        self.assertEqual([w.subject for w in report.zero_match], ["컨텍스트 admin"])
        self.assertEqual(report.violations, [])
        self.assertEqual(report.checked, 2)
        self.assertIn(f"[0건 경고] {RULE_ID}: {ZERO_MATCH_REASON} (컨텍스트 admin)",
                      render(report))

    def test_zero_source_warning_does_not_change_the_exit_code(self):
        self.domain(HEAD + CLAIM + ADMIN)
        self.kt("com.acme.claim", "Claim")
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.domain_path)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("[0건 경고]", result.stdout)

    def test_wrong_base_package_warns_for_every_context(self):
        # 기본 패키지 오타는 모든 컨텍스트를 0건으로 만든다 — 위반 0건과 구분되어야 한다.
        self.domain(HEAD.replace("- 기본 패키지: com.acme", "- 기본 패키지: com.acmee")
                    + CLAIM + ADMIN)
        self.kt("com.acme.claim", "Claim")
        self.kt("com.acme.admin", "AdminUser")
        report = self.check()
        self.assertEqual(sorted(w.subject for w in report.zero_match),
                         ["컨텍스트 admin", "컨텍스트 claim"])
        self.assertEqual(report.violations, [])

    def test_no_zero_match_warning_when_sources_match(self):
        self.two_contexts()
        self.assertEqual(self.check().zero_match, [])

    def test_missing_project_path_is_skipped_with_notice(self):
        self.domain(HEAD.replace("- 경로: .", "- 경로: backend") + CLAIM + ADMIN)
        report = self.check()
        self.assertEqual(report.violations, [])
        self.assertEqual(report.checked, 0)
        self.assertEqual(sorted(s.subject for s in report.skipped),
                         ["컨텍스트 admin", "컨텍스트 claim"])
        self.assertTrue(all("backend" in s.reason for s in report.skipped), report.skipped)
        self.assertTrue(all("경로가 아직 없습니다" in s.reason for s in report.skipped),
                        report.skipped)
        self.assertEqual(report.zero_match, [], "생략은 0건 경고와 겹치지 않는다")

    def test_project_without_sources_is_skipped_with_notice(self):
        self.domain(HEAD + CLAIM + ADMIN)
        (self.tmpdir / "app").mkdir()
        report = self.check()
        self.assertEqual(len(report.skipped), 2, report.skipped)
        self.assertNotIn("경로가 아직 없습니다", report.skipped[0].reason)
        self.assertIn(".kt/.java", report.skipped[0].reason)

    def test_unreadable_only_project_says_so_instead_of_no_sources(self):
        # 소스는 있는데 전부 읽지 못한 것이다. "소스가 없습니다"라고 말하면 바로 아래
        # `읽지 못한 소스 1건` 줄과 정면으로 모순된다 — 사용자가 엉뚱한 데를 본다.
        self.domain(HEAD + CLAIM + ADMIN)
        path = self.tmpdir / "app/src/main/kotlin/com/acme/claim/Cp949.kt"
        path.parent.mkdir(parents=True)
        path.write_bytes("package com.acme.claim\n\n// 주석\nclass Odd\n".encode("euc-kr"))
        report = self.check()
        self.assertEqual(len(report.skipped), 2, report.skipped)
        reason = report.skipped[0].reason
        self.assertIn("전부 읽지 못했습니다", reason)
        self.assertIn("인코딩", reason)
        self.assertNotIn("소스가 없습니다", reason)
        self.assertEqual(len(report.unreadable), 1, report.unreadable)
        lines = render(report)
        self.assertTrue(any("읽지 못한 소스 1건" in line for line in lines), lines)

    def test_project_path_pointing_at_a_file_says_so(self):
        # 경로는 있고 종류가 틀렸다 — "경로가 아직 없습니다"라고 하면 없는 것을 찾게 만든다.
        self.domain(HEAD.replace("- 경로: .", "- 경로: backend.txt") + CLAIM + ADMIN)
        (self.tmpdir / "backend.txt").write_text("파일이다\n", encoding="utf-8")
        report = self.check()
        self.assertEqual(len(report.skipped), 2, report.skipped)
        reason = report.skipped[0].reason
        self.assertIn("디렉터리가 아닙니다", reason)
        self.assertNotIn("경로가 아직 없습니다", reason)

    def test_only_the_barren_projects_contexts_are_skipped(self):
        self.domain(MULTI_PROJECT)
        self.kt("com.acme.claim", "Claim", module="backend")
        report = self.check()
        self.assertEqual([s.subject for s in report.skipped], ["컨텍스트 billing"])
        self.assertEqual(report.zero_match, [])
        self.assertEqual(report.checked, 1)

    def test_document_without_a_context_is_not_silent(self):
        self.domain(HEAD)
        self.kt("com.acme.claim", "Claim")
        report = self.check()
        self.assertEqual(report.violations, [])
        self.assertEqual(report.checked, 0)
        self.assertEqual(len(report.skipped), 1, report.skipped)
        self.assertIn("컨텍스트", report.skipped[0].reason)
        self.assertTrue(any(line.startswith("생략:") for line in render(report)))

    def test_unreadable_source_is_reported(self):
        # UTF-8이 아닌 소스는 파싱할 수 없다. 조용히 빼면 어떤 검사도 그 파일을 보지 못한다.
        self.two_contexts()
        path = self.tmpdir / "app/src/main/kotlin/com/acme/claim/Cp949.kt"
        path.write_bytes("package com.acme.claim\n\n// 주석\nclass Odd\n".encode("euc-kr"))
        report = self.check()
        self.assertEqual(len(report.unreadable), 1, report.unreadable)
        self.assertTrue(report.unreadable[0].endswith("Cp949.kt"), report.unreadable)
        self.assertTrue(any("읽지 못한 소스 1건" in line for line in render(report)))

    def test_footer_counts_checked_and_skipped(self):
        self.domain(MULTI_PROJECT)
        self.kt("com.acme.claim", "Claim", module="backend")
        report = self.check()
        lines = render(report)
        self.assertIn("검사한 규칙 1건 / 생략한 규칙 1건", lines)
        self.assertTrue(any(line.startswith("생략:") and "billing" in line for line in lines))

    def test_footer_states_the_limitation(self):
        self.two_contexts()
        lines = render(self.check())
        self.assertIn(LIMITATION_NOTE, lines)
        self.assertIn("같은 패키지", LIMITATION_NOTE)
        self.assertIn("FQN", LIMITATION_NOTE)

    def test_footer_does_not_promise_a_generated_test(self):
        # fitness 스킬은 삭제됐다 — 푸터의 한계 줄은 언제나 참이어야 한다.
        self.assertNotIn("Konsist", LIMITATION_NOTE)
        self.assertNotIn("ArchUnit", LIMITATION_NOTE)


class TestBaseline(CheckTestCase):
    """브라운필드의 래칫 — 기존 부채는 warn, 신규만 blocker."""

    def test_baselined_violation_not_reported(self):
        self.leaky_tree()
        self.baseline(self.entry(RULE_ID, LEAKY))
        report = self.check()
        self.assertEqual(report.violations, [], self.messages(report))
        self.assertEqual([(v.rule_id, v.path) for v in report.debt], [(RULE_ID, LEAKY)])

    def test_new_violation_reported_despite_baseline(self):
        # 같은 규칙이라도 다른 경로는 동결된 적이 없다 — 래칫의 본체다.
        self.leaky_tree()
        self.baseline(self.entry(RULE_ID, "app/src/main/kotlin/com/acme/claim/Old.kt"))
        report = self.check()
        self.assert_violation(report, count=1)
        self.assertEqual(report.debt, [])

    def test_note_field_is_optional(self):
        self.leaky_tree()
        self.baseline(self.entry(RULE_ID, LEAKY, note="2026-08-17 동결"))
        self.assertEqual([v.rule_id for v in self.check().debt], [RULE_ID])

    def test_blank_lines_are_tolerated(self):
        self.leaky_tree()
        self.baseline("", self.entry(RULE_ID, LEAKY), "   ")
        self.assertEqual([v.rule_id for v in self.check().debt], [RULE_ID])

    def test_same_rule_and_path_absorbs_additional_violations(self):
        # line을 키에서 뺀 대가 — 같은 파일의 **추가** 위반도 함께 흡수된다. 고지는 푸터가 한다.
        self.leaky_tree("com.acme.admin.AdminUser", "com.acme.admin.Role")
        self.baseline(self.entry(RULE_ID, LEAKY))
        report = self.check()
        self.assertEqual(len(report.debt), 2, report.debt)
        self.assertEqual(report.violations, [])
        self.assertIn(BASELINE_MATCH_NOTE, render(report))

    def test_footer_reports_the_debt_and_its_limit(self):
        self.leaky_tree()
        self.baseline(self.entry(RULE_ID, LEAKY))
        lines = render(self.check())
        self.assertTrue(any(line.startswith(f"[기존 부채] {LEAKY}:3: [{RULE_ID}]")
                            for line in lines), lines)
        self.assertTrue(any(line.startswith("기존 부채 1건") and BASELINE_RELATIVE in line
                            for line in lines), lines)
        self.assertIn(BASELINE_MATCH_NOTE, lines)
        self.assertIn("추가", BASELINE_MATCH_NOTE)

    def test_footer_reports_entries_that_matched_nothing(self):
        self.leaky_tree()
        self.baseline(self.entry(RULE_ID, LEAKY),
                      self.entry(RULE_ID, "app/src/main/kotlin/com/acme/claim/Gone.kt"))
        line = next(l for l in render(self.check()) if l.startswith("기존 부채"))
        self.assertIn("2개 항목 중 1개", line)

    def test_no_baseline_leaves_the_footer_silent(self):
        self.leaky_tree()
        lines = render(self.check())
        self.assertEqual([l for l in lines if l.startswith(("[기존 부채]", "기존 부채"))], [])
        self.assertNotIn(BASELINE_MATCH_NOTE, lines)

    def test_broken_line_is_an_error_not_a_silent_pass(self):
        # 깨진 줄 하나면 어느 위반이 동결분인지 전체를 알 수 없다 — 부분적으로 믿느니 세우지 않는다.
        self.leaky_tree()
        self.baseline(self.entry(RULE_ID, LEAKY), '{"rule": "derived.context-isolation"}')
        report = self.check()
        self.assertEqual(report.violations, [])
        self.assertEqual(len(report.errors), 1, report.errors)
        self.assertEqual(report.errors[0].line, 2)
        self.assertEqual(report.errors[0].path, BASELINE_RELATIVE)
        self.assertIn("path", report.errors[0].message)

    def test_malformed_json_line_is_an_error(self):
        self.leaky_tree()
        self.baseline("이건 JSON이 아니다")
        report = self.check()
        self.assertEqual(len(report.errors), 1, report.errors)
        self.assertEqual(report.errors[0].line, 1)


class TestCli(CheckTestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args],
                              capture_output=True, text=True)

    def test_exit_zero_when_clean(self):
        self.two_contexts()
        result = self.run_cli(str(self.domain_path))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(LIMITATION_NOTE, result.stdout)

    def test_exit_one_when_violation(self):
        self.leaky_tree()
        result = self.run_cli(str(self.domain_path))
        self.assertEqual(result.returncode, 1, result.stdout)
        line = next(l for l in result.stdout.split("\n") if RULE_ID in l)
        self.assertRegex(line, r"^.+Leaky\.kt:3: \[derived\.context-isolation\] ")

    def test_exit_two_when_unresolvable(self):
        self.two_contexts()
        self.domain(HEAD + CLAIM.replace("- 분류: core", "- 분류: bogus") + ADMIN)
        result = self.run_cli(str(self.domain_path))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr.startswith(f"{self.domain_path}:"), result.stderr)
        self.assertIn("분류 값 'bogus'", result.stderr)

    def test_exit_two_when_file_missing(self):
        result = self.run_cli(str(self.tmpdir / "없는파일.md"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("읽을 수 없습니다", result.stderr)

    def test_usage_error(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn("사용법", result.stderr)
        self.assertIn("DOMAIN.md", result.stderr)

    def test_json_output(self):
        self.leaky_tree()
        result = self.run_cli(str(self.domain_path), "--json")
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(sorted(payload),
                         ["ambiguous_package", "baseline", "checked", "inherited", "skipped",
                          "unreadable", "violations", "zero_match"])
        self.assertEqual(sorted(payload["violations"][0]),
                         ["line", "message", "path", "rule_id"])
        self.assertEqual(payload["violations"][0]["rule_id"], RULE_ID)
        self.assertEqual(payload["checked"], 2)

    def test_json_carries_warnings(self):
        self.domain(HEAD + CLAIM + ADMIN)
        self.kt("com.acme.claim", "Claim")
        result = self.run_cli(str(self.domain_path), "--json")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["violations"], [])
        self.assertTrue(payload["zero_match"], payload)
        self.assertEqual(sorted(payload["zero_match"][0]), ["message", "rule_id", "subject"])

    def test_json_carries_skips(self):
        self.domain(MULTI_PROJECT)
        self.kt("com.acme.claim", "Claim", module="backend")
        payload = json.loads(self.run_cli(str(self.domain_path), "--json").stdout)
        self.assertEqual(sorted(payload["skipped"][0]), ["reason", "rule_id", "subject"])
        self.assertEqual(payload["skipped"][0]["subject"], "컨텍스트 billing")

    def test_baseline_is_detected_without_a_flag_and_does_not_change_exit(self):
        self.leaky_tree()
        self.baseline(self.entry(RULE_ID, LEAKY))
        result = self.run_cli(str(self.domain_path))
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn(f"[기존 부채] {LEAKY}:3: [{RULE_ID}]", result.stdout)
        self.assertIn(BASELINE_MATCH_NOTE, result.stdout)

    def test_broken_baseline_line_exits_two(self):
        self.two_contexts()
        self.baseline('{"rule": "derived.context-isolation", "path": 3}')
        result = self.run_cli(str(self.domain_path))
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr.startswith(f"{BASELINE_RELATIVE}:1: "), result.stderr)

    def test_json_carries_the_baseline_channel(self):
        self.leaky_tree("com.acme.admin.AdminUser")
        self.kt("com.acme.claim", "Other", imports=["com.acme.admin.Role"])
        self.baseline(self.entry(RULE_ID, LEAKY))
        result = self.run_cli(str(self.domain_path), "--json")
        self.assertEqual(result.returncode, 1)      # Other.kt의 위반은 신규로 남는다
        payload = json.loads(result.stdout)
        self.assertEqual(sorted(payload["baseline"]), ["demoted", "entries", "note", "path"])
        self.assertEqual(payload["baseline"]["path"], BASELINE_RELATIVE)
        self.assertEqual(payload["baseline"]["entries"], 1)
        self.assertEqual([v["path"] for v in payload["baseline"]["demoted"]], [LEAKY])
        self.assertEqual(len(payload["violations"]), 1)
        self.assertTrue(payload["violations"][0]["path"].endswith("Other.kt"))

    def test_json_baseline_channel_is_empty_without_the_file(self):
        self.two_contexts()
        payload = json.loads(self.run_cli(str(self.domain_path), "--json").stdout)
        self.assertEqual(payload["baseline"],
                         {"path": None, "entries": 0, "demoted": [], "note": None})

    def test_violation_lines_are_sorted_by_path_and_line(self):
        self.two_contexts()
        self.kt("com.acme.claim", "BBB", imports=["com.acme.admin.AdminUser"])
        self.kt("com.acme.claim", "AAA", imports=["com.acme.admin.AdminUser"])
        result = self.run_cli(str(self.domain_path))
        lines = [l for l in result.stdout.split("\n") if l.startswith("app/")]
        self.assertEqual(lines, sorted(lines))
        self.assertEqual(len(lines), 2, lines)
        self.assertIn("AAA.kt", lines[0])
        self.assertIn("BBB.kt", lines[1])


if __name__ == "__main__":
    unittest.main()
