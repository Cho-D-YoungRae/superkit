"""Create disposable synthetic repositories; does not run or grade an LLM."""

import argparse
from pathlib import Path
import shutil
import subprocess


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout


def commit(repo, message):
    git(repo, "add", ".")
    git(repo, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
        "-c", "commit.gpgsign=false", "commit", "-qm", message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="New empty directory under /tmp")
    args = parser.parse_args()
    destination = args.destination.resolve()
    if not destination.is_relative_to(Path("/tmp").resolve()):
        parser.error("Use a disposable directory under /tmp")
    destination.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).resolve().parent / "fixtures"
    for fixture in sorted(source.iterdir()):
        if not fixture.is_dir():
            continue
        repo = destination / fixture.name
        shutil.copytree(fixture, repo)
        current = repo / "current-glossary.md"
        current_text = current.read_text() if current.exists() else None
        if current.exists():
            current.unlink()
        if fixture.name == "05-large":
            glossary = repo / "docs/superglossary/orders.md"
            with glossary.open("a") as output:
                for number in range(3600):
                    output.write(f"| 예시{number:04} | example{number:04} | | | 합성 fixture 용어 |\n")
                output.write("| 체결 | execution | | | 거래가 성립한 행위 |\n")
        git(repo, "init", "-q")
        commit(repo, "fixture baseline")
        if current_text is not None:
            (repo / "docs/superglossary/glossary.md").write_text(current_text)
        if fixture.name == "04-range":
            code = repo / "src/customer.ts"
            code.write_text('// Customer display name.\nexport const memberName = "example";\n')
            commit(repo, "historical customer change")
            glossary = repo / "docs/superglossary/glossary.md"
            glossary.write_text(glossary.read_text().replace("| member |", "| customer |"))
            code.write_text('// Customer display name.\nexport const customerName = "example";\n')
        print(f"{fixture.name}: {repo}")


if __name__ == "__main__":
    main()
