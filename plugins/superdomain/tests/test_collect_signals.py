import json, os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from collect_signals import (HOTSPOT_TOP, INTERPRETATION_NOTE, LIMITATION_NOTE, PATH_SAMPLES,
                             CollectError, collect, payload, render)

ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = Path(__file__).resolve().parent
SCRIPT = ROOT / "scripts" / "collect_signals.py"

HEAD = """# 샘플 — Domain
<!-- superdomain:template v1 -->

## 프로젝트: backend
- 경로: .
- 기본 패키지: com.acme
"""

CONTEXT = """
## 컨텍스트: {name}
- 분류: {classification}
"""

# 컨텍스트 둘 — 명시 `- 패키지:`가 없으므로 규약 기본값 `com.acme.<컨텍스트>..`가 쓰인다.
DOMAIN = (HEAD
          + CONTEXT.format(name="claim", classification="core")
          + CONTEXT.format(name="billing", classification="supporting"))

# 컨텍스트들이 나눠 갖지 않는 공용 패키지(`com.acme.web..`)가 있는 트리 — 어느 컨텍스트
# 패키지에도 들지 않으므로 그 아래 파일은 귀속을 판별할 수 없다.
SHARED_DOMAIN = """# 공용 패키지 — Domain
<!-- superdomain:template v1 -->

## 프로젝트: backend
- 경로: .
- 기본 패키지: com.acme

## 컨텍스트: claim
- 분류: core
- 패키지: com.acme.core.domain.claim..

## 컨텍스트: billing
- 분류: supporting
- 패키지: com.acme.core.domain.billing..
"""

# 필수 라벨(`기본 패키지`)이 없다 — parse_domain이 해석 불가로 거부한다.
BROKEN_DOMAIN = """# 깨진 문서
<!-- superdomain:template v1 -->

## 프로젝트: backend
- 경로: .
"""


def in_project(section, project):
    """컨텍스트 섹션에 `- 프로젝트:` 라벨을 붙인다 — 프로젝트가 둘 이상이면 필수다."""
    return section.replace("- 분류:", f"- 프로젝트: {project}\n- 분류:", 1)


# 모노레포 — 두 프로젝트가 **같은 기본 패키지**를 쓴다. 패키지 패턴만으로는 두 프로젝트가
# 구분되지 않으므로 귀속을 가르는 것은 경로 접두뿐이고, 접두를 보지 않으면 `services/pay` 아래의
# 파일이 루트 프로젝트로 새어 들어간다.
MULTI_DOMAIN = ("""# 모노레포 — Domain
<!-- superdomain:template v1 -->

## 프로젝트: root
- 경로: .
- 기본 패키지: com.acme

## 프로젝트: pay
- 경로: services/pay
- 기본 패키지: com.acme
"""
                + in_project(CONTEXT.format(name="claim", classification="core"), "root")
                + in_project(CONTEXT.format(name="billing", classification="supporting"), "pay"))


class SignalsTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="superdomain-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmpdir, True)
        self.repo = self.tmpdir / "repo"
        self.repo.mkdir()
        self.domain_path = self.repo / "DOMAIN.md"
        subprocess.run(["git", "-c", "init.defaultBranch=main", "init", "-q", str(self.repo)],
                       check=True, capture_output=True)
        for key, value in (("user.email", "t@example.com"), ("user.name", "T"),
                           ("commit.gpgsign", "false")):
            self.git("config", key, value)

    # ---- 저장소 도우미 ----------------------------------------------------

    def git(self, *args, env=None):
        return subprocess.run(["git", "-C", str(self.repo), *args],
                              check=True, capture_output=True, text=True, env=env).stdout

    def write(self, relpath, text):
        path = self.repo / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def domain(self, text=DOMAIN):
        self.write("DOMAIN.md", text)

    def kt(self, module, package, name, marker="1"):
        relpath = f"{module}/src/main/kotlin/{package.replace('.', '/')}/{name}.kt"
        return self.write(relpath, f"package {package}\n\nclass {name} // rev {marker}\n")

    def commit(self, message, date=None, committed=None):
        """`committed`를 따로 주면 작성자 날짜와 커밋터 날짜가 갈린다(축 검증용)."""
        env = None
        if date or committed:
            env = dict(os.environ, GIT_AUTHOR_DATE=date or committed,
                       GIT_COMMITTER_DATE=committed or date)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message, env=env)
        return self.git("rev-parse", "HEAD").strip()

    def base(self):
        """DOMAIN.md 하나만 담긴 첫 커밋. 반환값은 그 커밋 해시다."""
        self.domain()
        return self.commit("init")

    # ---- 실행 도우미 ------------------------------------------------------

    def collect(self, since=None):
        return collect(self.domain_path, since=since)

    def run_cli(self, *args, cwd=None):
        result = subprocess.run([sys.executable, str(SCRIPT), *args],
                                capture_output=True, text=True, cwd=str(cwd or self.repo))
        return result.returncode, result.stdout, result.stderr

    def by_key(self, signals):
        return {entry.key: entry for entry in signals.contexts}


