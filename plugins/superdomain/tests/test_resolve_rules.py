import json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from resolve_rules import (DERIVED_KINDS, KIND_APP_CONFINEMENT, derived_rule_id,
                           format_error, resolve, resolve_document)

ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = Path(__file__).resolve().parent
FIXTURES = TESTS_DIR / "fixtures"
SCRIPT = ROOT / "scripts" / "resolve_rules.py"
FULL_PATH = FIXTURES / "full.md"

MINIMAL = (FIXTURES / "minimal.md").read_text(encoding="utf-8")
FULL = FULL_PATH.read_text(encoding="utf-8")

# 커스텀 스타일 문서 — 대상 프로젝트의 docs/architecture/styles/<이름>.md에 놓인다.
PORTS_LITE = """# ports-lite

## 선언

- 레이어: core, edge

| 규칙 id | primitive | 파라미터 |
|---|---|---|
| pl.deps-inward | layer-order | layers=core,edge |
| pl.no-framework | forbid-import | from=core; to=org.springframework.. |
"""

# D3의 두 조건을 하나씩만 만족하는 스타일 둘 — 어느 쪽도 domain-pure가 아니다.
PORTS_PURE = """## 선언

- 레이어: core, edge

| 규칙 id | primitive | 파라미터 |
|---|---|---|
| pp.pure | confine-type | type=jpa-entity; allowed_layer=edge |
"""

PLAIN_DOMAIN = """## 선언

- 레이어: domain, edge

| 규칙 id | primitive | 파라미터 |
|---|---|---|
| pd.deps-inward | layer-order | layers=domain,edge |
"""

# 레이어 이름이 유효한 패키지 세그먼트가 아닌 스타일(§5.3 행 3의 재현).
HYPHEN_STYLE = """## 선언

- 레이어: domain, interface-adapter

| 규칙 id | primitive | 파라미터 |
|---|---|---|
| ia.deps-inward | layer-order | layers=domain,interface-adapter |
"""

# 파라미터 셀이 깨진 스타일 — 오류가 스타일 파일 경로로 전파되는지 본다.
BROKEN_STYLE = """## 선언

- 레이어: core, edge

| 규칙 id | primitive | 파라미터 |
|---|---|---|
| pl.deps-inward | layer-order | layers |
"""

HEAD = """# 샘플 — Architecture
<!-- superarchitect:template v1 -->

## 프로젝트: backend
- 경로: .
- 프로파일: kotlin-spring
- 기본 패키지: com.acme
- 아키텍처 테스트 위치: architecture-test/src/test/kotlin
"""

CUSTOM_ARCH = HEAD + """
## 컨텍스트: claim
- 분류: core
- 스타일: custom/{name}
- 모듈 구성: multi-module

| 모듈 | 경로 | 레이어 |
|---|---|---|
| claim-core | claim/core | {layer_a} |
| claim-edge | claim/edge | {layer_b} |
"""

TWO_CONTEXT_ARCH = HEAD + """
## 컨텍스트: claim
- 분류: core
- 스타일: custom/{name}
- 모듈 구성: single-module

| 모듈 | 경로 | 레이어 |
|---|---|---|
| claim | claim | all |

## 컨텍스트: billing
- 분류: supporting
- 스타일: custom/{name}
- 모듈 구성: single-module

| 모듈 | 경로 | 레이어 |
|---|---|---|
| billing | billing | all |
"""

SHARED_MODULE_TABLE = """
### 공용 모듈
| 모듈 | 경로 | 역할 |
|---|---|---|
| logging | support/logging | support |
"""

# 컨텍스트 이름이 유효한 패키지 세그먼트가 아닌 문서 — 기본 관례에서는 컨텍스트도 세그먼트다(§6).
HYPHEN_CONTEXT_ARCH = HEAD + """
## 컨텍스트: order-mgmt
- 분류: core
- 스타일: custom/ports-lite
- 모듈 구성: multi-module

| 모듈 | 경로 | 레이어 |
|---|---|---|
| order-core | order/core | core |
| order-edge | order/edge | edge |
"""

TEST_LOCATION_LINE = "- 아키텍처 테스트 위치: architecture-test/src/test/kotlin"

SHARED_ARCH = HEAD + SHARED_MODULE_TABLE + """
## 컨텍스트: claim
- 분류: core
- 스타일: custom/{name}
- 모듈 구성: multi-module

| 모듈 | 경로 | 레이어 |
|---|---|---|
| claim-a | claim/a | {layer_a} |
| claim-b | claim/b | {layer_b} |
"""


