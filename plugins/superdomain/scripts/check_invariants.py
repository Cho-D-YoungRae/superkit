"""불변식 ↔ 테스트 태그 대조 검사기 — domain 문서의 confirmed 항목이 코드로 강제되는지 본다.

**exit 계약: 0 = 위반 없음, 1 = 위반 발견(또는 검사 불능), 2 = 해석 불가·배치 오류 또는 사용법 오류.**
`check_imports.py`와 같은 의미다 — 1은 정상 판정 결과이고, 검사 자체가 성립하지 않은 경우만
2로 나간다. 다만 '검사 불능'(테스트 소스 0건)만은 판정을 내리지 못했는데도 1로 나가는데,
그것이 도메인 문서 표준 §4.4가 못박은 값이다: 태그가 있을 수 없는 환경에서 '위반 없음'은
거짓이므로 클린(0)으로 통과시키지 않는다.

**파싱 계약의 정본은 `references/governance/domain-doc-template.md` §2·§4다.** 이 스크립트와
그 문서의 해석이 갈리면 문서가 이기고 여기가 고쳐진다. 요약하면:

- 기계가 읽는 것은 `## 불변식` 아래 **첫 표 하나뿐**이다(§4.1). 창은 다음 레벨 2 헤딩
  직전까지이고 `###`는 창을 끊지 않는다. 표가 없으면 오류가 아니라 '불변식 0건'이다.
- 열은 **ID · 서술 · 상태** 순서 고정이고 **헤더 이름은 읽지 않는다**(§4.1).
- ID는 `INV-<컨텍스트 대문자>-<3자리>`이고, 컨텍스트는 선언 집합에 대한 **최장 일치**로
  정한다(§4.2 — `core`와 `core-api`가 함께 선언돼도 `INV-CORE-API-001`은 `core-api`다).
- 상태의 정규 값은 `proposed`·`confirmed` 둘뿐이다(§4.3).

§4.4의 세 채널을 여기서는 exit 코드 세 개로 나눈다.

| 정본의 판정 | 여기서 | exit |
|---|---|---|
| 오류(형식·중복·배치) | `report.errors` — 코퍼스를 신뢰할 수 없다 | 2 |
| 위반(confirmed인데 태그 없음) | `report.violations` | 1 |
| 경고(고아 태그·확정 전 구현·미선언 문서) | `report.warnings` — 코드를 바꾸지 않는다 | 그대로 |

**이 검사기는 강제의 정본이 아니다.** 리터럴 `@Tag("INV-...")`만 보고, 태그가 달렸다는 것이
그 테스트가 불변식을 실제로 검증한다는 뜻도 아니다(`LIMITATION_NOTE`). 그 대조는
`agents/domain-reviewer.md` C4(불변식 정합) (2)의 범주다.
"""

import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

# 소스 트리 관례(걷지 않는 디렉터리·소스 확장자)는 check_imports가 정본이다. 두 검사기가 서로
# 다른 파일 집합을 걸으면 한쪽이 본 생성물 사본의 태그가 다른 쪽 판정을 뒤집는다.
from check_imports import SKIP_DIRS, SOURCE_SUFFIXES, SRC_DIR
# 산출물 경로의 정본. 컨텍스트 문서의 자리를 여기서 다시 적지 않는다.
from layout import CONTEXTS_RELATIVE, DOMAIN_RELATIVE, LayoutError, from_domain_path
# 컨텍스트·프로젝트 경로의 정본 파서. 패키지 패턴을 쓰지 않으므로 context_packages()는 부르지
# 않는다 — 태그 스캔의 범위는 패키지가 아니라 프로젝트 경로 아래 테스트 디렉터리다
# (domain-doc-template.md §4.4). 오류 줄(`경로:라인: 메시지`)의 조립도 이 모듈이 정본이다.
from parse_domain import LocatedError, format_error, parse_domain