# ---------------------------------------------------------------------------
# 신호 ① 컨텍스트별 변경 빈도 / 귀속
# ---------------------------------------------------------------------------

class ContextFrequencyTest(SignalsTestCase):
    def test_commits_and_files_per_context(self):
        self.base()
        self.kt("claim/domain", "com.acme.claim.domain", "Claim")
        self.commit("claim 1")
        self.kt("claim/domain", "com.acme.claim.domain", "Claim", marker="2")
        self.kt("claim/application", "com.acme.claim.application", "ClaimService")
        self.commit("claim 2")
        self.kt("billing/domain", "com.acme.billing.domain", "Invoice")
        self.commit("billing 1")

        table = self.by_key(self.collect())
        self.assertEqual(table["backend:claim"].commits, 2)
        self.assertEqual(table["backend:claim"].files, 2)
        self.assertEqual(table["backend:claim"].changes, 3)
        self.assertEqual(table["backend:billing"].commits, 1)
        self.assertEqual(table["backend:billing"].files, 1)

    def test_contexts_sorted_by_commit_count(self):
        self.base()
        self.kt("billing/domain", "com.acme.billing.domain", "Invoice")
        self.commit("billing 1")
        for index in range(2):
            self.kt("claim/domain", "com.acme.claim.domain", "Claim", marker=str(index))
            self.commit(f"claim {index}")

        self.assertEqual([entry.key for entry in self.collect().contexts],
                         ["backend:claim", "backend:billing"])

    def test_test_sources_are_not_attributed(self):
        """`src/test` 아래는 프로덕션 소스가 아니다 — check_imports와 같은 경계."""
        self.base()
        self.write("claim/domain/src/test/kotlin/com/acme/claim/domain/ClaimTest.kt",
                   "package com.acme.claim.domain\n\nclass ClaimTest\n")
        self.commit("test only")

        self.assertEqual(self.by_key(self.collect()).get("backend:claim"), None)

    def test_sibling_package_prefix_is_not_absorbed(self):
        """`claim`과 `claiming`은 형제다 — 문자열 접두로만 보면 앞이 뒤를 삼킨다.

        `_package_as_path`가 끝에 `/`를 붙여 세그먼트 경계를 만드는 이유가 이것이다. 경계가
        없으면 `com/acme/claiming/Policy.kt`가 claim의 변경으로 세어져 그 컨텍스트의 변경
        빈도·핫스팟·동시 변경이 함께 부풀고, 그 파일은 '귀속 불가' 버킷에서도 사라진다 —
        오류도 경고도 없이 evolve가 읽는 수치만 틀어지는 채널이라 여기서 못박는다.
        같은 규칙을 check_imports(`_owning_context`)와 parse_domain(겹침 검사)도 잠그고 있다.
        """
        self.base()
        self.kt("claim", "com.acme.claim", "Claim")
        legacy = self.kt("claiming", "com.acme.claiming", "Policy")
        self.commit("claim + claiming")

        signals = self.collect()
        # claim이 가져가는 것은 자기 패키지의 파일 하나뿐이다.
        self.assertEqual(self.by_key(signals)["backend:claim"].files, 1)
        self.assertIn(str(legacy.relative_to(self.repo)), signals.unattributed.samples)

    def test_multi_project_attribution_follows_the_path_prefix(self):
        """모노레포에서 프로젝트를 가르는 것은 경로 접두다 — 두 프로젝트가 같은 기본 패키지를
        쓰면 패턴만으로는 갈리지 않고, 긴 접두가 이겨야 중첩 프로젝트가 루트로 새지 않는다.
        패턴 소유는 프로젝트 단위이므로 같은 패키지라도 다른 프로젝트에서는 귀속되지 않는다."""
        self.domain(MULTI_DOMAIN)
        self.commit("init")
        self.kt("claim/domain", "com.acme.claim.domain", "Claim")
        self.kt("services/pay/billing/domain", "com.acme.billing.domain", "Invoice")
        # `pay` 아래에 있지만 패키지는 `root`의 claim 것 — 그 패턴의 소유자는 `root`뿐이다.
        ghost = self.kt("services/pay/billing/domain", "com.acme.claim.domain", "Ghost")
        self.commit("sources")

        signals = self.collect()
        table = self.by_key(signals)
        self.assertEqual(sorted(table), ["pay:billing", "root:claim"])
        self.assertEqual(table["root:claim"].files, 1)
        self.assertEqual(table["pay:billing"].files, 1)
        self.assertIn(str(ghost.relative_to(self.repo)), signals.unattributed.samples)


