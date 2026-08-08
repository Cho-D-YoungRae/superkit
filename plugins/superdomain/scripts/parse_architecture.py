"""ARCHITECTURE.md 결정 템플릿의 구조 파싱 코어.

이 모듈은 `ARCHITECTURE.md`(결정 템플릿 문서)를 읽어 섹션·라벨·표를
`Architecture` 데이터클래스 트리로 추출하는 유일한 결정론적 리더다.
다른 모든 스크립트는 이 모듈의 `parse_architecture()`를 import해서 사용한다.

이 파일은 "구조 추출"만 담당한다(Task 2 범위). 필수 결정 누락·비정규
값 검증(Task 3)과 실현 정규화(Task 4)는 이후 별도 함수로 추가되며,
이 파일의 파싱 루프 자체는 그대로 재사용된다.
"""

import re
from dataclasses import dataclass, field

# 정규 값 집합 (Task 3의 검증이 참조한다. 이 태스크에서는 파싱에 사용하지 않는다.)
CLASSIFICATIONS = {"core", "supporting", "generic"}
MODULE_LAYOUTS = {"multi-module", "single-module", "app-embedded"}
SHARED_ROLES = {"shared-kernel", "infrastructure", "client", "support"}
RELATION_TYPES = {"partnership", "customer-supplier", "conformist", "acl", "open-host", "published-language"}
PRESET_STYLES = {"layered-simple", "layered-domain", "hexagonal", "clean"}
KNOWN_PROFILES = {"kotlin-spring", "java-spring"}
TEMPLATE_MARKER = "<!-- superarchitect:template v1 -->"


# 데이터클래스 (섹션·라벨·표 추출 결과의 계약 — 이후 모든 태스크가 이 형태를 소비한다)
@dataclass
class Application:
    name: str
    module_path: str
    contexts: list  # 컨텍스트명 목록 또는 ["all"]

@dataclass
class SharedModule:
    name: str
    path: str
    role: str

@dataclass
class Project:
    name: str
    line: int                 # 섹션 헤딩 라인 번호(1-기준)
    path: str = ""
    profile: str = ""
    base_package: str = ""
    test_location: str = ""
    applications: list = field(default_factory=list)    # [Application]
    shared_modules: list = field(default_factory=list)  # [SharedModule]
    package_conventions: dict = field(default_factory=dict)  # 레이어명 -> 패턴 문자열

@dataclass
class Module:
    name: str
    path: str
    layer: str

@dataclass
class Relation:
    target: str
    type: str
    contract: str

@dataclass
class RuleException:
    rule_id: str   # 예: "hex.ports-owned-inside" ("-" 접두 제거 후)
    adr: str       # 예: "ADR-0002" (없으면 "")

@dataclass
class Context:
    name: str
    line: int
    project: str = ""         # 프로젝트 1개면 파서가 자동 귀속
    classification: str = ""
    style: str = ""
    module_layout: str = ""
    patterns: list = field(default_factory=list)         # [str]
    rule_exceptions: list = field(default_factory=list)  # [RuleException]
    transition: tuple = ()    # (출발, 목표) — 파싱 성공(→ 존재) 시에만
    transition_raw: str = "" # 이행 라벨이 존재하면 원문 값을 그대로 보존(성공/실패 무관).
                              # ""=라벨 없음, 값 있음+transition=()는 형식 오류(Task 3 판정)
    modules: list = field(default_factory=list)          # [Module]
    relations: list = field(default_factory=list)        # [Relation]

@dataclass
class ParseError:
    line: int      # 0 = 문서 전체 수준 오류
    message: str   # 한국어

@dataclass
class Architecture:
    projects: list = field(default_factory=list)
    contexts: list = field(default_factory=list)
    has_template_marker: bool = False


# 정규식
RE_PROJECT = re.compile(r"^##\s+프로젝트:\s*(.+?)\s*$")
RE_CONTEXT = re.compile(r"^##\s+컨텍스트:\s*(.+?)\s*$")
RE_H2      = re.compile(r"^##\s+")
RE_H3      = re.compile(r"^###\s+(.+?)\s*$")
RE_LABEL   = re.compile(r"^-\s*(.+?)\s*:\s*(.+?)\s*$")
RE_TABLE   = re.compile(r"^\|")

