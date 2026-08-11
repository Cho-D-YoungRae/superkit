"""유효 규칙 해석기 — 해석 파이프라인의 최상층.

`parse_architecture.py`(결정 문서의 SSOT 파서)와 `parse_style.py`(스타일 선언 파서)를
조인해, 컨텍스트마다 **실제로 강제되는 규칙 집합**을 만든다.

    유효 규칙 = 스타일이 선언한 규칙 − `규칙 예외` + 파생 규칙 3종

소비자는 둘이다. `check_imports.py`는 이 결과로 소스를 검사하고, fitness 스킬은
프로파일의 `rule-mappings.md`로 번역해 Konsist/ArchUnit 테스트를 만든다. 두 소비자가
결정 문서·스타일 문서·정규화 규칙을 각자 다시 해석하지 않게 하는 것이 이 모듈의 존재
이유다 — 해석이 두 곳에 있으면 두 결과가 갈라진다.

정본과의 대응:

- 파생 규칙 3종의 의미 → `architecture-template.md` §5.1 규칙 5
- 교차 파일 검증 8종 → `architecture-template.md` §5.3(이번에 구현되는 행들)
- 정규화(컨텍스트 × 레이어 → 패키지 패턴) → `architecture-template.md` §6
- 레이어 이름 해석 (가)/(나) → `rule-vocabulary.md` §2.1

**오류는 여러 파일에서 나온다.** 결정 문서의 오류와 스타일 문서의 오류가 한 목록에
섞이므로, 이 모듈이 각 오류에 출처 경로를 붙인다(`LocatedError`). 출력은 언제나
`경로:라인: 메시지`이고, 그 조립은 `format_error()`가 한다.
"""

import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

# parse_architecture.py가 이 저장소의 SSOT 파서다. 오류 타입·정규 값 집합을 재사용해
# 세 파서의 동작과 오류 문체가 갈라지지 않게 한다.
from parse_architecture import PRESET_STYLES, ParseError, normalize, parse_architecture
from parse_style import GA_PARAMS, NA_PARAMS, parse_style

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
PRESET_STYLE_DIR = PLUGIN_ROOT / "references" / "knowledge" / "styles"
PATTERN_CATALOG_DIR = PLUGIN_ROOT / "references" / "knowledge" / "patterns"
CUSTOM_STYLE_DIR = "docs/architecture/styles"      # 대상 프로젝트의 ARCHITECTURE.md 기준
CUSTOM_PREFIX = "custom/"

DERIVED_PREFIX = "derived."                        # 파생 규칙 id 접두 (D1)
KIND_CONTEXT_ISOLATION = "context-isolation"
KIND_APP_CONFINEMENT = "app-confinement"
KIND_SHARED_MODULE_DIRECTION = "shared-module-direction"
DERIVED_KINDS = (KIND_CONTEXT_ISOLATION, KIND_APP_CONFINEMENT, KIND_SHARED_MODULE_DIRECTION)
ALL = "all"              # 모듈 표의 레이어 값이자 애플리케이션의 '포함 컨텍스트' 값
STAR = "*"               # 컨텍스트로 분할되지 않는 레이어(정규화 결과의 컨텍스트 자리)
DOMAIN_LAYER = "domain"
SHARED_KERNEL = "shared-kernel"
CONFINE_TYPE = "confine-type"

RE_PACKAGE_SEGMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class EffectiveRule:
    """스타일이 선언한 규칙 하나가 한 컨텍스트에서 갖는 최종 형태(예외 적용 후)."""

    project: str
    context: str
    rule_id: str
    primitive: str
    params: dict           # 선언 원문 파라미터 (키 -> 항목 목록)
    resolved: dict         # §2.1(가) 파라미터만. 레이어 항목이 패키지 패턴으로 치환된 결과.
                           # (나) 파라미터(layers/allowed_layer/layer)는 여기 없다 —
                           # 레이어 이름 그대로 params에서 읽고 layer_patterns로 번역한다.
    layer_patterns: dict   # 레이어명 -> [패턴]. 이 컨텍스트에 적용되는 정규화 결과이며
                           # 컨텍스트 비분할 레이어('*')와 'all'도 포함한다.


