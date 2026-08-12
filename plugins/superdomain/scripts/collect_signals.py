"""진화 신호 수집기 — 관측만 하고 판정하지 않는다.

    사용법: python3 collect_signals.py <ARCHITECTURE.md 경로> [--since <rev|날짜>] [--json]

**exit 계약: 0 = 산출, 1 = 산출 불가, 2 = 사용법 오류.**
`check_imports.py`(1 = 위반 발견)와도 `resolve_rules.py`(1 = 해석 오류)와도 뜻이 다르다. 이
스크립트는 아무것도 판정하지 않으므로 1은 언제나 "신호를 만들지 못했다"이고, 그 사유는
`경로:라인: ` 형식으로 stderr에 나간다 — git 부재·비 저장소·관측 창에 커밋 0건·
ARCHITECTURE.md 해석 실패가 전부다. 2는 인자 형태가 틀렸을 때만 쓴다.

**이 스크립트에는 임계값도 해석도 없다.** "몇 건부터 신호인가", "무엇을 의심할 것인가"의
정본은 `references/governance/evolution-signals.md`이고 그 문서를 읽어 적용하는 것은 `evolve`
스킬이다. 여기서 한 번 더 판정하면 정본이 둘이 되고, 둘은 반드시 갈라진다.

수집 항목 5종(계획 P5-D3):

| # | 항목 | 출처 |
|---|---|---|
| ① | 컨텍스트별 변경 빈도(커밋 수·파일 수) | `git log --numstat` |
| ② | 핫스팟 파일 상위 20 | 같은 로그 |
| ③ | 컨텍스트 쌍 동시 변경(한 커밋이 두 컨텍스트를 건드림) | 같은 로그 |
| ④ | review-log 반복 위반(rule id별 건수) | `docs/architecture/review-log.jsonl` |
| ⑤ | baseline 추이(줄 수 변화) | `docs/architecture/baseline.jsonl`의 git 이력 |

**파일 → 컨텍스트 귀속.** `resolve_rules.resolve_document()`의 정규화 패턴을 그대로 쓴다 —
유효 규칙의 `layer_patterns`와 파생 규칙 `context-isolation`의 `detail["from"]`을 합쳐
(프로젝트, 패키지 패턴) → 컨텍스트 표를 만들고, **두 컨텍스트 이상을 가리키는 패턴은 버린다**
(컨텍스트 비분할 레이어의 패턴은 판별력이 없다). 파일 경로에서 패키지를 얻는 관례는
`check_imports.py`와 같다: `src` 아래 첫 디렉터리가 소스셋이고(`test*`·`*Test`는 프로덕션
소스가 아니다), 그 다음이 `kotlin`·`java`면 언어 디렉터리이며, 나머지가 패키지다. 어느 규칙에도
걸리지 않은 파일은 침묵으로 사라지지 않고 **'귀속 불가' 버킷**에 담겨 리포트에 나온다.

**`--json` 계약.** 최상위 키는 열이고, 순서는 아래와 같다.

- `root` — git 루트 절대경로(문자열). 이하 모든 경로는 이 루트 기준 상대경로다.
- `since` — `{"given", "kind", "resolved"}`. `kind`는 `none`·`rev`·`date`.
- `range` — `{"commits", "files", "first", "last"}`. `files`는 창 안에서 바뀐 서로 다른 파일
  수이고(`hotspots`의 상한 20과 대조하는 값), `first`·`last`는 `{"commit", "date"}`로 오래된
  것이 `first`다. 관측 창이 비면 애초에 exit 1이므로 이 블록은 언제나 채워져 있다.
- `contexts` — 항목 ①. `[{"key", "project", "context", "commits", "files", "changes"}]`,
  커밋 수 내림차순. `key`는 `"<프로젝트>:<컨텍스트>"`이고 `hotspots`·`cochanges`가 이 키로
  같은 컨텍스트를 가리킨다. `changes`는 (커밋, 파일) 쌍의 수다.
- `unattributed` — 귀속 불가 버킷. `{"commits", "files", "changes", "samples"}`.
- `hotspots` — 항목 ②. `[{"path", "commits", "key"}]` 상위 20건. `key`가 빈 문자열이면 귀속 불가.
- `cochanges` — 항목 ③. `[{"a", "b", "commits"}]`, `a` < `b`인 컨텍스트 키 쌍.
- `review_log` — 항목 ④. `{"path", "present", "entries", "window", "rules", "broken"}`.
  `rules`는 `[{"rule", "count", "files", "reviews", "contexts", "notes"}]`, 건수 내림차순.
- `baseline` — 항목 ⑤. `{"path", "present", "lines", "rules", "history", "broken"}`.
  `history`는 `[{"commit", "date", "lines", "delta"}]`로 오래된 것부터다.
- `notices` — 고지 문자열 목록. 깨진 줄·부재 파일·근사한 창이 전부 여기에도 모인다.

**이 수집기가 보지 못하는 것.** 병합 커밋과 리네임은 세지 않는다(`--no-merges --no-renames`).
`review_log`의 `reviews`는 리뷰 id가 로그에 없어 **서로 다른 날짜 수로 근사**한 값이다.
`baseline`의 `history`는 커밋별 numstat을 누적해 되짚은 값이라 병합이 얽힌 이력에서는
근사이며, 그래서 현재 파일의 줄 수와 어긋나면 그 사실을 고지한다. 항목 ⑤의 추이는 관측 창과
무관하게 **전체 이력**이다 — 누적 재구성에는 시작점이 필요하기 때문이다.
"""

