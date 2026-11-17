"""check 스킬이 적어 둔 Git·검색 명령을 일회용 저장소에서 실제로 실행한다. 모델의 이름 판단은 돌리지 않는다.

0.9.0 전에는 Codex 전환본의 검사(porting/superglossary/check_git_scopes.py)였다. 공용 폴더로 합치면서
개발용 검사로 옮겼다. rg 예시까지 실행하므로 ripgrep이 필요하다. CI에서는 없으면 실패하고, 로컬에서는 건너뛴다.
"""
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CHECK_SKILL = ROOT / "plugins" / "superglossary" / "skills" / "check" / "SKILL.md"


def documented_commands():
    skill = CHECK_SKILL.read_text(encoding="utf-8")
    commands = re.findall(r"`((?:git|rg) [^`\n]+)`", skill)
    commands += re.findall(r"^(git -C [^\n]+)$", skill, re.MULTILINE)
    return commands


class DocumentedCommands(unittest.TestCase):
    def test_skill_documents_every_scope(self):
        commands = documented_commands()
        self.assertEqual(len([c for c in commands if c.endswith("-z")]), 3,
                         "unstaged·staged·untracked 목록 명령이 있어야 한다")
        self.assertEqual(len([c for c in commands if c.startswith('git -C "<프로젝트 루트>" diff')
                              and c.endswith("-- docs/superglossary/")]), 3,
                         "unstaged·staged·지정 범위의 사전 diff가 있어야 한다")
        self.assertTrue(any(c.endswith("diff <범위> --") for c in commands), "커밋 범위 diff가 없다")
        self.assertTrue(any(c.startswith("rg ") and "<검색어>" in c
                            and "<프로젝트 루트>/docs/superglossary/" in c for c in commands),
                        "현재 작업 트리 사전을 검색하는 예시가 없다")
        self.assertTrue(any(c.startswith("rg ") and "<이전 용어>" in c and "<현재 용어>" in c
                            for c in commands), "사전 변경의 영향을 받는 현재 코드를 찾는 예시가 없다")


@unittest.skipIf(shutil.which("rg") is None and not os.environ.get("CI"),
                 "ripgrep 실행 파일이 PATH에 없다(CI에서는 실패로 처리한다)")