@dataclass(frozen=True)
class DerivedRule:
    """선언에서 자동 생성되는 규칙(정본 §5.1 규칙 5). 전부 forbid-import 인스턴스다.

    `규칙 예외`의 대상이 아니다(D1) — 조절 수단은 관계 표, 포함 컨텍스트, 공용 모듈 역할이다.

    앱·공용 모듈의 **패키지는 여기 없다.** 선언되지 않고 관측되기 때문이다(D2) — 소비자가
    `module_path`·`path` 아래 소스의 `package` 선언을 읽어 채운다. 같은 이유로 앱 → 앱 의존
    금지도 이 모듈이 표현할 수 없다: 양쪽 다 관측 대상이므로, 소비자가 앱들의 관측 패키지를
    교차 조인해 만든다(정본 §3).
    """

    project: str
    kind: str              # DERIVED_KINDS 중 하나
    subject: str           # 컨텍스트명 | 앱명 | 공용 모듈명
    detail: dict           # kind별 고정 스키마 — _derive_* 함수의 docstring 참조


@dataclass
class LocatedError(ParseError):
    """ParseError + 출처 파일 경로. 여러 문서의 오류를 한 목록에 담기 위한 확장이다."""

    path: str = ""


@dataclass(frozen=True)
class ResolveWarning:
    """오류가 아닌 고지 — 해석은 성공했지만 그 규칙이 아무것도 검사하지 않는 상태.

    해석을 막지 않으므로 오류가 아니고(exit 코드에 영향 없음), 그렇다고 침묵할 수도 없다 —
    매칭 0건의 규칙은 리포트에서 '위반 없음'과 구분되지 않는다(어휘 §1, D4).
    """

    project: str
    context: str
    layer: str
    rules: list     # 이 레이어를 참조하는 유효 규칙 id
    line: int       # ARCHITECTURE.md의 컨텍스트 섹션 라인
    message: str


@dataclass
class Resolution:
    """resolve_document()의 전체 산출. resolve()는 이 중 앞 세 개만 돌려주는 얇은 겉면이다."""

    effective: list = field(default_factory=list)   # [EffectiveRule] — 컨텍스트 문서 순서
    derived: list = field(default_factory=list)     # [DerivedRule] — 프로젝트 문서 순서
    errors: list = field(default_factory=list)      # [LocatedError]
    warnings: list = field(default_factory=list)    # [ResolveWarning] — 오류 아님, exit에 영향 없음
    excluded: list = field(default_factory=list)    # [(프로젝트, 컨텍스트, 규칙 id)] — 예외로 제외됨
    projects: list = field(default_factory=list)    # [{name, path, profile,
                                                    #   base_package, test_location}]
    contexts: list = field(default_factory=list)    # [컨텍스트명] — 문서 순서


def derived_rule_id(kind) -> str:
    """파생 규칙의 id(D1). 리포트·생성 코드의 메시지에 쓴다 — 예: `derived.app-confinement`."""
    return f"{DERIVED_PREFIX}{kind}"


def format_error(error, default_path) -> str:
    """오류 한 건을 `경로:라인: 메시지`로 조립한다(경로가 없으면 default_path)."""
    return f"{getattr(error, 'path', '') or default_path}:{error.line}: {error.message}"


def _error_sort_key(error, default_path):
    return (getattr(error, "path", "") or str(default_path), error.line)


class _PatternIndex:
    """정규화 결과(컨텍스트 × 레이어 → 패키지 패턴)를 조회 형태로 담는다."""

    def __init__(self, normalized):
        self._by_context = {}   # (프로젝트, 컨텍스트) -> {레이어: [패턴]}
        self._star = {}         # 프로젝트 -> {레이어: [패턴]}  (컨텍스트 비분할 레이어)
        for pattern in normalized:
            if pattern.context == STAR:
                table = self._star.setdefault(pattern.project, {})
            else:
                table = self._by_context.setdefault((pattern.project, pattern.context), {})
            table.setdefault(pattern.layer, []).append(pattern.pattern)

    def layer_patterns(self, project, context) -> dict:
        """컨텍스트에 적용되는 레이어 -> [패턴]. 비분할 레이어는 모든 컨텍스트에 공통이다(§6)."""
        merged = {}
        for source in (self._by_context.get((project, context), {}), self._star.get(project, {})):
            for layer, patterns in source.items():
                merged.setdefault(layer, set()).update(patterns)
        return {layer: sorted(patterns) for layer, patterns in merged.items()}

    def context_patterns(self, project, context) -> list:
        """그 컨텍스트에만 속한 패턴. 비분할 레이어('*')는 포함하지 않는다."""
        table = self._by_context.get((project, context), {})
        return sorted({pattern for patterns in table.values() for pattern in patterns})

    def star_patterns(self, project) -> list:
        """컨텍스트로 분할되지 않는 레이어의 패턴(예: `{앱}` 전개로 생긴 앱 패키지)."""
        table = self._star.get(project, {})
        return sorted({pattern for patterns in table.values() for pattern in patterns})


