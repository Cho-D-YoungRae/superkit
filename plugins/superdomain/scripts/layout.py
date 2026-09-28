"""대상 프로젝트 안의 superdomain 산출물 배치 — 경로 지식의 유일한 자리.

0.3.0부터 superdomain이 대상 프로젝트에 만드는 파일은 전부 `docs/superdomain/` 아래에 있다.
다른 스크립트는 산출물 경로 문자열을 직접 갖지 않고 이 모듈에서만 받는다 — 경로가 두 곳에
적히면 쓰는 쪽과 읽는 쪽이 갈라지고, 갈라진 순간 검사가 조용히 '없음'을 본다.

**루트는 선언 파일이 정한다.** `…/docs/superdomain/DOMAIN.md`의 세 단계 위가 프로젝트 루트이고,
`- 경로:`·리포트의 표시 경로·`baseline.jsonl`의 `path`는 전부 그 루트 기준이다.

**옛 배치(0.2.x)는 읽지 않는다.** 루트 `DOMAIN.md`, `docs/domain/`, `docs/domain.md`,
`docs/domain-summary.md`를 조용히 무시하면 옛 자리의 불변식·부채가 검사에서 통째로 빠지므로,
감지해 `LayoutError`로 멈추고 실제로 있는 파일만 골라 옮기는 명령을 안내한다. 옮기는 일은
사용자가 한다 — 이 모듈은 파일을 건드리지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from parse_domain import MARKER_TEMPLATE

DOMAIN_DIR = "docs/superdomain"
DOMAIN_FILE = "DOMAIN.md"
DOMAIN_RELATIVE = f"{DOMAIN_DIR}/{DOMAIN_FILE}"
SUMMARY_RELATIVE = f"{DOMAIN_DIR}/summary.md"
CONTEXTS_RELATIVE = f"{DOMAIN_DIR}/contexts"
ADR_RELATIVE = f"{DOMAIN_DIR}/adr"
CONVENTIONS_RELATIVE = f"{DOMAIN_DIR}/conventions"
STATE_RELATIVE = f"{DOMAIN_DIR}/state"
BASELINE_RELATIVE = f"{STATE_RELATIVE}/baseline.jsonl"
REVIEW_LOG_RELATIVE = f"{STATE_RELATIVE}/review-log.jsonl"

# 옛 배치(0.2.x). 감지와 이행 안내, 그리고 baseline 이력을 이어 붙이는 데만 쓴다 — 이 경로의
# 내용을 검사 입력으로 읽는 코드는 없다.
LEGACY_DOMAIN = "DOMAIN.md"
LEGACY_SUMMARY = "docs/domain-summary.md"
LEGACY_CONTEXTS = "docs/domain"
LEGACY_CONSOLIDATED = "docs/domain.md"
LEGACY_BASELINE = f"{LEGACY_CONTEXTS}/baseline.jsonl"
LEGACY_REVIEW_LOG = f"{LEGACY_CONTEXTS}/review-log.jsonl"
LEGACY_DECISIONS = "docs/decisions"
LEGACY_CONVENTIONS = "docs/conventions"

CHANGELOG = Path(__file__).resolve().parent.parent / "CHANGELOG.md"


class LayoutError(Exception):
    """배치를 해석할 수 없다. `str(error)`가 사용자에게 그대로 보인다(스크립트는 exit 2)."""


@dataclass(frozen=True)
class Layout:
    root: Path                  # 프로젝트 루트(= DOMAIN.md의 세 단계 위)

    @property
    def domain(self) -> Path:
        return self.root / DOMAIN_RELATIVE

    @property
    def summary(self) -> Path:
        return self.root / SUMMARY_RELATIVE

    @property
    def contexts_dir(self) -> Path:
        return self.root / CONTEXTS_RELATIVE

    @property
    def adr_dir(self) -> Path:
        return self.root / ADR_RELATIVE

    @property
    def conventions_dir(self) -> Path:
        return self.root / CONVENTIONS_RELATIVE

    @property
    def state_dir(self) -> Path:
        return self.root / STATE_RELATIVE

    @property
    def baseline(self) -> Path:
        return self.root / BASELINE_RELATIVE

    @property
    def review_log(self) -> Path:
        return self.root / REVIEW_LOG_RELATIVE

    def display(self, path) -> str:
        """리포트에 쓰는 경로 — 루트 기준 POSIX 상대경로. 루트 밖이면 절대경로 그대로."""
        try:
            return Path(path).relative_to(self.root).as_posix()
        except ValueError:
            return Path(path).as_posix()


def _is_legacy_domain(path: Path) -> bool:
    """옛 배치의 루트 `DOMAIN.md`인가. 템플릿 마커가 있어야 superdomain 소유로 본다."""
    try:
        return MARKER_TEMPLATE in path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return False


def legacy_leftovers(root) -> list:
    """옛 배치에 남은 superdomain 산출물 — `[(옛 경로, 새 경로)]`, 실제로 있는 것만.

    `docs/decisions/`·`docs/conventions/`는 팀이 따로 쓰는 폴더일 수 있으므로 루트 `DOMAIN.md`가
    옛 배치로 판정됐을 때만 넣는다. `docs/domain.md`의 목적지는 파싱 없이는 컨텍스트 이름을 알
    수 없으므로 자리표시로 둔다.
    """
    root = Path(root)
    moves = []
    legacy_root = _is_legacy_domain(root / LEGACY_DOMAIN)
    if legacy_root:
        moves.append((LEGACY_DOMAIN, DOMAIN_RELATIVE))
    if (root / LEGACY_SUMMARY).is_file():
        moves.append((LEGACY_SUMMARY, SUMMARY_RELATIVE))
    if (root / LEGACY_CONSOLIDATED).is_file():
        moves.append((LEGACY_CONSOLIDATED, f"{CONTEXTS_RELATIVE}/<컨텍스트 이름>.md"))
    legacy_dir = root / LEGACY_CONTEXTS
    if legacy_dir.is_dir():
        for path in sorted(legacy_dir.glob("*.md")):
            moves.append((f"{LEGACY_CONTEXTS}/{path.name}", f"{CONTEXTS_RELATIVE}/{path.name}"))
        for old, new in ((LEGACY_BASELINE, BASELINE_RELATIVE),
                         (LEGACY_REVIEW_LOG, REVIEW_LOG_RELATIVE)):
            if (root / old).is_file():
                moves.append((old, new))
    if legacy_root:
        for old, new in ((LEGACY_DECISIONS, ADR_RELATIVE),
                         (LEGACY_CONVENTIONS, CONVENTIONS_RELATIVE)):
            if (root / old).is_dir():
                moves.append((old, new))
    return moves


def _migration_guide(moves) -> str:
    """옛 배치 전체를 옮기는 명령 목록. 실행 가능한 형태로, 있는 것만 적는다."""
    parents = sorted({str(PurePosixPath(new).parent) for _, new in moves})
    return "\n".join([
        f"옛 배치(superdomain 0.2.x)입니다 — 0.3.0부터 산출물은 {DOMAIN_DIR}/ 아래에 있습니다.",
        f"다음을 실행한 뒤 문서 간 링크를 고치고 파서를 다시 돌리세요(절차: {CHANGELOG} 0.3.0).",
        f"  mkdir -p {' '.join(parents)}",
        *(f"  git mv {old} {new}" for old, new in moves),
    ])


def _leftover_notice(moves) -> str:
    """새 선언이 있는데 옛 산출물이 남은 상태. 어느 쪽이 맞는지 모르므로 명령이 아니라 목록을 준다."""
    return "\n".join([
        f"이행이 끝나지 않았습니다 — {DOMAIN_RELATIVE}가 있는데 옛 배치의 산출물이 남아 있습니다.",
        "옛 자리의 문서는 어떤 검사도 읽지 않으므로 그대로 두면 그 안의 불변식·부채가 검사에서 빠집니다.",
        f"새 자리로 옮기거나(git mv) 이미 옮긴 사본이면 지우세요(절차: {CHANGELOG} 0.3.0).",
        *(f"  {old} → {new}" for old, new in moves),
    ])


def from_domain_path(path) -> Layout:
    """`…/docs/superdomain/DOMAIN.md` 경로에서 배치를 세운다. 세울 수 없으면 `LayoutError`.

    파일이 없어도 자리가 맞으면 배치를 돌려준다 — 읽기 실패는 파서가 자기 오류로 보고한다.
    """
    given = Path(path)
    resolved = given.resolve()
    if resolved.name == DOMAIN_FILE and resolved.parent.parts[-2:] == tuple(DOMAIN_DIR.split("/")):
        layout = Layout(resolved.parents[2])
        moves = legacy_leftovers(layout.root)
        if moves:
            raise LayoutError(_leftover_notice(moves) if resolved.is_file()
                              else _migration_guide(moves))
        return layout
    if resolved.name == DOMAIN_FILE and _is_legacy_domain(resolved):
        raise LayoutError(_migration_guide(legacy_leftovers(resolved.parent)))
    raise LayoutError(
        f"'{given}'은(는) 도메인 선언의 자리가 아닙니다 — 프로젝트 루트의 '{DOMAIN_RELATIVE}'를 "
        f"넘기세요.")