RE_RULE_EXCEPTION = re.compile(r"^-?\s*([A-Za-z0-9_.\-]+)\s*(?:\((ADR-\d{4})\))?$")

# 라벨 키(한국어) -> 필드명 매핑
PROJECT_LABELS = {
    "경로": "path",
    "프로파일": "profile",
    "기본 패키지": "base_package",
    "아키텍처 테스트 위치": "test_location",
}
CONTEXT_LABELS = {
    "프로젝트": "project",
    "분류": "classification",
    "스타일": "style",
    "모듈 구성": "module_layout",
}
# "패턴", "규칙 예외", "이행"은 값 형태가 단순 문자열이 아니라 별도 처리한다.

# 프로젝트 섹션의 알려진 표 소제목
APPLICATIONS_HEADING = "애플리케이션"
SHARED_MODULES_HEADING = "공용 모듈"
PACKAGE_CONVENTIONS_HEADING = "패키지 규약"
# 컨텍스트 섹션의 알려진 표 소제목
RELATIONS_HEADING = "관계"


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
    """표 데이터 행을 헤더가 선언한 칸 수만큼만 잘라 추출한다.

    화살표(←) 설명 주석이 붙은 행처럼 '|' 조각이 헤더보다 많이 나오면
    초과분은 버린다(스펙 예시의 presentation 행 참고).
    """
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


def _apply_label(current_project, current_context, key: str, value: str) -> None:
    """'- 키: 값' 한 줄을 현재 활성 섹션에 반영한다. 알려진 키만 처리한다."""
    if current_project is not None:
        field_name = PROJECT_LABELS.get(key)
        if field_name:
            setattr(current_project, field_name, _strip_comment(value))
        return

    if current_context is not None:
        if key in CONTEXT_LABELS:
            setattr(current_context, CONTEXT_LABELS[key], _strip_comment(value))
        elif key == "패턴":
            stripped = _strip_comment(value)
            current_context.patterns = [p.strip() for p in stripped.split(",") if p.strip()]
        elif key == "규칙 예외":
            # 각 항목의 '(...)'는 ADR 참조이므로 _strip_comment를 적용하지 않는다.
            exceptions = []
            for item in value.split(","):
                item = item.strip()
                if not item:
                    continue
                m = RE_RULE_EXCEPTION.match(item)
                if m:
                    exceptions.append(RuleException(rule_id=m.group(1), adr=m.group(2) or ""))
                else:
                    # 정규식에 맞지 않아도 항목을 버리지 않는다 — 앞의 '-'만 제거한
                    # 원문을 rule_id로 보존해 Task 3이 형식 오류로 판정할 수 있게 한다.
                    exceptions.append(RuleException(rule_id=re.sub(r"^-\s*", "", item), adr=""))
            current_context.rule_exceptions = exceptions
        elif key == "이행":
            stripped = _strip_comment(value)
            current_context.transition_raw = stripped
            if "→" in stripped:
                start, target = stripped.split("→", 1)
                current_context.transition = (start.strip(), target.strip())
            # '→'가 없으면 transition은 기본값 ()로 남는다. transition_raw는 채워져
            # 있으므로 "라벨 없음"과 "형식 오류"를 Task 3이 구분할 수 있다.
        # 그 외 모르는 키는 무시한다.