class UnattributedTest(SignalsTestCase):
    def test_non_source_file_goes_to_unattributed_bucket(self):
        self.base()
        self.write("README.md", "hello\n")
        self.commit("readme")

        signals = self.collect()
        self.assertIn("README.md", signals.unattributed.samples)
        self.assertGreaterEqual(signals.unattributed.commits, 1)

    def test_package_outside_every_pattern_is_unattributed(self):
        self.base()
        self.kt("misc", "com.other.tooling", "Thing")
        self.commit("misc")

        signals = self.collect()
        self.assertIn("misc/src/main/kotlin/com/other/tooling/Thing.kt",
                      signals.unattributed.samples)
        self.assertEqual(self.by_key(signals).get("backend:claim"), None)

    def test_package_shared_by_no_context_cannot_attribute(self):
        """컨텍스트들이 나눠 갖지 않는 공용 패키지는 판별력이 없다 — 아무 쪽에도 넣지 않는다.

        구 모델의 app-embedded는 `{앱}` 행으로 컨텍스트 비분할 패턴을 만들어 같은 상태를
        만들었다. 새 모델에서는 컨텍스트 패키지가 서로 겹치면 파서가 오류를 내므로, 남은
        갈래는 '어느 컨텍스트 패키지에도 들지 않는 공용 코드'다.
        """
        self.domain(SHARED_DOMAIN)
        self.commit("init")
        self.kt("app/web", "com.acme.web", "Controller")
        self.kt("core", "com.acme.core.domain.claim", "Claim")
        self.commit("app + domain")

        signals = self.collect()
        self.assertEqual([entry.key for entry in signals.contexts], ["backend:claim"])
        self.assertIn("app/web/src/main/kotlin/com/acme/web/Controller.kt",
                      signals.unattributed.samples)

    def test_project_outside_the_repository_is_announced(self):
        """저장소 밖 프로젝트는 영구 0건이다 — 사유 없이 조용히 빼면 '변경 없음'과 구분되지 않는다."""
        self.write("DOMAIN.md", DOMAIN.replace("- 경로: .", "- 경로: ../바깥"))
        self.commit("init")

        signals = self.collect()
        self.assertEqual(signals.contexts, [])
        self.assertTrue(any("저장소" in note and "바깥" in note for note in signals.notices),
                        signals.notices)

    def test_unattributed_is_announced_in_report(self):
        self.base()
        self.write("README.md", "hello\n")
        self.commit("readme")

        self.assertTrue(any("귀속 불가" in line for line in render(self.collect())))

    def test_sample_paths_are_capped_but_the_count_is_not(self):
        """`samples`는 예시라 상한이 있고 `files`는 전수다 — 둘이 같아지면 예시가 전부인 줄
        읽혀 귀속 불가의 크기를 과소평가한다."""
        self.base()                                  # DOMAIN.md 1건
        for index in range(12):
            self.write(f"docs/notes/n{index:02d}.md", "note\n")
        self.commit("notes")

        orphan = self.collect().unattributed
        self.assertEqual(len(orphan.samples), PATH_SAMPLES)
        self.assertEqual(orphan.files, 13)
        self.assertEqual(orphan.samples, sorted(orphan.samples))
        self.assertEqual(orphan.samples[0], "DOMAIN.md")


# ---------------------------------------------------------------------------
# 신호 ② 핫스팟
# ---------------------------------------------------------------------------