class _StyleSet:
    """컨텍스트가 채택한 스타일 선언을 문서당 한 번만 읽는다.

    같은 스타일을 여러 컨텍스트가 채택해도 선언의 파싱 오류는 한 번만 보고된다 — 오류는
    문서의 성질이지 채택 횟수의 성질이 아니다. 반면 '문서가 없다'는 채택한 컨텍스트마다
    보고한다(고쳐야 할 지점이 컨텍스트의 `스타일` 라벨이므로).
    """

    def __init__(self, arch_dir, arch_path, errors):
        self._arch_dir = Path(arch_dir)
        self._arch_path = arch_path
        self._errors = errors
        self._cache = {}    # 스타일 라벨 -> (StyleDeclaration|None, 표시 경로, 문서 부재 여부)

    def _locate(self, label):
        if label.startswith(CUSTOM_PREFIX):
            name = label[len(CUSTOM_PREFIX):]
            display = f"{CUSTOM_STYLE_DIR}/{name}.md"
            return name, self._arch_dir / display, display
        path = PRESET_STYLE_DIR / f"{label}.md"
        return label, path, str(path)

    def _load(self, label):
        if label in self._cache:
            return self._cache[label]
        name, path, display = self._locate(label)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            self._cache[label] = (None, display, True)
            return self._cache[label]
        declaration, errors = parse_style(text, name, str(path))
        for error in errors:
            self._errors.append(LocatedError(error.line, error.message, str(path)))
        self._cache[label] = (declaration, display, False)
        return self._cache[label]

    def declaration_for(self, context):
        """컨텍스트의 스타일 선언. 읽을 수 없으면 None(오류는 이미 보고되었다)."""
        label = context.style
        if not label:
            return None                      # 필수 라벨 누락 — parse_architecture가 보고했다
        if not (label in PRESET_STYLES or label.startswith(CUSTOM_PREFIX)):
            return None                      # 비정규 값 — parse_architecture가 보고했다
        declaration, display, missing = self._load(label)
        if missing:
            kind = "커스텀" if label.startswith(CUSTOM_PREFIX) else "프리셋"
            self._errors.append(LocatedError(
                context.label_lines.get("스타일", context.line),
                f"컨텍스트 '{context.name}'이(가) 채택한 {kind} 스타일 문서 '{display}'가 없습니다 "
                f"(선언 형식: architecture-template.md §7 — '## 선언' 아래 레이어 라벨과 규칙 표).",
                self._arch_path,
            ))
        return declaration


def _pattern_catalog():
    """`패턴` 라벨의 정규 값 집합 = references/knowledge/patterns/의 문서 key. 없으면 None."""
    try:
        keys = {path.stem for path in PATTERN_CATALOG_DIR.glob("*.md")}
    except OSError:
        return None
    return keys or None


