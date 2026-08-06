"""infra 하네스 공용 유틸 — 상향 탐색, frontmatter/harness.yaml 파서 (python3 stdlib 전용)."""
from pathlib import Path

FM_DELIM = "---"
ENTITY_DIRS = ("providers", "inventory")

REQUIRED_FIELDS = {
    "provider": ["id", "type", "kind"],
    "server": ["id", "type", "env", "provider", "runtime", "purpose", "access", "managed_by"],
    "k8s-cluster": ["id", "type", "env", "provider", "context", "access_recipe", "managed_by"],
    "component": ["id", "type", "category", "runs_on", "installed_by"],
}


class FrontmatterError(Exception):
    pass


class HarnessYamlError(Exception):
    pass


def find_harness_root(start=None):
    cur = Path(start or Path.cwd()).resolve()
    for p in [cur, *cur.parents]:
        if (p / "harness.yaml").is_file():
            return p
    return None


def _strip_comment(line):
    out, quote = [], None
    for i, ch in enumerate(line):
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch in ('"', "'"):
            quote = ch
            out.append(ch)
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            break
        else:
            out.append(ch)
    return "".join(out).rstrip()


def _scalar(s):
    s = s.strip()
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        return [] if not inner else [_scalar(x) for x in inner.split(",")]
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        return s[1:-1]
    if s == "true":
        return True
    if s == "false":
        return False
    return s


def as_list(value):
    """frontmatter 값을 리스트로 정규화한다.

    파서는 `k: [a, b]`를 리스트로, `k: a`를 문자열로 돌려준다. 문자열을 그대로
    순회하면 글자 단위로 쪼개져 엉뚱한 결과가 나오므로 단일 값은 1원소 리스트로
    감싼다.
    """
    if value is None or value == "":
        return []
    return value if isinstance(value, list) else [value]


def parse_frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != FM_DELIM:
        raise FrontmatterError("frontmatter 시작(---)이 없음")
    fm = {}
    for raw in lines[1:]:
        if raw.strip() == FM_DELIM:
            return fm
        line = _strip_comment(raw)
        if not line.strip():
            continue
        if line != line.lstrip(" "):
            raise FrontmatterError(
                f"frontmatter는 들여쓰기 없이 'key: value' 형태여야 합니다 — 선행 공백 발견: {raw!r}")
        if ":" not in line:
            raise FrontmatterError(f"지원하지 않는 구문: {raw!r}")
        key, _, val = line.partition(":")
        if val.strip() == "":
            raise FrontmatterError(
                f"중첩 맵은 지원하지 않습니다(엔티티 frontmatter는 플랫 구조): {raw!r}")
        fm[key.strip()] = _scalar(val)
    raise FrontmatterError("frontmatter 종료(---)가 없음")


def parse_yaml_subset(text):
    """harness.yaml용 YAML 서브셋 파서 — 중첩 맵, '- ' 리스트, 인라인 [a, b], 스칼라."""
    root = {}
    # stack 원소: [indent, container, parent, key_in_parent]
    stack = [[-1, root, None, None]]
    for raw in text.splitlines():
        line = _strip_comment(raw)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        body = line.strip()
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        top = stack[-1]
        container = top[1]
        if body.startswith("- "):
            if isinstance(container, dict):
                if container:
                    raise HarnessYamlError(f"리스트 위치 오류: {raw!r}")
                new_list = []
                top[2][top[3]] = new_list  # 빈 dict 자리에 리스트로 교체
                top[1] = new_list
                container = new_list
            container.append(_scalar(body[2:]))
        elif ":" in body:
            if not isinstance(container, dict):
                raise HarnessYamlError(f"맵 위치 오류: {raw!r}")
            key, _, val = body.partition(":")
            key, val = key.strip(), val.strip()
            if val == "":
                child = {}
                container[key] = child
                stack.append([indent, child, container, key])
            else:
                container[key] = _scalar(val)
        else:
            raise HarnessYamlError(f"지원하지 않는 구문: {raw!r}")
    return root


def load_harness_yaml(path):
    return parse_yaml_subset(Path(path).read_text(encoding="utf-8"))


def iter_entities(root):
    out = []
    for d in ENTITY_DIRS:
        base = Path(root) / d
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.md")):
            try:
                fm = parse_frontmatter(path.read_text(encoding="utf-8"))
            except FrontmatterError as e:
                fm = {"_error": str(e)}
            fm["_path"] = path
            fm["_stem"] = path.stem
            out.append(fm)
    return out
