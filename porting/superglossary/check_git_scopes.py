"""Exercise documented scope commands; this does not run model naming judgments."""
from pathlib import Path
import argparse
import re
import shlex
import subprocess
import tempfile


root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--skill", type=Path,
                    default=root / "plugins/superglossary-codex/skills/check/SKILL.md",
                    help="Check skill whose documented commands should be exercised")
parser.add_argument("--git-only", action="store_true",
                    help="Exercise shared Git commands without Codex search command examples")
args = parser.parse_args()
skill = args.skill.read_text()
commands = re.findall(r'`((?:git|rg) [^`\n]+)`', skill)
commands += re.findall(r'^(git -C [^\n]+)$', skill, re.MULTILINE)
selectors = [command for command in commands if command.endswith("-z")]
assert len(selectors) == 3, "Expected unstaged, staged, untracked selectors"
current_search = next(
    (command for command in commands
     if command.startswith("rg ") and "<검색어>" in command
     and "<프로젝트 루트>/docs/superglossary/" in command), None)
assert args.git_only or current_search, "All review scopes must search the current working-tree glossary"
glossary_diffs = [
    command for command in commands
    if command.startswith('git -C "<프로젝트 루트>" diff')
    and command.endswith("-- docs/superglossary/")
]
assert len(glossary_diffs) == 3, "Expected unstaged, staged, selected-range glossary diffs"
affected_search = next(
    (command for command in commands
     if command.startswith("rg ") and "<이전 용어>" in command and "<현재 용어>" in command), None)
assert args.git_only or affected_search, "Glossary changes need a current-code search example"

with tempfile.TemporaryDirectory(prefix="glossary scope ") as folder:
    repo = Path(folder)

    def git(*args, check=True):
        return subprocess.run(["git", "-C", str(repo), *args], check=check,
                              capture_output=True)

    def write(path, text):
        file = repo / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text)

    def documented(command, **values):
        replacements = {"<프로젝트 루트>": str(repo), **values}
        args = shlex.split(command)
        for key, value in replacements.items():
            args = [arg.replace(key, value) for arg in args]
        return subprocess.check_output(args, cwd=repo)

    git("init", "-q")
    git("config", "user.name", "Fixture")
    git("config", "user.email", "fixture@example.invalid")
    write("src/order item.py", "member_id = 1\n")
    write("src/unchanged.py", "legacy_owner_id = 1\ncurrent_owner_id = 2\n")
    write("src/removed.py", "removed_id = 1\n")
    write("docs/superglossary/glossary.md", "member standard at A\n")
    write(".gitignore", "ignored/\n")
    git("add", ".")
    git("commit", "-qm", "A")
    start = git("rev-parse", "HEAD").stdout.decode().strip()

    write("src/order item.py", "customer_id = 1\n")
    write("docs/superglossary/glossary.md", "customer standard at B\n")
    git("add", ".")
    git("commit", "-qm", "B")
    end = git("rev-parse", "HEAD").stdout.decode().strip()

    write("src/order item.py", "staged_id = 1\n")
    git("add", "src/order item.py")
    write("src/order item.py", "unstaged_id = 1\n")
    (repo / "src/removed.py").unlink()
    write("src/new item.py", "candidate_id = 1\n")
    write("ignored/skip.py", "legacy_owner_id = 1\n")
    selected = []
    for command in selectors:
        paths = documented(command).decode().split("\0")
        selected.append({path for path in paths if path})
    assert selected == [{"src/order item.py"}, {"src/order item.py"},
                        {"src/new item.py"}], selected
    assert b"+staged_id" in git("diff", "--cached", "--", "src/order item.py").stdout
    assert b"+unstaged_id" in git("diff", "--", "src/order item.py").stdout

    range_command = next(command for command in commands if command.endswith("diff <범위> --"))
    patch = documented(range_command, **{"<범위>": f"{start}..{end}"})
    assert b"+customer_id" in patch and b"staged_id" not in patch
    assert git("show", f"{end}:src/order item.py").stdout == b"customer_id = 1\n"
    write("docs/superglossary/glossary.md", "current standard, different from B\n")
    if not args.git_only:
        found = documented(current_search, **{"<검색어>": "current"})
        assert b"current standard, different from B" in found
    assert git("show", f"{end}:docs/superglossary/glossary.md").stdout == b"customer standard at B\n"

    # A range endpoint with no glossary still uses today's glossary.
    git("add", ".")
    git("commit", "-qm", "working changes")
    (repo / "docs/superglossary/glossary.md").unlink()
    git("add", "docs/superglossary/glossary.md")
    git("commit", "-qm", "endpoint without glossary")
    missing_end = git("rev-parse", "HEAD").stdout.decode().strip()
    write("docs/superglossary/glossary.md", "current glossary restored\n")
    assert git("show", f"{missing_end}:docs/superglossary/glossary.md",
               check=False).returncode != 0
    if not args.git_only:
        assert b"current glossary restored" in documented(current_search, **{"<검색어>": "current"})
    assert b"member_id" in documented(range_command, **{"<범위>": f"{start}..{missing_end}"})

    # Dictionary-only commits expand the impact search to unchanged current code.
    git("add", "docs/superglossary/glossary.md")
    git("commit", "-qm", "glossary baseline")
    glossary_start = git("rev-parse", "HEAD").stdout.decode().strip()
    write("docs/superglossary/glossary.md", "current_owner replaces legacy_owner\n")
    git("add", "docs/superglossary/glossary.md")
    git("commit", "-qm", "dictionary only")
    glossary_end = git("rev-parse", "HEAD").stdout.decode().strip()
    dictionary_range = f"{glossary_start}..{glossary_end}"
    assert git("diff", "--name-only", dictionary_range).stdout == b"docs/superglossary/glossary.md\n"
    assert not git("diff", dictionary_range, "--", "src/unchanged.py").stdout
    if not args.git_only:
        found = documented(affected_search, **{
            "<이전 용어>": "legacy_owner", "<현재 용어>": "current_owner",
        })
        assert b"src/unchanged.py:1:legacy_owner_id" in found, found
        assert b"src/unchanged.py:2:current_owner_id" in found, found
        assert b"docs/superglossary" not in found and b"ignored/skip.py" not in found

    # All glossary change sources remain visible; the selected range is not replaced.
    write("docs/superglossary/glossary.md", "staged_owner replaces legacy_owner\n")
    git("add", "docs/superglossary/glossary.md")
    write("docs/superglossary/glossary.md", "unstaged_owner replaces legacy_owner\n")
    diffs = [documented(command, **{"<범위>": dictionary_range}) for command in glossary_diffs]
    assert any(b"+staged_owner" in diff for diff in diffs), diffs
    assert any(b"+unstaged_owner" in diff for diff in diffs), diffs
    assert any(b"+current_owner" in diff for diff in diffs), diffs
    if not args.git_only:
        assert b"unstaged_owner" in documented(current_search, **{"<검색어>": "owner"})
    assert not git("diff", f"{glossary_end}..{glossary_end}", "--").stdout
    assert git("rev-parse", "--verify", "missing-ref^{commit}", check=False).returncode != 0
    assert git("show", f"{end}:missing-file.md", check=False).returncode != 0

print("PASS: staged/unstaged scopes, untracked/spaces/ignored/deleted, actual revision code, "
      "all glossary change scopes, empty/invalid ranges")
if args.git_only:
    print("SKIP: Codex search examples (shared Git commands only)")
else:
    print("PASS: current glossary despite differing/missing endpoint glossary, "
          "dictionary-only impact finds unchanged current code")