import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from itertools import combinations
from pathlib import Path

# resolve_rules.py가 해석의 정본이다. 정규화 패턴을 다시 만들지 않고 그 산출만 읽는다.
from resolve_rules import KIND_CONTEXT_ISOLATION, format_error, resolve_document

REVIEW_LOG = "docs/architecture/review-log.jsonl"
BASELINE = "docs/architecture/baseline.jsonl"

SOURCE_SUFFIXES = (".kt", ".java")
SRC_DIR = "src"
LANG_DIRS = frozenset({"kotlin", "java"})

HOTSPOT_TOP = 20        # 표시 상한이지 임계값이 아니다 — 전체 파일 수는 리포트에 함께 낸다
NOTE_SAMPLES = 5        # rule 하나당 싣는 대표 note 수(항목 ⑤ 주제 묶기의 입력)
PATH_SAMPLES = 10

LOG_FORMAT = "%x00%H%x00%aI"
RE_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

INTERPRETATION_NOTE = (
    "해석·임계값의 정본은 references/governance/evolution-signals.md이고 적용은 evolve의 "
    "몫입니다 — 이 스크립트는 관측만 합니다."
)
LIMITATION_NOTE = (
    "한계: 귀속은 정규화 패키지 패턴과 경로 관례(src/<소스셋>/<언어>/<패키지>)로만 합니다 — "
    "소스가 아닌 파일과 두 컨텍스트가 함께 쓰는 패턴에 든 파일은 '귀속 불가'로 갑니다. "
    "병합 커밋·리네임은 세지 않고, review-log의 '리뷰'는 서로 다른 날짜 수로 근사합니다."
)


class CollectError(Exception):
    """산출 불가(exit 1). `lines`가 있으면 그 줄들이 사유를 대신한다(해석 오류 목록)."""

    def __init__(self, message, lines=None):
        super().__init__(message)
        self.lines = list(lines or [])


@dataclass(frozen=True)
class Commit:
    sha: str
    date: str                                  # ISO 8601 author date
    paths: tuple


@dataclass(frozen=True)
class ContextChange:
    key: str
    project: str
    context: str
    commits: int
    files: int
    changes: int


@dataclass(frozen=True)
class Hotspot:
    path: str
    commits: int
    key: str                                   # "" = 귀속 불가


@dataclass(frozen=True)
class CoChange:
    a: str
    b: str
    commits: int


@dataclass(frozen=True)
class Unattributed:
    commits: int = 0
    files: int = 0
    changes: int = 0
    samples: list = field(default_factory=list)


@dataclass(frozen=True)
class RuleCount:
    rule: str
    count: int
    files: int
    reviews: int                               # 서로 다른 날짜 수 — 리뷰 건수의 근사
    contexts: int
    notes: list


@dataclass
class ReviewLog:
    path: str = REVIEW_LOG
    present: bool = False
    entries: int = 0
    window: str = ""                           # 적용한 날짜 컷오프("" = 전체)
    rules: list = field(default_factory=list)
    broken: list = field(default_factory=list)


@dataclass(frozen=True)
class BaselinePoint:
    commit: str
    date: str
    lines: int
    delta: int