class HotspotTest(SignalsTestCase):
    def test_most_changed_file_ranks_first(self):
        self.base()
        for index in range(3):
            self.kt("claim/domain", "com.acme.claim.domain", "Claim", marker=str(index))
            self.commit(f"claim {index}")
        self.kt("billing/domain", "com.acme.billing.domain", "Invoice")
        self.commit("billing")

        top = self.collect().hotspots[0]
        self.assertEqual(top.path, "claim/domain/src/main/kotlin/com/acme/claim/domain/Claim.kt")
        self.assertEqual(top.commits, 3)
        self.assertEqual(top.key, "backend:claim")

    def test_hotspot_carries_unattributed_marker(self):
        self.base()
        self.write("README.md", "1\n")
        self.commit("readme 1")
        self.write("README.md", "2\n")
        self.commit("readme 2")

        entry = next(h for h in self.collect().hotspots if h.path == "README.md")
        self.assertEqual(entry.key, "")

    def test_hotspot_list_is_capped_but_the_total_is_reported(self):
        """상한은 표시 상한이지 임계값이 아니다 — 잘린 목록만 남고 전체 파일 수가 사라지면
        `상위 20`이 '바뀐 파일이 20건'으로 읽힌다."""
        self.base()                                  # DOMAIN.md 1건
        for index in range(HOTSPOT_TOP + 1):
            self.kt("claim/domain", "com.acme.claim.domain", f"Type{index:02d}")
        self.commit("many")

        signals = self.collect()
        self.assertEqual(len(signals.hotspots), HOTSPOT_TOP)
        self.assertEqual(signals.span["files"], HOTSPOT_TOP + 2)
        self.assertIn(f"상위 {HOTSPOT_TOP} (바뀐 파일 {HOTSPOT_TOP + 2}건 중)",
                      "\n".join(render(signals)))


# ---------------------------------------------------------------------------
# 신호 ③ 컨텍스트 쌍 동시 변경
# ---------------------------------------------------------------------------

class CoChangeTest(SignalsTestCase):
    def test_pair_touched_in_one_commit(self):
        self.base()
        self.kt("claim/domain", "com.acme.claim.domain", "Claim")
        self.kt("billing/domain", "com.acme.billing.domain", "Invoice")
        self.commit("both")

        pairs = self.collect().cochanges
        self.assertEqual([(p.a, p.b, p.commits) for p in pairs],
                         [("backend:billing", "backend:claim", 1)])

    def test_single_context_commits_make_no_pair(self):
        self.base()
        self.kt("claim/domain", "com.acme.claim.domain", "Claim")
        self.commit("claim")
        self.kt("billing/domain", "com.acme.billing.domain", "Invoice")
        self.commit("billing")

        self.assertEqual(self.collect().cochanges, [])


# ---------------------------------------------------------------------------
# 신호 ④ review-log 반복 위반
# ---------------------------------------------------------------------------

def review_line(rule, path, date="2026-08-01", severity="blocker", note="관측"):
    return json.dumps({"date": date, "rule": rule, "path": path,
                       "severity": severity, "note": note}, ensure_ascii=False)


CLAIM_KT = "claim/domain/src/main/kotlin/com/acme/claim/domain/Claim.kt"