def line_of(text, needle):
    """needle이 처음 등장하는 줄의 1-기준 라인 번호."""
    for i, line in enumerate(text.split("\n")):
        if needle in line:
            return i + 1
    raise AssertionError(f"'{needle}'을(를) 문서에서 찾지 못했습니다.")


def with_label(text, after, label):
    """`after` 줄 바로 뒤에 한 덩어리를 끼워 넣는다."""
    return text.replace(after, f"{after}\n{label}", 1)


def with_conventions(text, *rows):
    """프로젝트 섹션 끝에 '### 패키지 규약' 표를 끼워 넣는다(행은 (레이어, 패턴) 쌍)."""
    body = "".join(f"| {layer} | {pattern} |\n" for layer, pattern in rows)
    return with_label(text, TEST_LOCATION_LINE,
                      f"\n### 패키지 규약\n| 레이어 | 패턴 |\n|---|---|\n{body}")


class ResolveTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(dir=TESTS_DIR, prefix="tmp"))

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def write(self, arch_text, styles=None):
        """임시 프로젝트에 ARCHITECTURE.md(+커스텀 스타일 문서)를 쓰고 그 경로를 돌려준다."""
        path = self.tmpdir / "ARCHITECTURE.md"
        path.write_text(arch_text, encoding="utf-8")
        for name, body in (styles or {}).items():
            style_path = self.tmpdir / "docs" / "architecture" / "styles" / f"{name}.md"
            style_path.parent.mkdir(parents=True, exist_ok=True)
            style_path.write_text(body, encoding="utf-8")
        return path

    def resolve_text(self, arch_text, styles=None):
        return resolve_document(self.write(arch_text, styles))

    def assert_clean(self, resolution):
        self.assertEqual([e.message for e in resolution.errors], [])
        return resolution

    def assert_one_error(self, resolution, needle, line=None):
        messages = [e.message for e in resolution.errors]
        self.assertEqual(len(messages), 1, f"오류 1건을 기대했지만 {messages}")
        self.assertIn(needle, messages[0])
        if line is not None:
            self.assertEqual(resolution.errors[0].line, line)
        return resolution.errors[0]

    def rules_of(self, resolution, context):
        return [r for r in resolution.effective if r.context == context]

    def derived_of(self, resolution, kind, subject=None):
        found = [d for d in resolution.derived if d.kind == kind
                 and (subject is None or d.subject == subject)]
        if subject is not None:
            self.assertEqual(len(found), 1, f"{kind}/{subject} 1건을 기대했지만 {len(found)}건")
            return found[0]
        return found