@dataclass
class Baseline:
    path: str = BASELINE
    present: bool = False
    lines: int = 0
    rules: list = field(default_factory=list)
    history: list = field(default_factory=list)
    broken: list = field(default_factory=list)


@dataclass
class Signals:
    root: str
    since: dict
    span: dict                                 # --json에서는 `range`
    contexts: list
    unattributed: Unattributed
    hotspots: list
    cochanges: list
    review_log: ReviewLog
    baseline: Baseline
    notices: list


# ---------------------------------------------------------------------------
# git — 유일한 외부 의존. 없으면 산출 불가이고 조용히 넘어가지 않는다.
# ---------------------------------------------------------------------------

def _git(cwd, *args) -> tuple:
    """(성공 여부, stdout, stderr). `core.quotePath=false`로 비 ASCII 경로가 깨지지 않게 한다."""
    try:
        result = subprocess.run(
            ["git", "-c", "core.quotePath=false", "-C", str(cwd), *args],
            capture_output=True, text=True)
    except OSError:
        raise CollectError("git을 실행하지 못했습니다 — 이 수집기는 git 이력을 읽습니다.")
    return result.returncode == 0, result.stdout, result.stderr


def _git_root(arch_dir) -> Path:
    ok, out, _ = _git(arch_dir, "rev-parse", "--show-toplevel")
    if not ok or not out.strip():
        raise CollectError(f"'{arch_dir}'가 git 저장소 안에 있지 않습니다 — 이력이 없으면 "
                           f"변경 신호를 수집할 수 없습니다.")
    return Path(out.strip())


def _since_spec(root, since) -> tuple:
    """(`since` 산출 dict, git log에 붙일 인자 목록). rev로 읽히면 rev, 아니면 날짜로 본다."""
    if since is None:
        return {"given": None, "kind": "none", "resolved": None}, []
    ok, out, _ = _git(root, "rev-parse", "--verify", "--quiet", f"{since}^{{commit}}")
    if ok and out.strip():
        return {"given": since, "kind": "rev", "resolved": out.strip()}, [f"{since}..HEAD"]
    return {"given": since, "kind": "date", "resolved": since}, [f"--since={since}"]


def _parse_log(text) -> list:
    """`--numstat --format=%x00%H%x00%aI` 출력을 커밋 목록으로. git 출력 순서(최신 우선)를 유지한다."""
    commits, sha, date, paths = [], None, "", []
    for line in text.split("\n"):
        if line.startswith("\x00"):
            if sha:
                commits.append(Commit(sha, date, tuple(paths)))
            parts = line.split("\x00")
            sha, date, paths = parts[1], parts[2] if len(parts) > 2 else "", []
            continue
        if sha is None or not line.strip():
            continue
        columns = line.split("\t")
        if len(columns) >= 3 and columns[2]:
            paths.append(columns[2])
    if sha:
        commits.append(Commit(sha, date, tuple(paths)))
    return commits


def _log(root, extra) -> list:
    ok, out, err = _git(root, "log", "--no-merges", "--no-renames", "--numstat",
                        f"--format={LOG_FORMAT}", *extra)
    if not ok:
        detail = next((line for line in err.splitlines() if line.strip()), "")
        raise CollectError("git 이력을 읽지 못했습니다 — 커밋이 하나도 없거나 지정한 범위가 "
                           "잘못되었습니다." + (f" (git: {detail.strip()})" if detail else ""))
    return _parse_log(out)


# ---------------------------------------------------------------------------
# 파일 → 컨텍스트 귀속
# ---------------------------------------------------------------------------

def _matches_package(package, pattern) -> bool:
    """`..`로 끝나면 그 패키지와 모든 하위, 아니면 정확히 그 패키지(어휘 §2)."""
    if pattern.endswith(".."):
        base = pattern[:-2]
        return package == base or package.startswith(base + ".")
    return package == pattern


def _is_test_dir(name) -> bool:
    return name.startswith("test") or name.endswith("Test")


def _package_of(relpath):
    """프로젝트 기준 상대경로에서 패키지를 얻는다. 프로덕션 소스가 아니면 None."""
    parts = relpath.split("/")
    if not parts[-1].endswith(SOURCE_SUFFIXES):
        return None
    dirs = parts[:-1]
    if SRC_DIR not in dirs:
        return None
    rest = dirs[len(dirs) - dirs[::-1].index(SRC_DIR):]     # 마지막 `src` 다음부터
    if not rest or _is_test_dir(rest[0]):
        return None                                          # src/test, src/androidTest …
    rest = rest[1:]
    if rest and rest[0] in LANG_DIRS:
        rest = rest[1:]
    return ".".join(rest)