def _check_module_layers(context, declaration, project, errors, arch_path):
    """모듈 표의 레이어 값을 스타일 선언·패키지 세그먼트 규칙과 대조한다(§5.3 행 2·3).

    모듈 행에는 라인 번호가 없으므로(구조 파서가 표 행의 위치를 보존하지 않는다) 오류는
    컨텍스트 섹션 헤딩을 지목한다 — parse_architecture의 표 관련 오류와 같은 관례다.
    """
    declared = declaration.layers if declaration else None
    uses_conventions = bool(project and project.package_conventions)
    for module in context.modules:
        if not module.layer:
            continue                          # 빈 값 — parse_architecture가 보고했다
        if declared and module.layer != ALL and module.layer not in declared:
            errors.append(LocatedError(
                context.line,
                f"컨텍스트 '{context.name}'의 모듈 '{module.name}' 레이어 '{module.layer}'는 "
                f"스타일 '{context.style}'이(가) 선언한 레이어가 아닙니다 "
                f"(선언된 레이어: {', '.join(declared)}, 또는 '{ALL}').",
                arch_path,
            ))
            continue     # 알 수 없는 레이어가 근본 원인이다 — 세그먼트 검사를 덧붙이지 않는다
        if not uses_conventions and not RE_PACKAGE_SEGMENT.match(module.layer):
            errors.append(LocatedError(
                context.line,
                f"컨텍스트 '{context.name}'의 모듈 '{module.name}' 레이어 '{module.layer}'는 "
                f"유효한 패키지 세그먼트가 아닙니다. 기본 관례에서는 레이어 이름이 그대로 패키지 "
                f"세그먼트가 되므로(§6) 이 이름은 성립하지 않는 패턴을 만들고 그 레이어의 규칙이 "
                f"0건을 매칭한 채 통과합니다 — 한 단어로 줄이거나 '패키지 규약' 표로 실제 "
                f"세그먼트를 매핑하세요.",
                arch_path,
            ))


def _check_convention_layers(project, contexts, declarations, errors, arch_path):
    """패키지 규약 표의 레이어 이름을 스타일 선언과 대조한다(§5.1 규칙 4, §5.3 행 1).

    규약은 프로젝트에 속한 모든 컨텍스트에 적용되므로(§6), 그 컨텍스트들이 채택한 스타일이
    선언한 레이어의 합집합을 기준으로 본다. 기준을 만들 수 없으면(스타일을 하나도 읽지
    못했으면) 검사하지 않는다 — 근거 없는 오류를 만들지 않기 위해서다.
    """
    if not project.package_conventions:
        return
    layers, labels = set(), []
    for context in contexts:
        declaration = declarations.get(context.name)
        if declaration is None or not declaration.layers:
            continue
        layers.update(declaration.layers)
        if context.style not in labels:
            labels.append(context.style)
    if not layers:
        return
    for layer in project.package_conventions:
        if layer not in layers:
            errors.append(LocatedError(
                project.line,
                f"프로젝트 '{project.name}'의 패키지 규약 레이어 '{layer}'는 이 프로젝트의 "
                f"컨텍스트가 채택한 스타일이 선언한 레이어가 아닙니다 "
                f"(스타일: {', '.join(labels)} / 선언된 레이어: {', '.join(sorted(layers))}).",
                arch_path,
            ))


def _check_patterns(context, catalog, errors, arch_path):
    """`패턴` 라벨의 값이 실재하는 knowledge 문서 key인지 확인한다(§5.3 행 5)."""
    if not context.patterns:
        return
    line = context.label_lines.get("패턴", context.line)
    if catalog is None:
        errors.append(LocatedError(
            line,
            f"패턴 카탈로그({PATTERN_CATALOG_DIR})를 읽을 수 없어 컨텍스트 '{context.name}'의 "
            f"'패턴' 값을 검증하지 못했습니다 (플러그인 설치를 확인하세요).",
            arch_path,
        ))
        return
    for key in context.patterns:
        if key not in catalog:
            errors.append(LocatedError(
                line,
                f"컨텍스트 '{context.name}'의 패턴 '{key}'에 해당하는 지식 문서가 없습니다 "
                f"(등록된 패턴: {', '.join(sorted(catalog))}).",
                arch_path,
            ))


