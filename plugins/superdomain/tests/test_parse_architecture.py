import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from parse_architecture import parse_architecture, normalize

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

    def test_line_numbers_are_one_based_heading_lines(self):
        # minimal.md: 4번째 줄이 "## 프로젝트: backend", 10번째 줄이 "## 컨텍스트: claim"
        arch, errors = parse_architecture(load("minimal.md"))
        self.assertEqual(errors, [])
        self.assertEqual(arch.projects[0].line, 4)
        self.assertEqual(arch.contexts[0].line, 10)

    def test_context_patterns_rule_exceptions_transition(self):
        arch, errors = parse_architecture(load("full.md"))
        self.assertEqual(errors, [])
        renewal = next(c for c in arch.contexts if c.name == "renewal")
        self.assertEqual(renewal.patterns, ["cqrs", "outbox"])
        self.assertEqual(len(renewal.rule_exceptions), 1)
        self.assertEqual(renewal.rule_exceptions[0].rule_id, "ld.domain-pure")
        self.assertEqual(renewal.rule_exceptions[0].adr, "ADR-0007")
        self.assertEqual(renewal.transition, ("layered-simple", "layered-domain"))
        self.assertEqual(renewal.transition_raw, "layered-simple → layered-domain")

    def test_transition_raw_preserved_when_arrow_missing(self):
        # "→"가 빠진 "이행" 값은 transition은 ()로 남지만, transition_raw에는 원문이 보존된다.
        # 이렇게 해야 파싱 결과만으로 "라벨 없음"과 "형식 오류"를 Task 3이 구분할 수 있다.
        text = load("full.md").replace(
            "- 이행: layered-simple → layered-domain",
            "- 이행: layered-simple",
        )
        arch, errors = parse_architecture(text)
        # Task 3 계약 변경: transition_raw는 채워져 있는데 transition이 ()면 형식 오류로
        # 판정된다(위 주석이 원래 의도한 대로) — 이 fixture 자체가 그 오류 케이스이므로
        # errors는 더 이상 빈 리스트가 아니다. validate() 도입 전에는 항상 []였을 뿐이다.
        self.assertEqual(len(errors), 1)
        self.assertIn("→", errors[0].message)
        renewal = next(c for c in arch.contexts if c.name == "renewal")
        self.assertEqual(renewal.transition, ())
        self.assertEqual(renewal.transition_raw, "layered-simple")

    def test_rule_exception_malformed_item_preserved_not_dropped(self):
        # 정규식에 맞지 않는 규칙 예외 항목도 조용히 버리지 않고 보존해야 한다
        # (Task 3의 검증기가 그 존재 자체를 볼 수 있어야 형식 오류로 판정 가능).
        text = load("full.md").replace(
            "- 규칙 예외: -ld.domain-pure (ADR-0007)",
            "- 규칙 예외: -ld.domain-pure (ADR-0007), 이상한 항목 !!",
        )
        arch, errors = parse_architecture(text)
        # Task 3 계약 변경: adr가 빈 규칙 예외는 검증 오류로 판정된다(위 주석이 원래 의도한
        # 대로) — "이상한 항목 !!"이 정확히 그 케이스라 errors는 더 이상 빈 리스트가 아니다.
        # 기존 유효한 예외(-ld.domain-pure, ADR-0007 있음)는 오류를 만들지 않으므로 오류는 1건뿐이다.
        self.assertEqual(len(errors), 1)
        self.assertIn("ADR", errors[0].message)
        self.assertIn("이상한 항목 !!", errors[0].message)
        renewal = next(c for c in arch.contexts if c.name == "renewal")
        self.assertEqual(len(renewal.rule_exceptions), 2)
        self.assertEqual(renewal.rule_exceptions[1].rule_id, "이상한 항목 !!")
        self.assertEqual(renewal.rule_exceptions[1].adr, "")

def _remove_heading_block(text, start_marker):
    """start_marker로 시작하는 라인부터, 다음 '##'/'###' 헤딩 라인 전까지 제거한다.

    표(레이어 값이 없는 자유 텍스트 포함) 전체를 헤딩 단위로 들어내되, 정확한
    바이트 스니펫에 의존하지 않도록 라인 기반으로 동작한다.
    """
    lines = text.split("\n")
    out = []
    skipping = False
    for ln in lines:
        if not skipping and ln.startswith(start_marker):
            skipping = True
            continue
        if skipping:
            if ln.startswith("##"):
                skipping = False
            else:
                continue
        out.append(ln)
    return "\n".join(out)


