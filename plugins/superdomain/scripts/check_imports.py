"""정적 import 검사기 — 해석 파이프라인의 첫 소비자.

**exit 계약: 0 = 위반 없음, 1 = 위반 발견, 2 = 해석 불가(규칙을 못 만듦) 또는 사용법 오류.**
`resolve_rules.py`와 의미가 다르다 — 저쪽의 1은 "해석 오류"다. 여기서 1은 정상 판정 결과이고,
검사 자체가 성립하지 않은 경우만 2로 나간다. CI에서 두 코드를 같게 다루면 안 된다.

`resolve_rules.resolve_document()`가 만든 유효 규칙(스타일 선언 − 규칙 예외)과 파생 규칙
3종을 받아, 대상 프로젝트의 `.kt`/`.java` 소스를 걸으며 위반을 찾는다. 소스는 정규식으로만
읽는다 — `package` 선언, `import` 목록(와일드카드 포함), 최상위 public 타입 이름, `@Entity`.

정본과의 대응:

- primitive 5종의 판정 의미 → `rule-vocabulary.md` §3
- 파생 규칙 3종의 의미 → `architecture-template.md` §5.1 규칙 5
- 앱 모듈 → 앱 모듈 의존 금지 → `architecture-template.md` §3
- 패키지 패턴 표기(`..` = 하위 포함) → `rule-vocabulary.md` §2

**이 검사기는 강제의 정본이 아니다.** import 문 없이 쓰이는 참조 — 같은 패키지 안의 타입,
완전 수식 이름(FQN)을 본문에 그대로 쓴 참조 — 를 보지 못한다. 강제의 정본은 fitness가
생성하는 Konsist/ArchUnit 테스트이고, 이 스크립트는 그 앞단에서 빠르게 도는 근사다. 그래서
리포트는 그 한계를 함께 출력한다 — `LIMITATION_NOTE`는 언제나, `CONFINE_SCOPE_NOTE`·
`BASELINE_MATCH_NOTE`는 그 규칙·그 파일이 이번 실행에 실제로 관여했을 때만(푸터의 한 줄은
읽는 사람에게 '언제나 참'이어야 한다).

**`이행` 프로젝트의 기존 부채는 별도 채널로 나간다**(정본 §5.1 규칙 8). `docs/architecture/
baseline.jsonl`이 있으면 플래그 없이 자동으로 읽어, 매칭되는 위반을 `[기존 부채]`로 강등한다 —
리포트에는 남지만 exit 코드에는 반영되지 않고 신규 위반만 1을 만든다. 매칭 키는 (규칙 id, 경로)
뿐이고 그 대가는 푸터가 밝힌다. 깨진 줄 하나면 어느 위반이 동결분인지 전체를 알 수 없으므로
**해석 불가(exit 2)로 다룬다** — 래칫을 부분적으로 믿느니 검사를 세우지 않는다.

같은 이유로 **아무것도 검사하지 않은 규칙을 침묵으로 넘기지 않는다.** 매칭 0건의 규칙은
리포트에서 '위반 없음'과 구분되지 않으므로(어휘 §1), 세 층위로 나누어 전부 고지한다.

| 층위 | 무엇이 없는가 | 출력 |
|---|---|---|
| 공허 레이어 | 레이어의 실현 패턴 자체가 없다 | `resolve`의 경고를 그대로 승계 |
| 0건 경고 | 패턴은 있으나 매칭 파일이 0건이다 | `[0건 경고] <rule id>: ...` |
| 생략 | 검사에 필요한 관측이 0건이다 | 푸터의 `생략:` 줄 |
"""

import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

# resolve_rules.py가 해석의 정본이다. 이 스크립트는 그 산출(EffectiveRule/DerivedRule)만
# 소비하며, 결정 문서·스타일 문서·정규화 규칙을 다시 해석하지 않는다.
from resolve_rules import (DOMAIN_LAYER, KIND_APP_CONFINEMENT, KIND_CONTEXT_ISOLATION,
                           KIND_SHARED_MODULE_DIRECTION, LocatedError, derived_rule_id,
                           format_error, resolve_document)

SOURCE_SUFFIXES = (".kt", ".java")
JPA_ENTITY = "jpa-entity"        # confine-type의 v1 셀렉터 — 어휘 §3.3

# 빌드 산출물·도구 디렉터리. 여기 있는 소스는 선언의 대상이 아니다(생성물이거나 사본이다).
SKIP_DIRS = frozenset({
    "build", "out", "target", ".git", ".gradle", ".idea", ".kotlin", ".settings",
    ".venv", "node_modules",
})
SRC_DIR = "src"                  # `src/test`, `src/androidTest` … 는 프로덕션 소스가 아니다