class TestEffectiveRules(ResolveTestCase):
    def test_hexagonal_effective_rules(self):
        resolution = self.assert_clean(self.resolve_text(MINIMAL))
        rules = self.rules_of(resolution, "claim")
        self.assertEqual([r.rule_id for r in rules],
                         ["hex.deps-inward", "hex.domain-pure",
                          "hex.domain-no-framework", "hex.ports-owned-inside"])
        self.assertEqual([r.project for r in rules], ["backend"] * 4)
        self.assertEqual([r.primitive for r in rules],
                         ["layer-order", "confine-type", "forbid-import", "naming-suffix"])

        by_id = {r.rule_id: r for r in rules}
        # (가) forbid-import의 from·to — 레이어는 패턴으로, 패키지 패턴은 그대로.
        no_framework = by_id["hex.domain-no-framework"]
        self.assertEqual(no_framework.resolved["from"], ["com.acme.claim.domain.."])
        self.assertEqual(no_framework.resolved["to"],
                         ["org.springframework..", "jakarta.persistence.."])
        self.assertEqual(no_framework.params["from"], ["domain"])   # 원문 보존
        # (가) naming-suffix의 scope.
        self.assertEqual(by_id["hex.ports-owned-inside"].resolved["scope"],
                         ["com.acme.claim.application.."])
        self.assertEqual(by_id["hex.ports-owned-inside"].params["suffixes"], ["Port", "UseCase"])

    def test_na_params_keep_layer_names(self):
        # §2.1(나) — layers·allowed_layer는 치환하지 않는다(프로파일이 layer_patterns를 함께 받는다).
        resolution = self.assert_clean(self.resolve_text(MINIMAL))
        by_id = {r.rule_id: r for r in self.rules_of(resolution, "claim")}
        self.assertEqual(by_id["hex.deps-inward"].params["layers"],
                         ["domain", "application", "adapter"])
        self.assertEqual(by_id["hex.deps-inward"].resolved, {})
        self.assertEqual(by_id["hex.domain-pure"].params["allowed_layer"], ["adapter"])
        self.assertEqual(by_id["hex.domain-pure"].resolved, {})

    def test_layer_patterns_carry_normalization(self):
        resolution = self.assert_clean(self.resolve_text(MINIMAL))
        rule = self.rules_of(resolution, "claim")[0]
        self.assertEqual(rule.layer_patterns, {
            "domain": ["com.acme.claim.domain.."],
            "application": ["com.acme.claim.application.."],
            "adapter": ["com.acme.claim.adapter.."],
        })

    def test_layer_patterns_include_project_wide_layer(self):
        # {컨텍스트} 없는 규약 레이어(presentation)는 모든 컨텍스트에 공통 적용된다.
        resolution = self.assert_clean(resolve_document(FULL_PATH))
        rule = self.rules_of(resolution, "brawlstars")[0]
        self.assertEqual(rule.layer_patterns["domain"], ["com.imstargg.core.domain.brawlstars.."])
        self.assertEqual(rule.layer_patterns["presentation"],
                         ["com.imstargg.core.admin..", "com.imstargg.core.api..",
                          "com.imstargg.core.batch..", "com.imstargg.core.worker.."])

    def test_resolve_tuple_facade(self):
        # T4가 소비하는 3-튜플 계약.
        effective, derived, errors = resolve(FULL_PATH)
        self.assertEqual(errors, [])
        self.assertEqual(len(effective), 15)   # 4개 컨텍스트 × 4규칙 − 예외 1
        self.assertEqual(len(derived), 12)     # 컨텍스트 4 + 앱 4 + 공용 모듈 4

    def test_missing_architecture_file(self):
        resolution = resolve_document(self.tmpdir / "없는파일.md")
        self.assertEqual(len(resolution.errors), 1)
        self.assertEqual(resolution.errors[0].line, 0)
        self.assertIn("읽을 수 없습니다", resolution.errors[0].message)


class TestExceptions(ResolveTestCase):
    def test_exception_removed_and_counted(self):
        text = with_label(MINIMAL, "- 모듈 구성: multi-module",
                          "- 규칙 예외: -hex.ports-owned-inside (ADR-0002)")
        resolution = self.assert_clean(self.resolve_text(text))
        rules = self.rules_of(resolution, "claim")
        self.assertEqual(len(rules), 3)
        self.assertNotIn("hex.ports-owned-inside", [r.rule_id for r in rules])
        self.assertEqual(resolution.excluded, [("backend", "claim", "hex.ports-owned-inside")])

    def test_exception_unknown_id_error(self):
        text = with_label(MINIMAL, "- 모듈 구성: multi-module",
                          "- 규칙 예외: -hex.no-such-rule (ADR-0002)")
        resolution = self.resolve_text(text)
        error = self.assert_one_error(resolution, "선언한 규칙 id가 아닙니다",
                                      line=line_of(text, "- 규칙 예외:"))
        self.assertIn("hex.no-such-rule", error.message)
        self.assertEqual(len(self.rules_of(resolution, "claim")), 4)   # 아무것도 제외되지 않는다

    def test_exception_derived_id_error(self):
        text = with_label(MINIMAL, "- 모듈 구성: multi-module",
                          "- 규칙 예외: -derived.context-isolation (ADR-0002)")
        error = self.assert_one_error(self.resolve_text(text), "예외로 뺄 수 없습니다",
                                      line=line_of(text, "- 규칙 예외:"))
        for guidance in ("관계 표", "포함 컨텍스트", "공용 모듈"):
            self.assertIn(guidance, error.message)


