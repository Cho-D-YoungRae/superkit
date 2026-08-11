"""ARCHITECTURE.md 결정 템플릿의 구조 파싱 코어.

이 모듈은 `ARCHITECTURE.md`(결정 템플릿 문서)를 읽어 섹션·라벨·표를
`Architecture` 데이터클래스 트리로 추출하는 유일한 결정론적 리더다.
다른 모든 스크립트는 이 모듈의 `parse_architecture()`를 import해서 사용한다.

구조 추출(Task 2)에 이어 필수 결정 누락·비정규 값 검증(`validate()`, Task 3)과
실현(multi-module/single-module/app-embedded) 정규화(`normalize()`, Task 4)까지
이 파일 하나가 담당한다.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

# 정규 값 집합 (Task 3의 검증이 참조한다. 이 태스크에서는 파싱에 사용하지 않는다.)
CLASSIFICATIONS = {"core", "supporting", "generic"}
MODULE_LAYOUTS = {"multi-module", "single-module", "app-embedded"}
SHARED_ROLES = {"shared-kernel", "infrastructure", "client", "support"}
RELATION_TYPES = {"partnership", "customer-supplier", "conformist", "acl", "open-host", "published-language"}
PRESET_STYLES = {"layered-simple", "layered-domain", "hexagonal", "clean"}
KNOWN_PROFILES = {"kotlin-spring", "java-spring"}   # profiles/를 읽을 수 없을 때의 폴백
TEMPLATE_MARKER = "<!-- superarchitect:template v1 -->"

PLUGIN_ROOT = Path(__file__).resolve().parent.parent


def _known_profiles() -> set:
    """`프로파일`의 정규 값 = 플러그인 루트 `profiles/`의 하위 디렉터리 이름(§4 라벨 사전).

    정본이 "디렉터리 목록"이라고 정한 것을 상수로 굳혀 두면 프로파일이 추가될 때 파서가
    새 값을 거부한다. 목록을 읽지 못하거나(설치가 깨졌거나 다른 곳에서 import된 경우)
    비어 있으면 `KNOWN_PROFILES`로 폴백해, 검증이 모든 프로파일을 거부하는 상태로
    무너지지 않게 한다.
    """
    try:
        names = {entry.name for entry in (PLUGIN_ROOT / "profiles").iterdir()
                 if entry.is_dir() and not entry.name.startswith(".")}
    except OSError:
        return set(KNOWN_PROFILES)
    return names or set(KNOWN_PROFILES)


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
    label_lines: dict = field(default_factory=dict)  # 라벨 키(한국어) -> 그 라벨이 등장한 1-기준 라인 번호

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
    relations: list = field(default_factory=list)         # [Relation]
    label_lines: dict = field(default_factory=dict)  # 라벨 키(한국어) -> 그 라벨이 등장한 1-기준 라인 번호

@dataclass
class ParseError:
    line: int      # 0 = 문서 전체 수준 오류
    message: str   # 한국어

@dataclass
class Architecture:
    projects: list = field(default_factory=list)
    contexts: list = field(default_factory=list)
    has_template_marker: bool = False

@dataclass(frozen=True)
class NormalizedPattern:
    project: str
    context: str   # "*" = 컨텍스트로 분할되지 않는 레이어(패키지 규약에 {컨텍스트} 없음)
    layer: str     # 모듈 표의 레이어 값 그대로("all" 가능)
    pattern: str   # 예: "com.acme.claim.domain.." (항상 ".." 접미)


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


def _apply_label(current_project, current_context, key: str, value: str, lineno: int) -> None:
    """'- 키: 값' 한 줄을 현재 활성 섹션에 반영한다. 알려진 키만 처리한다.

    라벨을 반영할 때마다 `label_lines[key] = lineno`도 함께 기록한다. 이는 Task 3의
    validate()가 라벨별 오류를 (섹션 헤딩 라인이 아니라) 그 라벨 자신의 라인에 붙일 수
    있게 하는 additive 필드로, 값이 여러 줄에 걸쳐 반복 등장하면 마지막 등장 라인이
    남는다(현재 템플릿 문법상 같은 키가 한 섹션에 두 번 나타나는 경우는 없다).
    """
    if current_project is not None:
        field_name = PROJECT_LABELS.get(key)
        if field_name:
            setattr(current_project, field_name, _strip_comment(value))
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
            current_context.label_lines[key] = lineno
        elif key == "이행":
            stripped = _strip_comment(value)
            current_context.transition_raw = stripped
            if "→" in stripped:
                start, target = stripped.split("→", 1)
                current_context.transition = (start.strip(), target.strip())
            # '→'가 없으면 transition은 기본값 ()로 남는다. transition_raw는 채워져
            # 있으므로 "라벨 없음"과 "형식 오류"를 Task 3이 구분할 수 있다.
            current_context.label_lines[key] = lineno
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
                _apply_label(current_project, current_context, m_label.group(1), m_label.group(2), lineno)
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


# 프로젝트 섹션의 필수 라벨(라벨 한국어 키 -> Project 필드명)
REQUIRED_PROJECT_LABELS = [
    ("경로", "path"),
    ("프로파일", "profile"),
    ("기본 패키지", "base_package"),
    ("아키텍처 테스트 위치", "test_location"),
]
# 컨텍스트 섹션의 필수 라벨(라벨 한국어 키 -> Context 필드명)
REQUIRED_CONTEXT_LABELS = [
    ("분류", "classification"),
    ("스타일", "style"),
    ("모듈 구성", "module_layout"),
]


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


def _check_duplicate_table_names(names: list, kind: str, project: Project, errors: list) -> None:
    """프로젝트 표의 이름 중복을 보고한다(스코프는 프로젝트 하나).

    표 행에는 라인 번호가 없으므로 섹션 헤딩을 지목한다. 이 이름들은 뒤에서 생성물의
    식별자(테스트 함수명 등)가 되므로, 중복은 조용한 덮어쓰기·충돌로 이어진다.
    """
    seen = set()
    for name in names:
        if not name:
            continue
        if name in seen:
            errors.append(ParseError(
                project.line,
                f"프로젝트 '{project.name}'의 {kind} 이름 '{name}'이(가) 중복되었습니다.",
            ))
        else:
            seen.add(name)


def _validate_project(project: Project, context_names: set, errors: list) -> None:
    """프로젝트 하나의 필수 라벨·값 유효성·표 내용을 검사한다."""
    for label, field_name in REQUIRED_PROJECT_LABELS:
        if not getattr(project, field_name):
            errors.append(ParseError(
                project.line,
                f"프로젝트 '{project.name}': 필수 라벨 '{label}'이(가) 없습니다.",
            ))

    known_profiles = _known_profiles()
    if project.profile and project.profile not in known_profiles:
        line = project.label_lines.get("프로파일", project.line)
        errors.append(ParseError(
            line,
            f"프로젝트 '{project.name}'의 프로파일 값 '{project.profile}'이(가) 올바르지 않습니다 "
            f"(허용값: {sorted(known_profiles)}).",
        ))

    _check_duplicate_table_names(
        [application.name for application in project.applications], "애플리케이션", project, errors)
    _check_duplicate_table_names(
        [shared_module.name for shared_module in project.shared_modules], "공용 모듈", project, errors)

    for shared_module in project.shared_modules:
        if shared_module.role and shared_module.role not in SHARED_ROLES:
            errors.append(ParseError(
                project.line,
                f"프로젝트 '{project.name}'의 공용 모듈 '{shared_module.name}' 역할 값 "
                f"'{shared_module.role}'이(가) 올바르지 않습니다 (허용값: {sorted(SHARED_ROLES)}).",
            ))

    for application in project.applications:
        for ctx_name in application.contexts:
            if ctx_name != "all" and ctx_name not in context_names:
                errors.append(ParseError(
                    project.line,
                    f"프로젝트 '{project.name}'의 애플리케이션 '{application.name}'이(가) 참조하는 "
                    f"컨텍스트 '{ctx_name}'을(를) 찾을 수 없습니다.",
                ))

    # 패키지 규약은 실현 형태를 가리지 않고 프로젝트 전체에 적용되므로(app-embedded 여부와
    # 무관), '{앱}' 플레이스홀더를 쓰는 레이어가 하나라도 있으면 애플리케이션 표가 있어야
    # 한다. 없으면 normalize()가 그 레이어의 패턴을 조용히 0개 만들고 끝나 버린다(app이 0개면
    # 전개할 대상이 없으므로) — 오류 없이 규칙이 사라지는 상태라 여기서 막는다.
    app_dependent_layers = sorted(
        layer for layer, pattern in project.package_conventions.items() if "{앱}" in pattern
    )
    if app_dependent_layers and not project.applications:
        for layer in app_dependent_layers:
            errors.append(ParseError(
                project.line,
                f"프로젝트 '{project.name}'의 패키지 규약 레이어 '{layer}'가 '{{앱}}' 패턴을 쓰는데 "
                f"'애플리케이션' 표가 없습니다 (애플리케이션 표를 추가하거나 패턴에서 "
                f"'{{앱}}'을 빼세요).",
            ))


def _validate_context(context: Context, project_names: set, context_names: set,
                       multiple_projects: bool, errors: list) -> None:
    """컨텍스트 하나의 필수 라벨·값 유효성·표·이행 규칙을 검사한다."""
    for label, field_name in REQUIRED_CONTEXT_LABELS:
        if not getattr(context, field_name):
            errors.append(ParseError(
                context.line,
                f"컨텍스트 '{context.name}': 필수 라벨 '{label}'이(가) 없습니다.",
            ))

    if context.classification and context.classification not in CLASSIFICATIONS:
        line = context.label_lines.get("분류", context.line)
        errors.append(ParseError(
            line,
            f"컨텍스트 '{context.name}'의 분류 값 '{context.classification}'이(가) 올바르지 않습니다 "
            f"(허용값: {sorted(CLASSIFICATIONS)}).",
        ))

    if context.style and not (context.style in PRESET_STYLES or context.style.startswith("custom/")):
        line = context.label_lines.get("스타일", context.line)
        errors.append(ParseError(
            line,
            f"컨텍스트 '{context.name}'의 스타일 값 '{context.style}'이(가) 올바르지 않습니다 "
            f"(허용값: {sorted(PRESET_STYLES)} 또는 custom/<이름>).",
        ))

    if context.module_layout and context.module_layout not in MODULE_LAYOUTS:
        line = context.label_lines.get("모듈 구성", context.line)
        errors.append(ParseError(
            line,
            f"컨텍스트 '{context.name}'의 모듈 구성 값 '{context.module_layout}'이(가) 올바르지 않습니다 "
            f"(허용값: {sorted(MODULE_LAYOUTS)}).",
        ))

    if context.module_layout == "multi-module" and not context.modules:
        line = context.label_lines.get("모듈 구성", context.line)
        errors.append(ParseError(
            line,
            f"컨텍스트 '{context.name}': 모듈 구성이 multi-module인데 모듈 표가 없습니다.",
        ))

    if context.module_layout == "single-module" and not context.modules:
        line = context.label_lines.get("모듈 구성", context.line)
        errors.append(ParseError(
            line,
            f"컨텍스트 '{context.name}': 모듈 구성이 single-module인데 모듈 표가 없습니다.",
        ))

    if context.module_layout == "app-embedded" and context.modules:
        line = context.label_lines.get("모듈 구성", context.line)
        errors.append(ParseError(
            line,
            f"컨텍스트 '{context.name}': 모듈 구성이 app-embedded이면 모듈 표를 작성할 수 없습니다.",
        ))

    for module in context.modules:
        if not module.layer:
            errors.append(ParseError(
                context.line,
                f"컨텍스트 '{context.name}'의 모듈 '{module.name}' 레이어 값이 비어 있습니다.",
            ))

    if context.project:
        if context.project not in project_names:
            line = context.label_lines.get("프로젝트", context.line)
            errors.append(ParseError(
                line,
                f"컨텍스트 '{context.name}'이(가) 참조하는 프로젝트 '{context.project}'를 찾을 수 없습니다.",
            ))
    elif multiple_projects:
        errors.append(ParseError(
            context.line,
            f"컨텍스트 '{context.name}': 프로젝트가 여러 개이므로 '- 프로젝트: <이름>' 라벨로 "
            f"속한 프로젝트를 지정해야 합니다.",
        ))

    for relation in context.relations:
        if relation.type and relation.type not in RELATION_TYPES:
            errors.append(ParseError(
                context.line,
                f"컨텍스트 '{context.name}'의 관계 유형 값 '{relation.type}'이(가) 올바르지 않습니다 "
                f"(허용값: {sorted(RELATION_TYPES)}).",
            ))
        if relation.target and relation.target not in context_names:
            errors.append(ParseError(
                context.line,
                f"컨텍스트 '{context.name}'의 관계 상대 '{relation.target}'을(를) 찾을 수 없습니다.",
            ))

    for rule_exception in context.rule_exceptions:
        if not rule_exception.adr:
            line = context.label_lines.get("규칙 예외", context.line)
            errors.append(ParseError(
                line,
                f"컨텍스트 '{context.name}'의 규칙 예외 '{rule_exception.rule_id}'에 ADR 참조가 없습니다 "
                f"(형식: <규칙 ID> (ADR-0001)).",
            ))

    if context.transition_raw:
        line = context.label_lines.get("이행", context.line)
        if context.transition == ():
            errors.append(ParseError(
                line,
                f"컨텍스트 '{context.name}'의 이행 값 '{context.transition_raw}'에 '→' 구분자가 없습니다 "
                f"(형식: <출발 스타일> → <목표 스타일>).",
            ))
        else:
            _start, target = context.transition
            if context.style and target != context.style:
                errors.append(ParseError(
                    line,
                    f"컨텍스트 '{context.name}'의 이행 목표 '{target}'이(가) 현재 스타일 "
                    f"'{context.style}'과(와) 같지 않습니다.",
                ))


def _validate_app_embedded_consistency(architecture: Architecture, errors: list) -> None:
    """app-embedded 컨텍스트가 있는 프로젝트는 애플리케이션·패키지 규약 표가 필수이고,
    같은 프로젝트에 속한 app-embedded 컨텍스트들은 같은 스타일을 가져야 한다."""
    by_project = {}
    for context in architecture.contexts:
        if context.module_layout == "app-embedded":
            by_project.setdefault(context.project, []).append(context)

    for project in architecture.projects:
        contexts = by_project.get(project.name)
        if not contexts:
            continue

        if not project.package_conventions:
            errors.append(ParseError(
                project.line,
                f"프로젝트 '{project.name}': app-embedded 컨텍스트가 있으면 "
                f"'패키지 규약' 표가 필수입니다.",
            ))
        if not project.applications:
            errors.append(ParseError(
                project.line,
                f"프로젝트 '{project.name}': app-embedded 컨텍스트가 있으면 "
                f"'애플리케이션' 표가 필수입니다.",
            ))

        styles = {c.style for c in contexts if c.style}
        if len(styles) > 1:
            detail = ", ".join(f"{c.name}={c.style}" for c in contexts)
            errors.append(ParseError(
                project.line,
                f"프로젝트 '{project.name}'의 app-embedded 컨텍스트들은 같은 스타일을 가져야 "
                f"합니다 ({detail}).",
            ))


def validate(architecture: Architecture) -> list:
    """Architecture를 검사해 [ParseError] 목록을 반환한다(문제 없으면 빈 리스트).

    구조 추출(Task 2) 이후 단계로, 필수 라벨 누락·비정규 값·상호 참조 무결성을
    확인한다. 모듈 표의 레이어 값을 스타일 문서와 대조하는 것, 커스텀 스타일
    문서의 실존 여부, 패턴 값의 유효성은 이 단계의 범위 밖이다(Phase 2).
    """
    errors = []

    if not architecture.has_template_marker:
        errors.append(ParseError(
            0,
            f"템플릿 마커({TEMPLATE_MARKER})가 없습니다. 결정 템플릿에서 문서를 생성했는지 확인하세요.",
        ))

    if not architecture.projects:
        errors.append(ParseError(
            0,
            "프로젝트 섹션이 없습니다. '## 프로젝트: <이름>' 섹션을 최소 1개 작성하세요.",
        ))

    _check_duplicate_names(architecture.projects, "프로젝트", errors)
    _check_duplicate_names(architecture.contexts, "컨텍스트", errors)

    project_names = {p.name for p in architecture.projects}
    context_names = {c.name for c in architecture.contexts}
    multiple_projects = len(architecture.projects) > 1

    for project in architecture.projects:
        _validate_project(project, context_names, errors)

    for context in architecture.contexts:
        _validate_context(context, project_names, context_names, multiple_projects, errors)

    _validate_app_embedded_consistency(architecture, errors)

    return errors


def _expand_app_placeholder(pattern: str, applications: list) -> list:
    """패턴의 '{앱}' 자리를 애플리케이션별로 전개한다(이름의 하이픈을 점으로 치환).

    패키지 세그먼트에는 하이픈을 쓸 수 없으므로 'core-api' -> 'core.api'로 바꿔 대입한다.
    """
    return [pattern.replace("{앱}", app.name.replace("-", ".")) for app in applications]


def _normalize_project_conventions(project: Project, contexts: list) -> list:
    """프로젝트의 '패키지 규약' 표를 컨텍스트x레이어 패턴으로 전개한다.

    이 경로는 실현 형태(multi-module/single-module/app-embedded)를 가리지 않는다 —
    규약 표가 있으면 그 프로젝트에 속한 모든 컨텍스트에 그대로 우선 적용된다.
    패턴에 '{컨텍스트}'가 있으면 컨텍스트마다 자기 이름만 대입해 하나씩 만들고,
    없으면 컨텍스트로 분할되지 않는 레이어이므로 프로젝트당 한 번만 context="*"로
    만든다. '{앱}'이 있으면 그 자리에서 다시 애플리케이션별로 전개된다.
    """
    results = []
    for layer, pattern in project.package_conventions.items():
        if "{컨텍스트}" in pattern:
            for context in contexts:
                expanded = pattern.replace("{컨텍스트}", context.name)
                if "{앱}" in expanded:
                    for final in _expand_app_placeholder(expanded, project.applications):
                        results.append(NormalizedPattern(project.name, context.name, layer, final))
                else:
                    results.append(NormalizedPattern(project.name, context.name, layer, expanded))
        elif "{앱}" in pattern:
            for final in _expand_app_placeholder(pattern, project.applications):
                results.append(NormalizedPattern(project.name, "*", layer, final))
        else:
            results.append(NormalizedPattern(project.name, "*", layer, pattern))
    return results


def _normalize_context_default(context: Context, project: Project) -> list:
    """패키지 규약이 없는 프로젝트의 컨텍스트에 기본 관례를 적용한다.

    모듈 표에 등장하는 레이어 값(중복 제거)마다 '{기본 패키지}.{컨텍스트}.{레이어}..'를
    만든다. 레이어 'all'은 컨텍스트 전체를 가리키므로 '{기본 패키지}.{컨텍스트}..'로 축약된다.
    """
    results = []
    for layer in {module.layer for module in context.modules if module.layer}:
        if layer == "all":
            pattern = f"{project.base_package}.{context.name}.."
        else:
            pattern = f"{project.base_package}.{context.name}.{layer}.."
        results.append(NormalizedPattern(project.name, context.name, layer, pattern))
    return results


def normalize(arch: Architecture) -> list:
    """Architecture를 [NormalizedPattern]으로 정규화한다(정렬·중복 제거 완료).

    실현 형태(multi-module/single-module/app-embedded)에 관계없이 컨텍스트x레이어를
    패키지 패턴으로 펼쳐, 이후 단계(Konsist/ArchUnit 규칙 생성)가 레이아웃을 몰라도
    되게 한다. 프로젝트에 '패키지 규약' 표가 있으면 그 규약이 모든 컨텍스트에 우선
    적용되고, 없으면 기본 관례('{기본 패키지}.{컨텍스트}.{레이어}..')를 적용한다.
    """
    contexts_by_project = {}
    for context in arch.contexts:
        contexts_by_project.setdefault(context.project, []).append(context)

    results = []
    for project in arch.projects:
        contexts = contexts_by_project.get(project.name, [])
        if project.package_conventions:
            results.extend(_normalize_project_conventions(project, contexts))
        else:
            for context in contexts:
                results.extend(_normalize_context_default(context, project))

    return sorted(set(results), key=lambda p: (p.project, p.context, p.layer, p.pattern))


def parse_architecture(text: str) -> tuple:
    """(Architecture, [ParseError])를 반환.

    구조를 추출한 뒤 validate()로 필수 결정 누락·비정규 값을 검사해 오류
    목록을 채운다. 실현(레이아웃) 정규화는 normalize()가 별도로 담당하며,
    이 함수는 정규화를 호출하지 않는다.
    """
    architecture = _parse_document(text)
    errors = validate(architecture)
    return architecture, errors


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "ARCHITECTURE.md"
    try:
        text = open(path, encoding="utf-8").read()
    except FileNotFoundError:
        print(f"오류: {path} 파일이 없습니다. /superarchitect:init으로 초기화하세요.", file=sys.stderr)
        sys.exit(1)
    arch, errors = parse_architecture(text)
    if errors:
        for e in sorted(errors, key=lambda e: e.line):
            print(f"{path}:{e.line}: {e.message}", file=sys.stderr)
        sys.exit(1)
    print(f"OK: 프로젝트 {len(arch.projects)}, 컨텍스트 {len(arch.contexts)}")
