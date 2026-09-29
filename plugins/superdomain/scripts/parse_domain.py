"""DOMAIN.md 결정 템플릿의 단층 파서 — 도메인 선언의 유일한 해석기.

`DOMAIN.md`(도메인 결정의 SSOT)를 읽어 섹션·라벨·표를 `Domain` 데이터클래스 트리로
추출하고, 필수 결정 누락·비정규 값·상호 참조 무결성까지 한 번에 검사한다.
`check_imports.py`·`check_invariants.py`·`collect_signals.py`는 전부 이 모듈 하나만
import한다 — 해석이 두 곳에 있으면 두 결과가 갈라지기 때문이다.

구 플러그인의 파서는 3층(`parse_architecture` → `parse_style` → `resolve_rules`)이었다.
스타일·레이어·모듈 개념이 사라지면서 층을 나눌 이유도 사라졌으므로, 그 세 파일이 하던 일 중
**도메인에 속하는 것만** 이 파일 하나가 맡는다:

- 유지: 섹션·라벨·표 파싱 루프, 괄호 주석 제거, 라인 번호 부착, 생성 구역 마커 무시,
  이름 중복 검증, 관계 표 파싱, 템플릿 버전 마커 검증
- 신설: `- 패키지:` 라벨(컨텍스트의 실현 위치)과 그 정규화, 컨텍스트 격리 allow-list,
  퇴역 라벨 명시 거부, 컨텍스트 패키지 접두 겹침 검증

**침묵하지 않는다**가 이 파서의 규율이다. 구 파서는 모르는 라벨을 조용히 버렸지만, 구 템플릿의
라벨 6종은 여기서 오류가 된다 — 조용히 버리면 사용자는 자기가 쓴 결정이 강제되고 있다고 믿는다.

exit 규약: 0 = OK, 1 = 해석 오류, 2 = 사용법 오류 또는 배치 오류(옛 배치 포함 — layout.py).
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# 템플릿 마커. 개명이 이 상수 하나만 바꾸면 끝나도록 문자열 리터럴을 여기 한 번만 둔다
# — 마커를 찾는 정규식도 이 상수에서 만든다.
MARKER_TEMPLATE = "superdomain:template"
TEMPLATE_VERSION = "v1"

# 정규 값 집합
CLASSIFICATIONS = ("core", "supporting", "generic")
RELATION_KINDS = ("partnership", "customer-supplier", "conformist", "acl",
                  "open-host", "published-language")

# 구 템플릿(ARCHITECTURE.md)의 라벨. 도메인 SSOT에는 자리가 없으므로 만나면 거부한다.
RETIRED_LABELS = ("스타일", "모듈 구성", "규칙 예외", "이행", "프로파일", "아키텍처 테스트 위치")
NEW_TEMPLATE_DOC = "domain-template.md"


# 데이터클래스 — 이후 모든 스크립트가 소비하는 계약이다.
@dataclass
class Relation:
    """`### 관계` 표 한 행. `line`은 그 행의 1-기준 라인 번호다."""

    partner: str
    kind: str
    contract: str
    line: int


@dataclass
class Project:
    """`## 프로젝트: <이름>` 섹션."""

    name: str
    line: int                              # 섹션 헤딩 라인 번호(1-기준)
    path: str | None = None                # - 경로:
    base_package: str | None = None        # - 기본 패키지:
    label_lines: dict = field(default_factory=dict)   # 라벨 키 -> 그 라벨의 라인 번호


@dataclass
class Context:
    """`## 컨텍스트: <이름>` 섹션."""

    name: str
    line: int
    project: str | None = None             # - 프로젝트: (유일 프로젝트면 파서가 자동 귀속)
    classification: str | None = None      # - 분류: core|supporting|generic
    patterns: list = field(default_factory=list)     # - 패턴: 쉼표 목록
    packages: list = field(default_factory=list)     # - 패키지: 쉼표 목록 (명시 시)
    relations: list = field(default_factory=list)    # [Relation]
    label_lines: dict = field(default_factory=dict)


@dataclass
class ParseError:
    """line 0 = 문서 전체 수준 오류. message는 한국어."""

    line: int
    message: str


@dataclass
class LocatedError(ParseError, Exception):
    """ParseError + 출처 파일 경로. 여러 문서의 오류를 한 목록에 담기 위한 확장이다.

    구 `resolve_rules.py`에서 이관했고 생성 시그니처는 그대로다(`LocatedError(line, message, path)`).
    다만 `context_packages()`가 해석 불가를 **던져서** 알리므로 `Exception`도 함께 상속한다 —
    기록으로 쓸 때(`errors` 목록에 담을 때)의 모양은 이관 전과 같다.

    `except LocatedError as e: print(e)`가 사용자에게 튜플(`(3, '메시지', '')`)을 보여주지 않도록
    `__str__`을 준다. 출처 경로를 기본값으로 채우려면 `format_error(e, 기본경로)`를 쓴다.
    """

    path: str = ""

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.message}" if self.path \
            else f"{self.line}: {self.message}"


@dataclass
class Domain:
    """파싱 + 검증의 전체 산출. **호출자는 errors가 비었는지 먼저 확인해야 한다.**

    오류가 있어도 해석 가능한 부분은 채워 돌려준다 — 한 번의 실행에서 오류를 모두 보여주기
    위해서다(구 파서들과 같은 방침).
    """

    projects: list = field(default_factory=list)   # [Project] — 문서 순서
    contexts: list = field(default_factory=list)   # [Context] — 문서 순서
    errors: list = field(default_factory=list)     # [ParseError]


# 정규식
RE_PROJECT = re.compile(r"^##\s+프로젝트:\s*(.+?)\s*$")
RE_CONTEXT = re.compile(r"^##\s+컨텍스트:\s*(.+?)\s*$")
RE_H2 = re.compile(r"^##\s+")
RE_H3 = re.compile(r"^###\s+(.+?)\s*$")
RE_LABEL = re.compile(r"^-\s*(.+?)\s*:\s*(.+?)\s*$")
RE_TABLE = re.compile(r"^\|")
# 헤더 구분선. 칸마다 **대시 3개 이상**(앞뒤 정렬 콜론 허용)이어야 한다.
#
# 줄 끝 공백과 칸 사이 공백은 허용한다 — 마크다운이 허용하고(줄 끝 2칸은 hard line break 관례)
# 에디터가 트림하지도 않으며, 헤더 검사(`_header_cells`의 칸별 strip())가 이미 그만큼 관대하다.
#
# 반대로 "대시·콜론·공백이면 아무거나"로 넓히면 `| - | - | - |` 같은 **데이터 행**이 구분선으로
# 읽혀 그 행이 오류 없이 통째로 사라진다. 마크다운 표준은 칸당 대시 1개도 허용하지만, 이
# 저장소의 템플릿은 일관되게 `|---|---|---|`를 쓰므로 3개 이상으로 좁히는 편이 정합하다.
RE_TABLE_DIVIDER = re.compile(r"^\|(?:\s*:?-{3,}:?\s*\|)+\s*$")
RE_TEMPLATE_MARKER = re.compile(
    r"^\s*<!--\s*" + re.escape(MARKER_TEMPLATE) + r"\s+v(\d+)\s*-->\s*$")
# 코드 펜스(``` 또는 ~~~, 3개 이상, 들여쓰기 3칸까지). 여는 줄 뒤에는 정보 문자열(```mermaid)이
# 올 수 있고, 닫는 줄은 같은 문자로 여는 줄 이상의 길이여야 하며 뒤에 아무것도 없어야 한다.
# 펜스 안은 헤딩·라벨·표가 아니다 — 예시로 적은 선언이 진짜 선언을 덮어쓰지 않게 한다.
# 백틱 펜스의 정보 문자열에는 백틱이 올 수 없다(CommonMark) — "```inline``` 표기"는 인라인 코드로
# 시작하는 문장이지 펜스가 아니다. 물결 펜스에는 이 제한이 없다.
RE_FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})(.*)$")

# 패키지 세그먼트 하나의 문법(구 `resolve_rules.RE_PACKAGE_SEGMENT`에서 이관).
# 컨텍스트 이름과 `기본 패키지`가 그대로 패키지 자리에 들어가므로 둘 다 이 문법을 지켜야 한다.
RE_PACKAGE_SEGMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# 라벨 키(한국어) -> 필드명
PROJECT_LABELS = {
    "경로": "path",
    "기본 패키지": "base_package",
}
CONTEXT_LABELS = {
    "프로젝트": "project",
    "분류": "classification",
}
# "패턴"·"패키지"는 값이 쉼표 목록이라 별도 처리한다.

RELATIONS_HEADING = "관계"
RELATION_HEADER = ("상대", "유형", "계약")

# 필수 라벨(한국어 키 -> 필드명)
REQUIRED_PROJECT_LABELS = [("경로", "path"), ("기본 패키지", "base_package")]
REQUIRED_CONTEXT_LABELS = [("분류", "classification")]


def format_error(error, default_path) -> str:
    """오류 한 건을 `경로:라인: 메시지`로 조립한다(경로가 없으면 default_path).

    구 `resolve_rules.py`에서 이관했다. `parse_domain()`은 경로 없는 `ParseError`를 담으므로
    호출자가 문서 경로를 default_path로 넘긴다.
    """
    return f"{getattr(error, 'path', '') or default_path}:{error.line}: {error.message}"


def _strip_comment(value: str) -> str:
    """후행 '(...)' 주석 제거. 예: 'core (core | supporting)' -> 'core'"""
    return re.sub(r"\s*\([^)]*\)\s*$", "", value).strip()


def _header_cells(line: str) -> list:
    """표 헤더 행에서 칸 이름 목록을 추출한다(앞뒤 '|'가 만드는 빈 문자열 제거)."""
    cells = [c.strip() for c in line.split("|")]
    if cells and cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    return cells


def _split_row(line: str, ncols: int) -> list:
    """표 데이터 행을 헤더가 선언한 칸 수만큼만 잘라 추출한다(초과분은 버린다)."""
    parts = line.split("|")
    cells = [p.strip() for p in parts[1:1 + ncols]]
    while len(cells) < ncols:
        cells.append("")
    return cells


def _collect_table_block(lines: list, start: int) -> tuple:
    """start부터 연속된 '|'로 시작하는 라인 블록을 모은다. (block, 다음 인덱스)를 반환."""
    block = []
    j = start
    n = len(lines)
    while j < n and RE_TABLE.match(lines[j]):
        block.append(lines[j])
        j += 1
    return block, j


def _parse_packages(raw: str, line: int, errors: list) -> list:
    """`- 패키지:` 값을 쉼표로 갈라 `..` 접미 접두 패턴으로 정규화한다.

    모든 패키지는 접두 패턴이다 — `com.acme.claim..`은 "그 패키지와 그 아래 전부"를 뜻한다.
    표기가 흔들리면(`com.acme.claim` / `com.acme.claim.`) 소비자마다 다르게 매칭하므로 여기서
    한 모양으로 굳힌다. 빈 항목·중복 항목은 `ParseError` — 조용히 버리면 사용자가 적은 위치가
    강제되고 있다고 잘못 믿게 된다.
    """
    packages = []
    for item in raw.split(","):
        base = item.strip().rstrip(".")
        if not base:
            errors.append(ParseError(
                line,
                f"'패키지' 값에 빈 항목이 있습니다 (쉼표 사이가 비었거나 점만 있습니다): '{raw}'.",
            ))
            continue
        pattern = f"{base}.."
        if pattern in packages:
            errors.append(ParseError(
                line,
                f"'패키지' 값에 중복 항목 '{pattern}'이(가) 있습니다.",
            ))
            continue
        packages.append(pattern)
    return packages


def _retired_label_error(key: str, lineno: int) -> ParseError:
    """구 템플릿 라벨의 명시 거부. 조용히 버리면 사용자는 그 결정이 강제된다고 믿는다."""
    return ParseError(
        lineno,
        f"'{key}'은(는) 구 템플릿(ARCHITECTURE.md)의 라벨입니다 — DOMAIN.md에는 쓸 수 "
        f"없습니다 ({NEW_TEMPLATE_DOC} 참조).",
    )


def _apply_label(current_project, current_context, key: str, value: str,
                 lineno: int, errors: list) -> None:
    """'- 키: 값' 한 줄을 현재 활성 섹션에 반영한다.

    라벨을 반영할 때마다 `label_lines[key] = lineno`도 기록해, 검증이 오류를 (섹션 헤딩이
    아니라) 그 라벨 자신의 줄에 붙일 수 있게 한다.
    """
    if key in RETIRED_LABELS:
        errors.append(_retired_label_error(key, lineno))
        return

    # 같은 섹션에 같은 라벨이 두 줄이면 뒤가 앞을 조용히 덮어쓴다. 복수 값은 쉼표로 한 줄에
    # 적는 문법이라 줄을 나눠 적는 실수가 자연스럽고, 그때 첫 줄이 말없이 사라진다.
    section = current_project if current_project is not None else current_context
    if section is not None and key in section.label_lines:
        errors.append(ParseError(
            lineno,
            f"'{key}' 라벨이 이 섹션에 두 번 나타납니다 "
            f"(처음 등장: {section.label_lines[key]}번째 줄). 뒤의 줄이 앞의 값을 덮어쓰므로 "
            f"한 줄로 합치세요 — 값이 여럿이면 쉼표로 구분합니다.",
        ))
        return

    if current_project is not None:
        field_name = PROJECT_LABELS.get(key)
        if field_name:
            # `기본 패키지`도 패키지 접두이므로 `- 패키지:`와 같은 규칙으로 후행 점을 떨어낸다.
            # 비대칭으로 두면 'com.acme.'이 'com.acme..claim..'을 만들어 0건 매칭이 된다.
            resolved = _strip_comment(value)
            if field_name == "base_package":
                resolved = resolved.rstrip(".") or resolved
            setattr(current_project, field_name, resolved)
            current_project.label_lines[key] = lineno
        return

    if current_context is not None:
        if key in CONTEXT_LABELS:
            setattr(current_context, CONTEXT_LABELS[key], _strip_comment(value))
            current_context.label_lines[key] = lineno
        elif key == "패턴":
            stripped = _strip_comment(value)
            current_context.patterns = [p.strip() for p in stripped.split(",") if p.strip()]
            current_context.label_lines[key] = lineno
        elif key == "패키지":
            current_context.packages = _parse_packages(_strip_comment(value), lineno, errors)
            current_context.label_lines[key] = lineno
        # 그 외 모르는 키는 무시한다(퇴역 라벨만 위에서 거부했다).


def _apply_table(current_context, subheading, block: list, start_lineno: int,
                 errors: list) -> None:
    """표 한 블록(헤더+구분선+데이터행)을 해석해 반영한다. v1의 표는 `### 관계` 하나뿐이다.

    표의 모양을 먼저 검증한다. 값은 **칸 순서**로 읽으므로 헤더가 다르면 값이 어긋나 매핑되고,
    구분선이 없으면 첫 데이터 행이 구분선 자리에 놓여 통째로 사라진다 — 둘 다 오류 없이
    "선언했는데 강제되지 않는" 상태를 만든다.
    """
    if current_context is None or subheading != RELATIONS_HEADING:
        return

    header = tuple(_header_cells(block[0]))
    if header != RELATION_HEADER:
        errors.append(ParseError(
            start_lineno,
            f"'### {RELATIONS_HEADING}' 표의 헤더가 '| {' | '.join(header)} |'입니다 "
            f"(기대: '| {' | '.join(RELATION_HEADER)} |'). 값을 칸 순서대로 읽으므로 헤더가 "
            f"다르면 상대·유형·계약이 서로 어긋나 매핑됩니다.",
        ))
        return

    if len(block) < 2 or not RE_TABLE_DIVIDER.match(block[1]):
        errors.append(ParseError(
            start_lineno + 1,
            f"'### {RELATIONS_HEADING}' 표에 헤더 구분선('|---|---|---|')이 없습니다. "
            f"구분선 다음 줄부터가 데이터 행이므로, 없으면 첫 관계 행이 통째로 사라집니다.",
        ))
        return

    ncols = len(header)
    for offset, line in enumerate(block[2:]):
        cells = _split_row(line, ncols)
        lineno = start_lineno + 2 + offset
        relation = Relation(partner=cells[0], kind=cells[1], contract=cells[2], line=lineno)
        # '계약'은 자유 문자열이라 빈 값을 허용한다. '상대'·'유형'이 비면 그 행은 아무 쌍도
        # 열지 못하는데, 사용자는 열었다고 믿는다 — 격리 검사가 정당한 참조를 위반으로 낸다.
        for label, cell in (("상대", relation.partner), ("유형", relation.kind)):
            if not cell:
                errors.append(ParseError(
                    lineno,
                    f"컨텍스트 '{current_context.name}'의 관계 표 행에 '{label}' 칸이 비어 "
                    f"있습니다 — 이 행은 아무 쌍도 열지 않습니다.",
                ))
        current_context.relations.append(relation)


def _check_template_marker(lines: list, errors: list) -> None:
    """마커의 존재와 버전을 확인한다. 파서가 아는 것보다 높은 버전이면 거부한다.

    조용히 읽어 버리면 새 문법으로 쓴 결정을 구 파서가 절반만 이해한 채 "OK"를 찍는다 —
    가장 나쁜 실패 모드다.
    """
    supported = int(TEMPLATE_VERSION.lstrip("v"))
    malformed = None
    for index, line in enumerate(lines):
        match = RE_TEMPLATE_MARKER.match(line)
        if match:
            version = int(match.group(1))
            if version > supported:
                errors.append(ParseError(
                    index + 1,
                    f"템플릿 버전 'v{version}'은(는) 이 파서가 아는 최신 버전 "
                    f"'{TEMPLATE_VERSION}'보다 높습니다. 플러그인을 최신으로 올린 뒤 다시 "
                    f"실행하세요.",
                ))
            return
        if malformed is None and MARKER_TEMPLATE in line:
            malformed = (index + 1, line.strip())

    # 마커가 '있는데 깨진 것'과 '아예 없는 것'은 고칠 자리가 다르다 — 뭉뚱그리면 사용자가
    # 이미 적어 둔 줄을 놔둔 채 새 줄을 하나 더 넣는다.
    if malformed is not None:
        errors.append(ParseError(
            malformed[0],
            f"템플릿 마커의 형식이 올바르지 않습니다 — '{malformed[1]}' "
            f"(기대: '<!-- {MARKER_TEMPLATE} {TEMPLATE_VERSION} -->'). 버전 표기가 빠졌거나 "
            f"줄에 다른 글자가 섞여 있습니다.",
        ))
        return

    errors.append(ParseError(
        0,
        f"템플릿 마커(<!-- {MARKER_TEMPLATE} {TEMPLATE_VERSION} -->)가 없습니다. "
        f"결정 템플릿({NEW_TEMPLATE_DOC})에서 문서를 생성했는지 확인하세요.",
    ))


def _parse_document(text: str) -> Domain:
    """라인 기반 상태 머신으로 문서를 파싱해 Domain을 만든다.

    **템플릿 밖의 서술은 파싱 결과를 바꾸지 않는다**(domain-template §1). 그 약속을 지키는 규칙이
    둘이다 — 라벨은 **섹션 머리**(`##` 헤딩 다음부터 그 섹션의 첫 `###` 전까지)에서만 읽고,
    **코드 펜스 안**은 어디서든 헤딩·라벨·표로 해석하지 않는다. `### 근거` 아래에 예시로 적은
    `- 패키지:`가 진짜 선언을 덮어쓰던 결함(2026-09-26 재현)을 이 둘이 막는다.

    생성 구역 마커(`<!-- ...:generated:... -->` 쌍)는 라벨도 표도 헤딩도 아니므로 다른 주석과
    똑같이 무시된다 — 스킬이 그 사이를 통째로 갈아 끼워도 파싱 결과는 변하지 않는다.
    """
    lines = text.split("\n")
    domain = Domain()
    _check_template_marker(lines, domain.errors)

    current_project = None
    current_context = None
    current_subheading = None
    fence = None          # (문자, 길이, 여는 줄 번호) — 펜스 안에 있는 동안만 채워진다

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        lineno = i + 1

        m_fence = RE_FENCE.match(line)
        if fence is not None:
            if (m_fence and m_fence.group(1)[0] == fence[0]
                    and len(m_fence.group(1)) >= fence[1] and not m_fence.group(2).strip()):
                fence = None
            i += 1
            continue
        if m_fence and not (m_fence.group(1)[0] == "`" and "`" in m_fence.group(2)):
            fence = (m_fence.group(1)[0], len(m_fence.group(1)), lineno)
            i += 1
            continue

        m_project = RE_PROJECT.match(line)
        if m_project:
            current_project = Project(name=m_project.group(1), line=lineno)
            domain.projects.append(current_project)
            current_context = None
            current_subheading = None
            i += 1
            continue

        m_context = RE_CONTEXT.match(line)
        if m_context:
            current_context = Context(name=m_context.group(1), line=lineno)
            domain.contexts.append(current_context)
            current_project = None
            current_subheading = None
            i += 1
            continue

        if RE_H2.match(line):
            # 알려지지 않은 '##' 헤딩(예: '## 컨텍스트 맵') — 섹션 없음(무시 모드)으로 전환.
            current_project = None
            current_context = None
            current_subheading = None
            i += 1
            continue

        m_h3 = RE_H3.match(line)
        if m_h3:
            current_subheading = m_h3.group(1)
            i += 1
            continue

        m_label = RE_LABEL.match(line)
        if m_label and current_subheading is None:
            if current_project is not None or current_context is not None:
                _apply_label(current_project, current_context,
                             m_label.group(1), m_label.group(2), lineno, domain.errors)
            elif m_label.group(1) in RETIRED_LABELS:
                # 문서 머리·모르는 '##' 섹션에는 라벨을 적용할 대상이 없다. 그래도 구 템플릿
                # 라벨은 여기서 거부한다 — 옛 문서의 머리에 남은 '- 스타일:'이 조용히 사라지면
                # 사용자는 그 결정이 아직 강제된다고 믿는다.
                domain.errors.append(_retired_label_error(m_label.group(1), lineno))
            i += 1
            continue

        if current_context is not None and RE_TABLE.match(line):
            block, next_i = _collect_table_block(lines, i)
            _apply_table(current_context, current_subheading, block, lineno, domain.errors)
            i = next_i
            continue

        i += 1

    if fence is not None:
        domain.errors.append(ParseError(
            fence[2],
            "닫히지 않은 코드 펜스입니다 — 이 줄 아래의 헤딩·라벨·표가 전부 무시됩니다. "
            "같은 문자로 된 닫는 펜스를 넣으세요.",
        ))

    if len(domain.projects) == 1:
        only_name = domain.projects[0].name
        for context in domain.contexts:
            if not context.project:
                context.project = only_name

    return domain


def _check_duplicate_names(items: list, kind: str, errors: list) -> None:
    """섹션 목록(프로젝트 또는 컨텍스트)에서 이름이 중복되는 항목을 찾아 보고한다."""
    first_seen = {}
    for item in items:
        if item.name in first_seen:
            errors.append(ParseError(
                item.line,
                f"{kind} 이름 '{item.name}'이(가) 중복되었습니다 "
                f"(처음 등장: {first_seen[item.name]}번째 줄).",
            ))
        else:
            first_seen[item.name] = item.line


def _is_package(value: str) -> bool:
    """점으로 이은 각 조각이 전부 유효한 패키지 세그먼트인가."""
    return all(RE_PACKAGE_SEGMENT.match(segment) for segment in value.split("."))


def _validate_project(project: Project, errors: list) -> None:
    for label, field_name in REQUIRED_PROJECT_LABELS:
        if not getattr(project, field_name):
            errors.append(ParseError(
                project.line,
                f"프로젝트 '{project.name}': 필수 라벨 '{label}'이(가) 없습니다.",
            ))

    if project.base_package and not _is_package(project.base_package):
        errors.append(ParseError(
            project.label_lines.get("기본 패키지", project.line),
            f"프로젝트 '{project.name}'의 기본 패키지 '{project.base_package}'이(가) 유효한 "
            f"패키지가 아닙니다. 이 값은 컨텍스트의 기본 규약 "
            f"('{{기본 패키지}}.{{컨텍스트}}..')의 앞자리에 그대로 들어가므로, 성립하지 않는 "
            f"패턴이 만들어지고 격리 검사가 0건을 매칭한 채 통과합니다 — 각 조각을 "
            f"영문자/밑줄로 시작하는 패키지 세그먼트로 적으세요.",
        ))


def _check_context_segment(context: Context, errors: list) -> None:
    """컨텍스트 이름이 유효한 패키지 세그먼트인지 확인한다(구 `resolve_rules._check_context_segment`).

    명시 `- 패키지:`가 있으면 이름이 패턴에 전혀 나타나지 않으므로 검사하지 않는다 — 구
    `_context_is_segment`가 "패키지 규약 표에 `{컨텍스트}` 치환이 없으면 검사하지 않는다"고
    판정한 것과 같은 논리다.

    `order-mgmt` 같은 이름은 선언 단계에서 멀쩡해 보이지만 기본 규약이 만드는
    `com.acme.order-mgmt..`는 어떤 소스에도 매칭되지 않는다. 그러면 그 컨텍스트의 격리 규칙은
    0건을 검사한 채 조용히 통과한다 — 위반이 없는 것과 구분되지 않는 가장 나쁜 상태다.
    """
    if context.packages or RE_PACKAGE_SEGMENT.match(context.name):
        return
    errors.append(ParseError(
        context.line,
        f"컨텍스트 이름 '{context.name}'이(가) 유효한 패키지 세그먼트가 아닙니다. "
        f"'- 패키지:'가 없으면 기본 규약('{{기본 패키지}}.{{컨텍스트}}..')의 세그먼트 자리에 이 "
        f"이름이 그대로 들어가므로, 이 컨텍스트의 패턴은 성립하지 않는 패키지가 되고 격리 검사가 "
        f"0건을 매칭한 채 통과합니다 — 이름을 패키지 세그먼트로 쓸 수 있게 바꾸거나 "
        f"'- 패키지:'로 실제 패키지를 명시하세요.",
    ))


def _validate_context(context: Context, project_names: set, context_names: set,
                      multiple_projects: bool, errors: list) -> None:
    _check_context_segment(context, errors)

    for label, field_name in REQUIRED_CONTEXT_LABELS:
        if not getattr(context, field_name):
            errors.append(ParseError(
                context.line,
                f"컨텍스트 '{context.name}': 필수 라벨 '{label}'이(가) 없습니다.",
            ))

    if context.classification and context.classification not in CLASSIFICATIONS:
        errors.append(ParseError(
            context.label_lines.get("분류", context.line),
            f"컨텍스트 '{context.name}'의 분류 값 '{context.classification}'이(가) 올바르지 "
            f"않습니다 (허용값: {sorted(CLASSIFICATIONS)}).",
        ))

    if context.project:
        if context.project not in project_names:
            errors.append(ParseError(
                context.label_lines.get("프로젝트", context.line),
                f"컨텍스트 '{context.name}'이(가) 참조하는 프로젝트 '{context.project}'를 "
                f"찾을 수 없습니다.",
            ))
    elif multiple_projects:
        errors.append(ParseError(
            context.line,
            f"컨텍스트 '{context.name}': 프로젝트가 여러 개이므로 '- 프로젝트: <이름>' 라벨로 "
            f"속한 프로젝트를 지정해야 합니다.",
        ))

    for relation in context.relations:
        if relation.kind and relation.kind not in RELATION_KINDS:
            errors.append(ParseError(
                relation.line,
                f"컨텍스트 '{context.name}'의 관계 유형 값 '{relation.kind}'이(가) 올바르지 "
                f"않습니다 (허용값: {sorted(RELATION_KINDS)}).",
            ))
        if relation.partner and relation.partner not in context_names:
            errors.append(ParseError(
                relation.line,
                f"컨텍스트 '{context.name}'의 관계 상대 '{relation.partner}'을(를) 찾을 수 "
                f"없습니다 (선언된 컨텍스트: {', '.join(sorted(context_names)) or '없음'}).",
            ))


def _covers(outer: str, inner: str) -> bool:
    """접두 패턴 outer가 inner를 덮는가. 비교는 패키지 **세그먼트 경계**에서 한다.

    문자열 접두로만 보면 `com.acme.claim..`이 `com.acme.claiming..`을 덮는 것으로 읽혀,
    형제 컨텍스트가 겹침 오류로 잘못 걸린다.
    """
    a, b = outer[:-2], inner[:-2]
    return a == b or b.startswith(f"{a}.")


def _safe_packages(domain: Domain, context: Context) -> list:
    """검증용 패키지 조회 — 정할 수 없으면 빈 목록(그 사유는 이미 다른 오류로 보고되었다)."""
    try:
        return context_packages(domain, context)
    except LocatedError:
        return []


def _check_package_overlap(domain: Domain, errors: list) -> None:
    """컨텍스트 패키지가 서로 접두로 겹치면 오류 — 소스의 귀속이 모호해진다.

    `check_imports.py`는 소스의 `package` 선언을 접두 최장 일치로 컨텍스트에 귀속시킨다.
    한 컨텍스트의 패턴이 다른 컨텍스트의 패턴 안쪽에 있으면, 그 사이의 코드가 어느 쪽 소유인지
    문서만으로는 정해지지 않는다. 격리 판정이 문서가 아니라 매칭 순서에 좌우되게 두지 않는다.
    """
    resolved = [(context, _safe_packages(domain, context)) for context in domain.contexts]
    for index, (first, first_packages) in enumerate(resolved):
        for second, second_packages in resolved[index + 1:]:
            for outer in first_packages:
                for inner in second_packages:
                    if not (_covers(outer, inner) or _covers(inner, outer)):
                        continue
                    errors.append(ParseError(
                        second.label_lines.get("패키지", second.line),
                        f"컨텍스트 '{second.name}'의 패키지 '{inner}'와 컨텍스트 "
                        f"'{first.name}'의 패키지 '{outer}'가 겹칩니다(한쪽이 다른 쪽의 접두) "
                        f"— 그 아래 코드가 어느 컨텍스트 소유인지 정해지지 않습니다.",
                    ))


def validate(domain: Domain) -> list:
    """Domain을 검사해 [ParseError] 목록을 반환한다(문제 없으면 빈 리스트)."""
    errors = []

    if not domain.projects:
        errors.append(ParseError(
            0,
            "프로젝트 섹션이 없습니다. '## 프로젝트: <이름>' 섹션을 최소 1개 작성하세요.",
        ))

    _check_duplicate_names(domain.projects, "프로젝트", errors)
    _check_duplicate_names(domain.contexts, "컨텍스트", errors)

    project_names = {project.name for project in domain.projects}
    context_names = {context.name for context in domain.contexts}
    multiple_projects = len(domain.projects) > 1

    for project in domain.projects:
        _validate_project(project, errors)

    for context in domain.contexts:
        _validate_context(context, project_names, context_names, multiple_projects, errors)

    _check_package_overlap(domain, errors)

    return errors


def context_packages(domain: Domain, context: Context) -> list:
    """컨텍스트가 실현되는 패키지 접두 패턴 목록.

    명시 `- 패키지:`가 있으면 그 목록 그대로(복수 위치 컨텍스트가 있으므로 순서를 보존한다),
    없으면 귀속 프로젝트의 `기본 패키지`로 규약 기본값 `[f"{base}.{name}.."]`을 만든다.
    모든 항목은 `..` 접미로 정규화된 접두 패턴이다.

    기본값을 만들 수 없으면(귀속 프로젝트가 없거나 그 프로젝트에 `기본 패키지`가 없으면)
    `LocatedError`를 던진다 — 빈 목록을 돌려주면 그 컨텍스트가 아무 소스도 갖지 않는 것으로
    보여 격리 검사가 0건을 검사한 채 통과한다.
    """
    if context.packages:
        return list(context.packages)

    project = next((p for p in domain.projects if p.name == context.project), None)
    if project is None or not project.base_package:
        raise LocatedError(
            context.line,
            f"컨텍스트 '{context.name}'의 패키지를 정할 수 없습니다 — '- 패키지:' 라벨이 없고 "
            f"귀속 프로젝트('{context.project or '미지정'}')의 '기본 패키지'도 없습니다.",
        )
    return [f"{project.base_package}.{context.name}.."]


def isolation_allowlist(domain: Domain) -> dict:
    """컨텍스트명 → 관계 표가 연 상대 컨텍스트명 집합(frozenset).

    **허용 단위는 쌍이고 방향을 구분하지 않는다.** 관계를 한쪽 컨텍스트에만 적어도 양쪽이
    열린다. 구 `resolve_rules._derive_context_isolation`·`_relation_partners`의 의미를 그대로
    옮긴 것이다("v1의 허용 단위는 쌍이고 방향을 구분하지 않는다") — 관계는 두 컨텍스트가 맺는
    하나의 사실이지 한쪽의 속성이 아니고, 방향을 구분하면 같은 사실을 두 줄로 적게 만든 뒤
    한 줄만 적힌 문서를 조용히 반쪽만 강제하게 된다.

    **키는 선언된 컨텍스트뿐이다.** 관계가 없어도 빈 frozenset으로 반드시 키를 갖고, 선언되지
    않은 상대(오타 등 — validate가 이미 오류로 보고했다)는 키를 만들지 않는다. 유령 키를 만들면
    소비자가 그것을 컨텍스트 목록으로 착각한다.
    """
    declared = {context.name for context in domain.contexts}
    partners = {name: set() for name in declared}
    for context in domain.contexts:
        for relation in context.relations:
            if not relation.partner or relation.partner not in declared:
                continue
            partners[context.name].add(relation.partner)
            partners[relation.partner].add(context.name)
    return {name: frozenset(values) for name, values in partners.items()}


def parse_domain(path) -> Domain:
    """DOMAIN.md 한 건을 파싱하고 검증해 Domain을 만든다.

    **호출자는 `domain.errors`가 비었는지 먼저 확인해야 한다.** 오류가 있어도 해석 가능한
    부분은 채워 돌려준다 — 한 번의 실행에서 오류를 모두 보여주기 위해서다.
    """
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError:
        return Domain(errors=[ParseError(
            0,
            f"'{path.name}' 파일을 읽을 수 없습니다. 경로를 확인하거나 "
            f"/superdomain:init으로 초기화하세요.",
        )])
    except UnicodeDecodeError as error:
        # 파일은 있다 — 초기화 안내는 틀린 처방이다. 트레이스백으로 죽으면 exit 1이 되어
        # check_imports·check_invariants에서 '위반'과 구별되지 않으므로 해석 오류로 돌려준다.
        return Domain(errors=[ParseError(
            error.object[:error.start].count(b"\n") + 1,
            f"'{path.name}' 파일을 UTF-8로 읽을 수 없습니다 — 다른 인코딩(cp949 등)으로 "
            f"저장된 것 같습니다. UTF-8로 다시 저장하세요.",
        )])

    domain = _parse_document(text)
    domain.errors.extend(validate(domain))
    return domain


def main(argv) -> int:
    # 배치 모듈은 CLI에서만 읽는다 — layout이 이 모듈의 마커 상수를 import하므로 모듈 수준에서
    # 서로 import하면 순환이 생긴다. 라이브러리 함수 parse_domain()은 배치를 모른다.
    from layout import DOMAIN_RELATIVE, LayoutError, from_domain_path

    if len(argv) != 1 or argv[0].startswith("-"):
        print(f"사용법: python3 parse_domain.py <프로젝트 루트>/{DOMAIN_RELATIVE}", file=sys.stderr)
        return 2

    path = argv[0]
    try:
        from_domain_path(path)
    except LayoutError as error:
        print(error, file=sys.stderr)
        return 2

    domain = parse_domain(path)
    if domain.errors:
        for error in sorted(domain.errors, key=lambda e: e.line):
            print(format_error(error, path), file=sys.stderr)
        return 1

    print(f"OK: 프로젝트 {len(domain.projects)}, 컨텍스트 {len(domain.contexts)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