def _check_exceptions(context, declaration, errors, arch_path):
    """`규칙 예외`를 검사하고 실제로 제외할 규칙 id 목록을 돌려준다(D1).

    id가 아무것도 가리키지 않는 예외를 통과시키면, 예외로 막고 있던 규칙이 조용히 되살아나는
    사고(어휘 §4)를 검출할 수단이 사라진다. 그래서 미선언 id도, 파생 규칙 id도 오류다.
    """
    line = context.label_lines.get("규칙 예외", context.line)
    declared = [rule.rule_id for rule in declaration.rules] if declaration else []
    excluded = []
    for exception in context.rule_exceptions:
        rule_id = exception.rule_id
        if rule_id.startswith(DERIVED_PREFIX):
            errors.append(LocatedError(
                line,
                f"컨텍스트 '{context.name}'의 규칙 예외 '{rule_id}'은(는) 파생 규칙이므로 예외로 뺄 수 "
                f"없습니다. 파생 규칙은 선언에서 자동 생성되며 조절 수단이 따로 있습니다 — "
                f"컨텍스트 간 참조는 관계 표('### 관계')에 쌍을 추가하고, 앱 봉쇄는 애플리케이션 "
                f"표의 '포함 컨텍스트' 칸을, 공용 모듈 방향은 공용 모듈 표의 '역할' 칸을 고치세요.",
                arch_path,
            ))
            continue
        if declaration is None:
            continue           # 대조 기준이 없다 — 스타일 문서 오류가 이미 보고되었다
        if rule_id not in declared:
            errors.append(LocatedError(
                line,
                f"컨텍스트 '{context.name}'의 규칙 예외 '{rule_id}'은(는) 스타일 "
                f"'{context.style}'이(가) 선언한 규칙 id가 아닙니다 "
                f"(선언된 id: {', '.join(declared) or '없음'}). 규칙 id가 바뀌었다면 예외도 함께 "
                f"고쳐야 합니다 — 그러지 않으면 예외로 막고 있던 규칙이 조용히 되살아납니다.",
                arch_path,
            ))
            continue
        if rule_id not in excluded:      # 같은 id를 두 번 적어도 제외되는 규칙은 하나다
            excluded.append(rule_id)
    return excluded


def _references_layer(rule, layer) -> bool:
    """유효 규칙이 그 레이어를 **레이어로서** 참조하는가(§2.1의 (가)·(나) 파라미터만 본다).

    접미사·셀렉터처럼 레이어를 받지 않는 키의 값이 우연히 레이어 이름과 같아도 참조가 아니다.
    """
    for key, items in rule.params.items():
        pair = (rule.primitive, key)
        if (pair in GA_PARAMS or pair in NA_PARAMS) and layer in items:
            return True
    return False


def _hollow_layer_warnings(context, declaration, layer_patterns, rules):
    """스타일이 선언했지만 실현 패턴이 0건인 레이어를 고지한다(오류 아님).

    레이어 이름과 실제 패키지가 어긋나는 실패 모드는 §2.1의 판별로도 §5.3의 대조로도 잡히지
    않는다(템플릿 §7) — 이름은 정상이고 어긋난 곳은 이름과 실현 사이다. 그 규칙은 0건을
    매칭한 채 통과하므로, 조용히 두지 않고 해석 단계에서 알린다.
    """
    warnings = []
    for layer in declaration.layers:
        if layer_patterns.get(layer):
            continue
        referencing = [rule.rule_id for rule in rules if _references_layer(rule, layer)]
        head = (f"경고: 컨텍스트 '{context.name}'의 레이어 '{layer}'는 스타일이 선언했으나 "
                f"실현 패턴이 없습니다")
        if referencing:
            message = (f"{head} — 이 레이어를 참조하는 규칙 {len(referencing)}건"
                       f"({', '.join(referencing)})이 아무것도 검사하지 않습니다")
        else:
            message = f"{head} — 이 레이어를 참조하는 유효 규칙은 없습니다"
        warnings.append(ResolveWarning(
            project=context.project, context=context.name, layer=layer,
            rules=referencing, line=context.line, message=message,
        ))
    return warnings


def _resolve_params(rule, layers, layer_patterns) -> dict:
    """§2.1(가) 파라미터의 레이어 항목을 패키지 패턴으로 치환한다.

    (가) = `forbid-import`의 from·to, `naming-suffix`의 scope. 항목이 선언된 레이어 이름과
    정확히 일치하면 그 레이어의 패턴 목록으로 펼치고, 아니면 패키지 패턴으로 보고 그대로 둔다.
    (나) 파라미터는 여기 담기지 않는다 — 레이어 이름을 유지해야 프로파일이 레이어 표기를
    쓰는 코드(Konsist의 `Layer`)로 번역할 수 있기 때문이다.
    """
    resolved = {}
    for key, items in rule.params.items():
        if (rule.primitive, key) not in GA_PARAMS:
            continue
        expanded = []
        for item in items:
            candidates = layer_patterns.get(item, []) if item in layers else [item]
            expanded.extend(pattern for pattern in candidates if pattern not in expanded)
        resolved[key] = expanded
    return resolved


