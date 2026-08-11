import json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from check_imports import LIMITATION_NOTE, check, render

ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = Path(__file__).resolve().parent
SCRIPT = ROOT / "scripts" / "check_imports.py"

# 커스텀 스타일 하나로 primitive 5종을 전부 선언한다 — 프리셋을 쓰면 규칙 조합을 검사마다
# 다시 고를 수 없고, 프리셋이 바뀌면 이 테스트가 함께 깨진다.
STYLE_FULL = """# full

## 선언

- 레이어: domain, application, adapter

| 규칙 id | primitive | 파라미터 |
|---|---|---|
| af.deps-inward | layer-order | layers=domain,application,adapter |
| af.domain-pure | confine-type | type=jpa-entity; allowed_layer=adapter |
| af.no-framework | forbid-import | from=domain; to=org.springframework.. |
| af.service-naming | naming-suffix | scope=application; suffixes=Service |
| af.no-service-chain | forbid-sibling-dependency | layer=application; suffix=Service |
"""

STYLE_STRICT = """# strict

## 선언

- 레이어: domain, application, adapter

| 규칙 id | primitive | 파라미터 |
|---|---|---|
| st.deps-inward | layer-order | layers=domain,application,adapter; strict=true |
"""

HEAD = """# 샘플 — Architecture
<!-- superarchitect:template v1 -->

## 프로젝트: backend
- 경로: .
- 프로파일: kotlin-spring
- 기본 패키지: com.acme
- 아키텍처 테스트 위치: architecture-test/src/test/kotlin
"""

CLAIM_MODULES = """
| 모듈 | 경로 | 레이어 |
|---|---|---|
| claim-domain | claim/domain | domain |
| claim-application | claim/application | application |
| claim-adapter | claim/adapter | adapter |
"""

# 단일 컨텍스트 — 파생 규칙이 하나도 생기지 않아 primitive 5종만 남는다.
MONO_ARCH = HEAD + """
## 컨텍스트: claim
- 분류: core
- 스타일: custom/full
- 모듈 구성: multi-module
""" + CLAIM_MODULES

STRICT_ARCH = HEAD + """
## 컨텍스트: claim
- 분류: core
- 스타일: custom/strict
- 모듈 구성: multi-module
""" + CLAIM_MODULES

# app-embedded 멀티 앱 — 파생 3종이 전부 생긴다.
APP_ARCH = """# multi — Architecture
<!-- superarchitect:template v1 -->

## 프로젝트: backend
- 경로: .
- 프로파일: kotlin-spring
- 기본 패키지: com.acme
- 아키텍처 테스트 위치: architecture-test/src/test/kotlin

### 애플리케이션
| 이름 | 모듈 경로 | 포함 컨텍스트 |
|---|---|---|
| web | app/web | claim |
| batch | app/batch | billing |

### 공용 모듈
| 모듈 | 경로 | 역할 |
|---|---|---|
| logging | support/logging | support |

### 패키지 규약
| 레이어 | 패턴 |
|---|---|
| domain | com.acme.core.domain.{컨텍스트}.. |
| application | com.acme.core.application.{컨텍스트}.. |
| adapter | com.acme.{앱}.. |

## 컨텍스트: claim
- 분류: core
- 스타일: custom/full
- 모듈 구성: app-embedded
<CLAIM_EXTRA>
## 컨텍스트: billing
- 분류: supporting
- 스타일: custom/full
- 모듈 구성: app-embedded
"""


def app_arch(claim_extra=""):
    """`{컨텍스트}`·`{앱}` 치환 변수가 있어 str.format을 쓸 수 없다 — 자리표시자를 바꿔 끼운다."""
    return APP_ARCH.replace("<CLAIM_EXTRA>", claim_extra)

RELATION_TABLE = """
### 관계
| 상대 | 유형 | 계약 |
|---|---|---|
| billing | customer-supplier | claim-events-v1 |
"""

# 애플리케이션 표는 있고 패키지 규약에 `{앱}` 행이 없다 — 앱 패키지를 관측으로만 알 수 있는 형태(D2).
OBS_APPS = """
### 애플리케이션
| 이름 | 모듈 경로 | 포함 컨텍스트 |
|---|---|---|
| web | app/web | claim |
| batch | app/batch | all |
"""

OBS_CLAIM = """
## 컨텍스트: claim
- 분류: core
- 스타일: custom/full
- 모듈 구성: multi-module
"""

