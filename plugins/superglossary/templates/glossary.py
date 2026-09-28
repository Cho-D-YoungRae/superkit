#!/usr/bin/env python3
"""프로젝트 용어사전 CLI (의존성 0 — Python 3 표준 라이브러리만 사용).

사용자 프로젝트의 `.claude/superglossary/`로 복사되어 동작한다.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

VERSION = "0.5.0"

# glossary.json 데이터 스키마 버전. 구조가 바뀔 때만 올린다(CLI 버전과 별개).
#   0 → schemaVersion 필드가 없던 0.4.0 이전 파일
#   1 → schemaVersion·stopwords 도입
SCHEMA_VERSION = 1

AUTOGEN = "<!-- 이 파일은 glossary.json에서 자동 생성됩니다. 직접 편집하지 마세요. (glossary.py build) -->"

RULE_COMMENT = "<!-- 규칙: 단일어만 등록·조합해 사용한다. 축약어는 이 표에 등록된 것만 허용한다. -->"

CORE_SPLIT_THRESHOLD = 180


class GlossaryError(Exception):
    """사용자에게 그대로 보여줄 수 있는 오류."""


class ViolationsFound(Exception):
    """lint --strict에서 [위반]이 있을 때. 결과(output)는 그대로 출력하고 종료 코드만 1로 만든다."""

    def __init__(self, output):
        super().__init__(output)
        self.output = output


def write_text(path, text):
    """임시 파일에 쓴 뒤 교체한다 — 쓰는 도중 실패해도 원본이 반쯤 잘린 채 남지 않는다."""
    if os.path.exists(path):
        mode = os.stat(path).st_mode & 0o7777
    else:
        umask = os.umask(0)
        os.umask(umask)
        mode = 0o666 & ~umask
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(path)),
                               prefix=f".{os.path.basename(path)}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.chmod(tmp, mode)  # mkstemp는 0600으로 만든다
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def migrate(data):
    """구 스키마 데이터를 현재 스키마로 올린다(메모리 상). 변경이 있었으면 True."""
    version = data.get("schemaVersion", 0)
    if not isinstance(version, int) or isinstance(version, bool):
        raise GlossaryError(f"glossary.json의 schemaVersion이 정수가 아닙니다: {json.dumps(version, ensure_ascii=False)}")
    if version > SCHEMA_VERSION:
        raise GlossaryError(
            f"glossary.json이 스키마 v{version}인데 이 CLI는 v{SCHEMA_VERSION}까지 지원합니다. "
            "CLI가 오래됐습니다 — /superglossary:init을 재실행해 갱신하세요."
        )
    if version == SCHEMA_VERSION:
        return False
    # v0 → v1: 0.3.0 이전 파일은 avoid 등 일부 필드가 없을 수 있다.
    # 구조가 틀린 항목은 건너뛰고 validate()가 보고하게 둔다.
    terms = data.get("terms")
    for term in terms if isinstance(terms, list) else []:
        if isinstance(term, dict):
            term.setdefault("abbreviation", None)
            term.setdefault("description", "")
            term.setdefault("relatedElements", [])
            term.setdefault("avoid", [])
    data["schemaVersion"] = SCHEMA_VERSION
    return True


def _is_str_list(value):
    return isinstance(value, list) and all(isinstance(v, str) for v in value)


def validate(data):
    """손으로 편집한 glossary.json의 구조를 검사한다. 용어 간 충돌은 find_all_conflicts가 본다."""
    terms = data.get("terms")
    if not isinstance(terms, list):
        raise GlossaryError("glossary.json의 terms는 배열이어야 합니다.")
    for i, term in enumerate(terms):
        if not isinstance(term, dict):
            raise GlossaryError(f"glossary.json terms[{i}]: 용어는 객체여야 합니다.")
        korean = term.get("korean")
        where = f"glossary.json terms[{i}]" + (f"({korean})" if isinstance(korean, str) and korean.strip() else "")
        for key in ("korean", "english"):
            value = term.get(key)
            if not isinstance(value, str) or not value.strip():
                raise GlossaryError(f"{where}: {key}가 비어 있거나 문자열이 아닙니다.")
        for key in ("abbreviation", "description"):
            if term.get(key) is not None and not isinstance(term[key], str):
                raise GlossaryError(f"{where}: {key}는 문자열 또는 null이어야 합니다.")
        for key in ("relatedElements", "avoid"):
            if term.get(key) is not None and not _is_str_list(term[key]):
                raise GlossaryError(f"{where}: {key}는 문자열 배열이어야 합니다.")
    stopwords = data.get("stopwords")
    if stopwords is not None:
        if not isinstance(stopwords, dict):
            raise GlossaryError('glossary.json의 stopwords는 {"add": [...], "remove": [...]} 형태의 객체여야 합니다.')
        for key in ("add", "remove"):
            if stopwords.get(key) is not None and not _is_str_list(stopwords[key]):
                raise GlossaryError(f"glossary.json의 stopwords.{key}는 문자열 배열이어야 합니다.")


def load_glossary(directory):
    path = os.path.join(directory, "glossary.json")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise GlossaryError("용어사전이 없습니다. /superglossary:init(또는 glossary.py init)을 먼저 실행하세요.")
    except ValueError as err:  # JSONDecodeError·UnicodeDecodeError
        raise GlossaryError(f"glossary.json을 읽을 수 없습니다({path}): {err}")
    if not isinstance(data, dict):
        raise GlossaryError("glossary.json의 최상위는 객체여야 합니다.")
    migrate(data)
    validate(data)
    return data


def find_all_conflicts(data):
    """사전 전체의 용어 간 충돌. 각 용어를 앞선 용어들과만 비교해도 모든 쌍이 검사된다."""
    terms = data["terms"]
    conflicts = []
    for i, t in enumerate(terms):
        conflict = find_conflict(terms[:i], t["korean"], t["english"], t.get("abbreviation"), avoid_of(t))
        if conflict:
            conflicts.append(f"{t['korean']}: {conflict}")
    return conflicts


def assert_consistent(data):
    conflicts = find_all_conflicts(data)
    if conflicts:
        raise GlossaryError(
            "용어사전에 충돌이 있습니다. glossary.json을 고치거나 update/remove로 해소하세요.\n"
            + "\n".join(f"  - {c}" for c in conflicts)
        )


def save_glossary(directory, data):
    # 충돌이 남은 사전은 디스크에 쓰지 않는다(손으로 고친 파일의 충돌도 여기서 걸린다).
    assert_consistent(data)
    # schemaVersion을 항상 첫 키로 써서 파일을 열었을 때 바로 보이게 한다.
    ordered = {"schemaVersion": data.get("schemaVersion", SCHEMA_VERSION)}
    ordered.update({k: v for k, v in data.items() if k != "schemaVersion"})
    write_text(os.path.join(directory, "glossary.json"), json.dumps(ordered, ensure_ascii=False, indent=2) + "\n")


def sorted_terms(data):
    # 한글 음절(U+AC00~U+D7A3)은 코드포인트 순서가 곧 가나다순이다.
    return sorted(data["terms"], key=lambda t: t["korean"])


def avoid_of(term):
    return term.get("avoid") or []


def related_of(term):
    return term.get("relatedElements") or []


def find_conflict(other_terms, korean, english, abbreviation=None, avoid=()):
    e = english.lower() if english else None
    a = abbreviation.lower() if abbreviation else None
    av = [s.lower() for s in avoid]
    if e and e in av:
        return f"금지 변형 '{english}'이(가) 자신의 영문과 같습니다"
    if a and a in av:
        return f"금지 변형 '{abbreviation}'이(가) 자신의 축약어와 같습니다"
    for t in other_terms:
        te = t["english"].lower()
        ta = t["abbreviation"].lower() if t.get("abbreviation") else None
        tav = [s.lower() for s in avoid_of(t)]
        if t["korean"] == korean:
            return f"이미 등록된 한글: {korean} → {t['english']}"
        if e == te:
            return f"이미 등록된 영문: {english} ({t['korean']})"
        if e and e == ta:
            return f"이미 등록된 축약어와 충돌: {english} ({t['korean']})"
        if e and e in tav:
            return f"'{english}'은(는) 금지 변형입니다. 표준: {t['english']}({t['korean']})"
        if a and a == ta:
            return f"이미 등록된 축약어: {abbreviation} ({t['korean']})"
        if a and a == te:
            return f"이미 등록된 영문과 충돌: {abbreviation} ({t['korean']})"
        if a and a in tav:
            return f"'{abbreviation}'은(는) 금지 변형입니다. 표준: {t['english']}({t['korean']})"
        for v in av:
            if v == te or v == ta:
                return f"금지 변형 '{v}'이(가) 등록 용어 {t['korean']}({t['english']})과(와) 충돌합니다"
            if v in tav:
                return f"금지 변형 '{v}'은(는) 이미 {t['korean']}({t['english']})의 금지 목록에 있습니다"
    return None


def require_names(korean, english):
    if not (korean or "").strip() or not (english or "").strip():
        raise GlossaryError("korean과 english는 필수입니다.")


def add_term(data, korean, english, abbreviation=None, description="", related_elements=None, avoid=None):
    require_names(korean, english)
    related_elements = list(related_elements or [])
    avoid = list(avoid or [])
    check_avoid_words(avoid)
    conflict = find_conflict(data["terms"], korean, english, abbreviation, avoid)
    if conflict:
        raise GlossaryError(conflict)
    data["terms"].append({
        "korean": korean,
        "english": english,
        "abbreviation": abbreviation,
        "description": description,
        "relatedElements": related_elements,
        "avoid": avoid,
    })
    return data


def find_term(data, korean):
    for t in data["terms"]:
        if t["korean"] == korean:
            return t
    return None


def update_term(data, korean, fields):
    term = find_term(data, korean)
    if term is None:
        raise GlossaryError(f"등록되지 않은 용어: {korean}")
    nxt = dict(term)
    for key in ("english", "abbreviation", "description", "relatedElements", "avoid"):
        if key in fields:
            nxt[key] = fields[key]
    require_names(nxt["korean"], nxt["english"])
    if "avoid" in fields:
        # 기존 값은 막지 않는다 — 다른 필드만 고치는 update가 옛 데이터 때문에 실패하지 않도록.
        check_avoid_words(fields["avoid"])
    others = [t for t in data["terms"] if t["korean"] != korean]
    conflict = find_conflict(
        others, nxt["korean"], nxt["english"], nxt.get("abbreviation"), avoid_of(nxt)
    )
    if conflict:
        raise GlossaryError(conflict)
    term.update(nxt)
    return data


def remove_term(data, korean):
    for i, t in enumerate(data["terms"]):
        if t["korean"] == korean:
            del data["terms"][i]
            return data
    raise GlossaryError(f"등록되지 않은 용어: {korean}")


def list_terms(data):
    return sorted_terms(data)


def lookup(data, query):
    q = query.lower()
    result = []
    for t in sorted_terms(data):
        abbr = t.get("abbreviation")
        if q in t["korean"].lower() or q in t["english"].lower() or (abbr and q in abbr.lower()):
            result.append(t)
    return result


def format_term_detail(t):
    abbr = f" (축약: {t['abbreviation']})" if t.get("abbreviation") else ""
    lines = [f"{t['korean']} → {t['english']}{abbr}"]
    if t.get("description"):
        lines.append(f"  설명: {t['description']}")
    if related_of(t):
        lines.append(f"  관련: {', '.join(related_of(t))}")
    if avoid_of(t):
        lines.append(f"  금지: {', '.join(avoid_of(t))}")
    return "\n".join(lines)


def escape_cell(value):
    return re.sub(r"\r?\n", "<br>", str(value if value is not None else "").replace("|", "\\|"))


def render_core(data):
    terms = sorted_terms(data)
    rows = "\n".join(
        f"| {escape_cell(t['korean'])} | {escape_cell(t['english'])} | {escape_cell(t.get('abbreviation') or '')} |"
        for t in terms
    )
    avoided = [t for t in terms if avoid_of(t)]
    if avoided:
        summary = "\n".join(
            f"- {', '.join(avoid_of(t))} → {t['english']}({t['korean']})" for t in avoided
        )
        avoid_block = f"\n금지 변형(대신 표준 사용):\n{summary}\n"
    else:
        avoid_block = ""
    return (
        f"{AUTOGEN}\n{RULE_COMMENT}\n\n"
        "| 한글 | 영문 | 축약 |\n| --- | --- | --- |\n"
        f"{rows}\n{avoid_block}"
    )


def render_terms(data):
    rows = "\n".join(
        "| {} | {} | {} | {} | {} | {} |".format(
            escape_cell(t["korean"]),
            escape_cell(t["english"]),
            escape_cell(t.get("abbreviation") or ""),
            escape_cell(t.get("description") or ""),
            escape_cell(", ".join(related_of(t))),
            escape_cell(", ".join(avoid_of(t))),
        )
        for t in sorted_terms(data)
    )
    return (
        f"{AUTOGEN}\n\n"
        "| 한글 | 영문 | 축약 | 설명 | 관련 요소 | 금지 |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        f"{rows}\n"
    )


def build(directory):
    data = load_glossary(directory)
    assert_consistent(data)
    core = render_core(data)
    write_text(os.path.join(directory, "core.md"), core)
    write_text(os.path.join(directory, "terms.md"), render_terms(data))
    notices = []
    lines = len(core.split("\n"))
    if lines > CORE_SPLIT_THRESHOLD:
        notices.append(f"안내: core.md가 {lines}줄입니다. core.md는 매 세션 컨텍스트에 올라가므로 "
                       "쓰지 않는 용어는 remove로 정리하세요.")
    for t in data["terms"]:
        for v in avoid_of(t):
            if not is_single_word(v):
                notices.append(f"안내: {t['korean']}의 금지 변형 '{v}'은(는) 단일어가 아니라 lint가 잡지 못합니다. "
                               "update --avoid로 단일어로 바꾸세요.")
    return "\n".join(notices) or None


def is_stale(directory, data):
    for name, render in (("core.md", render_core), ("terms.md", render_terms)):
        path = os.path.join(directory, name)
        if not os.path.exists(path):
            return True
        with open(path, encoding="utf-8") as f:
            if f.read() != render(data):
                return True
    return False


def warn_if_stale(directory, data):
    if is_stale(directory, data):
        print("⚠ core.md/terms.md가 glossary.json과 다릅니다. 'glossary.py build'를 실행하세요.", file=sys.stderr)


def tokenize(identifier):
    # 약어 경계(HTTPServer → HTTP Server)를 먼저 나눈다. 뒤따르는 소문자가 2자 이상일 때만
    # 나눠야 복수형 약어(URLs·IDs)가 UR+Ls처럼 쪼개지지 않는다.
    spaced = re.sub(r"([A-Z]+)([A-Z][a-z]{2,})", r"\1 \2", identifier)
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", spaced)
    return [part.lower() for part in re.split(r"[_\s]+", spaced) if part]


def is_single_word(value):
    """lint 토큰 하나로 매칭될 수 있는 값인가(영문·숫자만, 쪼개면 한 단어)."""
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", value)) and len(tokenize(value)) == 1


def check_avoid_words(avoid):
    for v in avoid:
        if not is_single_word(v):
            raise GlossaryError(
                f"금지 변형 '{v}'은(는) 단일어여야 합니다 — lint는 식별자를 단어로 나눠 비교하므로 "
                "여러 단어짜리 변형은 잡히지 않습니다(예: cust_no → cust)."
            )


# 결정 #11: 언어 키워드·표준 타입·기술 계층 어휘만 포함한다.
# 도메인 개연성이 있는 일반명사(user, order, item, price, status, state 등)는 넣지 않는다.
STOPWORDS = {
    # 언어 키워드 (JS/TS/Java/Kotlin/Python/Go/SQL)
    "abstract", "and", "as", "assert", "async", "await", "boolean", "break", "byte", "case", "cascade",
    "catch", "chan", "char", "class", "const", "constraint", "continue", "def", "default", "defer",
    "delete", "do", "double", "elif", "else", "enum", "except", "exists", "export", "extends", "false",
    "final", "finally", "float", "for", "foreign", "from", "fun", "func", "function", "global", "go",
    "having", "if", "implements", "import", "in", "init", "inner", "insert", "instanceof", "int",
    "interface", "internal", "is", "join", "key", "lambda", "left", "let", "like", "limit", "long",
    "module", "namespace", "new", "nil", "none", "nonlocal", "not", "null", "object", "of", "offset",
    "open", "or", "outer", "override", "package", "pass", "primary", "private", "protected", "public",
    "raise", "range", "readonly", "references", "require", "return", "right", "sealed", "select",
    "self", "short", "static", "struct", "super", "switch", "table", "this", "throw", "throws", "true",
    "try", "type", "typeof", "union", "unique", "val", "var", "void", "when", "where", "while", "with", "yield",
    # 표준 타입·라이브러리 어휘
    "array", "bigdecimal", "bigint", "biginteger", "buffer", "bytes", "calendar", "collection",
    "collections", "column", "com", "console", "date", "datetime", "dict", "duration", "error",
    "errors", "example", "exception", "file", "files", "fs", "http", "https", "index", "instant",
    "integer", "io", "iterator", "java", "javax", "json", "kotlin", "list", "local", "locale", "map",
    "math", "net", "node", "number", "optional", "os", "path", "process", "promise", "regex",
    "runtime", "set", "sql", "stream", "string", "sys", "time", "timestamp", "tuple", "uri", "url",
    "util", "utils", "uuid", "xml", "zone", "zoned",
    # 범용 프로그래밍 어휘
    "add", "app", "application", "apply", "arg", "args", "bar", "baz", "bin", "build", "builder",
    "by", "call", "check", "config", "configuration", "context", "convert", "count", "create",
    "current", "data", "dist", "doc", "docs", "empty", "execute", "fetch", "find", "first", "foo",
    "format", "get", "handle", "handler", "impl", "info", "invoke", "last", "length", "lib", "load",
    "main", "make", "max", "meta", "min", "mock", "next", "now", "old", "on", "opts", "options",
    "param", "params", "parse", "prev", "read", "remove", "request", "response", "result", "results",
    "run", "save", "size", "spec", "src", "start", "stop", "stub", "sum", "temp", "test", "tests",
    "tmp", "to", "token", "update", "validate", "value", "values", "verify", "view", "write",
    # 기술 계층 어휘 (결정 #11)
    "adapter", "api", "cli", "controller", "dao", "db", "dto", "entity", "facade", "factory", "grpc",
    "manager", "model", "orm", "provider", "proxy", "repository", "rest", "sdk", "service",
    "singleton", "ui", "vo",
}

# 탐색에서 제외할 디렉토리 — 생성물·의존성·VCS 메타데이터, Claude Code 설정(.claude — 용어사전 자신 포함).
IGNORED_DIRS = {
    ".claude", ".git", ".hg", ".svn", ".idea", ".vscode", ".gradle", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".next", ".nuxt", ".venv", "venv", "__pycache__", "node_modules",
    "dist", "build", "out", "target", "vendor", "coverage",
}

# 제외할 생성 파일 — 락 파일·번들 산출물. 해시·압축 코드가 무의미한 토큰을 쏟아낸다.
IGNORED_FILES = {
    "package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml", "bun.lock",
    "poetry.lock", "uv.lock", "Pipfile.lock", "Cargo.lock", "Gemfile.lock", "composer.lock",
    "go.sum", "gradle.lockfile", "mix.lock", "pubspec.lock", "Podfile.lock", "flake.lock",
    "packages.lock.json",
}
IGNORED_SUFFIXES = (".min.js", ".min.css", ".map")


def git_listed_files(directory):
    """git 저장소 안이면 .gitignore를 반영한 파일 목록(추적 + 미추적, directory 기준 상대 경로). 아니면 None."""
    try:
        done = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", "."],
            cwd=directory, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError):
        return None  # git 부재
    if done.returncode != 0:
        return None  # 저장소 밖
    return [os.fsdecode(rel) for rel in done.stdout.split(b"\0") if rel]


def collect_files(paths, exclude=None):
    """파일·디렉토리 경로를 실제 파일 목록으로 펼친다(디렉토리는 재귀, 중복 제거).

    git 저장소 안의 디렉토리는 .gitignore를 따른다. exclude 디렉토리 아래 파일과
    락 파일 같은 생성 파일은 경로를 직접 지정해도 건너뛴다.
    """
    files = []
    seen = set()
    skip = os.path.realpath(exclude) if exclude else None

    def push(path):
        name = os.path.basename(path)
        if name in IGNORED_FILES or name.endswith(IGNORED_SUFFIXES):
            return
        key = os.path.realpath(path)
        if skip and (key == skip or key.startswith(skip + os.sep)):
            return
        if key not in seen:
            seen.add(key)
            files.append(path)

    for path in paths:
        if os.path.isdir(path):
            listed = git_listed_files(path)
            # 비어 있으면(.gitignore로 통째로 무시된 디렉토리를 직접 준 경우 등) 아래의 직접 탐색으로 넘어간다.
            if listed:
                for rel in listed:
                    parts = rel.split("/")
                    full = os.path.join(path, *parts)
                    if not any(p in IGNORED_DIRS for p in parts[:-1]) and os.path.isfile(full):
                        push(full)
                continue
            for root, dirnames, filenames in os.walk(path):
                dirnames[:] = sorted(d for d in dirnames if d not in IGNORED_DIRS)
                for name in sorted(filenames):
                    push(os.path.join(root, name))
        elif os.path.isfile(path):
            push(path)
    return files


def read_text(path):
    """텍스트 파일 내용을 반환한다. 바이너리·읽기 실패 파일은 None."""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except (UnicodeDecodeError, OSError):
        return None


def effective_stopwords(data):
    """기본 스톱워드에 프로젝트별 add/remove 설정을 반영한 집합."""
    config = data.get("stopwords") or {}
    words = set(STOPWORDS)
    words |= {w.lower() for w in config.get("add") or []}
    words -= {w.lower() for w in config.get("remove") or []}
    return words


def lint_files(data, paths, all_tokens=False, exclude=None):
    missing = [p for p in paths if not os.path.exists(p)]
    if paths and len(missing) == len(paths):
        raise GlossaryError(f"존재하지 않는 경로입니다: {', '.join(missing)}")
    stopwords = effective_stopwords(data)
    known = set()
    avoid_map = {}
    for t in data["terms"]:
        # 식별자와 같은 규칙으로 쪼개야 order_item·orderItem·"Stock Keeping Unit"이 부분 단어로 매칭된다.
        known.update(tokenize(t["english"]))
        if t.get("abbreviation"):
            known.update(tokenize(t["abbreviation"]))
        for v in avoid_of(t):
            avoid_map[v.lower()] = t

    hits = {}
    for file in collect_files(paths, exclude):
        text = read_text(file)
        if text is None:
            continue
        for identifier in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text):
            for tok in tokenize(identifier):
                if len(tok) < 2 or tok in known:
                    continue
                if tok not in avoid_map and not all_tokens and tok in stopwords:
                    continue
                hit = hits.setdefault(tok, {"count": 0, "files": []})
                hit["count"] += 1
                if file not in hit["files"]:
                    hit["files"].append(file)

    entries = sorted(
        ({"token": tok, "count": hit["count"], "files": hit["files"]} for tok, hit in hits.items()),
        key=lambda e: -e["count"],
    )
    violations = []
    for entry in entries:
        if entry["token"] in avoid_map:
            standard = avoid_map[entry["token"]]
            violations.append({**entry, "standard": standard["english"], "korean": standard["korean"]})
    candidates = [e for e in entries if e["token"] not in avoid_map]
    return {"violations": violations, "candidates": candidates, "missing": missing}


def format_file_list(files):
    shown = ", ".join(files[:3])
    return f"{shown} 외 {len(files) - 3}" if len(files) > 3 else shown


INITIAL_DATA = {
    "schemaVersion": SCHEMA_VERSION,
    "terms": [
        {"korean": "식별자", "english": "identifier", "abbreviation": "id",
         "description": "데이터를 고유 식별하는 값. {엔티티}_id 형식", "relatedElements": [], "avoid": []},
        {"korean": "일시", "english": "datetime", "abbreviation": "at",
         "description": "날짜와 시각. created_at 처럼 _at 접미사로 사용", "relatedElements": [], "avoid": []},
        {"korean": "이름", "english": "name", "abbreviation": None,
         "description": "대상을 지칭하는 명칭", "relatedElements": [], "avoid": []},
    ]
}

CLAUDE_BLOCK = """## 용어 사전
@superglossary/core.md