def _derive_context_isolation(project, contexts, index, partners):
    """컨텍스트 간 직접 참조 금지 — 관계 표에 나타난 쌍만 열린다(§5.1 규칙 5).

    detail: {"from": [자기 패턴], "to": [타 컨텍스트 패턴 − 관계 쌍 상대 패턴]}

    v1의 허용 단위는 쌍이고 방향을 구분하지 않는다. 컨텍스트 비분할 레이어('*')의 패턴은
    모든 컨텍스트의 공용이므로 격리 대상이 아니다 — 어느 쪽에도 넣지 않는다.
    """
    rules = []
    for context in contexts:
        open_pairs = partners.get(context.name, set())
        blocked = sorted({pattern
                          for other in contexts
                          if other.name != context.name and other.name not in open_pairs
                          for pattern in index.context_patterns(project.name, other.name)})
        if not blocked:
            continue                     # 막을 상대가 없다 — 인스턴스를 만들지 않는다
        rules.append(DerivedRule(project.name, KIND_CONTEXT_ISOLATION, context.name, {
            "from": index.context_patterns(project.name, context.name),
            "to": blocked,
        }))
    return rules


def _app_convention_patterns(project, contexts):
    """패키지 규약의 `{앱}` 행을 앱별로 전개한다 — 앱 패키지가 **선언**으로 존재하는 유일한 경로.

    `{앱}` 행이 하나도 없으면 빈 dict다. 그때 앱 패키지는 관측으로만 알 수 있다(D2).
    치환 규칙은 §6과 같다 — 앱 이름의 하이픈은 점으로 바꾸고(`core-api` → `core.api`),
    같은 행에 `{컨텍스트}`가 함께 있으면 컨텍스트마다 하나씩 더 전개한다.
    """
    rows = [pattern for pattern in project.package_conventions.values() if "{앱}" in pattern]
    if not rows:
        return {}
    table = {}
    for application in project.applications:
        patterns = set()
        for row in rows:
            expanded = row.replace("{앱}", application.name.replace("-", "."))
            if "{컨텍스트}" in expanded:
                patterns.update(expanded.replace("{컨텍스트}", context.name) for context in contexts)
            else:
                patterns.add(expanded)
        table[application.name] = sorted(patterns)
    return table


def _derive_app_confinement(project, contexts, index):
    """애플리케이션 봉쇄 — 앱은 `포함 컨텍스트`의 코드만 참조하고, 컨텍스트 코드는 앱에
    의존할 수 없다(§5.1 규칙 5). 조립은 앱에서만 한다.

    detail: {"module_path": 프로젝트 경로 기준 모듈 경로,
             "forbidden": [미포함 컨텍스트 패턴],
             "reverse_from": [모든 컨텍스트 패턴],
             "app_patterns": {앱 이름: [패턴]}}   ← 선택 키

    `forbidden`·`reverse_from`에서는 컨텍스트 비분할 레이어('*')의 패턴을 뺀다 — `{앱}` 전개로
    생긴 그 패턴들은 대개 앱 자신의 패키지이고, 넣으면 앱이 자기 자신을 참조하지 못하게 된다.

    대신 그 패턴들을 `app_patterns`에 앱별로 갈라 담는다(패키지 규약에 `{앱}` 행이 있을 때만).
    소비자는 이 표로 from-측(자기 앱)과 **앱 → 앱 금지**(다른 앱들)를 선언만으로 만들 수 있고,
    키가 없으면 관측으로 폴백한다(D2).
    """
    every = sorted({pattern for context in contexts
                    for pattern in index.context_patterns(project.name, context.name)})
    app_patterns = _app_convention_patterns(project, contexts)
    rules = []
    for application in project.applications:
        included = set(application.contexts)
        forbidden = [] if ALL in included else sorted(
            {pattern for context in contexts if context.name not in included
             for pattern in index.context_patterns(project.name, context.name)})
        detail = {
            "module_path": application.module_path,
            "forbidden": forbidden,
            "reverse_from": every,
        }
        if app_patterns:
            detail["app_patterns"] = app_patterns
        rules.append(DerivedRule(project.name, KIND_APP_CONFINEMENT, application.name, detail))
    return rules