class ReviewLogTest(SignalsTestCase):
    def log(self, *lines):
        self.write("docs/domain/review-log.jsonl", "".join(f"{line}\n" for line in lines))

    def test_counts_per_rule_with_file_and_review_spread(self):
        self.base()
        claim = "claim/domain/src/main/kotlin/com/acme/claim/domain/Claim.kt"
        other = "claim/domain/src/main/kotlin/com/acme/claim/domain/Policy.kt"
        self.log(review_line("hex.domain-pure", claim, date="2026-08-01"),
                 review_line("hex.domain-pure", other, date="2026-08-02"),
                 review_line("hex.domain-pure", other, date="2026-08-02"),
                 review_line("ls.service-naming", claim, date="2026-08-03"))
        self.commit("log")

        rules = {entry.rule: entry for entry in self.collect().review_log.rules}
        self.assertEqual(rules["hex.domain-pure"].count, 3)
        self.assertEqual(rules["hex.domain-pure"].files, 2)
        self.assertEqual(rules["hex.domain-pure"].reviews, 2)
        self.assertEqual(rules["hex.domain-pure"].contexts, 1)
        self.assertEqual(rules["ls.service-naming"].count, 1)

    def test_rules_sorted_by_count(self):
        self.base()
        claim = "claim/domain/src/main/kotlin/com/acme/claim/domain/Claim.kt"
        self.log(review_line("a.one", claim),
                 review_line("b.two", claim),
                 review_line("b.two", claim, date="2026-08-02"))
        self.commit("log")

        self.assertEqual([entry.rule for entry in self.collect().review_log.rules],
                         ["b.two", "a.one"])

    def test_broken_line_is_announced_and_skipped(self):
        self.base()
        claim = "claim/domain/src/main/kotlin/com/acme/claim/domain/Claim.kt"
        self.log(review_line("a.one", claim), "{깨진 줄", review_line("a.one", claim))
        self.commit("log")

        signals = self.collect()
        self.assertEqual(len(signals.review_log.broken), 1)
        self.assertTrue(signals.review_log.broken[0].startswith(
            "docs/domain/review-log.jsonl:2:"))
        self.assertEqual(signals.review_log.rules[0].count, 2)
        self.assertIn(signals.review_log.broken[0], signals.notices)

    def test_entry_without_rule_key_is_announced(self):
        self.base()
        self.log(json.dumps({"date": "2026-08-01", "path": "x"}))
        self.commit("log")

        broken = self.collect().review_log.broken
        self.assertEqual(len(broken), 1)
        self.assertIn("rule", broken[0])

    def test_input_sentinel_is_not_counted_as_a_file(self):
        """`(input)`은 파일을 지목할 수 없다는 표식이다(review SKILL 5-b) — 파일 수에 들면
        한 파일짜리 지적이 '서로 다른 파일 2개 이상' 문턱을 넘는다."""
        self.base()
        self.log(review_line("a.one", CLAIM_KT),
                 review_line("a.one", "(input)"),
                 review_line("a.one", "(input)", date="2026-08-02"))
        self.commit("log")

        entry = self.collect().review_log.rules[0]
        self.assertEqual(entry.count, 3)
        self.assertEqual(entry.files, 1)
        self.assertEqual(entry.inputs, 2)

    def test_severity_distribution_is_carried_per_rule(self):
        """severity를 버리면 info 지적만으로 '3회 이상'이 채워진다 — 거르지 말고 노출한다."""
        self.base()
        self.log(review_line("a.one", CLAIM_KT, severity="blocker"),
                 review_line("a.one", CLAIM_KT, severity="blocker", date="2026-08-02"),
                 review_line("a.one", CLAIM_KT, severity="info", date="2026-08-03"))
        self.commit("log")

        entry = self.collect().review_log.rules[0]
        self.assertEqual(entry.severities,
                         [{"severity": "blocker", "count": 2}, {"severity": "info", "count": 1}])

    def test_missing_severity_is_kept_as_an_empty_value(self):
        """없는 값을 지어내지 않는다 — 빈 문자열로 싣고 표시에서만 (미기재)로 읽는다."""
        self.base()
        self.log(json.dumps({"date": "2026-08-01", "rule": "a.one", "path": CLAIM_KT}))
        self.commit("log")

        signals = self.collect()
        self.assertEqual(signals.review_log.rules[0].severities, [{"severity": "", "count": 1}])
        self.assertIn("(미기재)", "\n".join(render(signals)))

    def test_missing_severity_sorts_first_on_a_tie(self):
        """`_tally`는 건수 내림차순, 같으면 값 오름차순이다. 빈 문자열이 어떤 값보다 앞서므로
        동률이면 `(미기재)`가 먼저 나온다 — 표시 순서를 여기서 고정해 둔다."""
        self.base()
        self.log(json.dumps({"date": "2026-08-01", "rule": "a.one", "path": CLAIM_KT}),
                 review_line("a.one", CLAIM_KT, severity="blocker", date="2026-08-02"))
        self.commit("log")

        signals = self.collect()
        self.assertEqual(signals.review_log.rules[0].severities,
                         [{"severity": "", "count": 1}, {"severity": "blocker", "count": 1}])
        self.assertIn("심각도: (미기재) 1, blocker 1", "\n".join(render(signals)))

    def test_empty_rule_value_is_announced_precisely(self):
        self.base()
        self.log(json.dumps({"date": "2026-08-01", "rule": "", "path": CLAIM_KT}))
        self.commit("log")

        self.assertIn("비어 있습니다", self.collect().review_log.broken[0])

    @unittest.skipIf(getattr(os, "geteuid", lambda: 1)() == 0, "root는 권한 거부를 겪지 않는다")
    def test_unreadable_file_is_announced_not_raised(self):
        """읽지 못한 입력은 예외로 터지지 않고 고지로 남는다 — 침묵도 중단도 아니다."""
        self.base()
        path = self.write("docs/domain/review-log.jsonl",
                          review_line("a.one", "x.kt") + "\n")
        self.commit("log")
        path.chmod(0o000)
        try:
            signals = self.collect()
        finally:
            path.chmod(0o644)

        self.assertTrue(signals.review_log.present)
        self.assertEqual(signals.review_log.rules, [])
        self.assertTrue(any("읽지 못했습니다" in note for note in signals.notices))

    def test_missing_review_log_is_announced(self):
        self.base()
        signals = self.collect()
        self.assertFalse(signals.review_log.present)
        self.assertTrue(any("review-log.jsonl이 없습니다" in note for note in signals.notices))