OBS_ARCH = HEAD + OBS_APPS + OBS_CLAIM + CLAIM_MODULES

# 같은 형태 + 공용 모듈. `{앱}` 규약이 없으므로 앱 패키지가 star 패턴으로 존재하지 않는다 —
# 공용 모듈 → 앱 참조를 잡으려면 앱 패키지를 관측해 to-측에 합류시켜야 한다.
OBS_SHARED_ARCH = HEAD + OBS_APPS + """
### 공용 모듈
| 모듈 | 경로 | 역할 |
|---|---|---|
| logging | support/logging | support |
""" + OBS_CLAIM + CLAIM_MODULES

# confine-type의 allowed_package 분기 — 격리 범위를 레이어가 아니라 패키지 패턴으로 지정한다.
STYLE_PKG = """# pkg

## 선언

- 레이어: domain, application, adapter

| 규칙 id | primitive | 파라미터 |
|---|---|---|
| pk.domain-pure | confine-type | type=jpa-entity; allowed_package=com.acme.claim.adapter.persistence.. |
"""

PKG_ARCH = HEAD + """
## 컨텍스트: claim
- 분류: core
- 스타일: custom/pkg
- 모듈 구성: multi-module
""" + CLAIM_MODULES


class CheckTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(dir=TESTS_DIR, prefix="tmp"))
        self.arch_path = self.tmpdir / "ARCHITECTURE.md"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def arch(self, text, styles=None):
        self.arch_path.write_text(text, encoding="utf-8")
        for name, body in (styles or {"full": STYLE_FULL}).items():
            path = self.tmpdir / "docs" / "architecture" / "styles" / f"{name}.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        return self.arch_path

    def src(self, relpath, text):
        path = self.tmpdir / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def kt(self, module, package, name, imports=(), body=None, annotations=()):
        """`<module>/src/main/kotlin/<패키지 경로>/<이름>.kt`에 최소 Kotlin 파일을 쓴다."""
        lines = [f"package {package}", ""]
        lines += [f"import {i}" for i in imports]
        if imports:
            lines.append("")
        lines += [f"@{a}" for a in annotations]
        lines.append(body if body is not None else f"class {name}")
        relpath = f"{module}/src/main/kotlin/{package.replace('.', '/')}/{name}.kt"
        return self.src(relpath, "\n".join(lines) + "\n")

    # ---- 관측 도우미 ------------------------------------------------------

    def check(self):
        return check(self.arch_path)

    def ids(self, report):
        return [v.rule_id for v in report.violations]

    def of(self, report, rule_id):
        return [v for v in report.violations if v.rule_id == rule_id]

    def assert_violation(self, report, rule_id, needle=None, count=None):
        found = self.of(report, rule_id)
        self.assertTrue(found, f"{rule_id} 위반을 기대했지만 {self.ids(report)}")
        if count is not None:
            self.assertEqual(len(found), count, [v.message for v in found])
        if needle is not None:
            self.assertTrue(any(needle in v.message for v in found),
                            [v.message for v in found])
        return found[0]

    def assert_no_violation(self, report, rule_id):
        self.assertEqual(self.of(report, rule_id), [],
                         [v.message for v in self.of(report, rule_id)])

    # ---- 시나리오 --------------------------------------------------------

    def clean_tree(self):
        """MONO_ARCH를 통과하는 최소 소스 트리."""
        self.arch(MONO_ARCH)
        self.kt("claim/domain", "com.acme.claim.domain", "Claim")
        self.kt("claim/application", "com.acme.claim.application", "ClaimService",
                imports=["com.acme.claim.domain.Claim"])
        self.kt("claim/adapter", "com.acme.claim.adapter", "ClaimJpaEntity",
                imports=["com.acme.claim.domain.Claim"], annotations=["Entity"])

    def app_tree(self, claim_extra=""):
        self.arch(app_arch(claim_extra))
        self.kt("core/domain", "com.acme.core.domain.claim", "Claim")
        self.kt("core/domain", "com.acme.core.domain.billing", "Invoice")
        self.kt("app/web", "com.acme.web", "WebApp")
        self.kt("app/batch", "com.acme.batch", "BatchApp")
        self.kt("support/logging", "com.acme.logging", "Logger")