def _derive_shared_module_direction(project, contexts, index, domain_pure):
    """공용 모듈 의존 방향 — 공용 모듈은 앱·컨텍스트 코드에 의존할 수 없다(§5.1 규칙 5).

    detail: {"path": 모듈 경로, "role": 역할,
             "forbidden": [프로젝트의 모든 컨텍스트 패턴],
             "domain_restricted_contexts": [domain 레이어에서 이 모듈을 금지할 컨텍스트]}

    `forbidden`에는 컨텍스트 비분할 레이어('*')의 패턴도 넣는다. 정본이 금지하는 대상이
    "앱·컨텍스트 코드" 둘 다인데 app-embedded에서 앱 코드가 바로 그 패턴이기 때문이고,
    공용 모듈 자신의 패키지는 관측 대상이라 이 목록에 들어올 수 없어 자기 참조 위험도 없다.

    `domain_restricted_contexts`는 shared-kernel 외 역할이 domain-pure 컨텍스트의 domain
    레이어에서 금지된다는 세부다(D3). role이 shared-kernel이면 빈 목록이다.
    """
    every = sorted({pattern for context in contexts
                    for pattern in index.context_patterns(project.name, context.name)}
                   | set(index.star_patterns(project.name)))
    restricted = [context.name for context in contexts if context.name in domain_pure]
    rules = []
    for module in project.shared_modules:
        rules.append(DerivedRule(project.name, KIND_SHARED_MODULE_DIRECTION, module.name, {
            "path": module.path,
            "role": module.role,
            "forbidden": every,
            "domain_restricted_contexts": [] if module.role == SHARED_KERNEL else list(restricted),
        }))
    return rules


def _relation_partners(contexts):
    """관계 표가 연 쌍. v1의 허용 단위는 쌍이며 방향을 구분하지 않는다(§5.1 규칙 5)."""
    partners = {}
    for context in contexts:
        for relation in context.relations:
            if not relation.target:
                continue
            partners.setdefault(context.name, set()).add(relation.target)
            partners.setdefault(relation.target, set()).add(context.name)
    return partners


def _is_domain_pure(declaration, excluded) -> bool:
    """D3 — confine-type 인스턴스가 하나라도 **유효하면** 그 컨텍스트는 domain-pure다.

    기준은 선언이 아니라 예외 적용 **후**의 유효 규칙이다. 규칙 예외로 순수성을 뺀 컨텍스트에
    파생 제약을 걸면 근거 없는 금지가 되고, 파생 규칙은 예외 대상이 아니므로(D1) 그 금지를
    해제할 레버도 없다.
    """
    return declaration is not None and any(
        rule.primitive == CONFINE_TYPE for rule in declaration.rules
        if rule.rule_id not in excluded)


