"""스타일 선언(`## 선언` 섹션) 파서 — 규칙 어휘의 시행자.

`references/knowledge/styles/<이름>.md`(프리셋)와 대상 프로젝트의
`docs/architecture/styles/<이름>.md`(커스텀)는 같은 형식을 쓴다
(`references/governance/architecture-template.md` §7). 이 모듈은 그 섹션을 읽어
레이어 목록과 규칙 인스턴스 표를 `StyleDeclaration`으로 만든다.

정본과의 대응:

- 섹션 탐색·레이어 라벨·표 형식 → `architecture-template.md` §7
- 파라미터 셀 문법(`;` 분할 → `=` 분리 → trim → `,` 분할) → `rule-vocabulary.md` §2
- 레이어 이름 해석 (가)/(나) → `rule-vocabulary.md` §2.1
- primitive별 키·필수·형식·셀렉터 → `rule-vocabulary.md` §3

이 파서의 존재 이유는 **조용한 실패를 오류로 바꾸는 것**이다(어휘 §1). 오타 난 레이어
이름이나 알 수 없는 키는 매칭 0건의 규칙을 만들고, 리포트에서 "위반 없음"과 구분되지
않는다. 따라서 해석이 불확실한 선언은 통과시키지 않고 전부 `ParseError`로 보고한다.
"""

import re
from dataclasses import dataclass

# parse_architecture.py는 이 저장소의 SSOT 파서다. 오류 타입과 표·후행 주석 처리
# 관례를 그대로 재사용해 두 파서의 동작과 오류 문체가 갈라지지 않게 한다.
from parse_architecture import ParseError, _header_cells, _split_row, _strip_comment


PRIMITIVES = {
    #  primitive: {키: (필수?, 목록?)}  — 목록?=False면 항목 2개 이상 오류(어휘 §2)
    "layer-order": {"layers": (True, True), "strict": (False, False)},
    "forbid-import": {"from": (True, True), "to": (True, True)},
    "confine-type": {"type": (True, False), "allowed_layer": (False, True), "allowed_package": (False, True)},
    "naming-suffix": {"scope": (True, False), "suffixes": (True, True)},
    "forbid-sibling-dependency": {"layer": (True, False), "suffix": (True, False)},
}
SELECTORS = {"jpa-entity"}          # confine-type의 type 정규 값 (어휘 §3.3)
GA_PARAMS = {("forbid-import", "from"), ("forbid-import", "to"), ("naming-suffix", "scope")}   # §2.1(가)
NA_PARAMS = {("layer-order", "layers"), ("confine-type", "allowed_layer"), ("forbid-sibling-dependency", "layer")}  # §2.1(나)

# confine-type의 격리 범위 지정 키 — 정확히 하나만 있어야 한다(어휘 §3.3)
CONFINE_SCOPE_KEYS = ("allowed_layer", "allowed_package")
BOOLEAN_VALUES = ("true", "false")

DECLARATION_HEADING = "## 선언"

RE_H2 = re.compile(r"^##\s")                       # '###'는 매칭하지 않는다
RE_LAYER_LABEL = re.compile(r"^-\s*레이어\s*:\s*(.*)$")
RE_TABLE = re.compile(r"^\|")
RE_WHITESPACE = re.compile(r"\s")


@dataclass(frozen=True)
class RuleInstance:
    rule_id: str
    primitive: str
    params: dict      # 키 -> 항목 목록(list[str]). 모든 값은 목록(길이 1 포함)
    line: int         # 표 행의 1-기준 라인

    # 선언에 없는 선택 키의 기본값(어휘 §3의 '기본값' 열, 예: strict=false)은 여기서
    # 채우지 않는다. 파싱 결과는 "문서에 쓰인 것"이고, 기본값 적용은 규칙 해석
    # 단계(resolve_rules)의 몫이다.


@dataclass
class StyleDeclaration:
    name: str         # 파일명에서 유도한 스타일 이름
    layers: list      # ["domain", "application", "adapter"] — 선언 순서 그대로
    rules: list       # [RuleInstance]


def _find_declaration_section(lines: list) -> tuple:
    """`## 선언` 섹션의 (헤딩 인덱스, 끝 인덱스)를 찾는다. 없으면 None.

    헤딩은 **줄 전체 정확 일치**로만 찾는다 — `### 선언`은 매칭하지 않는다
    (템플릿 §7: 레벨 2는 권고가 아니라 요구다). 섹션은 다음 `##` 헤딩에서 끝난다.
    """
    start = None
    for i, line in enumerate(lines):
        if line.strip() == DECLARATION_HEADING:
            start = i
            break
    if start is None:
        return None

    end = len(lines)
    for j in range(start + 1, len(lines)):
        if RE_H2.match(lines[j].strip()):
            end = j
            break
    return start, end


