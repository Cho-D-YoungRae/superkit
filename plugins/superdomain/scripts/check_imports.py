"""컨텍스트 격리 검사기 — DOMAIN.md가 선언한 도메인 경계의 유일한 코드 검증.

**exit 계약: 0 = 위반 없음, 1 = 위반 발견, 2 = 해석 불가(검사를 세우지 못함) 또는 사용법 오류.**
`parse_domain.py`와 의미가 다르다 — 저쪽의 1은 "해석 오류"다. 여기서 1은 정상 판정 결과이고,
검사 자체가 성립하지 않은 경우만 2로 나간다. CI에서 두 코드를 같게 다루면 안 된다.

`parse_domain.parse_domain()`이 만든 `Domain`에서 두 가지만 받는다 — 컨텍스트가 실현되는
패키지 접두 패턴(`context_packages`)과 `### 관계` 표가 연 쌍(`isolation_allowlist`). 그다음
대상 프로젝트의 `.kt`/`.java` 소스를 걸으며 `package` 선언과 `import` 목록만 정규식으로 읽고,
**컨텍스트 경계를 넘는 참조가 관계 표에 열려 있는지** 하나만 판정한다.

**귀속은 패키지가 정한다(디렉터리가 아니다).** 소스의 `package` 선언과 import 대상의 완전 수식
이름을 각각 컨텍스트 패키지 패턴에 접두 최장 일치시켜 소유 컨텍스트를 정하고, 두 컨텍스트가
다르면서 그 쌍이 관계 표에 없으면 위반이다. 어느 컨텍스트에도 들지 않는 대상(`java.util`,
조립·설정 코드 등)은 도메인 경계 밖이므로 무시한다.

**허용 단위는 쌍이고 방향을 구분하지 않는다.** 한 줄을 쓰면 그 쌍의 참조가 양방향으로 열리고,
유형(`customer-supplier`·`acl` 등)은 허용 방향을 바꾸지 않는다 — 유형은 설계 의도의 기록이지
강제의 입력이 아니다(정본: `references/knowledge/strategic/context-mapping.md` R1).

**이 검사기가 보는 것이 경계의 전부가 아니다.** import 문 없이 쓰이는 참조 — 같은 패키지 안의
타입, 완전 수식 이름(FQN)을 본문에 그대로 쓴 참조 — 를 보지 못한다. 위반 0건은 경계 누수
0건이 아니고, 이 사각을 대신 덮어 줄 다른 강제 장치도 없다. 그래서 리포트는 그 한계를 푸터에
함께 출력한다(`LIMITATION_NOTE`는 언제나, `BASELINE_MATCH_NOTE`는 그 파일이 이번 실행에
실제로 관여했을 때만 — 푸터의 한 줄은 읽는 사람에게 '언제나 참'이어야 한다).

**소스는 원문 그대로 읽는다 — 주석·문자열 리터럴을 지우지 않는다.** 두 방향의 대가가 정반대라
한 방향만 보고 정할 수 없다. `import` 쪽에서 이 선택은 **오탐**을 만든다(블록 주석이나 raw
string 안의 `import`도 위반이 된다) — 시끄러운 실패이고, 사용자는 지목된 줄을 열면 바로 안다.
`package` 쪽에서는 반대로 **미탐**을 만든다: 선언은 첫 매칭이 귀속을 정하므로 주석 처리된 옛
선언이 앞에 있으면 파일이 통째로 엉뚱한 컨텍스트에 귀속되고, 그 파일의 위반은 어느 채널에도
나타나지 않는다 ✅ 실측. 마스킹 함수를 되살리면 그 함수의 결함 하나가 import를 통째로 삼켜
같은 침묵을 만들므로, 대신 **선언을 세어 2건 이상이면 그 사실 자체를 고지한다**
(`AmbiguousPackage`) — 조용한 오귀속을 시끄러운 고지로 바꾸는 값싼 수선이다.

**브라운필드의 기존 부채는 별도 채널로 나간다.** `docs/domain/baseline.jsonl`이 있으면
플래그 없이 읽어 매칭 위반을 `[기존 부채]`로 강등한다 — 리포트에는 남지만 exit 코드에는
반영되지 않고 신규 위반만 1을 만든다. 매칭 키는 (규칙 id, 경로)뿐이고 그 대가는 푸터가 밝힌다.
깨진 줄 하나면 어느 위반이 동결분인지 전체를 알 수 없으므로 **해석 불가(exit 2)로 다룬다** —
래칫을 부분적으로 믿느니 검사를 세우지 않는다.

같은 이유로 **아무것도 검사하지 않은 컨텍스트를 침묵으로 넘기지 않는다.** 이제 남은 코드 검증이
이 하나뿐이라 "위반 0건"과 "검사할 소스가 0건"이 뭉뚱그려지면 플러그인이 통째로 조용해진다.
네 층위로 나누어 전부 고지한다.

| 층위 | 무엇이 없는가 | 출력 |
|---|---|---|
| 0건 경고 | 컨텍스트 패키지에 귀속된 소스가 0건이다 | `[0건 경고] <rule id>: ...` |
| 생략 | 검사가 성립하지 않았다(프로젝트 경로·소스·컨텍스트 부재) | 푸터의 `생략:` 줄 |
| 귀속 불신 | `package` 선언이 여럿이라 어느 컨텍스트의 파일인지 믿을 수 없다 | 푸터의 `package 선언이 여러 건인 소스` 줄 |
| 읽지 못함 | 소스를 파싱하지 못했다(인코딩·권한) | 푸터의 `읽지 못한 소스` 줄 |
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

# parse_domain.py가 해석의 정본이다. 이 스크립트는 그 산출(Domain)만 소비하며 DOMAIN.md를
# 다시 해석하지 않는다 — 해석이 두 곳에 있으면 두 결과가 갈라진다.
from parse_domain import (LocatedError, context_packages, format_error, isolation_allowlist,
                          parse_domain)

SOURCE_SUFFIXES = (".kt", ".java")

# 빌드 산출물·도구 디렉터리. 여기 있는 소스는 선언의 대상이 아니다(생성물이거나 사본이다).
SKIP_DIRS = frozenset({
    "build", "out", "target", ".git", ".gradle", ".idea", ".kotlin", ".settings",
    ".venv", "node_modules",
})
SRC_DIR = "src"                  # `src/test`, `src/androidTest` … 는 프로덕션 소스가 아니다

# 위반·baseline 항목의 규칙 id. 문자열 리터럴을 여기 한 번만 둔다 — baseline.jsonl의 `rule`
# 칸이 이 값과 글자 그대로 대조되므로, 바꾸면 기존 동결분이 통째로 매칭에서 빠진다.
RULE_ID = "derived.context-isolation"

LIMITATION_NOTE = (
    "한계: 같은 패키지 안의 참조와 import 없이 쓰는 완전 수식 이름(FQN)은 이 검사가 보지 "
    "못합니다 — 위반 0건이 경계 누수 0건을 뜻하지는 않습니다."
)
ZERO_MATCH_REASON = "귀속된 소스 0건 — 컨텍스트 패키지와 실제 패키지의 불일치 가능성"

# 동결된 기존 부채. 경로는 DOMAIN.md가 있는 디렉터리(= git 루트) 기준이라 위반의 표시 경로와
# 같은 기준이고, 그래서 (규칙 id, 경로)로 바로 맞춰 볼 수 있다.
BASELINE_RELATIVE = "docs/domain/baseline.jsonl"
BASELINE_MATCH_NOTE = (
    "한계: 부채 매칭 키는 (규칙 id, 경로)뿐입니다 — 줄 번호를 키에 넣지 않아 리팩터링에는 견디는 "
    "대신, 같은 파일에서 같은 규칙을 어긴 추가 위반도 기존 부채로 함께 흡수됩니다. 그 파일의 "
    "부채를 migrate로 갚기 전까지 이 사각이 남습니다."
)

RE_PACKAGE = re.compile(r"^\s*package\s+([\w.]+)", re.M)
# `*`를 문자 집합에 넣어 두어야 와일드카드가 잘리지 않는다. Kotlin의 별칭(`... as Row`)과
# Java의 `;`는 공백·비문자에서 자연히 끊긴다.
RE_IMPORT = re.compile(r"^\s*import\s+(?:static\s+)?([\w.*]+)", re.M)


@dataclass(frozen=True)
class Import:
    text: str        # 원문 그대로 — 와일드카드는 `.*`를 달고 있다
    fqn: str         # 와일드카드를 뗀 형태(= 그 경우 패키지 이름)
    line: int


@dataclass(frozen=True)
class SourceFile:
    path: Path
    display: str     # 리포트에 쓰는 경로 — DOMAIN.md의 디렉터리 기준 상대경로
    package: str     # 첫 `package` 선언 — 귀속에 실제로 쓴 값
    package_lines: tuple  # 모든 `package` 매칭의 줄 번호(2건 이상이면 귀속을 믿을 수 없다)
    imports: tuple


@dataclass(frozen=True)
class Violation:
    path: str
    line: int
    rule_id: str
    message: str
    # 참조하는 쪽(소스의 소유 컨텍스트)과 참조되는 쪽(import 대상의 소유 컨텍스트). 소비자가
    # 컨텍스트 쌍을 메시지 문자열에서 파싱하지 않도록 필드로 준다.
    from_context: str = ""
    to_context: str = ""


@dataclass(frozen=True)
class ZeroMatch:
    """컨텍스트에 귀속된 소스가 0건이다. 오류가 아니고 exit 코드를 바꾸지 않는다."""

    rule_id: str
    subject: str     # "컨텍스트 claim"
    message: str


@dataclass(frozen=True)
class Skip:
    """검사를 아예 세우지 못했다 — 프로젝트 경로·소스가 없거나 컨텍스트 선언이 0건이다."""

    rule_id: str
    subject: str
    reason: str


@dataclass(frozen=True)
class AmbiguousPackage:
    """`package` 선언이 여러 건인 소스 — 그 파일의 귀속(따라서 판정)을 믿을 수 없다.

    `.kt`/`.java` 파일의 선언은 정확히 하나다. 둘 이상 잡혔다는 것은 주석 처리된 옛 선언이나
    문자열 리터럴이 섞였다는 뜻이고, 귀속은 **첫 매칭**이 정하므로 그 파일의 위반이 통째로
    사라질 수 있다. 오류가 아니고 exit 코드를 바꾸지 않는다 — 고칠 자리를 지목할 뿐이다.
    """

    path: str
    count: int
    package: str     # 첫 매칭 — 이번 실행이 실제로 귀속에 쓴 값


@dataclass(frozen=True)
class Baseline:
    """동결된 기존 부채 목록. 매칭 키는 (규칙 id, 경로)뿐이다 — 줄 번호는 리팩터링에 취약하다."""

    display: str     # 리포트·오류에 쓰는 경로(DOMAIN.md 기준 상대)
    keys: frozenset  # {(rule_id, path)}


@dataclass
class Report:
    violations: list = field(default_factory=list)
    zero_match: list = field(default_factory=list)
    # 해석 단계가 넘겨주는 경고 채널. `parse_domain`은 오류만 내고 경고를 내지 않으므로 지금은
    # 언제나 비어 있다 — 지금 이 키를 읽는 스킬은 없고, `--json` 스키마의 계약 안정성 때문에
    # 자리를 유지한다(키가 사라지면 스키마가 깨진다). 파서가 경고를 갖게 되면 여기로 승계한다.
    inherited: list = field(default_factory=list)
    skipped: list = field(default_factory=list)
    unreadable: list = field(default_factory=list)  # 읽지 못한 소스 — 검사에서 빠진 사각지대
    ambiguous_package: list = field(default_factory=list)   # [AmbiguousPackage] — 귀속 불신
    checked: int = 0                                # 검사한 컨텍스트 수
    errors: list = field(default_factory=list)      # 비어 있지 않으면 해석 불가(exit 2)
    baseline: object = None                         # Baseline | None — 자동 감지 결과
    debt: list = field(default_factory=list)        # [Violation] — 강등된 기존 부채(exit 미반영)


# ---------------------------------------------------------------------------
# 귀속 — 패키지를 컨텍스트에 접두 최장 일치시킨다
# ---------------------------------------------------------------------------

def _owning_context(package: str, scopes: list) -> str | None:
    """`package`(소스의 package 선언 또는 import 대상 FQN)를 소유한 컨텍스트명. 없으면 None.

    `scopes`는 `[(컨텍스트명, [접두 패턴])]`이고, 모든 패턴은 `..` 접미로 정규화되어 있다
    (`parse_domain.context_packages`의 계약).

    비교는 패키지 **세그먼트 경계**에서 한다 — 문자열 접두로만 보면 `com.acme.claim..`이
    `com.acme.claiming.Policy`를 삼켜 형제 컨텍스트의 코드가 남의 것으로 귀속된다.

    매칭이 여럿이면 접두가 가장 긴 컨텍스트가 이긴다. `parse_domain._check_package_overlap`이
    컨텍스트 패키지의 포함 관계를 이미 오류로 막으므로 오늘의 문서에서는 둘 이상 매칭될 수
    없지만, 그 보장이 흔들려도 귀속이 **매칭 순서에 좌우되지 않도록** 순서와 무관한 규칙을 쓴다.

    와일드카드 import(`a.b.*`)는 그 패키지의 멤버만 들여오므로 `fqn`이 패키지 이름 그대로다.
    "들여온 대상이 컨텍스트 접두 안에 있는가"라는 이 질문에는 타입 FQN과 같은 규칙이 맞는다 —
    `com.acme.*`는 `com.acme.claim`을 들여오지 않고, 실제로 여기서도 매칭되지 않는다.
    """
    owner, longest = None, -1
    for name, patterns in scopes:
        for pattern in patterns:
            base = pattern[:-2]
            if package != base and not package.startswith(base + "."):
                continue
            if len(base) > longest:
                owner, longest = name, len(base)
    return owner


# ---------------------------------------------------------------------------
# 소스 수집
# ---------------------------------------------------------------------------

def _is_test_dir(name) -> bool:
    return name.startswith("test") or name.endswith("Test")


def _walk_sources(root):
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        dirnames[:] = sorted(
            name for name in dirnames
            if name not in SKIP_DIRS and not (current.name == SRC_DIR and _is_test_dir(name)))
        for name in sorted(filenames):
            if name.endswith(SOURCE_SUFFIXES):
                yield current / name


def _line_of(text, position) -> int:
    return text.count("\n", 0, position) + 1


def _read_source(path, display):
    # utf-8-sig: 선두 BOM이 남으면 첫 줄의 `package`가 `^\s*`에 걸리지 않아 파일이 통째로 귀속을 잃는다.
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return None

    # 선언을 **세어 둔다**. 귀속은 예전처럼 첫 매칭이 정하지만, 2건 이상이면 그 사실을 고지해
    # 조용한 오귀속(주석 처리된 옛 선언이 앞에 있는 경우 ✅ 실측)을 시끄러운 고지로 바꾼다.
    matches = list(RE_PACKAGE.finditer(text))
    package = matches[0].group(1) if matches else ""
    package_lines = tuple(_line_of(text, match.start(1)) for match in matches)

    imports = []
    for match in RE_IMPORT.finditer(text):
        raw = match.group(1)
        fqn = raw[:-2] if raw.endswith(".*") else raw
        imports.append(Import(raw, fqn, _line_of(text, match.start(1))))
    return SourceFile(path, display, package, package_lines, tuple(imports))


def _load_sources(root, base) -> tuple:
    """(읽은 소스, 읽지 못한 파일의 표시 경로). 후자를 버리면 검사에 사각지대가 생긴다."""
    sources, unreadable = [], []
    for path in _walk_sources(root):
        try:
            display = path.relative_to(base).as_posix()
        except ValueError:
            display = path.as_posix()
        source = _read_source(path, display)
        if source is None:
            unreadable.append(display)
        else:
            sources.append(source)
    return sources, unreadable


# ---------------------------------------------------------------------------
# baseline — 동결된 기존 부채
# ---------------------------------------------------------------------------

def _load_baseline(base) -> tuple:
    """`docs/domain/baseline.jsonl`을 자동 감지한다 — (Baseline|None, [LocatedError]).

    **플래그를 두지 않는다.** 파일이 있다는 것은 그 프로젝트가 상환 중이라는 선언이고, 그때
    부채와 신규를 가르지 않은 판정은 언제나 틀린 판정이다 — 켜고 끌 대상이 아니다.
    """
    path = base / BASELINE_RELATIVE
    if not path.is_file():
        return None, []
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return None, [LocatedError(
            0, "baseline 파일을 읽지 못했습니다 — 인코딩(UTF-8)과 권한을 확인하세요",
            BASELINE_RELATIVE)]

    keys, errors = set(), []
    for number, line in enumerate(text.split("\n"), start=1):
        if not line.strip():
            continue          # 빈 줄은 위반을 담지 않으므로 래칫이 새지 않는다
        try:
            entry = json.loads(line)
        except ValueError:
            errors.append(LocatedError(
                number, "baseline 줄이 JSON이 아닙니다 — 한 줄에 위반 하나씩 "
                        '{"rule": ..., "path": ...} 형식입니다', BASELINE_RELATIVE))
            continue
        rule = entry.get("rule") if isinstance(entry, dict) else None
        target = entry.get("path") if isinstance(entry, dict) else None
        if not isinstance(rule, str) or not isinstance(target, str) or not (rule and target):
            errors.append(LocatedError(
                number, "baseline 줄에 문자열 'rule'과 'path'가 모두 있어야 합니다 "
                        "(path는 git 루트 기준 상대경로)", BASELINE_RELATIVE))
            continue
        keys.add((rule, target))
    if errors:
        return None, errors   # 한 줄이 깨지면 어느 위반이 동결분인지 전체를 알 수 없다
    return Baseline(BASELINE_RELATIVE, frozenset(keys)), []


def _split_debt(violations, baseline) -> tuple:
    """위반을 (신규, 기존 부채)로 가른다 — 매칭 키는 (규칙 id, 경로)."""
    fresh, debt = [], []
    for violation in violations:
        target = debt if (violation.rule_id, violation.path) in baseline.keys else fresh
        target.append(violation)
    return fresh, debt


# ---------------------------------------------------------------------------
# 검사
# ---------------------------------------------------------------------------

def _scopes(domain, errors) -> list:
    """`[(컨텍스트명, [접두 패턴])]`. 패키지를 정할 수 없는 컨텍스트는 오류로 기록한다.

    `context_packages`는 빈 목록 대신 `LocatedError`를 던진다 — 빈 목록을 받아 넘기면 그
    컨텍스트가 아무 소스도 갖지 않는 것으로 보여 검사가 0건을 검사한 채 통과한다.
    `domain.errors`가 비어 있으면 여기서 던질 수 없지만(필수 라벨 검증이 이미 막는다),
    파서의 보장이 흔들릴 때 조용히 통과하지 않도록 잡아 둔다.
    """
    scopes = []
    for context in domain.contexts:
        try:
            scopes.append((context.name, context_packages(domain, context)))
        except LocatedError as error:
            errors.append(error)
    return scopes


def _barren_reason(project, root, unreadable) -> str:
    """검사를 세우지 못한 사유. **고칠 자리가 다르므로 네 갈래를 뭉뚱그리지 않는다.**

    경로가 없는 것(`- 경로:`를 고치거나 코드가 생기길 기다린다), 경로가 디렉터리가 아닌 것
    (`- 경로:`가 파일을 가리킨다), 소스가 없는 것(코드가 아직 없다), 있는 소스를 전부 읽지
    못한 것(인코딩·권한을 고친다)은 서로 다른 상태다. 특히 마지막 갈래를 "소스가 없습니다"로
    말하면 바로 아래 `읽지 못한 소스 N건` 줄과 정면으로 모순된다.
    """
    where = f"프로젝트 '{project.name}'의 경로 '{project.path}'"
    if not root.exists():
        return f"{where} 아래 검사할 .kt/.java 소스가 없습니다 (경로가 아직 없습니다)"
    if not root.is_dir():
        return (f"{where}가 디렉터리가 아닙니다 — 그 아래를 걸을 수 없습니다 "
                f"('- 경로:'는 프로젝트 루트 디렉터리를 가리켜야 합니다)")
    if unreadable:
        return (f"{where} 아래에서 찾은 .kt/.java 소스 {len(unreadable)}건을 **전부 읽지 "
                f"못했습니다** — 인코딩(UTF-8)과 권한을 확인하세요 (아래 '읽지 못한 소스' 줄 참조)")
    return f"{where} 아래 검사할 .kt/.java 소스가 없습니다"


def _collect(report, domain, base) -> tuple:
    """프로젝트별로 소스를 걷는다 — ([소스], {소스가 0건인 프로젝트명: 사유}).

    같은 파일이 두 프로젝트 경로 아래에 걸쳐 있으면(경로가 겹칠 때) 한 번만 담는다.
    """
    sources, seen, barren = [], set(), {}
    seen_unreadable = set()
    for project in domain.projects:
        root = Path(os.path.normpath(base / project.path))
        loaded, unreadable = _load_sources(root, base) if root.is_dir() else ([], [])
        for item in unreadable:
            if item not in seen_unreadable:
                seen_unreadable.add(item)
                report.unreadable.append(item)
        if not loaded:
            barren[project.name] = _barren_reason(project, root, unreadable)
            continue
        for source in loaded:
            if source.path in seen:
                continue
            seen.add(source.path)
            sources.append(source)
            if len(source.package_lines) > 1:
                report.ambiguous_package.append(AmbiguousPackage(
                    source.display, len(source.package_lines), source.package))
    return sources, barren


def _judge(report, sources, scopes, allowlist) -> dict:
    """소스를 컨텍스트에 귀속시키고 경계를 넘는 참조를 판정한다 — {컨텍스트명: [귀속 소스]}."""
    members = {name: [] for name, _ in scopes}
    for source in sources:
        owner = _owning_context(source.package, scopes)
        if owner is None:
            continue          # 어느 컨텍스트에도 속하지 않는 코드는 도메인 경계 밖이다
        members[owner].append(source)
        for imported in source.imports:
            target = _owning_context(imported.fqn, scopes)
            if target is None or target == owner:
                continue
            if target in allowlist[owner]:
                continue      # 관계 표가 그 쌍을 열었다 — 방향은 구분하지 않는다
            report.violations.append(Violation(
                source.display, imported.line, RULE_ID,
                f"컨텍스트 '{owner}'가 다른 컨텍스트 '{target}'의 코드를 직접 참조합니다 — "
                f"{imported.text} ('### 관계' 표에 이 쌍이 없습니다)",
                owner, target))
    return members


def _account(report, domain, members, barren) -> None:
    """컨텍스트마다 검사·0건 경고·생략 중 하나를 반드시 기록한다(침묵 금지).

    생략과 0건 경고는 겹치지 않는다 — 프로젝트 경로가 아직 없는 것과 패키지가 어긋난 것은
    고칠 자리가 다르므로, 뭉뚱그리면 사용자가 엉뚱한 곳을 본다.
    """
    for context in domain.contexts:
        owned = members.get(context.name, [])
        if not owned and context.project in barren:
            report.skipped.append(
                Skip(RULE_ID, f"컨텍스트 {context.name}", barren[context.project]))
            continue
        report.checked += 1
        if not owned:
            subject = f"컨텍스트 {context.name}"
            report.zero_match.append(ZeroMatch(
                RULE_ID, subject, f"[0건 경고] {RULE_ID}: {ZERO_MATCH_REASON} ({subject})"))


# ---------------------------------------------------------------------------
# 진입점
# ---------------------------------------------------------------------------

def check(domain_path) -> Report:
    """DOMAIN.md 한 건을 해석하고 그 프로젝트들의 소스에서 컨텍스트 격리를 검사한다.

    **호출자는 report.errors가 비었는지 먼저 확인해야 한다.** 해석이 실패하면 검사가 서지
    않으므로 위반 목록은 비어 있고, 그것은 '클린'과 다른 상태다.
    """
    report = Report()
    domain = parse_domain(domain_path)
    if domain.errors:
        report.errors = list(domain.errors)
        return report

    base = Path(domain_path).resolve().parent
    report.baseline, baseline_errors = _load_baseline(base)
    if baseline_errors:
        report.errors = baseline_errors
        return report

    scopes = _scopes(domain, report.errors)
    if report.errors:
        return report

    if not scopes:
        # 컨텍스트가 0건이면 검사할 경계 자체가 없다. exit 0으로 조용히 나가면 "위반 없음"과
        # 구분되지 않으므로 생략으로 고지한다.
        report.skipped.append(Skip(
            RULE_ID, "문서 전체",
            "선언된 컨텍스트가 0건입니다 — 검사할 도메인 경계가 없습니다 "
            "('## 컨텍스트: <이름>' 섹션을 선언하세요)"))
        return report

    sources, barren = _collect(report, domain, base)
    members = _judge(report, sources, scopes, isolation_allowlist(domain))
    _account(report, domain, members, barren)

    report.violations = sorted(set(report.violations),
                               key=lambda v: (v.path, v.line, v.rule_id, v.message))
    if report.baseline is not None:
        report.violations, report.debt = _split_debt(report.violations, report.baseline)
    return report


def render(report) -> list:
    """리포트를 사람이 읽는 줄 목록으로 만든다. 위반·경고·생략·한계가 한 화면에 함께 있다."""
    lines = list(report.inherited)
    lines += [f"{v.path}:{v.line}: [{v.rule_id}] {v.message}" for v in report.violations]
    lines += [f"[기존 부채] {v.path}:{v.line}: [{v.rule_id}] {v.message}" for v in report.debt]
    lines += [warning.message for warning in report.zero_match]
    lines.append(f"검사한 컨텍스트 {report.checked}개 / 생략 {len(report.skipped)}개")
    if report.baseline is not None:
        matched = len({(v.rule_id, v.path) for v in report.debt})
        lines.append(
            f"기존 부채 {len(report.debt)}건 — exit 코드에 반영하지 않습니다 "
            f"({report.baseline.display}의 {len(report.baseline.keys)}개 항목 중 {matched}개가 "
            f"이번 실행의 위반과 매칭됐습니다. 나머지는 해소됐거나 이번 실행이 검사하지 않은 "
            f"규칙입니다 — 축소는 migrate만 합니다)")
    lines += [f"생략: {s.rule_id} ({s.subject}): {s.reason}" for s in report.skipped]
    if report.ambiguous_package:
        detail = ", ".join(f"{a.path}({a.count}건 → '{a.package}'로 귀속)"
                           for a in report.ambiguous_package)
        lines.append(
            f"package 선언이 여러 건인 소스 {len(report.ambiguous_package)}건 — 첫 선언으로 "
            f"귀속했으므로 이 파일들의 판정은 믿을 수 없습니다(주석 처리된 옛 선언을 "
            f"확인하세요): {detail}")
    if report.unreadable:
        lines.append(f"읽지 못한 소스 {len(report.unreadable)}건 — 이 파일들은 검사하지 "
                     f"않았습니다: {', '.join(report.unreadable)}")
    lines.append(LIMITATION_NOTE)
    if report.baseline is not None:
        lines.append(BASELINE_MATCH_NOTE)
    return lines


def _payload(report) -> dict:
    return {
        "violations": [asdict(v) for v in report.violations],
        "zero_match": [asdict(w) for w in report.zero_match],
        "inherited": list(report.inherited),
        "skipped": [asdict(s) for s in report.skipped],
        "unreadable": list(report.unreadable),
        # 텍스트 리포트에만 두면 `--json`을 읽는 소비자(스킬)에게서 이 고지가 사라진다.
        "ambiguous_package": [asdict(a) for a in report.ambiguous_package],
        "checked": report.checked,
        # 강등 채널은 violations와 겹치지 않는다 — 저쪽이 exit 1을 만드는 신규 위반이다.
        "baseline": {
            "path": report.baseline.display if report.baseline else None,
            "entries": len(report.baseline.keys) if report.baseline else 0,
            "demoted": [asdict(v) for v in report.debt],
            "note": BASELINE_MATCH_NOTE if report.baseline else None,
        },
    }


def main(argv) -> int:
    as_json = "--json" in argv
    args = [arg for arg in argv if arg != "--json"]
    if len(args) != 1 or any(arg.startswith("--") for arg in args):
        print("사용법: python3 check_imports.py <DOMAIN.md 경로> [--json]", file=sys.stderr)
        return 2

    path = args[0]
    report = check(path)
    if report.errors:
        for error in sorted(report.errors,
                            key=lambda e: (getattr(e, "path", "") or path, e.line)):
            print(format_error(error, path), file=sys.stderr)
        return 2

    if as_json:
        print(json.dumps(_payload(report), ensure_ascii=False, indent=2))
    else:
        for line in render(report):
            print(line)
    return 1 if report.violations else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