class TestClean(CheckTestCase):
    def test_clean_tree_has_no_violation(self):
        self.clean_tree()
        report = self.check()
        self.assertEqual([f"{v.rule_id}: {v.message}" for v in report.violations], [])
        self.assertEqual(report.errors, [])

    def test_clean_tree_counts_every_rule(self):
        self.clean_tree()
        report = self.check()
        self.assertEqual(report.checked, 5)      # 파생 0 + 스타일 5
        self.assertEqual(report.skipped, [])
        self.assertEqual(report.zero_match, [])

    def test_build_output_is_not_walked(self):
        self.clean_tree()
        self.src("claim/domain/build/generated/com/acme/claim/domain/Gen.kt",
                 "package com.acme.claim.domain\n\nimport org.springframework.stereotype.Component\n")
        self.src("claim/domain/out/Gen2.kt",
                 "package com.acme.claim.domain\n\nimport org.springframework.stereotype.Component\n")
        self.assertEqual(self.check().violations, [])

    def test_test_sources_are_not_walked(self):
        self.clean_tree()
        self.src("claim/domain/src/test/kotlin/com/acme/claim/domain/ClaimTest.kt",
                 "package com.acme.claim.domain\n\nimport org.springframework.stereotype.Component\n")
        self.assertEqual(self.check().violations, [])