class _Attributor:
    """정규화 패턴으로 git 경로를 `<프로젝트>:<컨텍스트>` 키에 귀속시킨다."""

    def __init__(self, resolution, arch_dir, root):
        self._prefixes = []          # [(저장소 기준 접두, 프로젝트명)] — 긴 접두 우선
        for project in resolution.projects:
            target = Path(os.path.normpath(Path(arch_dir) / project["path"]))
            try:
                relative = os.path.relpath(target, root)
            except ValueError:
                continue
            if relative.startswith(".."):
                continue             # 프로젝트가 저장소 밖이다 — 이 로그로는 볼 수 없다
            self._prefixes.append(("" if relative == "." else Path(relative).as_posix(),
                                   project["name"]))
        self._prefixes.sort(key=lambda item: -len(item[0]))

        owners = {}
        for rule in resolution.effective:
            for patterns in rule.layer_patterns.values():
                for pattern in patterns:
                    owners.setdefault((rule.project, pattern), set()).add(rule.context)
        for rule in resolution.derived:
            if rule.kind == KIND_CONTEXT_ISOLATION:
                for pattern in rule.detail.get("from", []):
                    owners.setdefault((rule.project, pattern), set()).add(rule.subject)
        # 두 컨텍스트 이상이 쓰는 패턴은 판별하지 못한다 — 그 파일은 귀속 불가로 간다.
        self._owners = {key: sorted(value)[0] for key, value in owners.items() if len(value) == 1}
        self._cache = {}

    def attribute(self, relpath) -> str:
        if relpath not in self._cache:
            self._cache[relpath] = self._attribute(relpath)
        return self._cache[relpath]

    def _attribute(self, relpath) -> str:
        for prefix, project in self._prefixes:
            if prefix and not relpath.startswith(prefix + "/"):
                continue
            package = _package_of(relpath[len(prefix) + 1:] if prefix else relpath)
            if not package:
                return ""
            best, winners = -1, set()
            for (owner_project, pattern), context in self._owners.items():
                if owner_project != project or not _matches_package(package, pattern):
                    continue
                length = len(pattern[:-2] if pattern.endswith("..") else pattern)
                if length > best:
                    best, winners = length, {context}
                elif length == best:
                    winners.add(context)
            return f"{project}:{winners.pop()}" if len(winners) == 1 else ""
        return ""


# ---------------------------------------------------------------------------
# 항목 ①②③ — git 로그 한 번을 세 갈래로 집계한다
# ---------------------------------------------------------------------------

def _change_signals(commits, attributor) -> tuple:
    buckets, per_file, pairs = {}, {}, {}
    for commit in commits:
        touched = set()
        for path in commit.paths:
            key = attributor.attribute(path)
            bucket = buckets.setdefault(key, {"commits": set(), "files": set(), "changes": 0})
            bucket["commits"].add(commit.sha)
            bucket["files"].add(path)
            bucket["changes"] += 1
            per_file.setdefault(path, set()).add(commit.sha)
            if key:
                touched.add(key)
        for pair in combinations(sorted(touched), 2):
            pairs.setdefault(pair, set()).add(commit.sha)

    contexts = []
    for key, bucket in buckets.items():
        if not key:
            continue
        project, _, context = key.partition(":")
        contexts.append(ContextChange(key, project, context, len(bucket["commits"]),
                                      len(bucket["files"]), bucket["changes"]))
    contexts.sort(key=lambda entry: (-entry.commits, -entry.changes, entry.key))

    orphan = buckets.get("")
    unattributed = Unattributed(
        len(orphan["commits"]), len(orphan["files"]), orphan["changes"],
        sorted(orphan["files"])[:PATH_SAMPLES]) if orphan else Unattributed()

    hotspots = [Hotspot(path, len(shas), attributor.attribute(path))
                for path, shas in sorted(per_file.items(),
                                         key=lambda item: (-len(item[1]), item[0]))][:HOTSPOT_TOP]
    cochanges = [CoChange(pair[0], pair[1], len(shas)) for pair, shas in
                 sorted(pairs.items(), key=lambda item: (-len(item[1]), item[0]))]
    return contexts, unattributed, hotspots, cochanges, len(per_file)