class GitScopes(unittest.TestCase):
    def test_documented_scopes(self):
        self.assertIsNotNone(shutil.which("rg"), "ripgrep이 필요하다")
        commands = documented_commands()
        selectors = [c for c in commands if c.endswith("-z")]
        glossary_diffs = [c for c in commands if c.startswith('git -C "<프로젝트 루트>" diff')
                          and c.endswith("-- docs/superglossary/")]
        range_command = next(c for c in commands if c.endswith("diff <범위> --"))
        current_search = next(c for c in commands if c.startswith("rg ") and "<검색어>" in c
                              and "<프로젝트 루트>/docs/superglossary/" in c)
        affected_search = next(c for c in commands if c.startswith("rg ")
                               and "<이전 용어>" in c and "<현재 용어>" in c)

        with tempfile.TemporaryDirectory(prefix="glossary scope ") as folder:
            repo = Path(folder)

            def git(*args, check=True):
                return subprocess.run(["git", "-C", str(repo), *args], check=check, capture_output=True)

            def write(path, body):
                file = repo / path
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text(body)

            def documented(command, **values):
                replacements = {"<프로젝트 루트>": str(repo), **values}
                args = shlex.split(command)
                for key, value in replacements.items():
                    args = [arg.replace(key, value) for arg in args]
                return subprocess.check_output(args, cwd=repo)

            git("init", "-q")
            git("config", "user.name", "Fixture")
            git("config", "user.email", "fixture@example.invalid")
            git("config", "commit.gpgsign", "false")
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

            # staged·unstaged는 따로 보이고, 삭제·ignored는 빠지며, 공백 경로가 보존된다
            write("src/order item.py", "staged_id = 1\n")
            git("add", "src/order item.py")
            write("src/order item.py", "unstaged_id = 1\n")
            (repo / "src/removed.py").unlink()
            write("src/new item.py", "candidate_id = 1\n")
            write("ignored/skip.py", "legacy_owner_id = 1\n")
            selected = [{p for p in documented(c).decode().split("\0") if p} for c in selectors]
            self.assertEqual(selected, [{"src/order item.py"}, {"src/order item.py"}, {"src/new item.py"}])
            self.assertIn(b"+staged_id", git("diff", "--cached", "--", "src/order item.py").stdout)
            self.assertIn(b"+unstaged_id", git("diff", "--", "src/order item.py").stdout)

            # 커밋 범위는 그 diff와 종료 리비전 코드만 보고, 사전은 현재 작업 트리를 쓴다
            patch = documented(range_command, **{"<범위>": f"{start}..{end}"})
            self.assertIn(b"+customer_id", patch)
            self.assertNotIn(b"staged_id", patch)
            self.assertEqual(git("show", f"{end}:src/order item.py").stdout, b"customer_id = 1\n")
            write("docs/superglossary/glossary.md", "current standard, different from B\n")
            self.assertIn(b"current standard, different from B",
                          documented(current_search, **{"<검색어>": "current"}))
            self.assertEqual(git("show", f"{end}:docs/superglossary/glossary.md").stdout,
                             b"customer standard at B\n")

            # 종료 리비전에 사전이 없어도 현재 사전을 쓴다
            git("add", ".")
            git("commit", "-qm", "working changes")
            (repo / "docs/superglossary/glossary.md").unlink()
            git("add", "docs/superglossary/glossary.md")
            git("commit", "-qm", "endpoint without glossary")
            missing_end = git("rev-parse", "HEAD").stdout.decode().strip()
            write("docs/superglossary/glossary.md", "current glossary restored\n")
            self.assertNotEqual(git("show", f"{missing_end}:docs/superglossary/glossary.md",
                                    check=False).returncode, 0)
            self.assertIn(b"current glossary restored", documented(current_search, **{"<검색어>": "current"}))
            self.assertIn(b"member_id", documented(range_command, **{"<범위>": f"{start}..{missing_end}"}))

            # 사전만 바뀐 범위에서도 바뀌지 않은 현재 코드를 찾는다
            git("add", "docs/superglossary/glossary.md")
            git("commit", "-qm", "glossary baseline")
            glossary_start = git("rev-parse", "HEAD").stdout.decode().strip()
            write("docs/superglossary/glossary.md", "current_owner replaces legacy_owner\n")
            git("add", "docs/superglossary/glossary.md")
            git("commit", "-qm", "dictionary only")
            glossary_end = git("rev-parse", "HEAD").stdout.decode().strip()
            dictionary_range = f"{glossary_start}..{glossary_end}"
            self.assertEqual(git("diff", "--name-only", dictionary_range).stdout,
                             b"docs/superglossary/glossary.md\n")
            self.assertFalse(git("diff", dictionary_range, "--", "src/unchanged.py").stdout)
            found = documented(affected_search, **{"<이전 용어>": "legacy_owner",
                                                   "<현재 용어>": "current_owner"})
            self.assertIn(b"src/unchanged.py:1:legacy_owner_id", found)
            self.assertIn(b"src/unchanged.py:2:current_owner_id", found)
            self.assertNotIn(b"docs/superglossary", found)
            self.assertNotIn(b"ignored/skip.py", found)

            # 세 사전 변경 출처가 모두 보이고, 지정 범위가 다른 출처를 대신하지 않는다
            write("docs/superglossary/glossary.md", "staged_owner replaces legacy_owner\n")
            git("add", "docs/superglossary/glossary.md")
            write("docs/superglossary/glossary.md", "unstaged_owner replaces legacy_owner\n")
            diffs = [documented(c, **{"<범위>": dictionary_range}) for c in glossary_diffs]
            self.assertTrue(any(b"+staged_owner" in d for d in diffs))
            self.assertTrue(any(b"+unstaged_owner" in d for d in diffs))
            self.assertTrue(any(b"+current_owner" in d for d in diffs))
            self.assertIn(b"unstaged_owner", documented(current_search, **{"<검색어>": "owner"}))

            # 빈 범위·없는 ref·없는 파일
            self.assertFalse(git("diff", f"{glossary_end}..{glossary_end}", "--").stdout)
            self.assertNotEqual(git("rev-parse", "--verify", "missing-ref^{commit}", check=False).returncode, 0)
            self.assertNotEqual(git("show", f"{end}:missing-file.md", check=False).returncode, 0)


if __name__ == "__main__":
    unittest.main()
