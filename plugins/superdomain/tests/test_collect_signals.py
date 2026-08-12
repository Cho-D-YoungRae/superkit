import json, os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from collect_signals import CollectError, collect, payload, render

ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = Path(__file__).resolve().parent
SCRIPT = ROOT / "scripts" / "collect_signals.py"

# 규칙 하나만 선언한 커스텀 스타일. 이 스크립트가 쓰는 것은 규칙의 판정이 아니라 그 규칙이
# 실어 오는 layer_patterns뿐이므로, 프리셋이 바뀌어도 흔들리지 않게 최소 선언만 둔다.
STYLE_FULL = """# full

## 선언

- 레이어: domain, application, adapter

| 규칙 id | primitive | 파라미터 |
|---|---|---|
| af.no-framework | forbid-import | from=domain; to=org.springframework.. |
"""

HEAD = """# 샘플 — Architecture
<!-- superarchitect:template v1 -->

## 프로젝트: backend
- 경로: .
- 프로파일: kotlin-spring
- 기본 패키지: com.acme
- 아키텍처 테스트 위치: architecture-test/src/test/kotlin
"""

CONTEXT = """
## 컨텍스트: {name}
- 분류: {classification}
- 스타일: custom/full
- 모듈 구성: multi-module

| 모듈 | 경로 | 레이어 |
|---|---|---|
| {name}-domain | {name}/domain | domain |
| {name}-application | {name}/application | application |
| {name}-adapter | {name}/adapter | adapter |
"""

# 컨텍스트 둘 — 기본 패키지 관례로 `com.acme.<컨텍스트>.<레이어>..` 패턴이 나온다.
ARCH = (HEAD
        + CONTEXT.format(name="claim", classification="core")
        + CONTEXT.format(name="billing", classification="supporting"))

# app-embedded — `패키지 규약`의 `{앱}` 행이 컨텍스트로 분할되지 않는 레이어를 만든다.
# 그 패턴은 두 컨텍스트의 layer_patterns에 함께 들어가므로 귀속을 판별하지 못한다.
APP_ARCH = """# 앱 임베디드 — Architecture
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

## 컨텍스트: billing
- 분류: supporting
- 스타일: custom/full
- 모듈 구성: app-embedded
"""

BROKEN_ARCH = """# 깨진 문서
<!-- superarchitect:template v1 -->

## 프로젝트: backend
- 경로: .
"""


class SignalsTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(dir=TESTS_DIR, prefix="tmp"))
        self.repo = self.tmpdir / "repo"
        self.repo.mkdir()
        self.arch_path = self.repo / "ARCHITECTURE.md"
        subprocess.run(["git", "-c", "init.defaultBranch=main", "init", "-q", str(self.repo)],
                       check=True, capture_output=True)
        for key, value in (("user.email", "t@example.com"), ("user.name", "T"),
                           ("commit.gpgsign", "false")):
            self.git("config", key, value)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ---- 저장소 도우미 ----------------------------------------------------

    def git(self, *args, env=None):
        return subprocess.run(["git", "-C", str(self.repo), *args],
                              check=True, capture_output=True, text=True, env=env).stdout

    def write(self, relpath, text):
        path = self.repo / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def arch(self, text=ARCH):
        self.write("ARCHITECTURE.md", text)
        self.write("docs/architecture/styles/full.md", STYLE_FULL)

    def kt(self, module, package, name, marker="1"):
        relpath = f"{module}/src/main/kotlin/{package.replace('.', '/')}/{name}.kt"
        return self.write(relpath, f"package {package}\n\nclass {name} // rev {marker}\n")

    def commit(self, message, date=None):
        env = None
        if date:
            env = dict(os.environ, GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message, env=env)
        return self.git("rev-parse", "HEAD").strip()

    def base(self):
        """ARCHITECTURE.md와 스타일 문서만 담긴 첫 커밋. 반환값은 그 커밋 해시다."""
        self.arch()
        return self.commit("init")

    # ---- 실행 도우미 ------------------------------------------------------

    def collect(self, since=None):
        return collect(self.arch_path, since=since)

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

    def test_context_unsplit_pattern_cannot_attribute(self):
        """두 컨텍스트가 함께 쓰는 패턴은 판별력이 없다 — 아무 쪽에도 넣지 않는다."""
        self.write("ARCHITECTURE.md", APP_ARCH)
        self.write("docs/architecture/styles/full.md", STYLE_FULL)
        self.commit("init")
        self.kt("app/web", "com.acme.web", "Controller")
        self.kt("core", "com.acme.core.domain.claim", "Claim")
        self.commit("app + domain")

        signals = self.collect()
        self.assertEqual([entry.key for entry in signals.contexts], ["backend:claim"])
        self.assertIn("app/web/src/main/kotlin/com/acme/web/Controller.kt",
                      signals.unattributed.samples)

    def test_unattributed_is_announced_in_report(self):
        self.base()
        self.write("README.md", "hello\n")
        self.commit("readme")

        self.assertTrue(any("귀속 불가" in line for line in render(self.collect())))


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