# ---------------------------------------------------------------------------
# 항목 ④ — review-log.jsonl
# ---------------------------------------------------------------------------

def _read_lines(root, relpath, broken) -> list:
    """파일의 줄 목록. 읽지 못하면 그 사실을 `broken`에 담고 빈 목록을 준다 — 침묵하지 않는다."""
    try:
        return (root / relpath).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as error:
        broken.append(f"{relpath}:0: 파일을 읽지 못했습니다({error.strerror or error}) — "
                      f"집계에서 제외합니다.")
        return []


def _jsonl(relpath, lines, broken) -> list:
    """(줄 번호, 객체) 목록. 읽지 못한 줄은 `broken`에 `경로:라인: `로 담고 건너뛴다."""
    entries = []
    for number, raw in enumerate(lines, 1):
        if not raw.strip():
            continue
        try:
            entry = json.loads(raw)
        except ValueError:
            broken.append(f"{relpath}:{number}: JSON으로 읽을 수 없는 줄입니다 — "
                          f"집계에서 건너뜁니다.")
            continue
        if not isinstance(entry, dict) or not entry.get("rule"):
            broken.append(f"{relpath}:{number}: 'rule' 키가 없습니다 — 집계에서 건너뜁니다.")
            continue
        entries.append((number, entry))
    return entries


def _review_log(root, attributor, window) -> ReviewLog:
    log = ReviewLog(window=window)
    if not (root / REVIEW_LOG).is_file():
        return log
    log.present = True
    entries = _jsonl(REVIEW_LOG, _read_lines(root, REVIEW_LOG, log.broken), log.broken)

    grouped = {}
    for number, entry in entries:
        date = str(entry.get("date", ""))
        if window:
            if not date:
                log.broken.append(f"{REVIEW_LOG}:{number}: 'date'가 없어 관측 창을 적용할 수 "
                                  f"없습니다 — 집계에서 건너뜁니다.")
                continue
            if date < window:
                continue
        log.entries += 1
        group = grouped.setdefault(str(entry["rule"]),
                                   {"count": 0, "files": set(), "dates": set(),
                                    "contexts": set(), "notes": []})
        group["count"] += 1
        path = str(entry.get("path", ""))
        group["files"].add(path)
        group["dates"].add(date)
        key = attributor.attribute(path) if path else ""
        if key:
            group["contexts"].add(key)
        note = str(entry.get("note", "")).strip()
        if note and note not in group["notes"] and len(group["notes"]) < NOTE_SAMPLES:
            group["notes"].append(note)

    log.rules = sorted(
        (RuleCount(rule, group["count"], len(group["files"]), len(group["dates"]),
                   len(group["contexts"]), group["notes"]) for rule, group in grouped.items()),
        key=lambda entry: (-entry.count, entry.rule))
    return log


# ---------------------------------------------------------------------------
# 항목 ⑤ — baseline.jsonl 추이
# ---------------------------------------------------------------------------

def _baseline(root) -> Baseline:
    """줄 수 추이는 관측 창과 무관하게 전체 이력이다 — 누적 재구성에 시작점이 필요하다."""
    baseline = Baseline()
    ok, out, _ = _git(root, "log", "--no-merges", "--no-renames", "--numstat",
                      f"--format={LOG_FORMAT}", "--", BASELINE)
    running = 0
    if ok:
        for sha, date, delta in reversed(_parse_log_numbers(out)):
            running += delta
            baseline.history.append(BaselinePoint(sha, date, running, delta))

    path = root / BASELINE
    if not path.is_file():
        return baseline
    baseline.present = True
    lines = _read_lines(root, BASELINE, baseline.broken)
    entries = _jsonl(BASELINE, lines, baseline.broken)
    baseline.lines = sum(1 for line in lines if line.strip())
    counts = {}
    for _, entry in entries:
        rule = str(entry["rule"])
        counts[rule] = counts.get(rule, 0) + 1
    baseline.rules = [{"rule": rule, "count": count} for rule, count in
                      sorted(counts.items(), key=lambda item: (-item[1], item[0]))]
    return baseline