class TestPrimitives(CheckTestCase):
    def test_layer_order_inner_to_outer(self):
        self.clean_tree()
        self.kt("claim/domain", "com.acme.claim.domain", "Leaky",
                imports=["com.acme.claim.adapter.ClaimJpaEntity"])
        report = self.check()
        violation = self.assert_violation(report, "af.deps-inward", needle="adapter")
        self.assertTrue(violation.path.endswith("Leaky.kt"), violation.path)
        self.assertEqual(violation.line, 3)

    def test_layer_order_outer_to_inner_is_allowed(self):
        self.clean_tree()
        self.kt("claim/adapter", "com.acme.claim.adapter", "ClaimController",
                imports=["com.acme.claim.application.ClaimService"])
        self.assert_no_violation(self.check(), "af.deps-inward")

    def test_layer_order_strict_forbids_skipping(self):
        self.arch(STRICT_ARCH, styles={"strict": STYLE_STRICT})
        self.kt("claim/adapter", "com.acme.claim.adapter", "ClaimController",
                imports=["com.acme.claim.domain.Claim"])
        self.kt("claim/domain", "com.acme.claim.domain", "Claim")
        self.kt("claim/application", "com.acme.claim.application", "ClaimService")
        self.assert_violation(self.check(), "st.deps-inward", needle="인접")

    def test_layer_order_strict_allows_adjacent(self):
        self.arch(STRICT_ARCH, styles={"strict": STYLE_STRICT})
        self.kt("claim/adapter", "com.acme.claim.adapter", "ClaimController",
                imports=["com.acme.claim.application.ClaimService"])
        self.kt("claim/domain", "com.acme.claim.domain", "Claim")
        self.kt("claim/application", "com.acme.claim.application", "ClaimService")
        self.assert_no_violation(self.check(), "st.deps-inward")

    def test_forbid_import(self):
        self.clean_tree()
        self.kt("claim/domain", "com.acme.claim.domain", "ClaimPolicy",
                imports=["org.springframework.stereotype.Component"],
                annotations=["Component"], body="class ClaimPolicy")
        violation = self.assert_violation(self.check(), "af.no-framework",
                                          needle="org.springframework..")
        self.assertEqual(violation.line, 3)

    def test_confine_type_declaration_violation(self):
        self.clean_tree()
        self.kt("claim/domain", "com.acme.claim.domain", "ClaimRow",
                annotations=["Entity"], body="class ClaimRow")
        violation = self.assert_violation(self.check(), "af.domain-pure", needle="선언")
        self.assertTrue(violation.path.endswith("ClaimRow.kt"), violation.path)

    def test_confine_type_reference_violation(self):
        self.clean_tree()
        self.kt("claim/application", "com.acme.claim.application", "LeakyService",
                imports=["com.acme.claim.adapter.ClaimJpaEntity"])
        violation = self.assert_violation(self.check(), "af.domain-pure", needle="참조")
        self.assertIn("ClaimJpaEntity", violation.message)

    def test_confine_type_reference_violation_via_wildcard(self):
        self.clean_tree()
        self.kt("claim/application", "com.acme.claim.application", "LeakyService",
                imports=["com.acme.claim.adapter.*"])
        self.assert_violation(self.check(), "af.domain-pure", needle="참조")

    def test_confine_type_allows_declaration_inside_range(self):
        self.clean_tree()
        self.assert_no_violation(self.check(), "af.domain-pure")

    def test_confine_type_allowed_package_narrows_below_the_layer(self):
        # allowed_package는 레이어가 아니라 패키지 패턴이다 — adapter 레이어 안이라도
        # 지정 패키지 밖이면 위반이어야 allowed_layer 분기와 구분된다.
        self.arch(PKG_ARCH, styles={"pkg": STYLE_PKG})
        self.kt("claim/adapter", "com.acme.claim.adapter.persistence", "ClaimJpaEntity",
                annotations=["Entity"], body="class ClaimJpaEntity")
        self.assert_no_violation(self.check(), "pk.domain-pure")
        self.kt("claim/adapter", "com.acme.claim.adapter", "OrphanRow",
                annotations=["Entity"], body="class OrphanRow")
        violation = self.assert_violation(self.check(), "pk.domain-pure", needle="OrphanRow")
        self.assertIn("com.acme.claim.adapter.persistence..", violation.message)

    def test_naming_suffix(self):
        self.clean_tree()
        self.kt("claim/application", "com.acme.claim.application", "ClaimApi")
        violation = self.assert_violation(self.check(), "af.service-naming", needle="ClaimApi")
        self.assertIn("Service", violation.message)

    def test_naming_suffix_ignores_private_and_internal(self):
        self.clean_tree()
        self.src("claim/application/src/main/kotlin/com/acme/claim/application/Hidden.kt",
                 "package com.acme.claim.application\n\n"
                 "internal class HiddenHelper\n\nprivate class Nested\n")
        self.assert_no_violation(self.check(), "af.service-naming")

    def test_naming_suffix_ignores_nested_types(self):
        self.clean_tree()
        self.src("claim/application/src/main/kotlin/com/acme/claim/application/Outer.kt",
                 "package com.acme.claim.application\n\n"
                 "class OuterService {\n    class Inner\n}\n")
        self.assert_no_violation(self.check(), "af.service-naming")

    def test_naming_suffix_sees_fun_interface_and_annotation_class(self):
        # SAM 포트는 `fun interface`가 관용이고, 그것이 naming-suffix가 겨냥하는 타입이다.
        self.clean_tree()
        self.src("claim/application/src/main/kotlin/com/acme/claim/application/Port.kt",
                 "package com.acme.claim.application\n\nfun interface ClaimPort\n")
        self.src("claim/application/src/main/kotlin/com/acme/claim/application/Mark.kt",
                 "package com.acme.claim.application\n\nannotation class ClaimMarker\n")
        messages = [v.message for v in self.of(self.check(), "af.service-naming")]
        self.assertEqual(len(messages), 2, messages)
        self.assertTrue(any("'ClaimPort'" in m for m in messages), messages)
        self.assertTrue(any("'ClaimMarker'" in m for m in messages), messages)

    def test_top_level_function_is_not_a_type(self):
        # `fun`을 수식어에 넣어도 최상위 함수가 타입으로 잡히면 안 된다.
        self.clean_tree()
        self.src("claim/application/src/main/kotlin/com/acme/claim/application/Ext.kt",
                 "package com.acme.claim.application\n\nfun claimOf(id: Long) = id\n")
        self.assert_no_violation(self.check(), "af.service-naming")

    def test_naming_suffix_java_public_types(self):
        self.clean_tree()
        self.src("claim/application/src/main/java/com/acme/claim/application/ClaimApi.java",
                 "package com.acme.claim.application;\n\npublic final class ClaimApi {}\n")
        self.assert_violation(self.check(), "af.service-naming", needle="ClaimApi")

    def test_forbid_sibling_dependency(self):
        self.clean_tree()
        self.kt("claim/application", "com.acme.claim.application", "PaymentService")
        self.kt("claim/application", "com.acme.claim.application", "OrderService",
                imports=["com.acme.claim.application.PaymentService"])
        violation = self.assert_violation(self.check(), "af.no-service-chain",
                                          needle="PaymentService")
        self.assertTrue(violation.path.endswith("OrderService.kt"), violation.path)

    def test_forbid_sibling_dependency_counts_fun_interface_as_own_type(self):
        # own 집합이 `fun interface`를 놓치면 그 파일의 형제 의존이 통째로 사라진다.
        self.clean_tree()
        self.kt("claim/application", "com.acme.claim.application", "PaymentService")
        self.src("claim/application/src/main/kotlin/com/acme/claim/application/OrderService.kt",
                 "package com.acme.claim.application\n\n"
                 "import com.acme.claim.application.PaymentService\n\n"
                 "fun interface OrderService\n")
        violation = self.assert_violation(self.check(), "af.no-service-chain",
                                          needle="PaymentService")
        self.assertIn("OrderService", violation.message)

    def test_forbid_sibling_dependency_ignores_other_suffix(self):
        self.clean_tree()
        self.kt("claim/application", "com.acme.claim.application", "PaymentPolicy")
        self.kt("claim/application", "com.acme.claim.application", "OrderService",
                imports=["com.acme.claim.application.PaymentPolicy"])
        self.assert_no_violation(self.check(), "af.no-service-chain")