ID_PREFIX = "INV-"
PROPOSED = "proposed"
CONFIRMED = "confirmed"
STATUSES = (PROPOSED, CONFIRMED)
COLUMNS = 3                                         # ID · 서술 · 상태

RE_INVARIANTS_HEADING = re.compile(r"^##\s+불변식\s*$")
# 레벨 2만 창을 끊는다 — `###`는 하위 헤딩이라 불변식 절 안에 머문다(§4.1).
RE_LEVEL2 = re.compile(r"^##(?!#)")
RE_TABLE = re.compile(r"^\|")
RE_NUMBER = re.compile(r"\d{3}")
# 리터럴만 본다. `@` 바로 뒤에 `Tag`가 와야 하므로 완전 수식 애너테이션
# (`@org.junit.jupiter.api.Tag`)은 매칭되지 않는다 — 그것이 §4.4가 고지한 한계 그대로다.
RE_TAG = re.compile(r'@Tag\s*\(\s*(?:value\s*=\s*)?"(INV-[^"\s]+)"\s*\)')

LIMITATION_NOTE = (
    "한계: 이 검사는 테스트 소스의 리터럴 @Tag(\"INV-...\")만 봅니다 — 상수 간접 참조"
    "(@Tag(INV_CLAIM_001))와 완전 수식 애너테이션(@org.junit.jupiter.api.Tag)은 보이지 "
    "않고, 반대로 주석·비활성 코드 안의 리터럴은 존재로 셉니다. 태그가 달렸다는 것이 그 "
    "테스트가 불변식을 실제로 검증한다는 뜻도 아닙니다"
    "(서술과 검증의 대조는 domain-reviewer의 불변식 정합 판정입니다)."
)
BLOCKED_HEAD = "검사 불능: 테스트 소스가 없습니다"

ORPHAN_TAG = "orphan-tag"
PROPOSED_TAGGED = "proposed-tagged"
STRAY_DOC = "stray-doc"


@dataclass(frozen=True)
class Invariant:
    id: str
    context: str
    description: str
    status: str
    path: str        # 리포트에 쓰는 경로 — 프로젝트 루트 기준 상대경로
    line: int


@dataclass(frozen=True)
class Tag:
    id: str
    path: str
    line: int


@dataclass(frozen=True)
class Violation:
    path: str        # 문서 쪽을 지목한다 — 고칠 곳은 태그가 아니라 상태이거나 테스트다
    line: int
    invariant_id: str
    message: str


@dataclass(frozen=True)
class InvariantWarning:
    """오류도 위반도 아닌 고지(§4.4의 경고 3종). exit 코드를 바꾸지 않는다."""

    path: str
    line: int            # 0 = 파일 수준
    kind: str            # ORPHAN_TAG | PROPOSED_TAGGED | STRAY_DOC
    invariant_id: str    # 문서·태그에 걸리지 않는 경고는 ""
    message: str


@dataclass
class Report:
    invariants: list = field(default_factory=list)
    violations: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    notices: list = field(default_factory=list)     # '불변식 0건' 등 — 문자열 그대로
    tags: list = field(default_factory=list)
    unreadable: list = field(default_factory=list)  # 읽지 못한 테스트 소스 — 태그의 사각지대
    test_sources: int = 0
    checked: int = 0                                # 실제로 대조한 불변식 수
    blocked: str = ""                               # 비어 있지 않으면 검사 불능(exit 1)
    errors: list = field(default_factory=list)      # 비어 있지 않으면 해석 불가(exit 2)


@dataclass(frozen=True)
class _Doc:
    path: Path
    display: str
    context: str     # 파일명이 못박는 컨텍스트


# ---------------------------------------------------------------------------
# 표 파싱 — 정본 §4.1
# ---------------------------------------------------------------------------

