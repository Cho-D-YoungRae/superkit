"""플러그인 레이아웃 불변식 — 슬래시 커맨드는 워크플로 스킬 4개, 나머지 스킬은 모델 전용.

커맨드는 공식 권장 형식인 `skills/<이름>/SKILL.md`로 둔다(`commands/`는 이전 형식).
호출명은 `/llm-wiki:<디렉토리명>`이므로 frontmatter `name`은 디렉토리명과 같아야 한다.
"""
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
WORKFLOWS = {"wiki-init", "wiki-ingest", "wiki-lint", "wiki-status"}


def frontmatter(path: Path) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.S)
    assert m, f"{path}: frontmatter 없음"
    return yaml.safe_load(m.group(1))


SKILL_FILES = sorted(SKILLS.glob("*/SKILL.md"))


@pytest.mark.parametrize("path", SKILL_FILES, ids=lambda p: p.parent.name)
def test_skill_name_matches_directory_and_has_description(path):
    fm = frontmatter(path)
    assert fm.get("name") == path.parent.name
    assert isinstance(fm.get("description"), str) and fm["description"].strip()


def test_slash_commands_are_exactly_the_four_workflows():
    visible = {p.parent.name for p in SKILL_FILES if frontmatter(p).get("user-invocable", True) is not False}
    assert visible == WORKFLOWS, "사용자 호출 슬래시 커맨드는 워크플로 4개만(보조 스킬은 user-invocable: false)"


def test_no_legacy_commands_directory():
    assert not (ROOT / "commands").exists(), "commands/와 skills/에 같은 이름이 있으면 충돌 동작이 문서화돼 있지 않다"


# 실행 점검에서 `cd <위키> && cat …`·셸 변수·플래그 붙은 cp 같은 복합 명령이 사용자의 권한 확인을 불렀다.
# 스킬은 위키 파일을 절대 경로로 가리키고, 읽기·검색은 Read·Glob·Grep 도구로 한다(ARCHITECTURE ADR-8).
@pytest.mark.parametrize("path", SKILL_FILES, ids=lambda p: p.parent.name)
def test_skills_do_not_prescribe_cd_chains(path):
    assert 'cd "<위키 루트>" &&' not in path.read_text(encoding="utf-8")


@pytest.mark.parametrize("path", SKILL_FILES, ids=lambda p: p.parent.name)
def test_wiki_check_invocations_pass_root(path):
    for line in path.read_text(encoding="utf-8").splitlines():
        if "uv run" in line and "wiki_check.py" in line:
            assert '--root "<위키 루트>"' in line, f"{path.parent.name}: cd 대신 --root로 위키를 가리킨다 — {line.strip()}"
