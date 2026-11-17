"""review 스킬이 적어 둔 Git 범위를 일회용 저장소에서 확인한다(모델을 돌리지 않는다).

0.10.0 전에는 Codex 전환본의 검사(porting/superdomain/check_git_scopes.py)였다. 공용 폴더로 합치면서
review 스킬의 범위 규칙이 두 런타임에 같으므로 플러그인 테스트로 옮겼다.

플러그인 디렉터리에서: python3 -m unittest discover -s tests -q
"""
import subprocess
import tempfile
import unittest
from pathlib import Path


class GitScopes(unittest.TestCase):
    def test_documented_scopes(self):
        with tempfile.TemporaryDirectory(prefix="superdomain-scope-") as temporary:
            root = Path(temporary)

            def git(*args, check=True):
                return subprocess.run(["git", "-C", str(root), *args], check=check, text=True, capture_output=True)

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
            # origin/HEAD가 없으면 기준 브랜치를 추측하지 않는다(1절)
            self.assertNotEqual(git("symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD", check=False).returncode, 0)
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

            # 대상 없음: merge-base 이후의 커밋·미커밋 변경과 새 파일
            branch = git("symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD").stdout.strip()
            self.assertEqual(git("merge-base", "HEAD", branch).stdout.strip(), base)
            self.assertEqual(
                set(git("diff", "--name-status", base).stdout.splitlines()),
                {"M\tdocs/superdomain/DOMAIN.md", "M\tsrc space/Order.kt", "D\tsrc/Deleted.java", "A\tsrc/Staged.java"},
            )
            self.assertEqual(git("ls-files", "--others", "--exclude-standard").stdout.splitlines(), ["src/New.kt"])
            # 경로: 공백 있는 경로도 하나의 대상
            self.assertEqual(git("diff", "--name-status", base, "--", "src space").stdout.splitlines(), ["M\tsrc space/Order.kt"])
            self.assertEqual(git("ls-files", "--others", "--exclude-standard", "--", "src space").stdout, "")
            # 커밋 범위: 그 범위의 커밋만, 문맥은 끝점 B에서 읽는다(작업 트리를 섞지 않는다)
            self.assertEqual(
                set(git("diff", "--name-status", f"{base}..{tip}").stdout.splitlines()),
                {"M\tdocs/superdomain/DOMAIN.md", "M\tsrc space/Order.kt"},
            )
            self.assertEqual(git("show", f"{tip}:src space/Order.kt").stdout, "committed\n")
            self.assertEqual(git("show", f"{tip}:docs/superdomain/DOMAIN.md").stdout, "committed domain\n")
            self.assertEqual(git("diff", "--name-status", f"{tip}..{tip}").stdout, "")


if __name__ == "__main__":
    unittest.main()