class TestDerivedContextIsolation(ResolveTestCase):
    def setUp(self):
        super().setUp()
        self.resolution = self.assert_clean(resolve_document(FULL_PATH))

    def test_context_isolation_pairs_open(self):
        # brawlstars ↔ statistics는 관계 표에 있으므로 양방향 모두 to에서 빠진다.
        brawlstars = self.derived_of(self.resolution, "context-isolation", "brawlstars")
        statistics = self.derived_of(self.resolution, "context-isolation", "statistics")
        self.assertEqual(brawlstars.detail["from"],
                         ["com.imstargg.core.application.brawlstars..",
                          "com.imstargg.core.domain.brawlstars.."])
        self.assertNotIn("com.imstargg.core.domain.statistics..", brawlstars.detail["to"])
        self.assertIn("com.imstargg.core.domain.operation..", brawlstars.detail["to"])
        self.assertNotIn("com.imstargg.core.domain.brawlstars..", statistics.detail["to"])
        # 관계가 없는 쌍은 서로를 계속 막는다.
        operation = self.derived_of(self.resolution, "context-isolation", "operation")
        self.assertIn("com.imstargg.core.domain.brawlstars..", operation.detail["to"])

    def test_context_isolation_star_pattern_excluded(self):
        # 컨텍스트 비분할 레이어(presentation)의 패턴은 from에도 to에도 들어가지 않는다.
        app_patterns = {"com.imstargg.core.api..", "com.imstargg.core.admin..",
                        "com.imstargg.core.batch..", "com.imstargg.core.worker.."}
        for rule in self.derived_of(self.resolution, "context-isolation"):
            self.assertEqual(app_patterns & set(rule.detail["from"] + rule.detail["to"]), set())

    def test_context_isolation_omitted_when_to_empty(self):
        # 컨텍스트가 하나뿐이면 막을 상대가 없으므로 인스턴스를 만들지 않는다.
        resolution = self.assert_clean(self.resolve_text(MINIMAL))
        self.assertEqual(self.derived_of(resolution, "context-isolation"), [])

    def test_derived_kinds_and_ids(self):
        self.assertEqual({d.kind for d in self.resolution.derived}, set(DERIVED_KINDS))
        self.assertEqual({d.project for d in self.resolution.derived}, {"imstargg-backend"})
        # 파생 규칙의 id는 접두 + kind다(D1) — 예외 검사와 소비자의 메시지가 같은 규약을 쓴다.
        self.assertEqual(derived_rule_id(KIND_APP_CONFINEMENT), "derived.app-confinement")