def _parse_log_numbers(text) -> list:
    """(sha, date, 증감)의 목록. numstat의 added-deleted를 한 커밋당 하나로 합친다."""
    rows, sha, date, delta = [], None, "", 0
    for line in text.split("\n"):
        if line.startswith("\x00"):
            if sha:
                rows.append((sha, date, delta))
            parts = line.split("\x00")
            sha, date, delta = parts[1], parts[2] if len(parts) > 2 else "", 0
            continue
        columns = line.split("\t")
        if sha and len(columns) >= 3 and columns[0].isdigit() and columns[1].isdigit():
            delta += int(columns[0]) - int(columns[1])
    if sha:
        rows.append((sha, date, delta))
    return rows


# ---------------------------------------------------------------------------
# 수집
# ---------------------------------------------------------------------------

def _window(since, commits, notices) -> str:
    """review-log에 적용할 날짜 컷오프. rev·상대 날짜는 범위의 가장 오래된 커밋으로 근사한다."""
    if since["kind"] == "none":
        return ""
    given = str(since["given"])
    if since["kind"] == "date" and RE_ISO_DATE.match(given):
        return given
    approximated = (commits[-1].date or "")[:10]
    notices.append(f"review-log 관측 창을 '{given}'에서 날짜로 곧장 얻지 못해 범위의 가장 "
                   f"오래된 커밋 날짜({approximated or '알 수 없음'})로 근사했습니다.")
    return approximated


def collect(arch_path, since=None) -> Signals:
    """ARCHITECTURE.md 한 건을 기준으로 수집 항목 5종을 만든다. 실패는 CollectError다."""
    arch_path = Path(arch_path)
    path_text = str(arch_path)
    resolution = resolve_document(arch_path)
    if resolution.errors:
        raise CollectError(
            "ARCHITECTURE.md를 해석하지 못해 파일을 컨텍스트에 귀속시킬 수 없습니다.",
            [format_error(error, path_text) for error in
             sorted(resolution.errors, key=lambda e: (getattr(e, "path", "") or path_text, e.line))])

    arch_dir = arch_path.resolve().parent
    root = _git_root(arch_dir)
    since_info, extra = _since_spec(root, since)
    commits = _log(root, extra)                 # git 로그 순서: 최신 우선
    if not commits:
        raise CollectError(f"관측 창에 커밋이 없습니다 — 범위: "
                           f"{' '.join(extra) if extra else '전체 이력'}.")

    attributor = _Attributor(resolution, arch_dir, root)
    contexts, unattributed, hotspots, cochanges, files = _change_signals(commits, attributor)

    notices = []
    window = _window(since_info, commits, notices)
    review_log = _review_log(root, attributor, window)
    baseline = _baseline(root)

    if not review_log.present:
        notices.append(f"{REVIEW_LOG}이 없습니다 — 항목 ④를 산출하지 못했습니다(review 스킬이 "
                       f"아직 기록하지 않았거나 경로가 다릅니다).")
    if not baseline.present:
        notices.append(f"baseline 없음 — {BASELINE}이 없습니다. 이행 선언이 없거나 아직 "
                       f"동결하지 않았습니다(항목 ⑤ 미산출).")
    elif baseline.history and baseline.history[-1].lines != baseline.lines:
        notices.append(f"{BASELINE}: 이력 누적 {baseline.history[-1].lines}줄과 현재 파일 "
                       f"{baseline.lines}줄이 다릅니다 — 추이는 근사입니다.")
    elif not baseline.history:
        notices.append(f"{BASELINE}: git 이력이 없습니다 — 아직 커밋되지 않았다면 추이는 "
                       f"다음 커밋부터 관측됩니다.")
    notices.extend(review_log.broken)
    notices.extend(baseline.broken)

    span = {"commits": len(commits), "files": files,
            "first": {"commit": commits[-1].sha, "date": commits[-1].date},
            "last": {"commit": commits[0].sha, "date": commits[0].date}}
    return Signals(str(root), since_info, span, contexts, unattributed, hotspots,
                   cochanges, review_log, baseline, notices)


# ---------------------------------------------------------------------------
# 출력
# ---------------------------------------------------------------------------

def payload(signals) -> dict:
    return {
        "root": signals.root,
        "since": signals.since,
        "range": signals.span,
        "contexts": [asdict(entry) for entry in signals.contexts],
        "unattributed": asdict(signals.unattributed),
        "hotspots": [asdict(entry) for entry in signals.hotspots],
        "cochanges": [asdict(entry) for entry in signals.cochanges],
        "review_log": asdict(signals.review_log),
        "baseline": asdict(signals.baseline),
        "notices": list(signals.notices),
    }


