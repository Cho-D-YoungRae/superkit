"""Exercise the check skill's documented Git commands in an isolated repository.

This checks file selection and revision reads, not model naming judgments.
"""
from pathlib import Path
import re
import shlex
import subprocess
import tempfile


root = Path(__file__).resolve().parents[2]
skill = (root / "plugins/superglossary-codex/skills/check/SKILL.md").read_text()
commands = re.findall(r'`(git -C "<프로젝트 루트>" [^`]+)`', skill)
selectors = [command for command in commands if command.endswith("-z")]
assert len(selectors) == 3, "Expected unstaged, staged, untracked selectors"

with tempfile.TemporaryDirectory(prefix="glossary scope ") as folder:
    repo = Path(folder)

    def git(*args, check=True):
        return subprocess.run(["git", "-C", str(repo), *args], check=check,
                              capture_output=True)

    def write(path, text):
        file = repo / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text)

    git("init", "-q")
    git("config", "user.name", "Fixture")
    git("config", "user.email", "fixture@example.invalid")
    write("src/order item.py", "member_id = 1\n")
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
    write("ignored/skip.py", "ignored_id = 1\n")

    selected = []
    for command in selectors:
        args = shlex.split(command)
        args[2] = str(repo)
        paths = subprocess.check_output(args).decode().split("\0")
        selected.append({path for path in paths if path})
    assert selected == [{"src/order item.py"}, {"src/order item.py"},
                        {"src/new item.py"}], selected
    assert b"+staged_id" in git("diff", "--cached", "--", "src/order item.py").stdout
    assert b"+unstaged_id" in git("diff", "--", "src/order item.py").stdout

    range_command = next(command for command in commands if "<범위>" in command)
    args = shlex.split(range_command)
    args[2] = str(repo)
    args[args.index("<범위>")] = f"{start}..{end}"
    patch = subprocess.check_output(args)
    assert b"+customer_id" in patch and b"staged_id" not in patch
    assert b"+customer standard at B" in patch
    (repo / "docs/superglossary/glossary.md").unlink()
    assert git("show", f"{end}:docs/superglossary/glossary.md").stdout == b"customer standard at B\n"
    assert not git("diff", f"{end}..{end}", "--").stdout
    assert git("rev-parse", "--verify", "missing-ref^{commit}", check=False).returncode != 0
    assert not git("show", f"{end}:missing-file.md", check=False).returncode == 0

print("PASS: staged/unstaged union, untracked, spaces, ignored/deleted files, commit-only diff, revision glossary, empty/invalid ranges")
