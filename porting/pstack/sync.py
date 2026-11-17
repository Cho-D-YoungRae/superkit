#!/usr/bin/env python3
"""plugins/pstack을 cursor/plugins의 Claude Code 생성본에서 만든다.

    python3 porting/pstack/sync.py --upstream <cursor/plugins 체크아웃>          # 갱신
    python3 porting/pstack/sync.py --upstream <cursor/plugins 체크아웃> --check  # 체크아웃과 대조
    python3 porting/pstack/sync.py --verify                                      # 오프라인 대조

갱신은 체크아웃의 HEAD를 upstream.json에 고정하고, 원본 파일의 해시를 upstream-manifest.json에 남긴다.
--verify는 체크아웃 없이 설치본을 그 해시와 변환 규칙에 대조한다(CI가 쓴다).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLUGIN = ROOT / "plugins" / "pstack"
OVERLAY = HERE / "overlay"
PIN = HERE / "upstream.json"
MANIFEST = HERE / "upstream-manifest.json"
TREE = "harness/pstack/claude-code"

CLAUDE_LINE = (
    "In Claude Code, read [the Claude Code adapter](../../docs/harness/claude-code.md) once per session "
    "before you follow this skill. It maps the Cursor names in pstack skills to Claude Code."
)
CODEX_LINE = (
    " In Codex, read [the Codex adapter](../../docs/harness/codex.md) once per session instead. "
    "It maps the same names to Codex."
)
OPENAI_YAML = b"policy:\n  allow_implicit_invocation: false\n"
PLUGIN_JSON = ".claude-plugin/plugin.json"
# 버전을 .claude-plugin/plugin.json 한 곳에만 둔다. Codex도 그 파일을 읽는다.
DROPPED = {"plugin.json"}
PLUGIN_JSON_OVERRIDES = {
    "homepage": "https://github.com/Cho-D-YoungRae/superkit/tree/main/plugins/pstack",
    "repository": "https://github.com/Cho-D-YoungRae/superkit",
}
SKILL_MD = re.compile(r"skills/([^/]+)/SKILL\.md")
OPENAI_YAML_PATH = re.compile(r"skills/([^/]+)/agents/openai\.yaml")
NO_IMPLICIT = re.compile(r"^disable-model-invocation:\s*true\s*$", re.M)
LINK = re.compile(r"\]\(([^)\s]+)\)")
FORBIDDEN_NAMES = {"CLAUDE.md", "CLAUDE.local.md"}

Tree = dict[str, tuple[bytes, bool]]


class SyncError(Exception):
    def __init__(self, problems: list[str]):
        super().__init__("\n".join(problems))
        self.problems = problems


def read_tree(directory: Path) -> Tree:
    tree: Tree = {}
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.name != ".DS_Store":
            tree[path.relative_to(directory).as_posix()] = (path.read_bytes(), bool(path.stat().st_mode & 0o111))
    return tree


def frontmatter(text: str) -> str:
    match = re.match(r"---\n(.*?)\n---", text, re.S)
    return match.group(1) if match else ""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def link_problems(files: Tree) -> list[str]:
    problems = []
    for path, (data, _) in files.items():
        if not path.endswith(".md"):
            continue
        for href in LINK.findall(data.decode("utf-8")):
            target = re.sub(r"[#?].*", "", href)
            if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("/"):
                continue
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), target))
            if resolved.startswith("../") or resolved == "..":
                problems.append(f"{path}: {href}가 플러그인 밖을 가리킨다")
            elif resolved not in files and not any(key.startswith(f"{resolved}/") for key in files):
                problems.append(f"{path}: {href}가 가리키는 파일이 없다")
    return problems


def render(upstream: Tree, overlay: Tree) -> Tree:
    """upstream 생성본과 overlay로 설치본을 만든다. 규칙에 어긋나면 SyncError."""
    problems = []
    files: Tree = {path: entry for path, entry in upstream.items() if path not in DROPPED}

    for path in files:
        if posixpath.basename(path) in FORBIDDEN_NAMES:
            problems.append(f"{path}: 저장소에는 CLAUDE.md 계열 파일을 두지 않는다")

    if PLUGIN_JSON not in files:
        problems.append(f"{PLUGIN_JSON}가 원본에 없다")
    else:
        manifest = json.loads(files[PLUGIN_JSON][0])
        manifest.update(PLUGIN_JSON_OVERRIDES)
        files[PLUGIN_JSON] = ((json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode(), False)

    for path in sorted(files):
        match = SKILL_MD.fullmatch(path)
        if not match:
            continue
        data, executable = files[path]
        text = data.decode("utf-8")
        if "docs/harness/claude-code.md" in text:
            if text.count(CLAUDE_LINE) != 1 or CODEX_LINE in text:
                problems.append(f"{path}: Claude Code 어댑터 문장이 예상한 한 줄과 다르다. sync.py의 CLAUDE_LINE을 확인한다")
            else:
                files[path] = (text.replace(CLAUDE_LINE, CLAUDE_LINE + CODEX_LINE).encode(), executable)
        if NO_IMPLICIT.search(frontmatter(text)):
            target = f"skills/{match.group(1)}/agents/openai.yaml"
            if target in files:
                problems.append(f"{target}: 원본이 이 파일을 내기 시작했다. 생성 규칙을 다시 정한다")
            else:
                files[target] = (OPENAI_YAML, False)

    for path, entry in overlay.items():
        if path in files:
            problems.append(f"{path}: 원본과 overlay가 같은 경로를 낸다")
        files[path] = entry

    problems += link_problems(files)
    if problems:
        raise SyncError(problems)
    return dict(sorted(files.items()))


def reconstruct(installed: Tree, overlay: Tree) -> Tree:
    """설치본에서 superkit이 더한 것을 걷어 원본 생성본을 되살린다(DROPPED는 되살리지 않는다)."""
    upstream: Tree = {}
    for path, (data, executable) in installed.items():
        if path in overlay:
            continue
        if OPENAI_YAML_PATH.fullmatch(path) and data == OPENAI_YAML:
            continue
        if SKILL_MD.fullmatch(path):
            data = data.replace((CLAUDE_LINE + CODEX_LINE).encode(), CLAUDE_LINE.encode())
        upstream[path] = (data, executable)
    return upstream


def compare(want: Tree, have: Tree) -> list[str]:
    drifted = []
    for path in sorted(set(want) | set(have)):
        if path not in have:
            drifted.append(f"{path}: 없다")
        elif path not in want:
            drifted.append(f"{path}: 생성 결과에 없는 파일이다")
        elif want[path] != have[path]:
            drifted.append(f"{path}: 내용이나 실행 권한이 다르다")
    return drifted


def verify() -> list[str]:
    """체크아웃 없이 plugins/pstack을 고정한 원본 해시와 변환 규칙에 대조한다."""
    pin = json.loads(PIN.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    overlay = read_tree(OVERLAY)
    installed = read_tree(PLUGIN)
    upstream = reconstruct(installed, overlay)

    problems = []
    for path in sorted((set(manifest) | set(upstream)) - DROPPED - {PLUGIN_JSON}):
        if path not in upstream:
            problems.append(f"{path}: 원본에 있는데 설치본에 없다")
        elif path not in manifest:
            problems.append(f"{path}: 원본({pin['commit'][:12]})에 없는 파일이다")
        elif sha256(upstream[path][0]) != manifest[path]["sha256"] or upstream[path][1] != manifest[path]["executable"]:
            problems.append(f"{path}: 원본({pin['commit'][:12]})과 다르다. 손으로 고치지 말고 sync.py를 돌린다")
    plugin_json = json.loads(installed.get(PLUGIN_JSON, (b"{}", False))[0])
    if plugin_json.get("name") != "pstack" or plugin_json.get("version") != pin["version"]:
        problems.append(f"{PLUGIN_JSON}: name·version이 pstack·{pin['version']}가 아니다")
    try:
        problems += compare(render(upstream, overlay), installed)
    except SyncError as error:
        problems += error.problems
    return problems


def git_head(checkout: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def write(files: Tree, upstream: Tree, commit: str) -> None:
    shutil.rmtree(PLUGIN, ignore_errors=True)
    for path, (data, executable) in files.items():
        target = PLUGIN / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        target.chmod(0o755 if executable else 0o644)
    manifest = {path: {"sha256": sha256(data), "executable": executable} for path, (data, executable) in upstream.items()}
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    version = json.loads(files[PLUGIN_JSON][0])["version"]
    pin = {"repository": "https://github.com/cursor/plugins", "tree": TREE, "commit": commit, "version": version}
    PIN.write_text(json.dumps(pin, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--upstream", type=Path, help="cursor/plugins 체크아웃 경로")
    parser.add_argument("--check", action="store_true", help="쓰지 않고 체크아웃의 생성 결과와 대조한다")
    parser.add_argument("--verify", action="store_true", help="체크아웃 없이 고정한 해시와 대조한다")
    args = parser.parse_args()

    if args.verify:
        problems = verify()
        for line in problems:
            print(f"✗ {line}")
        print("plugins/pstack이 고정한 원본과 맞다." if not problems else "plugins/pstack이 고정한 원본과 다르다.")
        return 1 if problems else 0
    if not args.upstream:
        parser.error("--upstream이나 --verify가 필요하다")

    source = args.upstream / TREE
    if not source.is_dir():
        parser.error(f"{source}가 없다")
    upstream = read_tree(source)
    try:
        files = render(upstream, read_tree(OVERLAY))
    except SyncError as error:
        for line in error.problems:
            print(f"✗ {line}")
        return 1
    commit = git_head(args.upstream)

    if args.check:
        problems = compare(files, read_tree(PLUGIN))
        pin = json.loads(PIN.read_text(encoding="utf-8"))
        if pin["commit"] != commit:
            problems.append(f"upstream.json의 커밋 {pin['commit'][:12]}이 체크아웃 {commit[:12]}과 다르다")
        for line in problems[:30]:
            print(f"✗ {line}")
        print("plugins/pstack이 최신이다." if not problems else "plugins/pstack이 낡았다. --check 없이 다시 돌린다.")
        return 1 if problems else 0

    write(files, upstream, commit)
    skills = sum(1 for path in files if SKILL_MD.fullmatch(path))
    hidden = sum(1 for path in files if OPENAI_YAML_PATH.fullmatch(path))
    print(f"{commit[:12]} → plugins/pstack: 파일 {len(files)}개, 스킬 {skills}개, 암묵 호출을 끈 스킬 {hidden}개")
    return 0


if __name__ == "__main__":
    sys.exit(main())