class TestSourceParsing(CheckTestCase):
    def test_wildcard_import_is_collected(self):
        self.clean_tree()
        self.kt("claim/domain", "com.acme.claim.domain", "Wild",
                imports=["com.acme.claim.adapter.*"])
        self.assert_violation(self.check(), "af.deps-inward", needle="com.acme.claim.adapter.*")

    def test_wildcard_import_does_not_reach_subpackages(self):
        # `com.acme.*`는 그 패키지의 멤버만 들여온다 — 하위 패키지는 들어오지 않는다.
        self.clean_tree()
        self.kt("claim/domain", "com.acme.claim.domain", "Wild", imports=["com.acme.*"])
        self.assert_no_violation(self.check(), "af.deps-inward")

    def test_kotlin_import_alias(self):
        self.clean_tree()
        self.kt("claim/domain", "com.acme.claim.domain", "Aliased",
                imports=["com.acme.claim.adapter.ClaimJpaEntity as Row"])
        self.assert_violation(self.check(), "af.deps-inward", needle="ClaimJpaEntity")

    def test_java_static_import(self):
        self.clean_tree()
        self.src("claim/domain/src/main/java/com/acme/claim/domain/Static.java",
                 "package com.acme.claim.domain;\n\n"
                 "import static org.springframework.util.Assert.notNull;\n\n"
                 "public class StaticHelper {}\n")
        self.assert_violation(self.check(), "af.no-framework")


class TestDerivedRules(CheckTestCase):
    def test_context_isolation_violation(self):
        self.app_tree()
        self.kt("core/domain", "com.acme.core.domain.claim", "Leaky",
                imports=["com.acme.core.domain.billing.Invoice"])
        violation = self.assert_violation(self.check(), "derived.context-isolation",
                                          needle="billing")
        self.assertIn("claim", violation.message)

    def test_relation_pair_opens_the_reference(self):
        self.app_tree(claim_extra=RELATION_TABLE)
        self.kt("core/domain", "com.acme.core.domain.claim", "Leaky",
                imports=["com.acme.core.domain.billing.Invoice"])
        self.assert_no_violation(self.check(), "derived.context-isolation")

    def test_app_confinement_forbids_excluded_context(self):
        self.app_tree()
        self.kt("app/web", "com.acme.web", "WebWiring",
                imports=["com.acme.core.domain.billing.Invoice"])
        violation = self.assert_violation(self.check(), "derived.app-confinement",
                                          needle="web")
        self.assertIn("billing", violation.message)

    def test_app_confinement_allows_included_context(self):
        self.app_tree()
        self.kt("app/web", "com.acme.web", "WebWiring",
                imports=["com.acme.core.domain.claim.Claim"])
        self.assert_no_violation(self.check(), "derived.app-confinement")

    def test_app_confinement_reverse_reference(self):
        self.app_tree()
        self.kt("core/domain", "com.acme.core.domain.claim", "Reverse",
                imports=["com.acme.web.WebApp"])
        self.assert_violation(self.check(), "derived.app-confinement", needle="역참조")

    def test_app_to_app_by_declaration(self):
        self.app_tree()
        self.kt("app/web", "com.acme.web", "CrossApp",
                imports=["com.acme.batch.BatchApp"])
        violation = self.assert_violation(self.check(), "derived.app-confinement",
                                          needle="batch")
        self.assertIn("앱", violation.message)

    def test_app_to_app_by_observation(self):
        self.arch(OBS_ARCH)
        self.kt("claim/domain", "com.acme.claim.domain", "Claim")
        self.kt("app/batch", "com.acme.batch", "BatchApp")
        self.kt("app/web", "com.acme.web", "CrossApp",
                imports=["com.acme.batch.BatchApp"])
        self.assert_violation(self.check(), "derived.app-confinement", needle="batch")

    def test_shared_module_may_not_depend_on_context(self):
        self.app_tree()
        self.kt("support/logging", "com.acme.logging", "ClaimLogger",
                imports=["com.acme.core.domain.claim.Claim"])
        self.assert_violation(self.check(), "derived.shared-module-direction",
                              needle="logging")

    def test_shared_module_forbidden_in_domain_of_pure_context(self):
        self.app_tree()
        self.kt("core/domain", "com.acme.core.domain.claim", "Logged",
                imports=["com.acme.logging.Logger"])
        violation = self.assert_violation(self.check(), "derived.shared-module-direction",
                                          needle="domain")
        self.assertIn("claim", violation.message)

    def test_shared_kernel_is_allowed_in_domain(self):
        self.app_tree()
        self.arch(app_arch().replace(
            "| logging | support/logging | support |",
            "| logging | support/logging | shared-kernel |"))
        self.kt("core/domain", "com.acme.core.domain.claim", "Logged",
                imports=["com.acme.logging.Logger"])
        self.assert_no_violation(self.check(), "derived.shared-module-direction")


