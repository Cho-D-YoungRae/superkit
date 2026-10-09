#!/usr/bin/env python3
"""Read-only file fingerprints for a port's source and managed output.

This is a change detector, not a converter or a compatibility validator.
JSON goes to stdout; callers choose where to save it outside the package.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys


IGNORED_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"}


def relative_path(value):
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("file paths must be nonempty POSIX relative paths")
    p = PurePosixPath(value)
    if p.is_absolute() or ".." in p.parts or str(p) != value or value == ".":
        raise ValueError("file paths must stay inside the package")
    return p


def fingerprint(path):
    mode = path.lstat().st_mode
    if stat.S_ISLNK(mode):
        return {"type": "symlink", "target": os.readlink(path)}
    if not stat.S_ISREG(mode):
        raise ValueError("only regular files and symlinks can be fingerprinted")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"type": "file", "sha256": digest.hexdigest(),
            "executable": bool(mode & 0o111)}


def snapshot(root, selected=None):
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("root must be a directory")
    paths = []
    if selected is not None:
        if not isinstance(selected, list):
            raise ValueError("paths file must contain a JSON array")
        for value in selected:
            rel = relative_path(value)
            # The leaf itself may be a symlink; never follow a symlink parent.
            current = root
            for part in rel.parts[:-1]:
                current = current / part
                if current.is_symlink():
                    raise ValueError("a selected path traverses a symlink")
            paths.append(root / rel)
    else:
        def fail(exc):
            raise exc
        for directory, dirs, files in os.walk(root, followlinks=False, onerror=fail):
            for name in list(dirs):
                path = Path(directory) / name
                if name in IGNORED_DIRS:
                    dirs.remove(name)
                elif path.is_symlink():
                    paths.append(path)
                    dirs.remove(name)
            paths.extend(Path(directory) / name for name in files)
    records = {p.relative_to(root).as_posix(): fingerprint(p) for p in paths}
    return {"schema_version": 1, "files": dict(sorted(records.items()))}


def validate_state(state):
    if (not isinstance(state, dict) or state.get("schema_version") != 1
            or not isinstance(state.get("files"), dict)):
        raise ValueError("unsupported or malformed snapshot")
    for path, record in state["files"].items():
        relative_path(path)
        if not isinstance(record, dict):
            raise ValueError("malformed file record")
        if record.get("type") == "file":
            digest = record.get("sha256")
            if (not isinstance(digest, str) or len(digest) != 64
                    or any(c not in "0123456789abcdef" for c in digest)
                    or not isinstance(record.get("executable"), bool)):
                raise ValueError("malformed regular-file record")
        elif record.get("type") == "symlink":
            if not isinstance(record.get("target"), str):
                raise ValueError("malformed symlink record")
        else:
            raise ValueError("unsupported file record")


def compare(before, after):
    validate_state(before)
    old, new = before["files"], after["files"]
    return {"added": sorted(new.keys() - old.keys()),
            "modified": sorted(p for p in old.keys() & new.keys() if old[p] != new[p]),
            "removed": sorted(old.keys() - new.keys())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    snap = sub.add_parser("snapshot")
    snap.add_argument("root")
    snap.add_argument("--paths-file", help="JSON list of managed relative file paths")
    diff = sub.add_parser("compare")
    diff.add_argument("before", help="previous snapshot JSON")
    diff.add_argument("root")
    args = parser.parse_args()
    try:
        if args.action == "snapshot":
            selected = None
            if args.paths_file:
                selected = json.loads(Path(args.paths_file).read_text(encoding="utf-8"))
            result = snapshot(args.root, selected)
        else:
            before = json.loads(Path(args.before).read_text(encoding="utf-8"))
            validate_state(before)
            result = compare(before, snapshot(args.root))
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    except (OSError, ValueError) as exc:
        # Never echo file contents from decoder/parser exceptions.
        print("error: cannot read a valid package/snapshot (" + type(exc).__name__ + ")",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