LIMITATION_NOTE = (
    "한계: 같은 패키지 안의 참조와 import 없이 쓰는 완전 수식 이름(FQN)은 이 검사가 보지 "
    "못합니다 — 강제의 정본은 생성된 Konsist/ArchUnit 아키텍처 테스트입니다."
)
# 좁힘으로 생긴 사각의 고지. **confine-type을 실제로 판정한 실행에서만 낸다** — 그 규칙이 없거나
# 생략된 프로젝트에 이 줄을 내면 없는 규칙의 한계를 읽는 사람이 떠안는다(푸터의 줄은 언제나 참이어야
# 한다). 규칙 단위 한계라는 점에서 언제나 참인 위 `LIMITATION_NOTE`와 결이 다르다.
CONFINE_SCOPE_NOTE = (
    "한계: confine-type의 참조 검사는 그 컨텍스트 범위(레이어 패턴 합집합) 안에서 선언된 "
    "@Entity만 봅니다 — 다른 컨텍스트의 엔티티 참조는 derived.context-isolation의 몫이고, "
    "그 쌍이 '### 관계'로 열려 있거나 엔티티가 어느 레이어 패턴에도 들지 않는 곳(공용 모듈 등)에 "
    "있으면 이 검사의 사각입니다."
)
ZERO_MATCH_REASON = "from-측 매칭 파일 0건 — 레이어·패키지 불일치 가능성"

# 동결된 기존 부채. 경로는 ARCHITECTURE.md가 있는 디렉터리(= git 루트) 기준이라 위반의 표시 경로와
# 같은 기준이고, 그래서 (규칙 id, 경로)로 바로 맞춰 볼 수 있다.
BASELINE_RELATIVE = "docs/architecture/baseline.jsonl"
BASELINE_MATCH_NOTE = (
    "한계: 부채 매칭 키는 (규칙 id, 경로)뿐입니다 — 줄 번호를 키에 넣지 않아 리팩터링에는 견디는 "
    "대신, 같은 파일에서 같은 규칙을 어긴 **추가** 위반도 기존 부채로 함께 흡수됩니다. 그 파일의 "
    "부채를 migrate로 갚기 전까지 이 사각이 남습니다."
)

RE_PACKAGE = re.compile(r"^\s*package\s+([\w.]+)", re.M)
# `*`를 문자 집합에 넣어 두어야 와일드카드가 잘리지 않는다. Kotlin의 별칭(`... as Row`)과
# Java의 `;`는 공백·비문자에서 자연히 끊긴다.
RE_IMPORT = re.compile(r"^\s*import\s+(?:static\s+)?([\w.*]+)", re.M)
RE_ENTITY = re.compile(r"@(?:jakarta\.persistence\.|javax\.persistence\.)?Entity\b")

# 최상위 public 타입 — 어휘 §3.4. `^`(MULTILINE)에 붙여 두는 것이 '최상위' 판별 그 자체다:
# 중첩 타입은 들여쓰여 있어 줄 첫 칸에서 시작하지 못한다. Kotlin의 가시성 키워드
# `private`·`internal`은 대안에 없으므로 그 선언은 애초에 매칭되지 않는다.
#
# `fun`(fun interface)과 `annotation`(annotation class)이 수식어에 있어야 한다 — SAM 포트는
# `fun interface`가 관용이고, 그것이 `hex.ports-owned-inside`가 겨냥하는 바로 그 타입이다.
# 최상위 함수(`fun foo()`)는 뒤따르는 class/interface/object가 없어 매칭되지 않는다.
RE_KOTLIN_TYPE = re.compile(
    r"^(?:@\w+\s*)*(?:public\s+)?"
    r"(?:(?:data|enum|sealed|abstract|open|value|fun|annotation)\s+)*"
    r"(?:class|interface|object)\s+(\w+)", re.M)
RE_JAVA_TYPE = re.compile(
    r"^(?:@\w+\s*)*public\s+(?:(?:final|abstract|static|strictfp|sealed|non-sealed)\s+)*"
    r"(?:class|interface|enum|record)\s+(\w+)", re.M)


@dataclass(frozen=True)
class Import:
    text: str        # 원문 그대로 — 와일드카드는 `.*`를 달고 있다
    fqn: str         # 와일드카드를 뗀 형태(= 그 경우 패키지 이름)
    wildcard: bool
    line: int


@dataclass(frozen=True)
class TypeDecl:
    name: str
    line: int
    entity: bool     # 이 선언에 `@Entity`가 붙어 있는가


@dataclass(frozen=True)
class SourceFile:
    path: Path
    display: str     # 리포트에 쓰는 경로 — ARCHITECTURE.md의 디렉터리 기준 상대경로
    package: str
    imports: tuple
    types: tuple
    entity_line: int  # `@Entity`는 있으나 최상위 타입을 찾지 못했을 때 지목할 줄(없으면 0)


@dataclass(frozen=True)
class Violation:
    path: str
    line: int
    rule_id: str
    message: str


@dataclass(frozen=True)
class ZeroMatch:
    """규칙의 from-측이 파일 0건을 매칭했다(D4). 오류가 아니고 exit 코드를 바꾸지 않는다."""

    rule_id: str
    subject: str     # "컨텍스트 claim" | "앱 web" | "공용 모듈 logging"
    message: str