class TestObservationFallback(CheckTestCase):
    def test_zero_observation_skips_shared_module_with_notice(self):
        self.app_tree()
        shutil.rmtree(self.tmpdir / "support")
        report = self.check()
        reasons = [s for s in report.skipped if s.rule_id == "derived.shared-module-direction"]
        self.assertEqual(len(reasons), 1, report.skipped)
        self.assertIn("관측 0건", reasons[0].reason)
        self.assertIn("logging", reasons[0].subject)

    def test_zero_observation_skips_app_with_notice(self):
        self.arch(OBS_ARCH)
        self.kt("claim/domain", "com.acme.claim.domain", "Claim")
        self.kt("app/web", "com.acme.web", "WebApp")
        report = self.check()
        skipped = [s for s in report.skipped if "batch" in s.subject]
        self.assertEqual(len(skipped), 1, report.skipped)
        self.assertIn("관측 0건", skipped[0].reason)

    def test_shared_module_to_app_uses_observed_app_packages(self):
        # `{앱}` 규약이 없으면 앱 패키지가 star 패턴으로 존재하지 않는다. 관측해서 to-측에
        # 합류시키지 않으면 공용 모듈 → 앱 참조가 어떤 채널에도 나타나지 않는다.
        self.arch(OBS_SHARED_ARCH)
        self.kt("claim/domain", "com.acme.claim.domain", "Claim")
        self.kt("app/web", "com.acme.web", "WebApp")
        self.kt("app/batch", "com.acme.batch", "BatchApp")
        self.kt("support/logging", "com.acme.logging", "WebLogger",
                imports=["com.acme.web.WebApp"])
        violation = self.assert_violation(self.check(), "derived.shared-module-direction",
                                          needle="logging")
        self.assertIn("com.acme.web.WebApp", violation.message)

    def test_unobservable_app_leaves_shared_module_blind_spot_notice(self):
        self.arch(OBS_SHARED_ARCH)
        self.kt("claim/domain", "com.acme.claim.domain", "Claim")
        self.kt("app/web", "com.acme.web", "WebApp")
        self.kt("support/logging", "com.acme.logging", "Logger")
        report = self.check()
        notices = [s for s in report.skipped
                   if s.rule_id == "derived.shared-module-direction" and "batch" in s.subject]
        self.assertEqual(len(notices), 1, report.skipped)
        self.assertIn("관측 0건", notices[0].reason)
        self.assertIn("공용 모듈", notices[0].reason)

    def test_declared_app_patterns_need_no_observation(self):
        # `{앱}` 규약이 있으면 앱 모듈에 소스가 없어도 역참조 검사가 산다(선언 전개).
        self.app_tree()
        shutil.rmtree(self.tmpdir / "app" / "batch")
        self.kt("core/domain", "com.acme.core.domain.billing", "Reverse",
                imports=["com.acme.batch.BatchApp"])
        report = self.check()
        self.assertEqual([s for s in report.skipped if "batch" in s.subject], [])
        self.assert_violation(report, "derived.app-confinement", needle="역참조")