# ---------------------------------------------------------------------------
# 신호 ⑤ baseline 추이
# ---------------------------------------------------------------------------

def baseline_line(rule, path, note=None):
    entry = {"rule": rule, "path": path}
    if note is not None:
        entry["note"] = note
    return json.dumps(entry, ensure_ascii=False)


class BaselineTest(SignalsTestCase):
    def baseline(self, *lines):
        self.write("docs/domain/baseline.jsonl", "".join(f"{line}\n" for line in lines))

    def test_line_count_trend_over_commits(self):
        self.base()
        self.baseline(baseline_line("hex.domain-pure", "a.kt"),
                      baseline_line("hex.domain-pure", "b.kt"),
                      baseline_line("hex.ports-owned-inside", "c.kt"))
        self.commit("freeze")
        self.baseline(baseline_line("hex.domain-pure", "a.kt"))
        self.commit("migrate one cluster")

        baseline = self.collect().baseline
        self.assertTrue(baseline.present)
        self.assertEqual([point.lines for point in baseline.history], [3, 1])
        self.assertEqual([point.delta for point in baseline.history], [3, -2])
        self.assertEqual(baseline.lines, 1)

    def test_current_rule_distribution(self):
        self.base()
        self.baseline(baseline_line("hex.domain-pure", "a.kt"),
                      baseline_line("hex.domain-pure", "b.kt"),
                      baseline_line("hex.ports-owned-inside", "c.kt"))
        self.commit("freeze")

        self.assertEqual(self.collect().baseline.rules,
                         [{"rule": "hex.domain-pure", "count": 2},
                          {"rule": "hex.ports-owned-inside", "count": 1}])

    def test_absent_baseline_is_announced(self):
        self.base()
        signals = self.collect()
        self.assertFalse(signals.baseline.present)
        self.assertEqual(signals.baseline.history, [])
        self.assertTrue(any("baseline 없음" in note for note in signals.notices))

    def test_broken_baseline_line_is_announced(self):
        self.base()
        self.baseline(baseline_line("hex.domain-pure", "a.kt"), "{깨짐")
        self.commit("freeze")

        broken = self.collect().baseline.broken
        self.assertEqual(len(broken), 1)
        self.assertTrue(broken[0].startswith("docs/domain/baseline.jsonl:2:"))


# ---------------------------------------------------------------------------
# 관측 창(--since)
# ---------------------------------------------------------------------------