def _remove_table_lines(text):
    """'|'로 시작하는 모든 라인을 제거한다 (단일 표만 있는 fixture에서 사용)."""
    return "\n".join(ln for ln in text.split("\n") if not ln.startswith("|"))


class TestValidation(unittest.TestCase):
    def _errors(self, text):
        _, errors = parse_architecture(text)
        return errors

    # --- 브리프 예시 그대로 ---

    def test_missing_required_project_label(self):
        text = load("minimal.md").replace("- 기본 패키지: com.acme\n", "")
        errs = self._errors(text)
        self.assertTrue(any("기본 패키지" in e.message for e in errs))

    def test_invalid_classification(self):
        text = load("minimal.md").replace("- 분류: core", "- 분류: important")
        errs = self._errors(text)
        self.assertTrue(any("분류" in e.message and "important" in e.message for e in errs))
        self.assertTrue(all(e.line > 0 for e in errs))

    # --- 표의 24개 케이스 ---

    def test_no_template_marker(self):
        text = load("minimal.md").replace("<!-- superarchitect:template v1 -->\n", "")
        errs = self._errors(text)
        self.assertTrue(any("템플릿 마커" in e.message for e in errs))

    def test_no_project(self):
        project_block = (
            "## 프로젝트: backend\n"
            "- 경로: .\n"
            "- 프로파일: kotlin-spring\n"
            "- 기본 패키지: com.acme\n"
            "- 아키텍처 테스트 위치: architecture-test/src/test/kotlin\n\n"
        )
        text = load("minimal.md").replace(project_block, "")
        self.assertNotIn("## 프로젝트:", text)
        errs = self._errors(text)
        self.assertTrue(any("프로젝트" in e.message for e in errs))

    def test_unknown_profile(self):
        # minimal.md: 4번째 줄이 "## 프로젝트: backend"(섹션 헤딩), 6번째 줄이 "- 프로파일: ...".
        # 오류가 라벨 자신의 라인(6)을 가리켜야 한다 — 헤딩 라인(4)으로 폴백하면 회귀다.
        text = load("minimal.md").replace("- 프로파일: kotlin-spring", "- 프로파일: rust-axum")
        errs = self._errors(text)
        matches = [e for e in errs if "프로파일" in e.message]
        self.assertTrue(matches)
        self.assertEqual(matches[0].line, 6)

    def test_context_missing_style(self):
        # 라벨 자체가 없으므로 label_lines에 항목이 없다 — 이 경우엔 섹션 헤딩 라인(10)으로
        # 폴백하는 것이 올바른 동작이다(라벨이 없으니 라벨 라인을 가리킬 수 없다).
        text = load("minimal.md").replace("- 스타일: hexagonal\n", "")
        errs = self._errors(text)
        matches = [e for e in errs if "스타일" in e.message]
        self.assertTrue(matches)
        self.assertEqual(matches[0].line, 10)

    def test_invalid_module_layout(self):
        # minimal.md: 10번째 줄이 "## 컨텍스트: claim"(섹션 헤딩), 13번째 줄이 "- 모듈 구성: ...".
        # 오류가 라벨 자신의 라인(13)을 가리켜야 한다 — 헤딩 라인(10)으로 폴백하면 회귀다.
        text = load("minimal.md").replace("- 모듈 구성: multi-module", "- 모듈 구성: mono")
        errs = self._errors(text)
        matches = [e for e in errs if "모듈 구성" in e.message]
        self.assertTrue(matches)
        self.assertEqual(matches[0].line, 13)

    def test_invalid_style_value(self):
        # minimal.md: 10번째 줄이 "## 컨텍스트: claim"(섹션 헤딩), 12번째 줄이 "- 스타일: ...".
        # 오류가 라벨 자신의 라인(12)을 가리켜야 한다 — 헤딩 라인(10)으로 폴백하면 회귀다.
        text = load("minimal.md").replace("- 스타일: hexagonal", "- 스타일: onion")
        errs = self._errors(text)
        matches = [e for e in errs if "스타일" in e.message and "onion" in e.message]
        self.assertTrue(matches)
        self.assertEqual(matches[0].line, 12)

    def test_custom_style_accepted(self):
        text = load("minimal.md").replace("- 스타일: hexagonal", "- 스타일: custom/our-hex")
        errs = self._errors(text)
        self.assertEqual(errs, [])

    def test_multi_module_requires_module_table(self):
        # minimal.md: 10번째 줄이 "## 컨텍스트: claim"(섹션 헤딩), 13번째 줄이
        # "- 모듈 구성: multi-module". 표 라인만 지우므로 라벨 라인은 그대로 13에 남는다.
        # 오류가 라벨 라인(13)을 가리켜야 한다 — 헤딩 라인(10)으로 폴백하면 회귀다.
        text = _remove_table_lines(load("minimal.md"))
        errs = self._errors(text)
        matches = [e for e in errs if "모듈 표" in e.message]
        self.assertTrue(matches)
        self.assertEqual(matches[0].line, 13)

    def test_app_embedded_forbids_module_table(self):
        # full.md: 33번째 줄이 "## 컨텍스트: brawlstars"(섹션 헤딩), 37번째 줄이
        # "- 모듈 구성: app-embedded"(cat -n으로 직접 세어 확인). 표는 그 라벨 뒤에
        # 삽입하므로 라벨 자신의 라인 번호는 바뀌지 않는다.
        # 오류가 라벨 라인(37)을 가리켜야 한다 — 헤딩 라인(33)으로 폴백하면 회귀다.
        anchor = "- 모듈 구성: app-embedded\n\n### 관계"
        insertion = (
            "- 모듈 구성: app-embedded\n\n"
            "| 모듈 | 경로 | 레이어 |\n|---|---|---|\n"
            "| brawlstars-domain | brawlstars/domain | domain |\n\n"
            "### 관계"
        )
        text = load("full.md")
        self.assertEqual(text.count(anchor), 1)
        text = text.replace(anchor, insertion)
        errs = self._errors(text)
        matches = [e for e in errs if "app-embedded" in e.message]
        self.assertTrue(matches)
        self.assertEqual(matches[0].line, 37)

    def test_app_embedded_requires_conventions(self):
        text = _remove_heading_block(load("full.md"), "### 패키지 규약")
        self.assertNotIn("패키지 규약", text)
        errs = self._errors(text)
        self.assertTrue(any("패키지 규약" in e.message for e in errs))

    def test_app_embedded_requires_applications(self):
        text = _remove_heading_block(load("full.md"), "### 애플리케이션")
        self.assertNotIn("### 애플리케이션", text)
        errs = self._errors(text)
        self.assertTrue(any("애플리케이션" in e.message for e in errs))

    def test_app_embedded_same_style(self):
        anchor = "## 컨텍스트: statistics\n- 프로젝트: imstargg-backend\n- 분류: core\n- 스타일: layered-domain"
        replacement = "## 컨텍스트: statistics\n- 프로젝트: imstargg-backend\n- 분류: core\n- 스타일: hexagonal"
        text = load("full.md")
        self.assertEqual(text.count(anchor), 1)
        text = text.replace(anchor, replacement)
        errs = self._errors(text)
        self.assertTrue(any("같은 스타일" in e.message for e in errs))

    def test_context_project_ref(self):
        anchor = "## 컨텍스트: claim\n- 분류: core"
        replacement = "## 컨텍스트: claim\n- 프로젝트: nothere\n- 분류: core"
        text = load("minimal.md")
        self.assertEqual(text.count(anchor), 1)
        text = text.replace(anchor, replacement)
        errs = self._errors(text)
        self.assertTrue(any("프로젝트" in e.message and "nothere" in e.message for e in errs))

    def test_ambiguous_project_when_multiple(self):
        second_project = (
            "## 프로젝트: frontend\n"
            "- 경로: frontend\n"
            "- 프로파일: kotlin-spring\n"
            "- 기본 패키지: com.acme.frontend\n"
            "- 아키텍처 테스트 위치: architecture-test/src/test/kotlin\n\n"
        )
        text = load("minimal.md").replace("## 컨텍스트: claim", second_project + "## 컨텍스트: claim", 1)
        errs = self._errors(text)
        self.assertTrue(any("프로젝트를 지정" in e.message for e in errs))

    def test_invalid_shared_role(self):
        anchor = "| core-enum | core/core-enum | shared-kernel |"
        replacement = "| core-enum | core/core-enum | common |"
        text = load("full.md")
        self.assertEqual(text.count(anchor), 1)
        text = text.replace(anchor, replacement)
        errs = self._errors(text)
        self.assertTrue(any("역할" in e.message and "common" in e.message for e in errs))

    def test_invalid_relation_type(self):
        anchor = "| statistics | customer-supplier | brawlstars-events-v1 |"
        replacement = "| statistics | friends | brawlstars-events-v1 |"
        text = load("full.md")
        self.assertEqual(text.count(anchor), 1)
        text = text.replace(anchor, replacement)
        errs = self._errors(text)
        self.assertTrue(any("관계 유형" in e.message and "friends" in e.message for e in errs))

    def test_relation_target_exists(self):
        anchor = "| statistics | customer-supplier | brawlstars-events-v1 |"
        replacement = "| ghost | customer-supplier | brawlstars-events-v1 |"
        text = load("full.md")
        self.assertEqual(text.count(anchor), 1)
        text = text.replace(anchor, replacement)
        errs = self._errors(text)
        self.assertTrue(any("ghost" in e.message for e in errs))

    def test_application_context_exists(self):
        anchor = "| core-worker | core/core-worker | brawlstars |"
        replacement = "| core-worker | core/core-worker | ghost |"
        text = load("full.md")
        self.assertEqual(text.count(anchor), 1)
        text = text.replace(anchor, replacement)
        errs = self._errors(text)
        self.assertTrue(any("ghost" in e.message for e in errs))

    def test_rule_exception_requires_adr(self):
        anchor = "- 모듈 구성: multi-module\n"
        text = load("minimal.md")
        self.assertEqual(text.count(anchor), 1)
        text = text.replace(anchor, anchor + "- 규칙 예외: -hex.domain-pure\n")
        errs = self._errors(text)
        self.assertTrue(any("ADR" in e.message for e in errs))

    def test_transition_target_matches_style(self):
        anchor = "- 모듈 구성: multi-module\n"
        text = load("minimal.md")
        self.assertEqual(text.count(anchor), 1)
        text = text.replace(anchor, anchor + "- 이행: layered-simple → clean\n")
        errs = self._errors(text)
        self.assertTrue(any("이행" in e.message for e in errs))

    def test_transition_format(self):
        anchor = "- 모듈 구성: multi-module\n"
        text = load("minimal.md")
        self.assertEqual(text.count(anchor), 1)
        text = text.replace(anchor, anchor + "- 이행: layered-simple\n")
        errs = self._errors(text)
        self.assertTrue(any("→" in e.message for e in errs))

    def test_duplicate_context_name(self):
        text = load("minimal.md")
        idx = text.index("## 컨텍스트: claim")
        context_block = text[idx:]
        text = text + "\n" + context_block
        self.assertEqual(text.count("## 컨텍스트: claim"), 2)
        errs = self._errors(text)
        self.assertTrue(any("중복" in e.message for e in errs))

    def test_duplicate_project_name(self):
        project_block = (
            "## 프로젝트: backend\n"
            "- 경로: .\n"
            "- 프로파일: kotlin-spring\n"
            "- 기본 패키지: com.acme\n"
            "- 아키텍처 테스트 위치: architecture-test/src/test/kotlin\n\n"
        )
        text = load("minimal.md")
        self.assertIn(project_block, text)
        text = text.replace(project_block, project_block + project_block, 1)
        self.assertEqual(text.count("## 프로젝트: backend"), 2)
        errs = self._errors(text)
        self.assertTrue(any("중복" in e.message for e in errs))

    # --- 결의안 2에서 명시한 "레이어 값 비어있지 않음" 확인 (표에는 없지만 브리프가 요구) ---

    def test_module_layer_empty(self):
        text = load("minimal.md").replace(
            "| claim-domain | claim/domain | domain |",
            "| claim-domain | claim/domain |  |",
        )
        errs = self._errors(text)
        self.assertTrue(any("레이어" in e.message for e in errs))

    # --- Task 4 컨트롤러 결의: single-module도 모듈 표가 필수다 ---

    def test_single_module_requires_module_table(self):
        # minimal.md: 13번째 줄이 "- 모듈 구성: multi-module". 표 라인만 지우고
        # multi-module -> single-module로 바꾸면, 모듈 표가 없는 single-module 컨텍스트가 된다.
        # 오류가 라벨 라인(13)을 가리켜야 한다 — 헤딩 라인(10)으로 폴백하면 회귀다.
        text = _remove_table_lines(load("minimal.md")).replace(
            "- 모듈 구성: multi-module", "- 모듈 구성: single-module"
        )
        errs = self._errors(text)
        matches = [e for e in errs if "모듈 표" in e.message and "single-module" in e.message]
        self.assertTrue(matches)
        self.assertEqual(matches[0].line, 13)

    def test_single_module_with_table_is_valid(self):
        # 모듈 표가 있으면 single-module도 오류 없이 통과한다(회귀 방지용 대조 케이스).
        text = load("minimal.md").replace("- 모듈 구성: multi-module", "- 모듈 구성: single-module")
        errs = self._errors(text)
        self.assertEqual(errs, [])