class ReviewLogTest(SignalsTestCase):
    def log(self, *lines):
        self.write("docs/architecture/review-log.jsonl", "".join(f"{line}\n" for line in lines))

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
            "docs/architecture/review-log.jsonl:2:"))
        self.assertEqual(signals.review_log.rules[0].count, 2)
        self.assertIn(signals.review_log.broken[0], signals.notices)

    def test_entry_without_rule_key_is_announced(self):
        self.base()
        self.log(json.dumps({"date": "2026-08-01", "path": "x"}))
        self.commit("log")

        broken = self.collect().review_log.broken
        self.assertEqual(len(broken), 1)
        self.assertIn("rule", broken[0])

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
        self.write("docs/architecture/baseline.jsonl", "".join(f"{line}\n" for line in lines))

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
        self.assertTrue(broken[0].startswith("docs/architecture/baseline.jsonl:2:"))


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
        self.write("docs/architecture/review-log.jsonl",
                   review_line("old.rule", claim, date="2026-01-05") + "\n"
                   + review_line("new.rule", claim, date="2026-06-05") + "\n")
        self.commit("log", date="2026-06-01T00:00:00+00:00")

        signals = self.collect(since="2026-03-01")
        self.assertEqual([entry.rule for entry in signals.review_log.rules], ["new.rule"])
        self.assertEqual(signals.review_log.window, "2026-03-01")

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
            (outside / "ARCHITECTURE.md").write_text(ARCH, encoding="utf-8")
            style = outside / "docs" / "architecture" / "styles" / "full.md"
            style.parent.mkdir(parents=True, exist_ok=True)
            style.write_text(STYLE_FULL, encoding="utf-8")
            with self.assertRaises(CollectError) as caught:
                collect(outside / "ARCHITECTURE.md")
            self.assertIn("git", str(caught.exception))
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_repository_without_commits(self):
        self.arch()
        with self.assertRaises(CollectError) as caught:
            self.collect()
        self.assertIn("커밋", str(caught.exception))

    def test_unresolvable_architecture_document(self):
        self.write("ARCHITECTURE.md", BROKEN_ARCH)
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
        code, _, err = self.run_cli("ARCHITECTURE.md", "--nope")
        self.assertEqual(code, 2)
        self.assertIn("사용법", err)

    def test_usage_error_when_since_has_no_value(self):
        self.base()
        code, _, err = self.run_cli("ARCHITECTURE.md", "--since")
        self.assertEqual(code, 2)
        self.assertIn("사용법", err)

    def test_exit_zero_on_collection(self):
        self.base()
        self.kt("claim/domain", "com.acme.claim.domain", "Claim")
        self.commit("claim")
        code, out, _ = self.run_cli("ARCHITECTURE.md")
        self.assertEqual(code, 0)
        self.assertIn("backend:claim", out)

    def test_exit_one_when_not_collectable(self):
        self.arch()
        code, _, err = self.run_cli("ARCHITECTURE.md")
        self.assertEqual(code, 1)
        self.assertRegex(err, r"ARCHITECTURE\.md:\d+: ")

    def test_resolve_error_is_reported_with_path_and_line(self):
        self.write("ARCHITECTURE.md", BROKEN_ARCH)
        self.commit("broken")
        code, _, err = self.run_cli("ARCHITECTURE.md")
        self.assertEqual(code, 1)
        self.assertRegex(err, r"ARCHITECTURE\.md:\d+: ")

    def test_json_top_level_keys(self):
        self.base()
        self.kt("claim/domain", "com.acme.claim.domain", "Claim")
        self.commit("claim")
        code, out, _ = self.run_cli("ARCHITECTURE.md", "--json")
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