@dataclass(frozen=True)
class Skip:
    """규칙을 아예 검사하지 못했다 — 관측 0건이거나 프로젝트 경로가 없다."""

    rule_id: str
    subject: str
    reason: str


@dataclass(frozen=True)
class Baseline:
    """동결된 기존 부채 목록. 매칭 키는 (규칙 id, 경로)뿐이다 — 줄 번호는 리팩터링에 취약하다."""

    display: str     # 리포트·오류에 쓰는 경로(ARCHITECTURE.md 기준 상대)
    keys: frozenset  # {(rule_id, path)}


@dataclass
class Report:
    violations: list = field(default_factory=list)
    zero_match: list = field(default_factory=list)
    inherited: list = field(default_factory=list)   # resolve의 경고를 문자열 그대로 승계
    skipped: list = field(default_factory=list)
    unreadable: list = field(default_factory=list)  # 읽지 못한 소스 — 검사에서 빠진 사각지대
    checked: int = 0
    errors: list = field(default_factory=list)      # 비어 있지 않으면 해석 불가(exit 2)
    baseline: object = None                         # Baseline | None — 자동 감지 결과
    debt: list = field(default_factory=list)        # [Violation] — 강등된 기존 부채(exit 미반영)
    confine_scoped: bool = False                    # confine-type을 실제로 판정했는가


# ---------------------------------------------------------------------------
# 패키지 패턴 매칭 — `..`로 끝나면 그 패키지와 모든 하위, 아니면 정확히 그 패키지·타입
# ---------------------------------------------------------------------------

def _matches_package(package, pattern) -> bool:
    if pattern.endswith(".."):
        base = pattern[:-2]
        return package == base or package.startswith(base + ".")
    return package == pattern


def _matches_import(imported, pattern) -> bool:
    """import 한 건이 패턴에 걸리는가.

    와일드카드(`a.b.c.*`)는 **그 패키지의 멤버만** 들여온다 — 하위 패키지는 들어오지
    않으므로 패키지 매칭과 같은 규칙으로 본다. 그 밖의 import는 타입의 완전 수식 이름이다.
    """
    if imported.wildcard:
        return _matches_package(imported.fqn, pattern)
    if pattern.endswith(".."):
        base = pattern[:-2]
        return imported.fqn == base or imported.fqn.startswith(base + ".")
    # `..` 없는 패턴은 "정확히 그 패키지·타입"이다 — 타입 자신이거나 그 패키지 소속 타입.
    return imported.fqn == pattern or imported.fqn.rsplit(".", 1)[0] == pattern


def _file_in(source, patterns) -> bool:
    return any(_matches_package(source.package, pattern) for pattern in patterns)


def _import_in(imported, patterns) -> bool:
    return any(_matches_import(imported, pattern) for pattern in patterns)


def _first_match(imported, patterns):
    for pattern in patterns:
        if _matches_import(imported, pattern):
            return pattern
    return None


def _entity_names(imported, entity_types, entity_packages) -> list:
    """import 한 건이 들여오는 `@Entity` 타입의 단순 이름들. 두 표는 한 범위에서 모은 것이다."""
    if imported.wildcard:
        return sorted(entity_packages.get(imported.fqn, []))
    name = entity_types.get(imported.fqn)
    return [name] if name else []


def _observed_patterns(sources) -> list:
    """소스들의 `package` 선언을 패턴 목록으로 관측한다(D2).

    선언되지 않은 앱·공용 모듈의 패키지를 아는 유일한 방법이다. 하위 패키지는 상위 패턴에
    흡수해 목록을 뿌리만 남긴다 — 정렬하면 접두가 항상 먼저 오므로 한 번 훑으면 된다.
    """
    roots = []
    for package in sorted({source.package for source in sources if source.package}):
        if any(package == root or package.startswith(root + ".") for root in roots):
            continue
        roots.append(package)
    return [f"{root}.." for root in roots]


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


def _entity_declaration_lines(lines) -> set:
    """`@Entity`가 붙은 선언의 줄 번호 집합.

    애노테이션과 선언이 다른 줄에 있는 흔한 형태를 잡기 위해 줄 단위로 상태를 든다. 첫 칸에서
    시작하는 `@...` 줄이 애노테이션 블록을 열고, 들여쓴 줄과 닫는 괄호는 그 블록의 연속으로
    보아(여러 줄 인자) 상태를 유지하며, 빈 줄이나 다른 코드가 오면 블록이 닫힌다.
    """
    marked, pending = set(), False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            pending = False
            continue
        if line[:1] == "@":
            pending = pending or bool(RE_ENTITY.search(line))
            continue
        if line[:1].isspace() or stripped.startswith(")"):
            continue
        if pending:
            marked.add(index + 1)
        pending = False
    return marked