class TestDerivedAppAndShared(ResolveTestCase):
    def setUp(self):
        super().setUp()
        self.resolution = self.assert_clean(resolve_document(FULL_PATH))

    def test_app_confinement_all(self):
        admin = self.derived_of(self.resolution, "app-confinement", "core-admin")
        self.assertEqual(admin.detail["module_path"], "core/core-admin")
        self.assertEqual(admin.detail["forbidden"], [])          # 포함 컨텍스트: all
        self.assertEqual(len(admin.detail["reverse_from"]), 8)   # 4 컨텍스트 × 2 레이어

    def test_app_confinement_partial(self):
        worker = self.derived_of(self.resolution, "app-confinement", "core-worker")
        self.assertNotIn("com.imstargg.core.domain.brawlstars..", worker.detail["forbidden"])
        self.assertIn("com.imstargg.core.domain.statistics..", worker.detail["forbidden"])
        self.assertEqual(len(worker.detail["forbidden"]), 6)     # 미포함 컨텍스트 3 × 2 레이어
        # 앱 패키지({앱} 전개)는 앱 자신을 가리키므로 어느 쪽에도 넣지 않는다.
        self.assertNotIn("com.imstargg.core.worker..",
                         worker.detail["forbidden"] + worker.detail["reverse_from"])

    def test_shared_module_roles(self):
        kernel = self.derived_of(self.resolution, "shared-module-direction", "core-enum")
        infra = self.derived_of(self.resolution, "shared-module-direction", "db-core")
        self.assertEqual(kernel.detail["role"], "shared-kernel")
        self.assertEqual(kernel.detail["domain_restricted_contexts"], [])
        self.assertEqual(infra.detail["path"], "infrastructure/db-core")
        # renewal은 -ld.domain-pure 예외를 걸었으므로 domain-pure가 아니다(예외 적용 후 기준).
        self.assertEqual(infra.detail["domain_restricted_contexts"],
                         ["brawlstars", "statistics", "operation"])
        # 공용 모듈은 컨텍스트 코드와 앱 코드 양쪽에 의존할 수 없다(정본 §5.1 규칙 5).
        self.assertIn("com.imstargg.core.domain.brawlstars..", infra.detail["forbidden"])
        self.assertIn("com.imstargg.core.api..", infra.detail["forbidden"])

    def test_exception_restores_domain_purity_when_removed(self):
        # 대조군 — 예외 줄만 빼면 renewal이 다시 domain-pure가 된다(판정 기준이 예외임을 고정).
        text = FULL.replace("- 규칙 예외: -ld.domain-pure (ADR-0007)\n", "")
        resolution = self.assert_clean(self.resolve_text(text))
        infra = self.derived_of(resolution, "shared-module-direction", "db-core")
        self.assertEqual(infra.detail["domain_restricted_contexts"],
                         ["brawlstars", "statistics", "operation", "renewal"])

    def test_app_patterns_from_convention_rows(self):
        # 패키지 규약의 `{앱}` 행은 앱 패키지의 선언 경로다 — 관측 없이도 앱↔앱을 만들 수 있다.
        for subject in ("core-api", "core-worker"):
            detail = self.derived_of(self.resolution, "app-confinement", subject).detail
            self.assertEqual(detail["app_patterns"], {
                "core-api": ["com.imstargg.core.api.."],
                "core-batch": ["com.imstargg.core.batch.."],
                "core-worker": ["com.imstargg.core.worker.."],
                "core-admin": ["com.imstargg.core.admin.."],
            })

    def test_app_patterns_absent_without_app_rows(self):
        # `{앱}` 행이 없으면 키 자체를 넣지 않는다 — 소비자는 관측으로 폴백한다(D2).
        text = FULL.replace("| presentation | com.imstargg.{앱}.. |",
                            "| presentation | com.imstargg.presentation.{컨텍스트}.. |")
        resolution = self.assert_clean(self.resolve_text(text))
        detail = self.derived_of(resolution, "app-confinement", "core-api").detail
        self.assertNotIn("app_patterns", detail)

    def test_domain_restricted_needs_confine_type(self):
        # 'domain' 레이어는 있지만 confine-type이 없다 → domain-pure가 아니다(D3).
        text = SHARED_ARCH.format(name="plain-domain", layer_a="domain", layer_b="edge")
        resolution = self.assert_clean(self.resolve_text(text, {"plain-domain": PLAIN_DOMAIN}))
        shared = self.derived_of(resolution, "shared-module-direction", "logging")
        self.assertEqual(shared.detail["domain_restricted_contexts"], [])

    def test_domain_restricted_needs_domain_layer(self):
        # confine-type은 있지만 'domain' 레이어가 없다 → 세부를 생성하지 않는다(D3).
        text = SHARED_ARCH.format(name="ports-pure", layer_a="core", layer_b="edge")
        resolution = self.assert_clean(self.resolve_text(text, {"ports-pure": PORTS_PURE}))
        shared = self.derived_of(resolution, "shared-module-direction", "logging")
        self.assertEqual(shared.detail["domain_restricted_contexts"], [])
        self.assertEqual(shared.detail["forbidden"],
                         ["com.acme.claim.core..", "com.acme.claim.edge.."])

    def test_domain_restricted_lists_domain_pure_contexts(self):
        # 두 조건을 모두 만족하면 목록에 들어간다(대조군 — full.md는 프리셋 경로).
        text = SHARED_ARCH.format(name="pure-domain", layer_a="domain", layer_b="edge")
        style = PLAIN_DOMAIN.rstrip("\n") + \
            "\n| pd.domain-pure | confine-type | type=jpa-entity; allowed_layer=edge |\n"
        resolution = self.assert_clean(self.resolve_text(text, {"pure-domain": style}))
        shared = self.derived_of(resolution, "shared-module-direction", "logging")
        self.assertEqual(shared.detail["domain_restricted_contexts"], ["claim"])