def resolve_document(arch_path) -> Resolution:
    """ARCHITECTURE.md 한 건을 해석해 Resolution을 만든다.

    **호출자는 errors가 비었는지 먼저 확인해야 한다.** parse_style과 같은 방침으로, 오류가
    있어도 해석 가능한 부분은 채워 돌려준다 — 한 번의 실행에서 오류를 모두 보여주기 위해서다.
    """
    arch_path = Path(arch_path)
    path_text = str(arch_path)
    result = Resolution()

    try:
        text = arch_path.read_text(encoding="utf-8")
    except OSError:
        result.errors.append(LocatedError(
            0,
            f"'{arch_path.name}' 파일을 읽을 수 없습니다. 경로를 확인하거나 "
            f"/superarchitect:init으로 초기화하세요.",
            path_text,
        ))
        return result

    architecture, arch_errors = parse_architecture(text)
    result.errors.extend(LocatedError(e.line, e.message, path_text) for e in arch_errors)
    result.projects = [{
        "name": project.name,
        "path": project.path,
        "profile": project.profile,
        "base_package": project.base_package,
        "test_location": project.test_location,
    } for project in architecture.projects]
    result.contexts = [context.name for context in architecture.contexts]

    styles = _StyleSet(arch_path.parent, path_text, result.errors)
    index = _PatternIndex(normalize(architecture))
    catalog = _pattern_catalog()

    projects_by_name = {project.name: project for project in architecture.projects}
    contexts_by_project = {}
    for context in architecture.contexts:
        contexts_by_project.setdefault(context.project, []).append(context)

    declarations = {}
    exclusions = {}
    for context in architecture.contexts:
        declaration = styles.declaration_for(context)
        declarations[context.name] = declaration
        project = projects_by_name.get(context.project)

        _check_module_layers(context, declaration, project, result.errors, path_text)
        _check_patterns(context, catalog, result.errors, path_text)
        excluded = _check_exceptions(context, declaration, result.errors, path_text)
        exclusions[context.name] = excluded
        result.excluded.extend((context.project, context.name, rule_id) for rule_id in excluded)

        if declaration is None:
            continue
        layer_patterns = index.layer_patterns(context.project, context.name)
        rules = []
        for rule in declaration.rules:
            if rule.rule_id in excluded:
                continue
            rules.append(EffectiveRule(
                project=context.project,
                context=context.name,
                rule_id=rule.rule_id,
                primitive=rule.primitive,
                params=dict(rule.params),
                resolved=_resolve_params(rule, declaration.layers, layer_patterns),
                layer_patterns=layer_patterns,
            ))
        result.effective.extend(rules)
        result.warnings.extend(_hollow_layer_warnings(context, declaration, layer_patterns, rules))

    for project in architecture.projects:
        contexts = contexts_by_project.get(project.name, [])
        _check_convention_layers(project, contexts, declarations, result.errors, path_text)

        domain_pure = {context.name for context in contexts
                       if _is_domain_pure(declarations.get(context.name),
                                          exclusions.get(context.name, []))
                       and DOMAIN_LAYER in declarations[context.name].layers}
        result.derived.extend(_derive_context_isolation(
            project, contexts, index, _relation_partners(contexts)))
        result.derived.extend(_derive_app_confinement(project, contexts, index))
        result.derived.extend(_derive_shared_module_direction(
            project, contexts, index, domain_pure))

    return result


def resolve(arch_path) -> tuple:
    """(list[EffectiveRule], list[DerivedRule], list[ParseError]) — 소비자용 겉면.

    오류의 출처 경로가 필요하면 `format_error(error, arch_path)`를 쓴다(스타일 문서에서 온
    오류는 ARCHITECTURE.md가 아니라 그 스타일 문서를 가리킨다).
    """
    resolution = resolve_document(arch_path)
    return resolution.effective, resolution.derived, resolution.errors


def _json_payload(resolution) -> dict:
    return {
        "projects": resolution.projects,
        "effective": [asdict(rule) for rule in resolution.effective],
        "derived": [asdict(rule) for rule in resolution.derived],
        "warnings": [asdict(warning) for warning in resolution.warnings],
    }


def main(argv) -> int:
    as_json = "--json" in argv
    args = [arg for arg in argv if arg != "--json"]
    if len(args) != 1 or any(arg.startswith("--") for arg in args):
        print("사용법: python3 resolve_rules.py <ARCHITECTURE.md 경로> [--json]", file=sys.stderr)
        return 2

    path = args[0]
    resolution = resolve_document(path)
    if resolution.errors:
        for error in sorted(resolution.errors, key=lambda e: _error_sort_key(e, path)):
            print(format_error(error, path), file=sys.stderr)
        return 1

    if as_json:
        print(json.dumps(_json_payload(resolution), ensure_ascii=False, indent=2))
        return 0

    for warning in resolution.warnings:
        print(f"{path}:{warning.line}: {warning.message}")

    style_count = len(resolution.effective)
    derived_count = len(resolution.derived)
    print(f"OK: 컨텍스트 {len(resolution.contexts)}, "
          f"유효 규칙 {style_count + derived_count} "
          f"(스타일 {style_count}, 파생 {derived_count}, 예외 제외 {len(resolution.excluded)})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