def _table_rows(text) -> tuple:
    """(데이터 행, 표를 찾았는가). 행은 (1-기준 라인 번호, 원문)이다.

    `## 불변식`의 **첫 표**만 읽고, 창은 다음 레벨 2 헤딩 직전(마지막 절이면 문서 끝)까지다.
    창 안에 표가 없으면 다음 절로 넘어가 찾지 않는다 — `## 애그리거트`의 표가 불변식 표로
    잘못 읽히는 일은 그래서 없다.
    """
    lines = text.split("\n")
    start = None
    for index, line in enumerate(lines):
        if RE_INVARIANTS_HEADING.match(line):
            start = index
            break
    if start is None:
        return [], False

    end = len(lines)
    for index in range(start + 1, len(lines)):
        if RE_LEVEL2.match(lines[index]):
            end = index
            break

    first = next((index for index in range(start + 1, end)
                  if RE_TABLE.match(lines[index])), None)
    if first is None:
        return [], False

    block, index = [], first
    while index < end and RE_TABLE.match(lines[index]):    # 빈 줄이 표를 끝낸다
        block.append((index + 1, lines[index]))
        index += 1

    # 머리 행과 그 다음 한 줄은 언제나 버린다 — 구분선이 없으면 첫 데이터 행이 구분선
    # 자리에서 버려진다는 것이 계약이다(§4.1). 여기서 되살리면 문서와 검사가 갈라진다.
    return block[2:], True


def _cells(line) -> list:
    """데이터 행의 칸. 앞뒤 울타리 `|`가 만드는 빈 칸만 떼고 **빈 칸 자체는 남긴다.**

    `| a | b |  |`는 셋째 칸이 빈 3칸 행(비정규 상태 오류)이고 `| a | b |`는 2칸 결손
    행(칸 부족 오류)이다. 둘을 뭉개면 결손 행이 조용히 지나간다(§4.1).
    """
    parts = line.split("|")[1:]          # RE_TABLE이 선두 울타리를 보장한다
    if parts and parts[-1].strip() == "":
        parts = parts[:-1]
    return [part.strip() for part in parts]


def _resolve_context(invariant_id, contexts) -> tuple:
    """(컨텍스트, 오류 사유). 컨텍스트가 None이면 사유가 채워진다(§4.2)."""
    if not invariant_id.startswith(ID_PREFIX):
        return None, ("ID 형식이 아닙니다 — 'INV-<컨텍스트 대문자>-<3자리>'로 씁니다"
                      "(도메인 문서 표준 §4.2)")
    body = invariant_id[len(ID_PREFIX):]
    # 최장 일치가 하이픈의 중의성을 없앤다 — `core`·`core-api`가 함께 선언돼 있어도
    # `INV-CORE-API-001`은 `core-api`의 것이다.
    matched = [name for name in contexts if body.startswith(name.upper() + "-")]
    if not matched:
        return None, ("어느 선언 컨텍스트에도 붙지 않습니다 — 컨텍스트를 먼저 "
                      "DOMAIN.md에 등록하세요(§4.2)")
    context = max(matched, key=lambda name: (len(name), name))
    number = body[len(context) + 1:]
    if not RE_NUMBER.fullmatch(number):
        return None, (f"컨텍스트 '{context}' 뒤의 '{number}'가 3자리 zero-pad 번호가 "
                      f"아닙니다(§4.2)")
    return context, ""


# ---------------------------------------------------------------------------
# 문서 발견 — 정본 §2 · §4.4
# ---------------------------------------------------------------------------