class TestHollowLayerWarnings(ResolveTestCase):
    """선언된 레이어에 실현 패턴이 0건이면 경고한다 — 오류가 아니고 exit에 영향도 없다."""

    def test_warns_for_unrealized_layer(self):
        # layered-domain은 4레이어를 선언하지만 규약 표는 3개만 실현한다 → infrastructure 공허.
        resolution = self.assert_clean(resolve_document(FULL_PATH))
        self.assertEqual({(w.context, w.layer) for w in resolution.warnings},
                         {(name, "infrastructure")
                          for name in ("brawlstars", "statistics", "operation", "renewal")})
        by_context = {w.context: w for w in resolution.warnings}
        self.assertEqual(by_context["brawlstars"].rules, ["ld.domain-pure", "ld.infra-isolated"])
        self.assertIn("경고: 컨텍스트 'brawlstars'의 레이어 'infrastructure'는 스타일이 선언했으나 "
                      "실현 패턴이 없습니다", by_context["brawlstars"].message)
        self.assertIn("규칙 2건(ld.domain-pure, ld.infra-isolated)이 아무것도 검사하지 않습니다",
                      by_context["brawlstars"].message)
        # 예외로 빠진 규칙은 세지 않는다 — renewal은 -ld.domain-pure를 걸었다.
        self.assertEqual(by_context["renewal"].rules, ["ld.infra-isolated"])
        self.assertEqual(by_context["brawlstars"].line,
                         line_of(FULL, "## 컨텍스트: brawlstars"))

    def test_all_layer_realization_makes_every_style_layer_hollow(self):
        text = MINIMAL.replace("- 모듈 구성: multi-module", "- 모듈 구성: single-module")
        for layer in ("domain", "application", "adapter"):
            text = text.replace(f"| {layer} |", "| all |")
        resolution = self.assert_clean(self.resolve_text(text))
        self.assertEqual([w.layer for w in resolution.warnings],
                         ["domain", "application", "adapter"])
        self.assertEqual({w.layer: w.rules for w in resolution.warnings}, {
            "domain": ["hex.deps-inward", "hex.domain-no-framework"],
            "application": ["hex.deps-inward", "hex.ports-owned-inside"],
            "adapter": ["hex.deps-inward", "hex.domain-pure"],
        })

    def test_no_warning_when_layers_realized(self):
        # 반증 — 모듈 표를 레이어별 행으로 나누면 경고가 사라진다.
        self.assertEqual(self.assert_clean(self.resolve_text(MINIMAL)).warnings, [])

    def test_warning_is_not_an_error(self):
        text = MINIMAL.replace("| claim-adapter-in | claim/adapter-in | adapter |\n", "") \
                      .replace("| claim-adapter-out | claim/adapter-out | adapter |\n", "")
        resolution = self.resolve_text(text)
        self.assertEqual([e.message for e in resolution.errors], [])   # exit 0을 유지한다
        self.assertEqual([w.layer for w in resolution.warnings], ["adapter"])

    def test_non_layer_params_do_not_count_as_references(self):
        # suffixes=domain처럼 레이어를 받지 않는 키의 값은 레이어 참조가 아니다(§2.1).
        style = ("## 선언\n\n- 레이어: core, edge\n\n| 규칙 id | primitive | 파라미터 |\n|---|---|---|\n"
                 "| nm.naming | naming-suffix | scope=core; suffixes=edge |\n")
        text = CUSTOM_ARCH.format(name="only-core", layer_a="core", layer_b="core")
        resolution = self.assert_clean(self.resolve_text(text, {"only-core": style}))
        self.assertEqual([(w.layer, w.rules) for w in resolution.warnings], [("edge", [])])
        self.assertIn("참조하는 유효 규칙은 없습니다", resolution.warnings[0].message)