def _parse_layers(lines: list, start: int, end: int, style_name: str, errors: list) -> list:
    """섹션의 `- 레이어:` 라벨을 읽어 레이어 이름 목록을 만든다(오류는 errors에 누적).

    라벨이 여러 번 나오면 마지막 값이 남는다(parse_architecture의 라벨 관례와 같다).
    """
    raw_value = None
    label_line = None
    for i in range(start + 1, end):
        # 들여쓴 줄은 라벨이 아니다 — parse_architecture의 RE_LABEL과 같은 관례.
        match = RE_LAYER_LABEL.match(lines[i])
        if match:
            raw_value = match.group(1)
            label_line = i + 1

    if label_line is None:
        errors.append(ParseError(
            start + 1,
            f"스타일 '{style_name}': '- 레이어:' 라벨이 없습니다 "
            f"(형식: - 레이어: <이름1>, <이름2>).",
        ))
        return []

    names = [name.strip() for name in _strip_comment(raw_value).split(",") if name.strip()]
    if not names:
        errors.append(ParseError(
            label_line,
            f"스타일 '{style_name}': '- 레이어:' 목록이 비어 있습니다 "
            f"(레이어 이름을 쉼표로 나열하세요).",
        ))
        return []

    unique = []
    for name in names:
        if name in unique:
            errors.append(ParseError(
                label_line,
                f"스타일 '{style_name}': 레이어 이름 '{name}'이(가) 중복되었습니다.",
            ))
        else:
            unique.append(name)
    return unique


def _find_rule_table(lines: list, start: int, end: int) -> tuple:
    """섹션 안의 **첫** 표 블록을 (블록, 시작 인덱스)로 반환한다. 없으면 (None, None)."""
    for i in range(start + 1, end):
        if RE_TABLE.match(lines[i]):
            block = []
            j = i
            while j < end and RE_TABLE.match(lines[j]):
                block.append(lines[j])
                j += 1
            return block, i
    return None, None


def _parse_param_cell(cell: str, rule_id: str, line: int, errors: list) -> tuple:
    """파라미터 셀을 어휘 §2의 절차대로 파싱해 (params, cell_ok)를 반환한다.

    `cell_ok=False`는 키가 값을 제대로 묶지 못한 오류가 있었다는 뜻이다. 이때 호출자는
    '필수 키 누락'처럼 **키의 존재**를 보는 검사를 건너뛴다 — 오타 하나가 두 개의 오류로
    불어나 진짜 원인을 가리는 것을 막기 위해서다.
    """
    params = {}
    cell_ok = True

    if not cell:
        errors.append(ParseError(line, f"규칙 '{rule_id}': 파라미터 셀이 비어 있습니다."))
        return params, False

    for piece in cell.split(";"):                       # 1. 셀을 ';'로 분할
        if not piece.strip():
            errors.append(ParseError(
                line,
                f"규칙 '{rule_id}': 빈 파라미터가 있습니다 (후행 또는 연속된 ';'를 제거하세요).",
            ))
            cell_ok = False
            continue

        equals = piece.count("=")                       # 2. '=' 하나로 키와 값을 나눈다
        if equals != 1:
            detail = "'=' 없음" if equals == 0 else f"'=' {equals}개"
            errors.append(ParseError(
                line,
                f"규칙 '{rule_id}': 파라미터 '{piece.strip()}'이(가) '키=값' 형식이 아닙니다 ({detail}).",
            ))
            cell_ok = False
            continue

        raw_key, raw_value = piece.split("=", 1)
        key = raw_key.strip()                           # 3. 키와 값을 trim
        value = raw_value.strip()

        if not key:
            errors.append(ParseError(line, f"규칙 '{rule_id}': 빈 키가 있습니다 ('{piece.strip()}')."))
            cell_ok = False
            continue
        if RE_WHITESPACE.search(key):
            errors.append(ParseError(line, f"규칙 '{rule_id}': 키 '{key}'에 공백이 있습니다."))
            cell_ok = False
            continue
        if key in params:
            errors.append(ParseError(
                line,
                f"규칙 '{rule_id}': 키 '{key}'가 중복되었습니다 (목록은 ','로 씁니다).",
            ))
            continue
        if not value:
            errors.append(ParseError(line, f"규칙 '{rule_id}': 키 '{key}'의 값이 빈 값입니다."))
            cell_ok = False
            continue

        items = []
        for raw_item in value.split(","):               # 4. 값을 ','로 분할하고 항목마다 trim
            item = raw_item.strip()
            if not item:
                errors.append(ParseError(
                    line,
                    f"규칙 '{rule_id}': 키 '{key}'에 빈 항목이 있습니다 ('{value}').",
                ))
                continue
            if RE_WHITESPACE.search(item):
                errors.append(ParseError(
                    line,
                    f"규칙 '{rule_id}': 키 '{key}'의 항목 '{item}'에 공백이 있습니다 "
                    f"(항목은 공백을 포함할 수 없습니다).",
                ))
                continue
            items.append(item)

        if not items:
            cell_ok = False
            continue
        params[key] = items

    return params, cell_ok