class TestHonesty(CheckTestCase):
    def test_zero_match_warning_for_unmatched_from_side(self):
        self.arch(MONO_ARCH)
        # 소스는 있지만 어느 레이어 패턴에도 걸리지 않는다 — 규칙이 0건을 검사한 채 통과한다.
        self.kt("claim/model", "com.acme.claim.model", "Claim")
        report = self.check()
        warned = {w.rule_id for w in report.zero_match}
        self.assertIn("af.no-framework", warned)
        self.assertIn("af.service-naming", warned)
        lines = render(report)
        self.assertIn("[0건 경고] af.no-framework: from-측 매칭 파일 0건 — "
                      "레이어·패키지 불일치 가능성 (컨텍스트 claim)", lines)

    def test_layer_order_warns_per_layer_not_per_rule(self):
        # 레이어 하나만 파일이 있어도 나머지 레이어의 어긋남은 고지되어야 한다 —
        # 규칙 단위로 묶으면 이 primitive에서만 침묵이 샌다.
        self.arch(MONO_ARCH)
        self.kt("claim/domain", "com.acme.claim.domain", "Claim")
        report = self.check()
        self.assertEqual(sorted(w.subject for w in report.zero_match
                                if w.rule_id == "af.deps-inward"),
                         ["컨텍스트 claim의 'adapter' 레이어",
                          "컨텍스트 claim의 'application' 레이어"])
        self.assertIn("[0건 경고] af.deps-inward: from-측 매칭 파일 0건 — "
                      "레이어·패키지 불일치 가능성 (컨텍스트 claim의 'adapter' 레이어)",
                      render(report))

    def test_hollow_layer_is_not_reported_as_zero_match(self):
        # 실현 패턴 자체가 없는 레이어는 resolve의 공허 레이어 경고가 지목하는 다른 층위다.
        self.arch(MONO_ARCH.replace("| claim-adapter | claim/adapter | adapter |\n", ""))
        self.kt("claim/domain", "com.acme.claim.domain", "Claim")
        self.kt("claim/application", "com.acme.claim.application", "ClaimService")
        report = self.check()
        self.assertEqual([w.subject for w in report.zero_match
                          if w.rule_id == "af.deps-inward"], [])
        self.assertTrue(any("adapter" in line and "실현 패턴이 없습니다" in line
                            for line in report.inherited), report.inherited)

    def test_no_zero_match_warning_when_files_match(self):
        self.clean_tree()
        self.assertEqual([w.rule_id for w in self.check().zero_match], [])

    def test_resolve_warnings_are_inherited(self):
        # 스타일이 선언한 adapter 레이어를 모듈 표가 실현하지 않는다 — resolve의 공허 레이어 경고.
        text = MONO_ARCH.replace("| claim-adapter | claim/adapter | adapter |\n", "")
        self.arch(text)
        self.kt("claim/domain", "com.acme.claim.domain", "Claim")
        report = self.check()
        self.assertTrue(report.inherited, "resolve의 경고가 승계되지 않았다")
        self.assertTrue(any("adapter" in line and "실현 패턴이 없습니다" in line
                            for line in report.inherited), report.inherited)
        self.assertTrue(any("adapter" in line for line in render(report)))

    def test_missing_project_path_is_skipped_with_notice(self):
        self.arch(MONO_ARCH.replace("- 경로: .", "- 경로: backend"))
        report = self.check()
        self.assertEqual(report.violations, [])
        self.assertEqual(len(report.skipped), 5, report.skipped)
        self.assertTrue(all("backend" in s.reason for s in report.skipped), report.skipped)

    def test_hollow_allowed_layer_skips_confine_type(self):
        # adapter 레이어가 실현되지 않으면 '허용 범위'가 비어 모든 @Entity가 범위 밖이 된다 —
        # 선언 결함 하나가 파일 수만큼의 위반으로 불어나지 않도록 판정을 세우지 않고 고지한다.
        self.arch(MONO_ARCH.replace("| claim-adapter | claim/adapter | adapter |\n", ""))
        self.kt("claim/domain", "com.acme.claim.domain", "ClaimRow",
                annotations=["Entity"], body="class ClaimRow")
        report = self.check()
        self.assert_no_violation(report, "af.domain-pure")
        skipped = [s for s in report.skipped if s.rule_id == "af.domain-pure"]
        self.assertEqual(len(skipped), 1, report.skipped)
        self.assertIn("실현 패턴이 0건", skipped[0].reason)
        self.assertTrue(any("adapter" in line and "실현 패턴이 없습니다" in line
                            for line in report.inherited), report.inherited)

    def test_unreadable_source_is_reported(self):
        # UTF-8이 아닌 소스는 파싱할 수 없다. 조용히 빼면 어떤 규칙도 그 파일을 보지 못한다.
        self.clean_tree()
        path = self.tmpdir / "claim/domain/src/main/kotlin/com/acme/claim/domain/Cp949.kt"
        path.write_bytes("package com.acme.claim.domain\n\n// 주석\nclass Odd\n".encode("euc-kr"))
        report = self.check()
        self.assertEqual(len(report.unreadable), 1, report.unreadable)
        self.assertTrue(report.unreadable[0].endswith("Cp949.kt"), report.unreadable)
        self.assertTrue(any("읽지 못한 소스 1건" in line for line in render(report)))

    def test_footer_states_the_limitation(self):
        self.clean_tree()
        lines = render(self.check())
        self.assertIn(LIMITATION_NOTE, lines)
        self.assertIn("같은 패키지", LIMITATION_NOTE)
        self.assertIn("Konsist", LIMITATION_NOTE)
        self.assertIn("ArchUnit", LIMITATION_NOTE)

    def test_footer_counts_checked_and_skipped(self):
        self.app_tree()
        shutil.rmtree(self.tmpdir / "support")
        lines = render(self.check())
        report = self.check()
        self.assertIn(f"검사한 규칙 {report.checked}건 / 생략한 규칙 {len(report.skipped)}건", lines)
        self.assertTrue(any(line.startswith("생략:") and "logging" in line for line in lines))