class TestCrossFileValidation(ResolveTestCase):
    def test_custom_style_missing_error(self):
        text = CUSTOM_ARCH.format(name="ports-lite", layer_a="core", layer_b="edge")
        error = self.assert_one_error(self.resolve_text(text), "커스텀 스타일 문서",
                                      line=line_of(text, "- 스타일:"))
        self.assertIn("docs/architecture/styles/ports-lite.md", error.message)

    def test_custom_style_resolved(self):
        text = CUSTOM_ARCH.format(name="ports-lite", layer_a="core", layer_b="edge")
        resolution = self.assert_clean(self.resolve_text(text, {"ports-lite": PORTS_LITE}))
        rules = self.rules_of(resolution, "claim")
        self.assertEqual([r.rule_id for r in rules], ["pl.deps-inward", "pl.no-framework"])
        self.assertEqual(rules[1].resolved["from"], ["com.acme.claim.core.."])

    def test_style_parse_error_uses_style_path(self):
        text = CUSTOM_ARCH.format(name="ports-lite", layer_a="core", layer_b="edge")
        resolution = self.resolve_text(text, {"ports-lite": BROKEN_STYLE})
        self.assertEqual(len(resolution.errors), 1)
        error = resolution.errors[0]
        self.assertIn("'키=값' 형식이 아닙니다", error.message)
        self.assertTrue(error.path.endswith("docs/architecture/styles/ports-lite.md"), error.path)
        self.assertEqual(error.line, 7)   # 스타일 문서의 규칙 행
        self.assertTrue(format_error(error, "ARCHITECTURE.md").endswith(
            f"ports-lite.md:7: {error.message}"))

    def test_style_error_reported_once_for_shared_style(self):
        # 같은 스타일을 두 컨텍스트가 채택해도 선언 파싱은 한 번이다.
        text = TWO_CONTEXT_ARCH.format(name="ports-lite")
        resolution = self.resolve_text(text, {"ports-lite": BROKEN_STYLE})
        self.assertEqual(len(resolution.errors), 1)

    def test_convention_layer_not_in_style_error(self):
        text = FULL.replace("| presentation | com.imstargg.{앱}.. |",
                            "| presentation | com.imstargg.{앱}.. |\n| bogus | com.imstargg.bogus.. |")
        error = self.assert_one_error(self.resolve_text(text), "패키지 규약 레이어 'bogus'")
        self.assertIn("layered-domain", error.message)
        self.assertEqual(error.line, line_of(text, "## 프로젝트: imstargg-backend"))

    def test_module_layer_not_in_style_error(self):
        text = MINIMAL.replace("| claim-adapter-in | claim/adapter-in | adapter |",
                               "| claim-adapter-in | claim/adapter-in | bogus |")
        error = self.assert_one_error(self.resolve_text(text), "레이어 'bogus'")
        self.assertIn("선언한 레이어가 아닙니다", error.message)
        self.assertEqual(error.line, line_of(text, "## 컨텍스트: claim"))

    def test_module_layer_all_allowed(self):
        text = MINIMAL.replace("- 모듈 구성: multi-module", "- 모듈 구성: single-module")
        for layer in ("domain", "application", "adapter"):
            text = text.replace(f"| {layer} |", "| all |")
        self.assert_clean(self.resolve_text(text))

    def test_invalid_segment_layer_error(self):
        text = CUSTOM_ARCH.format(name="hyphen", layer_a="domain", layer_b="interface-adapter")
        error = self.assert_one_error(self.resolve_text(text, {"hyphen": HYPHEN_STYLE}),
                                      "유효한 패키지 세그먼트가 아닙니다")
        self.assertIn("interface-adapter", error.message)

    def test_invalid_segment_not_flagged_with_convention_table(self):
        # 패키지 규약 표가 있으면 레이어 이름이 패키지 세그먼트가 되지 않는다.
        text = CUSTOM_ARCH.format(name="hyphen", layer_a="domain", layer_b="interface-adapter")
        text = with_conventions(text,
                                ("domain", "com.acme.{컨텍스트}.domain.."),
                                ("interface-adapter", "com.acme.{컨텍스트}.adapter.."))
        self.assert_clean(self.resolve_text(text, {"hyphen": HYPHEN_STYLE}))

    def test_invalid_segment_context_error(self):
        # 기본 관례에서는 컨텍스트 이름도 그대로 세그먼트가 된다 — 레이어와 같은 계열의 오류다.
        error = self.assert_one_error(
            self.resolve_text(HYPHEN_CONTEXT_ARCH, {"ports-lite": PORTS_LITE}),
            "유효한 패키지 세그먼트가 아닙니다",
            line=line_of(HYPHEN_CONTEXT_ARCH, "## 컨텍스트: order-mgmt"))
        self.assertIn("컨텍스트 이름 'order-mgmt'", error.message)

    def test_invalid_segment_context_error_in_placeholder_convention(self):
        # 규약 표가 있어도 `{컨텍스트}` 행이 있으면 이름이 그대로 세그먼트 자리에 들어간다.
        text = with_conventions(HYPHEN_CONTEXT_ARCH,
                                ("core", "com.acme.{컨텍스트}.core.."),
                                ("edge", "com.acme.{컨텍스트}.edge.."))
        error = self.assert_one_error(self.resolve_text(text, {"ports-lite": PORTS_LITE}),
                                      "유효한 패키지 세그먼트가 아닙니다")
        self.assertIn("컨텍스트 이름 'order-mgmt'", error.message)
        self.assertIn("{컨텍스트}", error.message)   # 고칠 자리를 지목한다

    def test_invalid_segment_context_not_flagged_without_placeholder(self):
        # `{컨텍스트}` 없는 규약이면 컨텍스트 이름이 패키지에 나타나지 않는다 — 이름 모양은 무관하다.
        text = with_conventions(HYPHEN_CONTEXT_ARCH,
                                ("core", "com.acme.core.."), ("edge", "com.acme.edge.."))
        self.assert_clean(self.resolve_text(text, {"ports-lite": PORTS_LITE}))

    def test_valid_context_name_not_flagged(self):
        # 대조군 — 같은 문서에서 이름만 합법 세그먼트로 바꾸면 통과한다.
        text = HYPHEN_CONTEXT_ARCH.replace("## 컨텍스트: order-mgmt", "## 컨텍스트: order_mgmt")
        self.assert_clean(self.resolve_text(text, {"ports-lite": PORTS_LITE}))

    def test_unknown_pattern_key_error(self):
        text = with_label(MINIMAL, "- 모듈 구성: multi-module", "- 패턴: nosuch")
        error = self.assert_one_error(self.resolve_text(text), "지식 문서가 없습니다",
                                      line=line_of(text, "- 패턴:"))
        self.assertIn("nosuch", error.message)

    def test_known_pattern_keys_accepted(self):
        text = with_label(MINIMAL, "- 모듈 구성: multi-module", "- 패턴: cqrs, outbox")
        self.assert_clean(self.resolve_text(text))

    def test_architecture_errors_are_forwarded(self):
        text = MINIMAL.replace("- 분류: core", "- 분류: bogus")
        error = self.assert_one_error(self.resolve_text(text), "분류 값 'bogus'")
        self.assertTrue(error.path.endswith("ARCHITECTURE.md"), error.path)