class TestNormalize(unittest.TestCase):
    def test_multi_module_default_convention(self):
        arch, _ = parse_architecture(load("minimal.md"))
        pats = normalize(arch)
        got = {(p.context, p.layer, p.pattern) for p in pats}
        self.assertIn(("claim", "domain", "com.acme.claim.domain.."), got)
        self.assertIn(("claim", "application", "com.acme.claim.application.."), got)
        self.assertIn(("claim", "adapter", "com.acme.claim.adapter.."), got)
        self.assertEqual(len([p for p in pats if p.layer == "adapter"]), 1)  # in/out 중복 제거

    def test_app_embedded_conventions(self):
        arch, _ = parse_architecture(load("full.md"))
        pats = normalize(arch)
        got = {(p.context, p.layer, p.pattern) for p in pats}
        self.assertIn(("brawlstars", "domain", "com.imstargg.core.domain.brawlstars.."), got)
        self.assertIn(("brawlstars", "application", "com.imstargg.core.application.brawlstars.."), got)
        # {앱} 패턴은 앱별 전개(하이픈→점 치환), 컨텍스트 비분할이므로 context="*"
        self.assertIn(("*", "presentation", "com.imstargg.core.api.."), got)
        self.assertIn(("*", "presentation", "com.imstargg.core.batch.."), got)

    def test_presentation_star_pattern_emitted_once_per_app_not_per_context(self):
        # full.md는 컨텍스트 4개(brawlstars/statistics/operation/renewal)를 가진 프로젝트에
        # presentation 규약(컨텍스트 비분할, {앱} 포함)을 선언한다. 컨텍스트마다 한 번씩
        # 돌면서 전개하면 4(컨텍스트) x 4(앱) = 16개가 생기는 버그가 될 수 있다 — 실제로는
        # 프로젝트당 1회만 전개되어 앱 개수만큼(4개)만 나와야 한다.
        arch, _ = parse_architecture(load("full.md"))
        pats = normalize(arch)
        star_presentation = [p for p in pats if p.context == "*" and p.layer == "presentation"]
        self.assertEqual(len(star_presentation), 4)
        self.assertEqual(
            {p.pattern for p in star_presentation},
            {
                "com.imstargg.core.api..",
                "com.imstargg.core.batch..",
                "com.imstargg.core.worker..",
                "com.imstargg.core.admin..",
            },
        )

    def test_single_module_all_layer(self):
        text = load("minimal.md").replace("- 모듈 구성: multi-module", "- 모듈 구성: single-module") \
            .replace("| claim-domain | claim/domain | domain |", "| claim | claim | all |")
        # 나머지 모듈 행 3개 삭제
        for row in ["| claim-application | claim/application | application |",
                    "| claim-adapter-in | claim/adapter-in | adapter |",
                    "| claim-adapter-out | claim/adapter-out | adapter |"]:
            text = text.replace(row + "\n", "")
        arch, errors = parse_architecture(text)
        self.assertEqual(errors, [])
        pats = normalize(arch)
        self.assertIn(("claim", "all", "com.acme.claim.."), {(p.context, p.layer, p.pattern) for p in pats})

    def test_result_sorted_and_deduplicated(self):
        arch, _ = parse_architecture(load("minimal.md"))
        pats = normalize(arch)
        as_tuples = [(p.project, p.context, p.layer, p.pattern) for p in pats]
        self.assertEqual(as_tuples, sorted(set(as_tuples)))
        self.assertEqual(len(as_tuples), len(set(as_tuples)))


if __name__ == "__main__":
    unittest.main()