def render(signals) -> list:
    span, since = signals.span, signals.since
    scope = {"none": "전체 이력", "rev": f"rev {since['given']} 이후",
             "date": f"{since['given']} 이후"}[since["kind"]]
    lines = [f"루트: {signals.root}",
             f"관측 범위: 커밋 {span['commits']}건 ({scope}) — "
             f"{span['first']['date']} ~ {span['last']['date']}",
             "",
             "[수집 ①] 컨텍스트별 변경 빈도"]
    lines += [f"- {entry.key} — 커밋 {entry.commits}, 파일 {entry.files}, 변경 {entry.changes}"
              for entry in signals.contexts] or ["- 귀속된 컨텍스트가 없습니다."]
    orphan = signals.unattributed
    lines.append(f"- 귀속 불가 — 커밋 {orphan.commits}, 파일 {orphan.files}, "
                 f"변경 {orphan.changes}" + (f" (예: {', '.join(orphan.samples)})"
                                             if orphan.samples else ""))

    lines += ["", f"[수집 ②] 핫스팟 파일 상위 {HOTSPOT_TOP} (바뀐 파일 {span['files']}건 중)"]
    lines += [f"- {entry.path} — 커밋 {entry.commits} ({entry.key or '귀속 불가'})"
              for entry in signals.hotspots] or ["- 변경된 파일이 없습니다."]

    lines += ["", "[수집 ③] 컨텍스트 쌍 동시 변경"]
    lines += [f"- {entry.a} ↔ {entry.b} — 커밋 {entry.commits}"
              for entry in signals.cochanges] or [
                  "- 한 커밋이 두 컨텍스트를 함께 건드린 적이 없습니다."]

    log = signals.review_log
    lines += ["", f"[수집 ④] review-log 반복 위반"
                  f"{f' (창: {log.window} 이후)' if log.window else ''}"]
    if not log.present:
        lines.append(f"- {REVIEW_LOG}이 없습니다.")
    elif not log.rules:
        lines.append("- 창 안에 기록이 없습니다.")
    else:
        for entry in log.rules:
            lines.append(f"- {entry.rule} — {entry.count}건 (파일 {entry.files}, "
                         f"리뷰 {entry.reviews}, 컨텍스트 {entry.contexts})")
            lines += [f"    note: {note}" for note in entry.notes]

    baseline = signals.baseline
    lines += ["", "[수집 ⑤] baseline 추이 (관측 창과 무관한 전체 이력 — 누적에 시작점이 필요합니다)"]
    if not baseline.present:
        lines.append(f"- baseline 없음 — {BASELINE}이 없습니다.")
    else:
        distribution = ", ".join(f"{item['rule']} {item['count']}" for item in baseline.rules)
        lines.append(f"- 현재 {baseline.lines}줄" + (f" — {distribution}" if distribution else ""))
    lines += [f"- {point.date[:10]} {point.commit[:8]} {point.lines}줄 "
              f"({point.delta:+d})" for point in baseline.history]

    if signals.notices:
        lines += ["", "고지:"] + [f"- {notice}" for notice in signals.notices]
    lines += ["", LIMITATION_NOTE, INTERPRETATION_NOTE]
    return lines


def main(argv) -> int:
    as_json = "--json" in argv
    args = [arg for arg in argv if arg != "--json"]
    since = None
    if "--since" in args:
        index = args.index("--since")
        if index + 1 >= len(args) or args[index + 1].startswith("--"):
            return _usage()
        since = args[index + 1]
        args = args[:index] + args[index + 2:]
    if len(args) != 1 or any(arg.startswith("--") for arg in args):
        return _usage()

    try:
        signals = collect(args[0], since=since)
    except CollectError as error:
        for line in error.lines or [f"{args[0]}:0: 산출 불가 — {error}"]:
            print(line, file=sys.stderr)
        return 1

    if as_json:
        print(json.dumps(payload(signals), ensure_ascii=False, indent=2))
    else:
        for line in render(signals):
            print(line)
    return 0


def _usage() -> int:
    print("사용법: python3 collect_signals.py <ARCHITECTURE.md 경로> [--since <rev|날짜>] "
          "[--json]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