- 클래스/변수/함수/컬럼/테이블 등 모든 네이밍은 위 표의 영문명만 사용한다. 축약어는 표에 등록된 것만 쓰고, 금지 변형은 표준으로 대체한다.
- 표에 없는 단일어가 필요하면 임의로 짓지 말고 superglossary의 add 스킬로 등록한다(복합어는 단일어로 분해). 플러그인이 없으면 `python3 .claude/superglossary/glossary.py add <korean> <english> [abbreviation]`을 직접 실행한다. 변경은 같은 diff에 포함한다.
- 용어의 의미가 모호하면 `python3 .claude/superglossary/glossary.py lookup <질의>` 또는 `.claude/superglossary/terms.md`에서 상세를 확인한다.
- 수정·삭제는 `glossary.py update/remove`를 쓴다(자동 재빌드). core.md·terms.md는 생성물이므로 직접 편집하지 않는다.
- 기존 모듈 수정 시 그 모듈의 기존 컨벤션을 우선하고, 신규 코드에는 사전을 우선한다. 임의 리네이밍은 하지 않는다.
- 워크플로: 작업 시작 전 핵심 개념 정렬 → 작업 중 사전에 없는 용어만 추가 → 완료 후 check 스킬로 검토.
"""

# init이 CLAUDE.md에서 관리하는 구간. 마커 안쪽은 init을 다시 실행할 때마다 최신 CLAUDE_BLOCK으로 바뀐다.
BLOCK_BEGIN = "<!-- superglossary:begin — /superglossary:init이 관리합니다. 고친 내용은 init을 다시 실행하면 덮어써집니다. -->"
BLOCK_END = "<!-- superglossary:end -->"
MANAGED_BLOCK_RE = re.compile(r"<!-- superglossary:begin\b.*?-->.*?<!-- superglossary:end -->\n?", re.S)
LEGACY_SECTION_RE = re.compile(r"^## 용어 사전\n.*?(?=^#{1,2} |\Z)", re.S | re.M)

# 마커 도입 전 init이 넣던 블록의 SHA-256(앞뒤 공백 제거). 사용자가 고치지 않은 블록만 마커 블록으로 바꾼다.
LEGACY_BLOCK_SHA256 = {
    "932361ed00cbe1ce3130a33a1035ed6c7311779a7e7e8f76b5e423d534698516",  # v0.2.0 (node glossary.mjs)
    "efe537cbe40a29b2159aa44e93fd0fe1e4a618218f98b000c85ad3e0b7738de7",  # v0.3.0 (node glossary.mjs)
    "93ceb7e127b05efb3ff895971cf9dce9ddd58d41f7a03408f9e897235148c4fa",  # v0.4.0
}


def upsert_claude_block(existing):
    """CLAUDE.md 내용에 최신 용어사전 블록을 넣거나 갱신한다. (새 내용, 경고 목록)을 반환한다."""
    block = f"{BLOCK_BEGIN}\n{CLAUDE_BLOCK}{BLOCK_END}\n"
    if MANAGED_BLOCK_RE.search(existing):
        return MANAGED_BLOCK_RE.sub(lambda _: block, existing, count=1), []
    legacy = LEGACY_SECTION_RE.search(existing)
    if legacy:
        digest = hashlib.sha256(legacy.group(0).strip().encode("utf-8")).hexdigest()
        if digest not in LEGACY_BLOCK_SHA256:
            return existing, [
                "⚠ .claude/CLAUDE.md의 '## 용어 사전' 섹션이 직접 수정되어 있어 갱신하지 않았습니다. "
                "최신 안내로 바꾸려면 그 섹션을 지우고 init을 다시 실행하세요."
            ]
        rest = existing[legacy.end():]
        return existing[:legacy.start()] + block + ("\n" + rest if rest else ""), []
    head = existing.rstrip()
    return (head + "\n\n" if head else "") + block, []


def parse_version(text):
    matched = re.search(r'^VERSION = "(\d+)\.(\d+)\.(\d+)', text, re.M)
    return tuple(int(x) for x in matched.groups()) if matched else None


def install_cli_copy(data_dir, source=None):
    """실행 중인 CLI를 프로젝트 복사본(glossary.py)으로 둔다 — 플러그인이 없는 팀원·CI용. 경고 목록을 반환한다."""
    source = os.path.abspath(source or __file__)
    dest = os.path.join(data_dir, "glossary.py")
    if os.path.exists(dest):
        if os.path.samefile(source, dest):
            return []  # 복사본 자신이 init을 실행하는 중
        try:
            with open(dest, encoding="utf-8") as f:
                existing = parse_version(f.read())
        except (OSError, UnicodeDecodeError):
            existing = None
        current = parse_version(f'VERSION = "{VERSION}"')
        if existing and existing > current:
            return [f"⚠ 프로젝트의 CLI 복사본(v{'.'.join(map(str, existing))})이 이 CLI(v{VERSION})보다 새 버전이라 "
                    "덮어쓰지 않았습니다. 플러그인을 업데이트하세요."]
    shutil.copy(source, dest)  # 실행 권한 비트도 함께 복사
    return []


CLAUDE_DIR_NAME = ".claude"
DATA_DIR_NAME = "superglossary"


def is_data_dir(path):
    normalized = os.path.normpath(path)
    return (os.path.basename(normalized) == DATA_DIR_NAME
            and os.path.basename(os.path.dirname(normalized)) == CLAUDE_DIR_NAME)


def project_claude_dir(data_dir):
    """표준 배치(<프로젝트>/.claude/superglossary)면 그 .claude/ 디렉토리, 비표준 위치면 None."""
    return os.path.dirname(os.path.normpath(data_dir)) if is_data_dir(data_dir) else None


def assert_data_dir_placement(data_dir):
    if not is_data_dir(data_dir):
        raise GlossaryError(
            "용어사전 디렉토리는 <프로젝트>/.claude/superglossary/ 여야 합니다. "
            "프로젝트 루트에서 실행하거나 SUPERGLOSSARY_DIR로 경로를 지정하세요."
        )


def resolve_data_dir(script_path=None, cwd=None, env=None):
    """CLI가 다룰 .claude/superglossary 디렉토리를 찾는다.

    1. SUPERGLOSSARY_DIR 환경변수 — 명시적 지정
    2. 스크립트 자신이 .claude/superglossary 안에 있으면 그 디렉토리 — 프로젝트 복사본 모드
    3. 현재 디렉토리에서 위로 올라가며 탐색 — 플러그인 bin/ 모드, 하위 디렉토리에서 실행할 때
    4. 못 찾으면 <cwd>/.claude/superglossary — init이 새로 만들 자리
    """
    env = os.environ if env is None else env
    override = env.get("SUPERGLOSSARY_DIR")
    if override:
        return os.path.abspath(override)
    if script_path:
        script_dir = os.path.dirname(os.path.abspath(script_path))
        if is_data_dir(script_dir):
            return script_dir
    cwd = os.path.abspath(cwd if cwd else os.getcwd())
    current = cwd
    while True:
        candidate = os.path.join(current, CLAUDE_DIR_NAME, DATA_DIR_NAME)
        if os.path.isdir(candidate):
            return candidate
        parent = os.path.dirname(current)
        if parent == current:
            return os.path.join(cwd, CLAUDE_DIR_NAME, DATA_DIR_NAME)
        current = parent


def git_ignore_warnings(data_dir):
    root = os.path.dirname(os.path.dirname(os.path.normpath(data_dir)))
    warnings = []
    targets = [os.path.join(".claude", "superglossary", "glossary.json"), os.path.join(".claude", "CLAUDE.md")]
    for rel in targets:
        try:
            done = subprocess.run(
                ["git", "check-ignore", "-q", rel], cwd=root,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except (OSError, subprocess.SubprocessError):
            return []  # git 부재 — 판단 불가이므로 경고하지 않는다
        if done.returncode == 0:
            warnings.append(f"⚠ {rel} 이(가) .gitignore에 의해 무시되어 팀과 공유되지 않습니다.")
    if warnings:
        warnings += [
            "  .gitignore를 다음과 같이 조정하세요:",
            "    .claude/*",
            "    !.claude/CLAUDE.md",
            "    !.claude/superglossary/",
        ]
    return warnings


def scaffold(data_dir):
    assert_data_dir_placement(data_dir)
    os.makedirs(data_dir, exist_ok=True)
    if os.path.exists(os.path.join(data_dir, "glossary.json")):
        # 기존 사전은 보존하되, 구 스키마면 여기서 올린다(init 재실행 = 업그레이드 경로).
        save_glossary(data_dir, load_glossary(data_dir))
    else:
        save_glossary(data_dir, INITIAL_DATA)
    notice = build(data_dir)
    warnings = notice.split("\n") if notice else []
    warnings += install_cli_copy(data_dir)
    if os.path.exists(os.path.join(data_dir, "glossary.mjs")):
        warnings.append("⚠ 0.4.0 이전 CLI 복사본 glossary.mjs가 남아 있습니다. 더 이상 쓰이지 않으니 삭제하세요.")
    claude_md = os.path.join(os.path.dirname(os.path.normpath(data_dir)), "CLAUDE.md")
    existing = ""
    if os.path.exists(claude_md):
        with open(claude_md, encoding="utf-8") as f:
            existing = f.read()
    updated, block_warnings = upsert_claude_block(existing)
    if updated != existing:
        write_text(claude_md, updated)
    return warnings + block_warnings + git_ignore_warnings(data_dir)


BOOLEAN_OPTIONS = {"all", "strict"}


def parse_args(rest):
    positional = []
    options = {}
    i = 0
    while i < len(rest):
        arg = rest[i]
        if arg.startswith("--"):
            name, sep, inline = arg[2:].partition("=")
            if sep:
                options[name] = inline
            elif name in BOOLEAN_OPTIONS:
                options[name] = True
            elif i + 1 < len(rest) and not rest[i + 1].startswith("--"):
                i += 1
                options[name] = rest[i]
            else:
                # 값 누락 — 다음 옵션을 값으로 먹지 않는다. check_args가 오류로 알린다.
                options[name] = None
        else:
            positional.append(arg)
        i += 1
    return positional, options


def _csv_option(options, key):
    """쉼표 목록 옵션. 주지 않았으면 None, 빈 값("")이면 [] — update에서 목록을 비울 때 쓴다."""
    if key not in options:
        return None
    return [s.strip() for s in options[key].split(",") if s.strip()]


USAGE = """사용법: python3 .claude/superglossary/glossary.py <subcommand>
       (플러그인이 활성화되어 있으면 `superglossary <subcommand>`로도 실행됩니다)
  init                                          초기화·업그레이드(사전·생성물·CLI 복사본·CLAUDE.md 블록)
  build                                         glossary.json → core.md·terms.md 재생성
  add <korean> <english> [abbreviation] [--desc "설명"] [--related "a,b"] [--avoid "a,b"]
      (축약어는 --abbreviation A로도 지정 가능)
  update <korean> [--english E] [--abbreviation A] [--desc D] [--related "a,b"] [--avoid "a,b"]
      (--related ""·--avoid ""는 목록을 비운다)
  remove <korean>
  list                                          전체 용어(간결)
  lookup <질의>                                  용어 상세 검색
  lint [--all] [--strict] <paths...>            코드 대조([위반]/[후보], 디렉토리 재귀·.gitignore 반영, .claude/·락 파일 제외)
      (--all=스톱워드 해제, --strict=[위반]이 있으면 종료 코드 1)
  version | help"""

# 서브커맨드별 (최소 위치 인자 수, 최대 위치 인자 수 — None은 무제한, 허용 옵션)
COMMANDS = {
    "init": (0, 0, set()),
    "build": (0, 0, set()),
    "add": (2, 3, {"abbreviation", "desc", "related", "avoid"}),
    "update": (1, 1, {"english", "abbreviation", "desc", "related", "avoid"}),
    "remove": (1, 1, set()),
    "list": (0, 0, set()),
    "lookup": (0, 1, set()),
    "lint": (0, None, {"all", "strict"}),  # 경로 누락은 lint 전용 안내로 처리
    "version": (0, 0, set()),
    "help": (0, 0, set()),
}


def check_args(cmd, positional, options):
    """모르는 옵션·값 누락·인자 수 오류를 조용히 버리지 않고 알린다."""
    min_args, max_args, allowed = COMMANDS[cmd]
    unknown = [f"--{name}" for name in options if name not in allowed]
    if unknown:
        hint = ", ".join(f"--{name}" for name in sorted(allowed)) or "없음"
        raise GlossaryError(f"{cmd}에서 쓸 수 없는 옵션: {', '.join(unknown)} (사용 가능: {hint})\n{USAGE}")
    for name, value in options.items():
        if name in BOOLEAN_OPTIONS:
            if value is not True:
                raise GlossaryError(f"--{name}은(는) 값을 받지 않습니다.")
        elif value is None:
            raise GlossaryError(f"--{name}에 값이 없습니다. 비우려면 --{name} \"\"처럼 빈 값을 넘기세요.")
    if len(positional) < min_args:
        raise GlossaryError(f"{cmd}에 필요한 인자가 부족합니다.\n{USAGE}")
    if max_args is not None and len(positional) > max_args:
        extra = " ".join(positional[max_args:])
        raise GlossaryError(f"{cmd}의 인자가 너무 많습니다: {extra} — 공백이 든 값은 따옴표로 감싸세요.\n{USAGE}")


def run(argv, data_dir):
    if not argv:
        raise GlossaryError(f"커맨드를 지정하세요.\n{USAGE}")
    cmd, rest = argv[0], argv[1:]
    if cmd not in COMMANDS:
        raise GlossaryError(f"알 수 없는 커맨드: {cmd}\n{USAGE}")
    positional, options = parse_args(rest)
    check_args(cmd, positional, options)

    def at(index):
        return positional[index] if len(positional) > index else None

    if cmd == "init":
        warnings = scaffold(data_dir)
        return "\n".join([f"초기화 완료: {data_dir}", *warnings])

    if cmd == "build":
        notice = build(data_dir)
        return "\n".join(x for x in ["빌드 완료: core.md, terms.md", notice] if x)

    if cmd == "add":
        korean, english, abbreviation = at(0), at(1), at(2)
        if "abbreviation" in options:
            if abbreviation is not None:
                raise GlossaryError("축약어를 위치 인자와 --abbreviation으로 두 번 지정했습니다. 하나만 쓰세요.")
            abbreviation = options["abbreviation"] or None
        data = load_glossary(data_dir)
        add_term(
            data, korean, english, abbreviation,
            description=options.get("desc", ""),
            related_elements=_csv_option(options, "related") or [],
            avoid=_csv_option(options, "avoid") or [],
        )
        save_glossary(data_dir, data)
        notice = build(data_dir)
        return "\n".join(x for x in [f"추가: {korean} → {english}", notice] if x)

    if cmd == "update":
        korean = at(0)
        data = load_glossary(data_dir)
        fields = {}
        if "english" in options:
            fields["english"] = options["english"]
        if "abbreviation" in options:
            fields["abbreviation"] = options["abbreviation"] or None
        if "desc" in options:
            fields["description"] = options["desc"]
        related = _csv_option(options, "related")
        if related is not None:
            fields["relatedElements"] = related
        avoid = _csv_option(options, "avoid")
        if avoid is not None:
            fields["avoid"] = avoid
        update_term(data, korean, fields)
        save_glossary(data_dir, data)
        notice = build(data_dir)
        return "\n".join(x for x in [f"수정: {korean}", notice] if x)

    if cmd == "remove":
        korean = at(0)
        data = load_glossary(data_dir)
        remove_term(data, korean)
        save_glossary(data_dir, data)
        notice = build(data_dir)
        return "\n".join(x for x in [f"삭제: {korean}", notice] if x)

    if cmd == "list":
        data = load_glossary(data_dir)
        warn_if_stale(data_dir, data)
        return "\n".join(
            f"{t['korean']}\t{t['english']}\t{t.get('abbreviation') or ''}" for t in list_terms(data)
        )

    if cmd == "lookup":
        data = load_glossary(data_dir)
        warn_if_stale(data_dir, data)
        found = lookup(data, at(0) or "")
        return "\n\n".join(format_term_detail(t) for t in found) if found else "일치하는 용어 없음"

    if cmd == "lint":
        if not positional:
            raise GlossaryError(f"lint에는 검사할 파일이나 디렉토리를 지정하세요. 예: lint src/\n{USAGE}")
        data = load_glossary(data_dir)
        warn_if_stale(data_dir, data)
        report = lint_files(data, positional, all_tokens=options.get("all") is True,
                            exclude=project_claude_dir(data_dir))
        for path in report["missing"]:
            print(f"⚠ 존재하지 않는 경로를 건너뜁니다: {path}", file=sys.stderr)
        lines = []
        if report["violations"]:
            lines.append("[위반]")
            for v in report["violations"]:
                lines.append(f"{v['token']}\t{v['standard']}({v['korean']})\t{v['count']}\t{format_file_list(v['files'])}")
        if report["candidates"]:
            lines.append("[후보]")
            for c in report["candidates"]:
                lines.append(f"{c['token']}\t{c['count']}\t{format_file_list(c['files'])}")
        output = "\n".join(lines) if lines else "이상 없음"
        if options.get("strict") and report["violations"]:
            raise ViolationsFound(output)
        return output

    if cmd == "version":
        return f"superglossary CLI v{VERSION}"

    if cmd == "help":
        return USAGE

    raise GlossaryError(f"알 수 없는 커맨드: {cmd}\n{USAGE}")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    try:
        out = run(argv, resolve_data_dir(__file__))
    except ViolationsFound as found:
        print(found.output)
        return 1
    except (GlossaryError, OSError, ValueError) as err:
        print(f"✗ {err}", file=sys.stderr)
        return 1
    if out:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