def _read_source(path, display):
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    package_match = RE_PACKAGE.search(text)
    package = package_match.group(1) if package_match else ""

    imports = []
    for match in RE_IMPORT.finditer(text):
        raw = match.group(1)
        wildcard = raw.endswith(".*")
        imports.append(Import(raw, raw[:-2] if wildcard else raw, wildcard,
                              _line_of(text, match.start(1))))

    entity_lines = _entity_declaration_lines(text.split("\n"))
    pattern = RE_JAVA_TYPE if path.suffix == ".java" else RE_KOTLIN_TYPE
    types = []
    for match in pattern.finditer(text):
        line = _line_of(text, match.start(1))
        entity = line in entity_lines or bool(RE_ENTITY.search(match.group(0)))
        types.append(TypeDecl(match.group(1), line, entity))

    entity_search = RE_ENTITY.search(text)
    entity_line = _line_of(text, entity_search.start()) if entity_search else 0
    return SourceFile(path, display, package, tuple(imports), tuple(types), entity_line)


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
# baseline — 동결된 기존 부채(정본 §5.1 규칙 8)
# ---------------------------------------------------------------------------

def _load_baseline(base) -> tuple:
    """`docs/architecture/baseline.jsonl`을 자동 감지한다 — (Baseline|None, [LocatedError]).

    **플래그를 두지 않는다.** 파일이 있다는 것은 그 프로젝트가 이행 중이라는 선언이고, 그때
    부채와 신규를 가르지 않은 판정은 언제나 틀린 판정이다 — 켜고 끌 대상이 아니다.
    """
    path = base / BASELINE_RELATIVE
    if not path.is_file():
        return None, []
    try:
        text = path.read_text(encoding="utf-8")
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