def _discover(layout, contexts, target, report) -> list:
    """읽을 도메인 문서 목록. 드리프트 경고를 여기서 낸다.

    컨텍스트 문서의 자리는 `docs/superdomain/contexts/<컨텍스트>.md` 하나뿐이다 — 컨텍스트가
    하나여도 같다(0.2.x의 통합 배치 파일은 없어졌고, 남아 있으면 layout이 막는다).

    `--context`는 **수집 코퍼스**만 좁힌다. 미선언 문서 경고는 좁히지 않는다 — 찾는 문서가 안
    보이는 이유가 바로 그 파일명 오타일 수 있기 때문이다.
    """
    declared, stray = {}, []
    if layout.contexts_dir.is_dir():
        for path in sorted(layout.contexts_dir.glob("*.md")):
            if path.stem in contexts:
                declared[path.stem] = path
            else:
                stray.append(path)

    for path in stray:
        # 표가 있든 없든 낸다. 거버넌스 밖 파일이므로 불변식은 수집하지 않는다(§4.4).
        report.warnings.append(InvariantWarning(
            layout.display(path), 0, STRAY_DOC, "",
            f"'{path.stem}'은(는) DOMAIN.md에 선언된 컨텍스트가 아닙니다 — 이 문서의 "
            f"불변식은 수집하지 않습니다(컨텍스트를 지웠거나 파일명 오타입니다)."))

    docs = [_Doc(path, layout.display(path), name) for name, path in sorted(declared.items())]
    if target is not None:
        docs = [doc for doc in docs if doc.context == target]

    for name in contexts:
        if (target is None or name == target) and name not in declared:
            report.notices.append(
                f"고지: 컨텍스트 '{name}'의 도메인 문서가 없습니다"
                f"({CONTEXTS_RELATIVE}/{name}.md) — 불변식 0건")
    return docs


def _collect(doc, contexts, report) -> None:
    """도메인 문서 하나의 불변식 표를 읽어 코퍼스에 넣는다. 중복 판정의 범위는 문서 하나다."""
    def fail(line, message):
        report.errors.append(LocatedError(line, message, doc.display))

    try:
        text = doc.path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        fail(0, "도메인 문서를 읽지 못했습니다 — 이 문서의 불변식은 대조하지 않았습니다.")
        return

    rows, found = _table_rows(text)
    if not found:
        report.notices.append(f"고지: {doc.display}: '## 불변식' 표가 없습니다 — 불변식 0건")
        return
    if not rows:
        report.notices.append(
            f"고지: {doc.display}: '## 불변식' 표에 데이터 행이 없습니다 — 불변식 0건")
        return

    seen = {}
    for line, raw in rows:
        cells = _cells(raw)
        if len(cells) < COLUMNS:
            fail(line, f"불변식 표의 데이터 행에 칸이 {len(cells)}개뿐입니다 — ID·서술·상태 "
                       f"세 칸을 채우거나 행을 지우세요(§4.1).")
            continue
        # 넷째 칸부터는 버린다. 헤더 이름은 읽지 않는다 — 계약은 열의 순서다(§4.1).
        invariant_id, description, status = cells[0], cells[1], cells[2]

        context, reason = _resolve_context(invariant_id, contexts)
        if context is None:
            fail(line, f"불변식 ID '{invariant_id}': {reason}.")
            continue
        if context != doc.context:
            fail(line, f"불변식 ID '{invariant_id}'의 컨텍스트 '{context}'가 파일명 컨텍스트 "
                       f"'{doc.context}'와 다릅니다 — 문서를 잘못 찾아 들어간 항목입니다(§4.4).")
            continue
        if invariant_id in seen:
            fail(line, f"불변식 ID '{invariant_id}'가 이 문서에서 두 번 선언됐습니다"
                       f"(앞선 선언: {seen[invariant_id]}행) — 번호는 문서 안에서 "
                       f"유일합니다(§4.2).")
            continue
        if status not in STATUSES:
            head = ("상태 칸이 비어 있습니다" if not status
                    else f"상태 '{status}'은(는) 정규 값이 아닙니다")
            fail(line, f"불변식 ID '{invariant_id}': {head} — 정규 값은 '{PROPOSED}'와 "
                       f"'{CONFIRMED}' 둘뿐입니다(§4.3).")
            continue

        seen[invariant_id] = line
        report.invariants.append(
            Invariant(invariant_id, context, description, status, doc.display, line))