class SinceTest(SignalsTestCase):
    def test_since_revision_excludes_earlier_commits(self):
        self.base()
        self.kt("claim/domain", "com.acme.claim.domain", "Claim")
        cut = self.commit("claim")
        self.kt("billing/domain", "com.acme.billing.domain", "Invoice")
        self.commit("billing")

        signals = self.collect(since=cut)
        self.assertEqual(signals.since["kind"], "rev")
        self.assertEqual([entry.key for entry in signals.contexts], ["backend:billing"])
        # rev에서는 review-log 창을 날짜로 곧장 얻지 못한다 — 근사했다는 사실을 고지한다.
        self.assertTrue(any("근사했습니다" in note for note in signals.notices))

    def test_since_date_excludes_earlier_commits(self):
        self.base()
        self.kt("claim/domain", "com.acme.claim.domain", "Claim")
        self.commit("claim", date="2026-01-01T00:00:00+00:00")
        self.kt("billing/domain", "com.acme.billing.domain", "Invoice")
        self.commit("billing", date="2026-06-01T00:00:00+00:00")

        signals = self.collect(since="2026-03-01")
        self.assertEqual(signals.since["kind"], "date")
        self.assertEqual([entry.key for entry in signals.contexts], ["backend:billing"])

    def test_review_log_window_follows_since_date(self):
        self.base()
        claim = "claim/domain/src/main/kotlin/com/acme/claim/domain/Claim.kt"
        self.write("docs/domain/review-log.jsonl",
                   review_line("old.rule", claim, date="2026-01-05") + "\n"
                   + review_line("new.rule", claim, date="2026-06-05") + "\n")
        self.commit("log", date="2026-06-01T00:00:00+00:00")

        signals = self.collect(since="2026-03-01")
        self.assertEqual([entry.rule for entry in signals.review_log.rules], ["new.rule"])
        self.assertEqual(signals.review_log.window, "2026-03-01")

    def test_window_and_reported_dates_share_the_committer_axis(self):
        """git의 --since는 커밋터 날짜로 거른다 — 표시 날짜가 작성자 날짜면 rebase·squash
        이력에서 관측 범위가 요청한 창 밖으로 나간다."""
        self.domain()
        self.commit("init", date="2026-01-01T00:00:00+00:00",
                    committed="2026-07-01T00:00:00+00:00")
        self.kt("claim/domain", "com.acme.claim.domain", "Claim")
        self.commit("claim", date="2026-01-02T00:00:00+00:00",
                    committed="2026-07-02T00:00:00+00:00")

        signals = self.collect(since="2026-04-01")
        self.assertEqual(signals.span["commits"], 2)
        self.assertGreaterEqual(signals.span["first"]["date"][:10], "2026-04-01")
        self.assertTrue(signals.span["last"]["date"].startswith("2026-07-02"))

    def test_empty_range_is_not_collectable(self):
        head = self.base()
        with self.assertRaises(CollectError) as caught:
            self.collect(since=head)
        self.assertIn("커밋", str(caught.exception))


# ---------------------------------------------------------------------------
# 산출 불가 · 사용법
# ---------------------------------------------------------------------------

class NotCollectableTest(SignalsTestCase):
    def test_outside_git_repository(self):
        """저장소 밖이어야 하므로 tests/ 아래(플러그인 저장소 안)를 쓸 수 없다."""
        outside = Path(tempfile.mkdtemp())
        try:
            (outside / "DOMAIN.md").write_text(DOMAIN, encoding="utf-8")
            with self.assertRaises(CollectError) as caught:
                collect(outside / "DOMAIN.md")
            self.assertIn("git", str(caught.exception))
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_repository_without_commits(self):
        self.domain()
        with self.assertRaises(CollectError) as caught:
            self.collect()
        self.assertIn("커밋", str(caught.exception))

    def test_git_executable_is_missing(self):
        """git은 이 수집기의 유일한 외부 의존이다 — 실행 자체가 안 되면 `OSError`를 흘리지 않고
        산출 불가로 말한다. 트레이스백이 새면 호출자가 exit 1과 exit 2를 가릴 수 없다."""
        self.base()
        empty = self.tmpdir / "nobin"          # git이 없는 PATH
        empty.mkdir()
        with mock.patch.dict(os.environ, {"PATH": str(empty)}):
            with self.assertRaises(CollectError) as caught:
                self.collect()
        self.assertIn("git", str(caught.exception))

    def test_unresolvable_domain_document(self):
        self.write("DOMAIN.md", BROKEN_DOMAIN)
        self.commit("broken")
        with self.assertRaises(CollectError):
            self.collect()