class _Checker:
    """한 프로젝트의 소스에 대해 그 프로젝트의 규칙을 전부 판정한다."""

    def __init__(self, report, project_root, sources, effective, derived):
        self.report = report
        self.root = project_root
        self.sources = sources
        # confine-type 위반 B는 "@Entity 타입을 참조했는가"이므로 타입 집합이 먼저 필요하다.
        # 그 집합은 **규칙의 컨텍스트 범위마다** 다르므로 범위를 키로 캐시한다(`_entities_in`).
        self._entities = {}
        # 공용 모듈의 domain 제한은 컨텍스트의 domain 패턴이 필요하다. 한 컨텍스트의
        # EffectiveRule들은 같은 layer_patterns를 들고 있으므로 아무 인스턴스나 하나면 된다.
        self.domain_patterns = {}
        for rule in effective:
            self.domain_patterns.setdefault(rule.context,
                                            rule.layer_patterns.get(DOMAIN_LAYER, []))
        self.app_paths = {rule.subject: rule.detail["module_path"]
                          for rule in derived if rule.kind == KIND_APP_CONFINEMENT}
        # `{앱}` 규약이 있으면 앱 패키지가 선언으로 존재한다 — 그때는 관측할 이유가 없다.
        self.app_patterns_table = next(
            (rule.detail["app_patterns"] for rule in derived
             if rule.kind == KIND_APP_CONFINEMENT and rule.detail.get("app_patterns")), None)
        self._app_code = None           # 공용 모듈의 to-측에 합류할 앱 패턴(한 번만 계산)
        self._dirs = {}                 # 모듈 상대경로 -> 정규화된 절대 경로(귀속 판정용)

    # -- 기록 ---------------------------------------------------------------

    def _violate(self, rule_id, source, line, message):
        self.report.violations.append(Violation(source.display, line, rule_id, message))

    def _zero(self, rule_id, subject, matched):
        if not matched:
            self.report.zero_match.append(ZeroMatch(
                rule_id, subject, f"[0건 경고] {rule_id}: {ZERO_MATCH_REASON} ({subject})"))

    def _skip(self, rule_id, subject, reason):
        self.report.skipped.append(Skip(rule_id, subject, reason))

    def _under(self, source, relative_path) -> bool:
        """파일이 그 모듈 경로 아래에 있는가 — 앱·공용 모듈의 from-측 귀속은 경로가 정한다."""
        directory = self._dirs.get(relative_path)
        if directory is None:
            directory = self._dirs[relative_path] = Path(
                os.path.normpath(self.root / relative_path))
        try:
            source.path.relative_to(directory)
        except ValueError:
            return False
        return True

    # -- 유효 규칙 ----------------------------------------------------------

    def check_effective(self, rule) -> bool:
        handler = {
            "layer-order": self._layer_order,
            "forbid-import": self._forbid_import,
            "confine-type": self._confine_type,
            "naming-suffix": self._naming_suffix,
            "forbid-sibling-dependency": self._forbid_sibling,
        }.get(rule.primitive)
        if handler is None:      # 어휘 밖 primitive는 parse_style이 이미 거부했다
            return False
        return handler(rule, f"컨텍스트 {rule.context}") is not False

    def _scope_of(self, rule) -> list:
        """컨텍스트의 전체 범위 = 그 컨텍스트에 적용되는 모든 레이어 패턴의 합집합."""
        return sorted({pattern for patterns in rule.layer_patterns.values()
                       for pattern in patterns})

    def _layer_order(self, rule, subject):
        layers = rule.params.get("layers", [])
        strict = (rule.params.get("strict") or ["false"])[0] == "true"
        patterns = {layer: rule.layer_patterns.get(layer, []) for layer in layers}
        members = {layer: [s for s in self.sources if _file_in(s, patterns[layer])]
                   for layer in layers}
        # 0건 경고는 **레이어별**이다. 규칙 단위로 묶으면 레이어 하나만 파일이 있어도 침묵하는데,
        # 어휘 §5·템플릿 §7이 지목한 실패 모드(레이어 이름과 실제 패키지의 어긋남)는 정확히 그
        # 레이어 하나에서 일어난다. 실현 패턴이 아예 없는 레이어는 여기서 다루지 않는다 —
        # 그건 resolve의 공허 레이어 경고가 이미 지목한 다른 층위다.
        for layer in layers:
            if patterns[layer]:
                self._zero(rule.rule_id, f"{subject}의 '{layer}' 레이어", members[layer])

        for inner, layer in enumerate(layers):
            for source in members[layer]:
                for imported in source.imports:
                    for index, other in enumerate(layers):
                        if index == inner or not _import_in(imported, patterns[other]):
                            continue
                        if index > inner:
                            self._violate(rule.rule_id, source, imported.line,
                                          f"컨텍스트 '{rule.context}': 안쪽 '{layer}' 레이어가 "
                                          f"바깥 '{other}' 레이어를 import합니다 — "
                                          f"{imported.text}")
                        elif strict and inner - index > 1:
                            self._violate(rule.rule_id, source, imported.line,
                                          f"컨텍스트 '{rule.context}': strict 순서에서 "
                                          f"'{layer}' 레이어는 인접 레이어에만 의존할 수 있는데 "
                                          f"'{other}' 레이어를 건너뛰어 import합니다 — "
                                          f"{imported.text}")

    def _forbid_import(self, rule, subject):
        from_patterns = rule.resolved.get("from", [])
        to_patterns = rule.resolved.get("to", [])
        sources = [s for s in self.sources if _file_in(s, from_patterns)]
        self._zero(rule.rule_id, subject, sources)
        for source in sources:
            for imported in source.imports:
                matched = _first_match(imported, to_patterns)
                if matched:
                    self._violate(rule.rule_id, source, imported.line,
                                  f"컨텍스트 '{rule.context}': 금지된 대상 '{matched}'을(를) "
                                  f"import합니다 — {imported.text}")

    def _confine_type(self, rule, subject):
        if (rule.params.get("type") or [""])[0] != JPA_ENTITY:
            return False                    # v1의 셀렉터는 jpa-entity 하나뿐이다(어휘 §3.3)
        layers = rule.params.get("allowed_layer")
        if layers:
            allowed = [pattern for layer in layers
                       for pattern in rule.layer_patterns.get(layer, [])]
        else:
            allowed = list(rule.params.get("allowed_package", []))
        if not allowed:
            # 허용 레이어가 공허하면 "범위 밖"이 곧 "전부"가 되어, 선언의 결함 하나가 파일 수만큼의
            # 위반으로 불어난다. 근본 원인은 resolve가 이미 공허 레이어 경고로 지목했으므로 여기서는
            # 판정을 세우지 않고 생략을 고지한다 — 그래야 그 경고의 문면과도 어긋나지 않는다.
            self._skip(rule.rule_id, subject,
                       f"격리 범위로 지정한 레이어 {', '.join(layers)}의 실현 패턴이 0건 — "
                       f"모든 @Entity가 범위 밖이 되어 판정이 성립하지 않습니다 "
                       f"(위 공허 레이어 경고를 먼저 해소하세요)")
            return False
        scope = self._scope_of(rule)
        # 여기서부터가 실제 판정이다 — 푸터의 범위 한계 고지는 이 지점을 밟은 실행만 낸다.
        self.report.confine_scoped = True
        scoped = [s for s in self.sources if _file_in(s, scope)]
        self._zero(rule.rule_id, subject, scoped)
        shown = ", ".join(allowed) or "없음"
        entity_types, entity_packages = self._entities_in(scope)

        for source in scoped:
            if _file_in(source, allowed):
                continue
            declared = [t for t in source.types if t.entity]
            for entity in declared:
                self._violate(rule.rule_id, source, entity.line,
                              f"컨텍스트 '{rule.context}': @Entity 타입 '{entity.name}'이(가) "
                              f"격리 범위 밖에서 선언되었습니다 (허용: {shown})")
            if not declared and source.entity_line:
                self._violate(rule.rule_id, source, source.entity_line,
                              f"컨텍스트 '{rule.context}': @Entity가 격리 범위 밖 패키지 "
                              f"'{source.package}'에서 선언되었습니다 (허용: {shown})")
            for imported in source.imports:
                names = _entity_names(imported, entity_types, entity_packages)
                if names:
                    self._violate(rule.rule_id, source, imported.line,
                                  f"컨텍스트 '{rule.context}': 격리 범위 밖에서 @Entity 타입 "
                                  f"{', '.join(names)}을(를) 참조합니다 — {imported.text} "
                                  f"(허용: {shown})")

    def _entities_in(self, scope) -> tuple:
        """그 범위 안에서 선언된 `@Entity`만 모은다 — (FQN -> 단순 이름, 패키지 -> [단순 이름]).

        **수집도 검사도 컨텍스트 범위 안에서 한다**(`rule-mappings.md` §3의 `contextScope`와 같은
        의미론이며, 그 범위를 만드는 필터도 여기 `_scope_of`와 같다). 전역으로 모으면 교차
        컨텍스트 참조 한 건이 `derived.context-isolation`과 이 규칙 양쪽에서 보고되는데,
        `allowed_layer`가 가리키는 격리 범위는 그 컨텍스트의 것이므로 남의 엔티티를 그 잣대로
        재는 것은 범주 오류다 — 사용자는 고칠 선언('### 관계' 표)이 아니라 엉뚱한
        선언(`allowed_layer`)을 보게 된다. 금지 자체는 파생 규칙이 이미 완전히 덮는다.
        """
        key = tuple(scope)
        collected = self._entities.get(key)
        if collected is None:
            types, packages = {}, {}
            for source in self.sources:
                if not _file_in(source, scope):
                    continue
                for declared in source.types:
                    if declared.entity:
                        types[f"{source.package}.{declared.name}"] = declared.name
                        packages.setdefault(source.package, []).append(declared.name)
            collected = self._entities[key] = (types, packages)
        return collected

    def _naming_suffix(self, rule, subject):
        suffixes = rule.params.get("suffixes", [])
        scoped = [s for s in self.sources if _file_in(s, rule.resolved.get("scope", []))]
        self._zero(rule.rule_id, subject, scoped)
        for source in scoped:
            for declared in source.types:
                if any(declared.name.endswith(suffix) for suffix in suffixes):
                    continue
                self._violate(rule.rule_id, source, declared.line,
                              f"컨텍스트 '{rule.context}': 최상위 public 타입 "
                              f"'{declared.name}'이(가) 접미사 "
                              f"{', '.join(suffixes)} 중 어느 것으로도 끝나지 않습니다")

    def _forbid_sibling(self, rule, subject):
        layer = (rule.params.get("layer") or [""])[0]
        suffix = (rule.params.get("suffix") or [""])[0]
        patterns = rule.layer_patterns.get(layer, [])
        scoped = [s for s in self.sources if _file_in(s, patterns)]
        self._zero(rule.rule_id, subject, scoped)
        for source in scoped:
            own = sorted({t.name for t in source.types if t.name.endswith(suffix)})
            if not own:
                continue
            for imported in source.imports:
                if imported.wildcard:
                    continue            # 와일드카드로는 어떤 타입이 들어오는지 알 수 없다
                simple = imported.fqn.rsplit(".", 1)[-1]
                if not simple.endswith(suffix) or not _import_in(imported, patterns):
                    continue
                if imported.fqn == f"{source.package}.{simple}" and simple in own:
                    continue            # 자기 자신에 대한 참조는 두 타입 간 의존이 아니다
                self._violate(rule.rule_id, source, imported.line,
                              f"컨텍스트 '{rule.context}': '{layer}' 레이어의 "
                              f"{', '.join(own)}이(가) 같은 레이어의 '{simple}'을(를) "
                              f"import합니다 — {imported.text}")

    # -- 파생 규칙 ----------------------------------------------------------

    def check_derived(self, rule) -> bool:
        if rule.kind == KIND_CONTEXT_ISOLATION:
            return self._context_isolation(rule)
        if rule.kind == KIND_APP_CONFINEMENT:
            return self._app_confinement(rule)
        if rule.kind == KIND_SHARED_MODULE_DIRECTION:
            return self._shared_module(rule)
        return False

    def _context_isolation(self, rule) -> bool:
        rule_id = derived_rule_id(rule.kind)
        sources = [s for s in self.sources if _file_in(s, rule.detail["from"])]
        self._zero(rule_id, f"컨텍스트 {rule.subject}", sources)
        for source in sources:
            for imported in source.imports:
                if _import_in(imported, rule.detail["to"]):
                    self._violate(rule_id, source, imported.line,
                                  f"컨텍스트 '{rule.subject}'가 다른 컨텍스트의 코드를 직접 "
                                  f"참조합니다 — {imported.text} "
                                  f"('### 관계' 표에 이 쌍이 없습니다)")
        return True

    def _app_confinement(self, rule) -> bool:
        rule_id = derived_rule_id(rule.kind)
        detail = rule.detail
        subject = f"앱 {rule.subject}"
        # app_patterns는 같은 프로젝트의 인스턴스들이 공유하는 dict다 — 읽기만 한다.
        table = detail.get("app_patterns")
        if table:
            own = list(table.get(rule.subject, []))
            others = {name: list(patterns) for name, patterns in table.items()
                      if name != rule.subject}
        else:
            own = _observed_patterns([s for s in self.sources
                                      if self._under(s, detail["module_path"])])
            others = {}
            for name, module_path in self.app_paths.items():
                if name == rule.subject:
                    continue
                patterns = _observed_patterns([s for s in self.sources
                                               if self._under(s, module_path)])
                if patterns:
                    others[name] = patterns
        if not own:
            self._skip(rule_id, subject,
                       f"모듈 경로 '{detail['module_path']}' 아래 .kt/.java 소스 관측 0건 — "
                       f"앱 패키지를 알 수 없어 검사하지 않았습니다 "
                       f"(패키지 규약에 '{{앱}}' 행을 두면 선언으로 알 수 있습니다)")
            return False

        sources = [s for s in self.sources
                   if self._under(s, detail["module_path"]) or _file_in(s, own)]
        self._zero(rule_id, subject, sources)

        for source in sources:
            for imported in source.imports:
                matched = _first_match(imported, detail["forbidden"])
                if matched:
                    self._violate(rule_id, source, imported.line,
                                  f"앱 '{rule.subject}'이(가) '포함 컨텍스트'에 없는 코드를 "
                                  f"import합니다 — {imported.text}")
                if _import_in(imported, own):
                    continue         # 자기 앱의 코드다
                for other, patterns in sorted(others.items()):
                    if _import_in(imported, patterns):
                        self._violate(rule_id, source, imported.line,
                                      f"앱 '{rule.subject}'이(가) 다른 앱 '{other}'의 코드를 "
                                      f"import합니다 — {imported.text} "
                                      f"(조립 지점이 두 곳으로 갈라집니다)")

        for source in self.sources:
            if self._under(source, detail["module_path"]) or _file_in(source, own):
                continue
            if not _file_in(source, detail["reverse_from"]):
                continue
            for imported in source.imports:
                if _import_in(imported, own):
                    self._violate(rule_id, source, imported.line,
                                  f"컨텍스트 코드가 앱 '{rule.subject}'의 코드를 역참조합니다 "
                                  f"— {imported.text} (조립은 앱에서만 합니다)")
        return True

    def _app_code_patterns(self) -> list:
        """공용 모듈이 참조하면 안 되는 '앱 코드'의 패턴.

        `{앱}` 규약이 있으면 그 전개형이 컨텍스트 비분할 레이어로서 이미
        `detail["forbidden"]`에 들어 있다(§6). 규약이 없으면 앱 패키지는 선언되지 않으므로
        여기서 관측한다(D2) — 관측하지 않으면 공용 모듈 → 앱 참조가 어떤 채널에도 나타나지
        않는다. 정본이 금지하는 대상은 "앱·컨텍스트 코드" 둘 다이므로 앱 쪽만 빠질 수 없다.

        프로젝트당 한 번만 계산한다. 공용 모듈이 여럿이어도 관측 0건 고지는 앱당 한 줄이다.
        """
        if self._app_code is not None:
            return self._app_code
        patterns, unobserved = [], []
        if not self.app_patterns_table:
            for name, module_path in self.app_paths.items():
                observed = _observed_patterns(
                    [s for s in self.sources if self._under(s, module_path)])
                if observed:
                    patterns.extend(observed)
                else:
                    unobserved.append(name)
        for name in unobserved:
            self._skip(derived_rule_id(KIND_SHARED_MODULE_DIRECTION), f"앱 {name}의 패키지",
                       f"모듈 경로 '{self.app_paths[name]}' 아래 .kt/.java 소스 관측 0건 — "
                       f"공용 모듈이 이 앱의 코드를 참조해도 검출하지 못합니다 "
                       f"(패키지 규약에 '{{앱}}' 행을 두면 선언으로 알 수 있습니다)")
        self._app_code = sorted(set(patterns))
        return self._app_code

    def _shared_module(self, rule) -> bool:
        rule_id = derived_rule_id(rule.kind)
        detail = rule.detail
        subject = f"공용 모듈 {rule.subject}"
        module_sources = [s for s in self.sources if self._under(s, detail["path"])]
        own = _observed_patterns(module_sources)
        if not own:
            self._skip(rule_id, subject,
                       f"경로 '{detail['path']}' 아래 .kt/.java 소스 관측 0건 — 공용 모듈의 "
                       f"패키지를 알 수 없어 검사하지 않았습니다")
            return False

        forbidden = list(detail["forbidden"]) + self._app_code_patterns()
        for source in module_sources:
            for imported in source.imports:
                if _import_in(imported, own):
                    continue
                matched = _first_match(imported, forbidden)
                if matched:
                    self._violate(rule_id, source, imported.line,
                                  f"공용 모듈 '{rule.subject}'이(가) 앱·컨텍스트 코드 "
                                  f"'{matched}'을(를) import합니다 — {imported.text} "
                                  f"(의존 방향은 한쪽입니다)")

        for context in detail["domain_restricted_contexts"]:
            patterns = self.domain_patterns.get(context, [])
            for source in self.sources:
                if not _file_in(source, patterns) or _file_in(source, own):
                    continue
                for imported in source.imports:
                    if _import_in(imported, own):
                        self._violate(rule_id, source, imported.line,
                                      f"컨텍스트 '{context}'의 domain 레이어가 역할 "
                                      f"'{detail['role']}'인 공용 모듈 '{rule.subject}'을(를) "
                                      f"import합니다 — {imported.text} "
                                      f"(domain에서 허용되는 역할은 shared-kernel뿐입니다)")
        return True