# ---------------------------------------------------------------------------
# 태그 스캔 — domain-doc-template.md §4.4
# ---------------------------------------------------------------------------

def _is_test_path(parts) -> bool:
    """디렉터리 세그먼트만 보고 테스트 소스인지 판정한다(`src/test/`·`test/` 관례).

    `src/<소스셋>`이 나오면 **그 소스셋이 판정을 끝낸다.** `src/main/kotlin/com/acme/test/`처럼
    프로덕션 아래 `test` 패키지가 있어도 테스트 소스가 아니다 — 여기서 끊지 않으면 프로덕션
    코드의 `@Tag` 리터럴이 confirmed를 충족시켜 검사가 조용히 통과한다.

    `src/` 아래의 테스트 소스셋 이름(`test*`·`*Test`)은 check_imports가 프로덕션에서 걷어내는
    것과 같은 규칙이지만 그쪽 판정 함수는 비공개라 여기 다시 적었다 — 임포트가 보장하는
    공유는 `SKIP_DIRS`와 소스 확장자뿐이므로 이 규칙은 갈라질 수 있다.
    """
    for index, part in enumerate(parts[:-1]):
        if index and parts[index - 1] == SRC_DIR:
            return part.startswith("test") or part.endswith("Test")
        if part == "test":
            return True
    return False


def _scan_tags(layout, projects, report) -> None:
    """선언된 프로젝트 경로 아래 테스트 소스에서 `@Tag("INV-...")` 리터럴을 모은다.

    **범위를 정하는 것은 경로 관례뿐이다.** 구 템플릿에는 `- 아키텍처 테스트 위치:` 라벨이 있어
    임의의 트리를 선언으로 끌어올 수 있었지만, 그 라벨은 fitness와 함께 퇴역했다(DOMAIN.md에
    쓰면 파서가 거부한다). 남은 것은 `_is_test_path`의 두 갈래뿐이다 — 경로에 `test` 세그먼트가
    있거나(`test/`, `architecture-test/src/test/kotlin` …), `src` 바로 아래 소스셋 이름이
    `test`로 시작하거나 `Test`로 끝나거나(`src/test`, `src/testFixtures`, `src/integrationTest`).
    **사각지대는 그 둘 다 아닌 트리뿐이다** — `itest/kotlin`처럼 `src` 아래도 아니고 이름에
    `test`도 없는 경우다.

    그런 트리의 태그는 보이지 않는다. 결과는 **둘 중 하나이고 어느 쪽도 침묵이 아니다.**
    관례 안에 다른 테스트 소스가 하나라도 있으면 confirmed 불변식이 **거짓 위반**으로 뜨고,
    그 트리가 유일한 테스트 트리이면 `test_sources`가 0이라 **검사 불능**으로 나간다
    (`_judge`). 둘 다 exit 1이고 리포트가 그 사실을 말하므로, 사용자는 지목된 줄이나
    `검사 불능` 줄에서 바로 알아챈다.
    """
    # 프로젝트 경로는 겹칠 수 있다(모노레포의 `.`과 `backend`). 같은 파일을 두 번 세면
    # 관측 건수가 부풀고 고아 태그 경고가 중복된다.
    scanned = set()
    for project in projects:
        root = Path(os.path.normpath(layout.root / project.path))
        if not root.is_dir():
            continue

        for dirpath, dirnames, filenames in os.walk(root):
            current = Path(dirpath)
            dirnames[:] = sorted(name for name in dirnames if name not in SKIP_DIRS)
            for name in sorted(filenames):
                if not name.endswith(SOURCE_SUFFIXES):
                    continue
                path = current / name
                if not _is_test_path(path.relative_to(root).parts):
                    continue
                if path in scanned:
                    continue
                scanned.add(path)
                display = layout.display(path)
                report.test_sources += 1
                try:
                    text = path.read_text(encoding="utf-8-sig")
                except (OSError, UnicodeDecodeError):
                    report.unreadable.append(display)
                    continue
                for match in RE_TAG.finditer(text):
                    report.tags.append(Tag(match.group(1), display,
                                           text.count("\n", 0, match.start(1)) + 1))