def _check_schema(rule: RuleInstance, cell_ok: bool, errors: list) -> None:
    """primitive가 정의한 키·형식·정규 값에 맞는지 검사한다(어휘 §2·§3)."""
    spec = PRIMITIVES[rule.primitive]

    for key, items in rule.params.items():
        if key not in spec:
            errors.append(ParseError(
                rule.line,
                f"규칙 '{rule.rule_id}': primitive '{rule.primitive}'에 알 수 없는 키 '{key}'입니다 "
                f"(허용 키: {sorted(spec)}).",
            ))
            continue
        _required, is_list = spec[key]
        if not is_list and len(items) > 1:
            errors.append(ParseError(
                rule.line,
                f"규칙 '{rule.rule_id}': 키 '{key}'는 목록 형식이 아닌데 항목이 {len(items)}개입니다 "
                f"({', '.join(items)}).",
            ))

    if rule.primitive == "layer-order":
        for item in rule.params.get("strict", []):
            if item not in BOOLEAN_VALUES:
                errors.append(ParseError(
                    rule.line,
                    f"규칙 '{rule.rule_id}': strict 값 '{item}'이(가) 올바르지 않습니다 "
                    f"(허용값: {list(BOOLEAN_VALUES)}).",
                ))

    if rule.primitive == "confine-type":
        for item in rule.params.get("type", []):
            if item not in SELECTORS:
                errors.append(ParseError(
                    rule.line,
                    f"규칙 '{rule.rule_id}': 등록되지 않은 셀렉터 '{item}'입니다 "
                    f"(등록된 셀렉터: {sorted(SELECTORS)}).",
                ))

    if not cell_ok:
        # 키가 값을 묶지 못한 셀이다 — 존재 여부를 보는 아래 검사는 신뢰할 수 없다.
        return

    for key, (required, _is_list) in spec.items():
        if required and key not in rule.params:
            errors.append(ParseError(
                rule.line,
                f"규칙 '{rule.rule_id}': primitive '{rule.primitive}'의 필수 키 '{key}'가 없습니다.",
            ))

    if rule.primitive == "confine-type":
        present = [key for key in CONFINE_SCOPE_KEYS if key in rule.params]
        if len(present) != 1:
            found = ", ".join(present) if present else "없음"
            errors.append(ParseError(
                rule.line,
                f"규칙 '{rule.rule_id}': allowed_layer와 allowed_package 중 정확히 하나만 있어야 합니다 "
                f"(현재: {found}).",
            ))


def _check_layer_references(rule: RuleInstance, layers: list, errors: list) -> None:
    """레이어 이름을 받는 파라미터의 항목을 어휘 §2.1로 판별한다.

    (나)는 선언된 레이어만 받는다. (가)는 레이어 이름 또는 패키지 패턴을 받되,
    `.`이 없으면서 레이어도 아닌 항목은 매칭 0건의 규칙이 되므로 오류로 막는다.
    """
    declared = ", ".join(layers)
    for key, items in rule.params.items():
        pair = (rule.primitive, key)
        if pair in NA_PARAMS:
            for item in items:
                if item not in layers:
                    errors.append(ParseError(
                        rule.line,
                        f"규칙 '{rule.rule_id}': 키 '{key}'의 '{item}'은(는) 이 스타일이 선언한 "
                        f"레이어가 아닙니다 (선언된 레이어: {declared}).",
                    ))
        elif pair in GA_PARAMS:
            for item in items:
                if item not in layers and "." not in item:
                    errors.append(ParseError(
                        rule.line,
                        f"규칙 '{rule.rule_id}': 키 '{key}'의 '{item}'은(는) 선언된 레이어도 아니고 "
                        f"패키지 패턴도 아닙니다 ('.'이 없습니다). 레이어라면 오타를 고치고, "
                        f"최상위 패키지라면 '{item}..'처럼 '..'를 붙이세요 "
                        f"(선언된 레이어: {declared}).",
                    ))