# ---------------------------------------------------------------------------
# 진입점
# ---------------------------------------------------------------------------

def check(arch_path) -> Report:
    """ARCHITECTURE.md 한 건을 해석하고 그 프로젝트들의 소스를 검사한다.

    **호출자는 report.errors가 비었는지 먼저 확인해야 한다.** 해석이 실패하면 검사 대상
    규칙 자체가 없으므로 위반 목록은 비어 있고, 그것은 '클린'과 다른 상태다.
    """
    report = Report()
    resolution = resolve_document(arch_path)
    if resolution.errors:
        report.errors = list(resolution.errors)
        return report

    # 공허 레이어 경고는 해석 단계의 사실이다 — 여기서 삼키면 그 규칙이 아무것도 검사하지
    # 않는다는 것을 알릴 곳이 사라진다(D4).
    report.inherited = [f"{arch_path}:{warning.line}: {warning.message}"
                        for warning in resolution.warnings]

    base = Path(arch_path).resolve().parent
    report.baseline, baseline_errors = _load_baseline(base)
    if baseline_errors:
        report.errors = baseline_errors
        return report
    for project in resolution.projects:
        name = project["name"]
        effective = [rule for rule in resolution.effective if rule.project == name]
        derived = [rule for rule in resolution.derived if rule.project == name]
        root = Path(os.path.normpath(base / project["path"]))
        sources, unreadable = _load_sources(root, base) if root.is_dir() else ([], [])
        report.unreadable.extend(unreadable)
        if not sources:
            reason = (f"프로젝트 '{name}'의 경로 '{project['path']}' 아래 검사할 .kt/.java "
                      f"소스가 없습니다" + ("" if root.is_dir() else " (경로가 아직 없습니다)"))
            for rule in effective:
                report.skipped.append(Skip(rule.rule_id, f"컨텍스트 {rule.context}", reason))
            for rule in derived:
                report.skipped.append(
                    Skip(derived_rule_id(rule.kind), f"대상 {rule.subject}", reason))
            continue

        checker = _Checker(report, root, sources, effective, derived)
        for rule in effective:
            if checker.check_effective(rule):
                report.checked += 1
        for rule in derived:
            if checker.check_derived(rule):
                report.checked += 1

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
    lines.append(f"검사한 규칙 {report.checked}건 / 생략한 규칙 {len(report.skipped)}건")
    if report.baseline is not None:
        matched = len({(v.rule_id, v.path) for v in report.debt})
        lines.append(
            f"기존 부채 {len(report.debt)}건 — exit 코드에 반영하지 않습니다 "
            f"({report.baseline.display}의 {len(report.baseline.keys)}개 항목 중 {matched}개가 "
            f"이번 실행의 위반과 매칭됐습니다. 나머지는 해소됐거나 이번 실행이 검사하지 않은 "
            f"규칙입니다 — 축소는 migrate만 합니다)")
    lines += [f"생략: {s.rule_id} ({s.subject}): {s.reason}" for s in report.skipped]
    if report.unreadable:
        lines.append(f"읽지 못한 소스 {len(report.unreadable)}건 — 이 파일들은 어떤 규칙도 "
                     f"검사하지 않았습니다: {', '.join(report.unreadable)}")
    lines.append(LIMITATION_NOTE)
    if report.baseline is not None:
        lines.append(BASELINE_MATCH_NOTE)
    if report.confine_scoped:
        lines.append(CONFINE_SCOPE_NOTE)
    return lines


def _payload(report) -> dict:
    return {
        "violations": [asdict(v) for v in report.violations],
        "zero_match": [asdict(w) for w in report.zero_match],
        "inherited": list(report.inherited),
        "skipped": [asdict(s) for s in report.skipped],
        "unreadable": list(report.unreadable),
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
        print("사용법: python3 check_imports.py <ARCHITECTURE.md 경로> [--json]", file=sys.stderr)
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