# ---------------------------------------------------------------------------
# 판정 — 정본 §4.4
# ---------------------------------------------------------------------------

def _judge(report, contexts, target) -> None:
    if not report.test_sources:
        # 태그가 있을 수 없는 환경에서 '위반 없음'은 거짓이다 — 클린으로 통과시키지 않는다.
        confirmed = sum(1 for item in report.invariants if item.status == CONFIRMED)
        report.blocked = (
            f"{BLOCKED_HEAD} — confirmed {confirmed}건을 대조할 수 없습니다"
            if confirmed else
            f"{BLOCKED_HEAD} — confirmed 0건이지만 태그를 관측할 수 없는 환경이라 클린으로 "
            f"판정하지 않습니다")
        return

    report.checked = len(report.invariants)
    sites = {}
    for tag in report.tags:
        sites.setdefault(tag.id, []).append(f"{tag.path}:{tag.line}")

    for item in report.invariants:
        if item.status == CONFIRMED and item.id not in sites:
            report.violations.append(Violation(
                item.path, item.line, item.id,
                "confirmed 불변식에 대응 테스트 태그가 없습니다"))
        elif item.status == PROPOSED and item.id in sites:
            report.warnings.append(InvariantWarning(
                item.path, item.line, PROPOSED_TAGGED, item.id,
                f"proposed 불변식에 테스트 태그가 있습니다 — 확정 전 구현입니다 "
                f"(태그: {', '.join(sites[item.id])})."))

    known = {item.id for item in report.invariants}
    for tag in report.tags:
        if tag.id in known:
            continue
        # 필터가 걸린 실행에서 다른 컨텍스트의 태그는 이 실행의 관심사가 아니다. 다만 어느
        # 컨텍스트에도 붙지 않는 태그는 어느 실행에서든 깨진 것이므로 언제나 낸다.
        if target is not None and _resolve_context(tag.id, contexts)[0] not in (None, target):
            continue
        report.warnings.append(InvariantWarning(
            tag.path, tag.line, ORPHAN_TAG, tag.id,
            "태그가 가리키는 불변식이 문서에 없습니다 — 문서에서 지웠거나 오타입니다."))


# ---------------------------------------------------------------------------
# 진입점
# ---------------------------------------------------------------------------

def check(domain_path, context=None) -> Report:
    """DOMAIN.md 한 건의 도메인 문서와 테스트 태그를 대조한다.

    **호출자는 report.errors가 비었는지 먼저 확인해야 한다.** 오류가 있으면 코퍼스 자체가
    불완전하므로 위반 목록은 '클린'과 다른 상태다. `report.blocked`도 같은 뜻으로 먼저
    본다 — 대조를 하지 못한 실행의 빈 위반 목록은 위반 없음이 아니다. 배치가 틀리면(옛 배치
    포함) `LayoutError`를 던진다.
    """
    layout = from_domain_path(domain_path)
    report = Report()
    path_text = str(domain_path)

    # 읽기 실패도 `parse_domain`이 오류 하나로 돌려준다 — 해석의 입구를 두 곳에 두지 않는다.
    domain = parse_domain(domain_path)
    if domain.errors:
        # 컨텍스트 집합을 못 믿으면 ID의 최장 일치도 못 믿는다 — 여기서 멈춘다.
        report.errors.extend(LocatedError(e.line, e.message, path_text) for e in domain.errors)
        return report

    contexts = [item.name for item in domain.contexts]
    if context is not None and context not in contexts:
        report.errors.append(LocatedError(
            0,
            f"컨텍스트 '{context}'는 DOMAIN.md에 선언되지 않았습니다 — 선언된 컨텍스트: "
            f"{', '.join(contexts) or '없음'}.",
            path_text))
        return report

    for doc in _discover(layout, contexts, context, report):
        _collect(doc, contexts, report)
    _scan_tags(layout, domain.projects, report)

    report.invariants.sort(key=lambda item: (item.path, item.line))
    report.tags.sort(key=lambda tag: (tag.path, tag.line, tag.id))
    _judge(report, contexts, context)

    report.violations.sort(key=lambda v: (v.path, v.line, v.invariant_id))
    report.warnings.sort(key=lambda w: (w.path, w.line, w.kind, w.invariant_id))
    report.notices.sort()
    return report