class TestCli(ResolveTestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args],
                              capture_output=True, text=True)

    def test_cli_ok_line_format(self):
        result = self.run_cli(str(FULL_PATH))
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.strip().split("\n")
        self.assertEqual(lines[-1],
                         "OK: 컨텍스트 4, 유효 규칙 27 (스타일 15, 파생 12, 예외 제외 1)")
        # 경고는 OK 줄 앞에 나오고 exit 코드를 바꾸지 않는다.
        self.assertEqual(len(lines), 5)
        for line in lines[:-1]:
            self.assertTrue(line.startswith(f"{FULL_PATH}:"), line)
            self.assertIn("경고: 컨텍스트", line)

    def test_cli_no_warning_lines_when_all_realized(self):
        path = self.write(MINIMAL)
        result = self.run_cli(str(path))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(),
                         "OK: 컨텍스트 1, 유효 규칙 4 (스타일 4, 파생 0, 예외 제외 0)")

    def test_cli_error_exit_code(self):
        text = with_label(MINIMAL, "- 모듈 구성: multi-module",
                          "- 규칙 예외: -hex.no-such-rule (ADR-0002)")
        path = self.write(text)
        result = self.run_cli(str(path))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr.startswith(f"{path}:{line_of(text, '- 규칙 예외:')}: "),
                        result.stderr)

    def test_cli_missing_file(self):
        result = self.run_cli(str(self.tmpdir / "없는파일.md"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("읽을 수 없습니다", result.stderr)

    def test_cli_usage_error(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn("사용법", result.stderr)

    def test_cli_json_output(self):
        result = self.run_cli(str(FULL_PATH), "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(sorted(payload), ["derived", "effective", "projects", "warnings"])
        self.assertEqual(len(payload["effective"]), 15)
        self.assertEqual(len(payload["derived"]), 12)
        self.assertEqual(sorted(payload["effective"][0]),
                         ["context", "layer_patterns", "params", "primitive",
                          "project", "resolved", "rule_id"])
        self.assertEqual(sorted(payload["derived"][0]), ["detail", "kind", "project", "subject"])
        self.assertEqual(len(payload["warnings"]), 4)
        self.assertEqual(sorted(payload["warnings"][0]),
                         ["context", "layer", "line", "message", "project", "rules"])

    def test_cli_json_projects_metadata(self):
        result = self.run_cli(str(FULL_PATH), "--json")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["projects"], [{
            "name": "imstargg-backend",
            "path": "imstargg-backend",
            "profile": "kotlin-spring",
            "base_package": "com.imstargg",
            "test_location": "architecture-test/src/test/kotlin",
        }])


if __name__ == "__main__":
    unittest.main()
