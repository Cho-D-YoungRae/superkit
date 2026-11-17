"""Check catalog routing and reviewed baselines without modifying repository files."""
from pathlib import Path
import argparse
import json
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
records = root / "porting/superglossary"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--source-state", type=Path, default=records / "source-state.json",
                    help="Review candidate to check before promoting the source baseline")
parser.add_argument("--target-state", type=Path, default=records / "target-state.json",
                    help="Review candidate to check before promoting the target baseline")
args = parser.parse_args()
target = root / "plugins/superglossary-codex"
manifest = json.loads((target / "plugin.json").read_text())
catalog = json.loads((root / ".agents/plugins/marketplace.json").read_text())
claude = json.loads((root / ".claude-plugin/marketplace.json").read_text())
claude_packages = {(root / entry["source"]).resolve() for entry in claude["plugins"]}
entries = catalog["plugins"]
assert len({entry["name"] for entry in entries}) == len(entries), "Duplicate Codex plugin names"
for entry in entries:
    source = entry["source"]
    assert source["source"] == "local", "Repository catalog uses local packages"
    assert source["path"].startswith("./"), source
    package = (root / source["path"]).resolve()
    assert package.is_relative_to(root), "Catalog source escapes repository"
    shared_manifest = package / ".claude-plugin/plugin.json"
    if shared_manifest.exists():
        # A folder both runtimes read (llm-wiki): allowed only when it is the Claude catalog's
        # package too and no `-codex` port exists, so a ported original is still rejected here.
        assert package in claude_packages, "Codex catalog points at a Claude original"
        assert not package.with_name(f"{package.name}-codex").exists(), "Shared plugin also has a -codex port"
        package_manifest = json.loads(shared_manifest.read_text())
    else:
        package_manifest = json.loads((package / "plugin.json").read_text())
    assert entry["name"] == package_manifest["name"], "Catalog and manifest names differ"
    assert "version" not in entry, "Version belongs in plugin.json"
    assert entry["policy"]["installation"] == "AVAILABLE", "Catalog must not auto-install"
    assert entry["policy"]["authentication"] == "ON_INSTALL", "Unexpected authentication policy"
    assert entry["category"], "Missing category"
entry = next(entry for entry in entries if entry["name"] == manifest["name"])
assert (root / entry["source"]["path"]).resolve() == target, "Wrong superglossary package"

assert all((root / entry["source"]).resolve() != target for entry in claude["plugins"]), "Codex package in Claude catalog"
helper = root / ".agents/skills/claude-to-codex/scripts/tree_state.py"
# Source paths mapped to `omit` in decisions.md are not inputs to the Codex package.
# Paths are relative to the source root; a trailing "/" covers a directory.
# Since 0.8.0 removes legacy migration guidance, CHANGELOG.md is entirely omitted.
omitted = ("AGENTS.md", "CHANGELOG.md", "docs/superpowers/")


def is_omitted(path):
    return any(path.startswith(item) if item.endswith("/") else path == item for item in omitted)


for baseline, folder in ((args.source_state, root / "plugins/superglossary"), (args.target_state, target)):
    result = json.loads(subprocess.check_output([
        sys.executable, str(helper), "compare", str(baseline), str(folder),
    ], text=True))
    is_source = folder == root / "plugins/superglossary"
    if is_source:
        ignored = sorted(path for paths in result.values() for path in paths if is_omitted(path))
        result = {kind: [path for path in paths if not is_omitted(path)] for kind, paths in result.items()}
        if ignored:
            print("Omitted source files differ from the baseline (not ported):", ignored)
    assert not result["modified"] and not result["removed"], (baseline, result)
    if is_source:
        assert not result["added"], (baseline, result)
    elif result["added"]:
        print("Unmanaged target files preserved:", result["added"])
managed = json.loads((records / "managed-paths.json").read_text())
assert len(set(managed)) == len(managed), "Duplicate managed paths"
assert sorted(managed) == sorted(json.loads(args.target_state.read_text())["files"])
print("PASS: platform catalogs, package identity, reviewed source/target baselines, managed paths")