class TestCli(CheckTestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args],
                              capture_output=True, text=True)

    def test_exit_zero_when_clean(self):
        self.clean_tree()
        result = self.run_cli(str(self.arch_path))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(LIMITATION_NOTE, result.stdout)

    def test_exit_one_when_violation(self):
        self.clean_tree()
        self.kt("claim/domain", "com.acme.claim.domain", "Leaky",
                imports=["com.acme.claim.adapter.ClaimJpaEntity"])
        result = self.run_cli(str(self.arch_path))
        self.assertEqual(result.returncode, 1, result.stdout)
        line = next(l for l in result.stdout.split("\n") if "af.deps-inward" in l)
        self.assertRegex(line, r"^.+Leaky\.kt:3: \[af\.deps-inward\] ")

    def test_exit_two_when_unresolvable(self):
        self.arch(MONO_ARCH.replace("- 분류: core", "- 분류: bogus"))
        result = self.run_cli(str(self.arch_path))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr.startswith(f"{self.arch_path}:"), result.stderr)
        self.assertIn("분류 값 'bogus'", result.stderr)

    def test_exit_two_when_file_missing(self):
        result = self.run_cli(str(self.tmpdir / "없는파일.md"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("읽을 수 없습니다", result.stderr)

    def test_usage_error(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn("사용법", result.stderr)

    def test_json_output(self):
        self.clean_tree()
        self.kt("claim/domain", "com.acme.claim.domain", "Leaky",
                imports=["com.acme.claim.adapter.ClaimJpaEntity"])
        result = self.run_cli(str(self.arch_path), "--json")
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(sorted(payload),
                         ["checked", "inherited", "skipped", "unreadable",
                          "violations", "zero_match"])
        self.assertEqual(sorted(payload["violations"][0]),
                         ["line", "message", "path", "rule_id"])
        self.assertEqual(payload["violations"][0]["rule_id"], "af.deps-inward")

    def test_json_carries_warnings(self):
        self.arch(MONO_ARCH)
        self.kt("claim/model", "com.acme.claim.model", "Claim")
        result = self.run_cli(str(self.arch_path), "--json")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["violations"], [])
        self.assertTrue(payload["zero_match"], payload)
        self.assertEqual(sorted(payload["zero_match"][0]), ["message", "rule_id", "subject"])

    def test_violation_lines_are_sorted_by_path_and_line(self):
        self.clean_tree()
        self.kt("claim/domain", "com.acme.claim.domain", "AAA",
                imports=["com.acme.claim.adapter.ClaimJpaEntity"])
        self.kt("claim/domain", "com.acme.claim.domain", "BBB",
                imports=["org.springframework.stereotype.Component"])
        result = self.run_cli(str(self.arch_path))
        lines = [l for l in result.stdout.split("\n") if l.startswith("claim/")]
        self.assertEqual(lines, sorted(lines))
        self.assertTrue(lines[0].startswith("claim/domain/src/main/kotlin/"), lines)


if __name__ == "__main__":
    unittest.main()