def _apply_table(current_project, current_context, subheading: str, block: list,
                  module_table_seen: bool) -> bool:
    """표 한 블록(헤더+구분선+데이터행)을 위치 규칙에 따라 해석해 반영하고,
    갱신된 module_table_seen 플래그를 반환한다."""
    if len(block) < 2:
        return module_table_seen

    header = _header_cells(block[0])
    ncols = len(header)
    data_lines = block[2:]
    rows = [_split_row(line, ncols) for line in data_lines]

    if current_project is not None:
        if subheading == APPLICATIONS_HEADING:
            for cells in rows:
                name = cells[0] if ncols > 0 else ""
                module_path = cells[1] if ncols > 1 else ""
                contexts_raw = cells[2] if ncols > 2 else ""
                contexts = [c.strip() for c in contexts_raw.split(",") if c.strip()]
                current_project.applications.append(Application(name=name, module_path=module_path, contexts=contexts))
        elif subheading == SHARED_MODULES_HEADING:
            for cells in rows:
                name = cells[0] if ncols > 0 else ""
                path = cells[1] if ncols > 1 else ""
                role = cells[2] if ncols > 2 else ""
                current_project.shared_modules.append(SharedModule(name=name, path=path, role=role))
        elif subheading == PACKAGE_CONVENTIONS_HEADING:
            for cells in rows:
                layer = cells[0] if ncols > 0 else ""
                pattern = cells[1] if ncols > 1 else ""
                current_project.package_conventions[layer] = pattern
        # 그 외 소제목의 표는 무시한다.
        return module_table_seen

    if current_context is not None:
        if subheading is None:
            if not module_table_seen:
                for cells in rows:
                    name = cells[0] if ncols > 0 else ""
                    path = cells[1] if ncols > 1 else ""
                    layer = cells[2] if ncols > 2 else ""
                    current_context.modules.append(Module(name=name, path=path, layer=layer))
                module_table_seen = True
            return module_table_seen
        if subheading == RELATIONS_HEADING:
            for cells in rows:
                target = cells[0] if ncols > 0 else ""
                rtype = cells[1] if ncols > 1 else ""
                contract = cells[2] if ncols > 2 else ""
                current_context.relations.append(Relation(target=target, type=rtype, contract=contract))
            return module_table_seen
        # 그 외 소제목의 표는 무시한다.
        return module_table_seen

    return module_table_seen


def _parse_document(text: str) -> Architecture:
    """라인 기반 상태 머신으로 문서를 파싱해 Architecture를 만든다(검증 없음)."""
    lines = text.split("\n")
    architecture = Architecture(has_template_marker=any(TEMPLATE_MARKER in line for line in lines))

    current_project = None
    current_context = None
    current_subheading = None  # None = 아직 '###' 소제목 없음(섹션 최상단)
    module_table_seen = False  # 현재 컨텍스트에서 소제목 없는 첫 표를 이미 소비했는가

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        lineno = i + 1

        m_project = RE_PROJECT.match(line)
        if m_project:
            current_project = Project(name=m_project.group(1), line=lineno)
            architecture.projects.append(current_project)
            current_context = None
            current_subheading = None
            module_table_seen = False
            i += 1
            continue

        m_context = RE_CONTEXT.match(line)
        if m_context:
            current_context = Context(name=m_context.group(1), line=lineno)
            architecture.contexts.append(current_context)
            current_project = None
            current_subheading = None
            module_table_seen = False
            i += 1
            continue

        if RE_H2.match(line):
            # 알려지지 않은 '##' 헤딩 — 섹션 없음(무시 모드)으로 전환.
            current_project = None
            current_context = None
            current_subheading = None
            module_table_seen = False
            i += 1
            continue

        m_h3 = RE_H3.match(line)
        if m_h3:
            current_subheading = m_h3.group(1)
            i += 1
            continue

        if current_project is not None or current_context is not None:
            m_label = RE_LABEL.match(line)
            if m_label:
                _apply_label(current_project, current_context, m_label.group(1), m_label.group(2))
                i += 1
                continue

            if RE_TABLE.match(line):
                block, next_i = _collect_table_block(lines, i)
                module_table_seen = _apply_table(
                    current_project, current_context, current_subheading, block, module_table_seen
                )
                i = next_i
                continue

        i += 1

    if len(architecture.projects) == 1:
        only_name = architecture.projects[0].name
        for context in architecture.contexts:
            if not context.project:
                context.project = only_name

    return architecture


def parse_architecture(text: str) -> tuple:
    """(Architecture, [ParseError])를 반환.

    이 함수는 구조 추출만 수행한다 — 오류 목록은 항상 빈 리스트([])다.
    필수 결정 누락·비정규 값 검증(Task 3)은 이후 validate(architecture)
    호출을 여기에 추가해 채워진다.
    """
    architecture = _parse_document(text)
    errors = []  # Task 3에서 validate(architecture)를 호출해 여기에 채운다.
    return architecture, errors