def _parse_rules(block: list, block_start: int, style_name: str, errors: list) -> list:
    """규칙 표 블록(헤더+구분선+데이터 행)을 [RuleInstance]로 만든다.

    열 순서는 고정이다 — 규칙 id, primitive, 파라미터(템플릿 §7).
    """
    header = _header_cells(block[0])
    ncols = max(len(header), 3)
    data_lines = block[2:]

    if not data_lines:
        errors.append(ParseError(
            block_start + 1,
            f"스타일 '{style_name}': 규칙 표에 규칙이 한 개도 없습니다 "
            f"(선언만 되고 강제되지 않는 스타일이 됩니다).",
        ))
        return []

    rules = []
    for offset, line_text in enumerate(data_lines):
        lineno = block_start + 3 + offset      # 헤더·구분선 두 줄을 건너뛴 1-기준 라인
        cells = _split_row(line_text, ncols)
        rule_id, primitive, cell = cells[0], cells[1], cells[2]

        params, cell_ok = _parse_param_cell(cell, rule_id, lineno, errors)
        rule = RuleInstance(rule_id=rule_id, primitive=primitive, params=params, line=lineno)
        rules.append(rule)

        if primitive not in PRIMITIVES:
            # 어휘는 닫혀 있다(§1). 스키마를 모르므로 이 행의 키 검사는 하지 않는다.
            errors.append(ParseError(
                lineno,
                f"규칙 '{rule_id}': primitive '{primitive}'은(는) 어휘에 없습니다 "
                f"(허용: {sorted(PRIMITIVES)}).",
            ))
            continue

        _check_schema(rule, cell_ok, errors)

    return rules


def _check_duplicate_rule_ids(rules: list, style_name: str, errors: list) -> None:
    """규칙 id 중복을 보고한다 — id는 컨텍스트가 예외를 지목하는 유일한 수단이다(어휘 §4)."""
    first_seen = {}
    for rule in rules:
        if rule.rule_id in first_seen:
            errors.append(ParseError(
                rule.line,
                f"스타일 '{style_name}': 규칙 id '{rule.rule_id}'이(가) 중복되었습니다 "
                f"(처음 등장: {first_seen[rule.rule_id]}번째 줄).",
            ))
        else:
            first_seen[rule.rule_id] = rule.line


def parse_style(text: str, style_name: str, path: str = "<style>") -> tuple:
    """(StyleDeclaration | None, [ParseError]) — 오류가 있어도 파싱 가능한 부분은 채운다.

    `## 선언` 섹션 자체가 없을 때만 선언이 None이다. 그 밖의 오류(문법·어휘·레이어)는
    선언을 돌려주면서 함께 보고하므로, **호출자는 errors가 비었는지 먼저 확인해야 한다.**

    `path`는 호출자가 오류를 `경로:라인: 메시지`로 출력할 때 쓰는 파일 이름이다. 메시지
    본문에는 넣지 않는다 — parse_architecture와 같은 출력 관례를 유지하기 위해서다.
    """
    lines = text.split("\n")
    errors = []

    section = _find_declaration_section(lines)
    if section is None:
        errors.append(ParseError(
            0,
            f"스타일 '{style_name}': '## 선언' 섹션이 없습니다 "
            f"('### 선언'은 매칭하지 않습니다 — 레벨 2 헤딩이어야 합니다).",
        ))
        return None, errors

    start, end = section
    layers = _parse_layers(lines, start, end, style_name, errors)

    block, block_start = _find_rule_table(lines, start, end)
    if block is None:
        errors.append(ParseError(
            start + 1,
            f"스타일 '{style_name}': 규칙 표가 없습니다 "
            f"(열 순서 고정: 규칙 id | primitive | 파라미터).",
        ))
        rules = []
    else:
        rules = _parse_rules(block, block_start, style_name, errors)

    _check_duplicate_rule_ids(rules, style_name, errors)

    # 레이어 목록 자체가 없거나 비면 판별의 기준이 없다. 이때 모든 항목을 "레이어가
    # 아니다"로 보고하면 진짜 원인(라벨 오류) 하나가 규칙 수만큼의 오류에 묻힌다.
    if layers:
        for rule in rules:
            _check_layer_references(rule, layers, errors)

    return StyleDeclaration(name=style_name, layers=layers, rules=rules), errors


if __name__ == "__main__":
    import sys
    from pathlib import Path

    if len(sys.argv) < 2:
        print("사용법: python3 parse_style.py <스타일 문서 경로>", file=sys.stderr)
        sys.exit(2)

    style_path = sys.argv[1]
    try:
        document = open(style_path, encoding="utf-8").read()
    except FileNotFoundError:
        print(f"오류: {style_path} 파일이 없습니다.", file=sys.stderr)
        sys.exit(1)

    declaration, parse_errors = parse_style(document, Path(style_path).stem, style_path)
    if parse_errors:
        for error in sorted(parse_errors, key=lambda e: e.line):
            print(f"{style_path}:{error.line}: {error.message}", file=sys.stderr)
        sys.exit(1)
    print(f"OK: 스타일 {declaration.name}, 레이어 {len(declaration.layers)}, "
          f"규칙 {len(declaration.rules)}")