def _warning_line(warning) -> str:
    head = f"{warning.path}:{warning.line}: 경고: "
    return head + (f"[{warning.invariant_id}] " if warning.invariant_id else "") + warning.message


def render(report) -> list:
    """리포트를 사람이 읽는 줄 목록으로 만든다. 위반·경고·고지·한계가 한 화면에 함께 있다."""
    lines = [f"{v.path}:{v.line}: [{v.invariant_id}] {v.message}" for v in report.violations]
    lines += [_warning_line(w) for w in report.warnings]

    confirmed = sum(1 for item in report.invariants if item.status == CONFIRMED)
    proposed = len(report.invariants) - confirmed
    if report.blocked:
        lines.append(report.blocked)
        lines.append(f"수집한 불변식 {len(report.invariants)}건"
                     f"(confirmed {confirmed} · proposed {proposed}) — 대조하지 못했습니다")
    else:
        lines.append(f"대조한 불변식 {report.checked}건"
                     f"(confirmed {confirmed} · proposed {proposed}) / "
                     f"위반 {len(report.violations)}건 / 경고 {len(report.warnings)}건 — "
                     f"테스트 소스 {report.test_sources}건에서 태그 {len(report.tags)}건 관측")

    lines += report.notices
    if report.unreadable:
        lines.append(f"읽지 못한 테스트 소스 {len(report.unreadable)}건 — 이 파일들의 태그는 "
                     f"보지 못했습니다: {', '.join(report.unreadable)}")
    lines.append(LIMITATION_NOTE)
    return lines


def _payload(report) -> dict:
    confirmed = sum(1 for item in report.invariants if item.status == CONFIRMED)
    return {
        "violations": [asdict(v) for v in report.violations],
        "warnings": [asdict(w) for w in report.warnings],
        "notices": list(report.notices),
        "invariants": [asdict(item) for item in report.invariants],
        "tags": [asdict(tag) for tag in report.tags],
        "checked": report.checked,
        "confirmed": confirmed,
        "proposed": len(report.invariants) - confirmed,
        "test_sources": report.test_sources,
        "unreadable": list(report.unreadable),
        "blocked": report.blocked,
        # 한계는 리포트의 일부다 — 사람이 읽는 쪽에만 붙이면 JSON 소비자가 근거 없이 신뢰한다.
        "limitation": LIMITATION_NOTE,
    }


def _usage() -> int:
    print(f"사용법: python3 check_invariants.py <프로젝트 루트>/{DOMAIN_RELATIVE} "
          "[--context <이름>] [--json]", file=sys.stderr)
    return 2


def main(argv) -> int:
    as_json = "--json" in argv
    args = [arg for arg in argv if arg != "--json"]

    context = None
    if "--context" in args:
        index = args.index("--context")
        if index + 1 >= len(args) or args[index + 1].startswith("--"):
            return _usage()
        context = args[index + 1]
        args = args[:index] + args[index + 2:]

    if len(args) != 1 or any(arg.startswith("--") for arg in args):
        return _usage()

    path = args[0]
    try:
        report = check(path, context)
    except LayoutError as error:
        print(error, file=sys.stderr)
        return 2
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
    return 1 if (report.violations or report.blocked) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