class CliTest(SignalsTestCase):
    def test_usage_error_without_arguments(self):
        code, _, err = self.run_cli()
        self.assertEqual(code, 2)
        self.assertIn("사용법", err)

    def test_usage_error_on_unknown_flag(self):
        self.base()
        code, _, err = self.run_cli("DOMAIN.md", "--nope")
        self.assertEqual(code, 2)
        self.assertIn("사용법", err)

    def test_usage_error_when_since_has_no_value(self):
        self.base()
        code, _, err = self.run_cli("DOMAIN.md", "--since")
        self.assertEqual(code, 2)
        self.assertIn("사용법", err)

    def test_exit_zero_on_collection(self):
        self.base()
        self.kt("claim/domain", "com.acme.claim.domain", "Claim")
        self.commit("claim")
        code, out, _ = self.run_cli("DOMAIN.md")
        self.assertEqual(code, 0)
        self.assertIn("backend:claim", out)

    def test_exit_one_when_not_collectable(self):
        self.domain()
        code, _, err = self.run_cli("DOMAIN.md")
        self.assertEqual(code, 1)
        self.assertRegex(err, r"DOMAIN\.md:\d+: ")

    def test_resolve_error_is_reported_with_path_and_line(self):
        self.write("DOMAIN.md", BROKEN_DOMAIN)
        self.commit("broken")
        code, _, err = self.run_cli("DOMAIN.md")
        self.assertEqual(code, 1)
        self.assertRegex(err, r"DOMAIN\.md:\d+: ")

    def test_json_top_level_keys(self):
        self.base()
        self.kt("claim/domain", "com.acme.claim.domain", "Claim")
        self.commit("claim")
        code, out, _ = self.run_cli("DOMAIN.md", "--json")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(sorted(data), sorted([
            "root", "since", "range", "contexts", "unattributed", "hotspots",
            "cochanges", "review_log", "baseline", "notices"]))

    def test_json_entry_shapes(self):
        self.base()
        self.kt("claim/domain", "com.acme.claim.domain", "Claim")
        self.commit("claim")
        data = payload(self.collect())
        self.assertEqual(sorted(data["contexts"][0]),
                         sorted(["key", "project", "context", "commits", "files", "changes"]))
        self.assertEqual(sorted(data["hotspots"][0]), sorted(["path", "commits", "key"]))
        self.assertEqual(sorted(data["range"]), sorted(["commits", "files", "first", "last"]))
        self.assertEqual(sorted(data["since"]), sorted(["given", "kind", "resolved"]))
        self.assertEqual(sorted(data["unattributed"]),
                         sorted(["commits", "files", "changes", "samples"]))

    def test_json_shapes_of_the_remaining_signals(self):
        """`cochanges`·`baseline`은 위 케이스의 트리에서 비어 있어 항목 모양이 고정되지 않는다 —
        둘 다 채워진 트리에서 따로 못박는다. 주 소비자(evolve)가 키로 읽기 때문이다."""
        self.base()
        self.write("docs/domain/baseline.jsonl",
                   json.dumps({"rule": "af.no-framework", "path": CLAIM_KT}) + "\n")
        self.kt("claim/domain", "com.acme.claim.domain", "Claim")
        self.kt("billing/domain", "com.acme.billing.domain", "Invoice")
        self.commit("baseline + 두 컨텍스트를 한 커밋에서")

        data = payload(self.collect())
        self.assertEqual(sorted(data["cochanges"][0]), sorted(["a", "b", "commits"]))
        self.assertEqual(sorted(data["baseline"]),
                         sorted(["path", "present", "lines", "rules", "history", "broken"]))
        self.assertEqual(sorted(data["baseline"]["rules"][0]), sorted(["rule", "count"]))
        self.assertEqual(sorted(data["baseline"]["history"][0]),
                         sorted(["commit", "date", "lines", "delta"]))

    def test_json_notices_carry_the_standing_notes(self):
        """한계와 '해석은 evolve의 몫' 고지가 텍스트에만 있으면 주 소비자가 못 읽는다."""
        self.base()
        self.kt("claim/domain", "com.acme.claim.domain", "Claim")
        self.commit("claim")
        notices = payload(self.collect())["notices"]
        self.assertIn(LIMITATION_NOTE, notices)
        self.assertIn(INTERPRETATION_NOTE, notices)

    def test_json_review_rule_shape(self):
        self.base()
        self.write("docs/domain/review-log.jsonl", review_line("a.one", CLAIM_KT) + "\n")
        self.commit("log")
        rule = payload(self.collect())["review_log"]["rules"][0]
        self.assertEqual(sorted(rule), sorted(
            ["rule", "count", "files", "inputs", "reviews", "contexts", "severities", "notes"]))

    def test_report_names_every_collected_signal(self):
        self.base()
        self.kt("claim/domain", "com.acme.claim.domain", "Claim")
        self.commit("claim")
        text = "\n".join(render(self.collect()))
        for marker in ("수집 ①", "수집 ②", "수집 ③", "수집 ④", "수집 ⑤"):
            self.assertIn(marker, text)
        self.assertIn("evolution-signals.md", text)


if __name__ == "__main__":
    unittest.main()
