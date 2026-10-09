"""Exercise documented Git scopes in a disposable repo, without running a model."""
from pathlib import Path
import subprocess
import tempfile


with tempfile.TemporaryDirectory(prefix="superdomain-scope-") as temporary:
    root = Path(temporary)

    def git(*args, check=True):
        return subprocess.run(
            ["git", "-C", str(root), *args], check=check,
            text=True, capture_output=True,
        )

    def write(name, content):
        destination = root / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content)

    git("init", "-b", "main")
    git("config", "user.name", "Scope Fixture")
    git("config", "user.email", "scope@example.invalid")
    git("config", "commit.gpgsign", "false")
    write("docs/superdomain/DOMAIN.md", "base domain\n")
    write("src space/Order.kt", "base\n")
    write("src/Deleted.java", "deleted later\n")
    git("add", ".")
    git("commit", "-m", "base")
    base = git("rev-parse", "HEAD").stdout.strip()
    assert git("symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD", check=False).returncode != 0
    git("update-ref", "refs/remotes/origin/main", base)
    git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    git("switch", "-c", "feature")
    write("src space/Order.kt", "committed\n")
    write("docs/superdomain/DOMAIN.md", "committed domain\n")
    git("add", ".")
    git("commit", "-m", "feature")
    tip = git("rev-parse", "HEAD").stdout.strip()
    write("src space/Order.kt", "working tree\n")
    write("docs/superdomain/DOMAIN.md", "working tree domain\n")
    write("src/Staged.java", "staged\n")
    git("add", "src/Staged.java")
    write("src/New.kt", "untracked\n")
    (root / "src/Deleted.java").unlink()

    branch = git("symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD").stdout.strip()
    assert git("merge-base", "HEAD", branch).stdout.strip() == base
    changed = git("diff", "--name-status", base).stdout.splitlines()
    assert set(changed) == {
        "M\tdocs/superdomain/DOMAIN.md", "M\tsrc space/Order.kt",
        "D\tsrc/Deleted.java", "A\tsrc/Staged.java",
    }
    assert git("ls-files", "--others", "--exclude-standard").stdout.splitlines() == ["src/New.kt"]
    assert git("diff", "--name-status", base, "--", "src space").stdout.splitlines() == ["M\tsrc space/Order.kt"]
    assert git("ls-files", "--others", "--exclude-standard", "--", "src space").stdout == ""
    assert set(git("diff", "--name-status", f"{base}..{tip}").stdout.splitlines()) == {
        "M\tdocs/superdomain/DOMAIN.md", "M\tsrc space/Order.kt",
    }
    assert git("show", f"{tip}:src space/Order.kt").stdout == "committed\n"
    assert git("show", f"{tip}:docs/superdomain/DOMAIN.md").stdout == "committed domain\n"
    assert git("diff", "--name-status", f"{tip}..{tip}").stdout == ""

print("PASS: missing origin/HEAD, default changes, path with spaces, commit-only scope, revision reads, empty range")
