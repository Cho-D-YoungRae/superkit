#!/usr/bin/env python3
"""하네스 정합성 검증 — 스키마·참조·시크릿 스캔·정책 조합·키 만료·harness.yaml (stdlib 전용)."""
import argparse
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_lib  # noqa: E402

SECRET_PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID(AKIA...)"),
    (r"ASIA[0-9A-Z]{16}", "AWS 임시 Access Key ID"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "개인키 블록"),
    (r"aws_secret_access_key\s*[:=]", "AWS Secret Key 할당문"),
    (r"ghp_[A-Za-z0-9]{36}", "GitHub PAT"),
    (r"github_pat_[A-Za-z0-9_]{20,}", "GitHub fine-grained PAT"),
    (r"xox[baprs]-[A-Za-z0-9-]{10,}", "Slack 토큰"),
    (r"AIza[0-9A-Za-z_-]{35}", "Google API Key"),
    (r"AGE-SECRET-KEY-1[A-Z0-9]{20,}", "age 복호키"),
]
AGE_PREFIXES = (b"age-encryption.org/v1", b"-----BEGIN AGE ENCRYPTED FILE-----")
VALID_SHARING = {"local", "git", "shared-drive"}
VALID_SECRETS_MODE = {"none", "plaintext", "encrypted"}
EXPIRY_WINDOW_DAYS = 30
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
KEYS_ANCHOR_RE = re.compile(r"keys\.md#([A-Za-z0-9_.-]+)")
SCAN_SKIP_DIRS = {".git", "secrets", ".claude"}
CONFLICT_COPY_RE = re.compile(r"\(\d+\)\.md$|conflicted copy|conflict\b", re.I)


def key_names(root):
    """access/keys.md 표의 '이름' 컬럼 값 집합."""
    path = Path(root) / "access" / "keys.md"
    names = set()
    if not path.is_file():
        return names
    for line in path.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 7 and cells[0] not in ("이름", "") and not set(cells[0]) <= {"-"}:
            names.add(cells[0])
    return names


def check_schema_and_refs(root, failures):
    ents = harness_lib.iter_entities(root)
    ids = {e.get("id") for e in ents if e.get("id")}
    provider_ids = {e["id"] for e in ents if e.get("type") == "provider" and e.get("id")}
    host_ids = {e["id"] for e in ents if e.get("type") in ("server", "k8s-cluster") and e.get("id")}
    keys = key_names(root)
    for e in ents:
        rel = e["_path"].relative_to(root)
        if "_error" in e:
            failures.append(f"[스키마] {rel}: frontmatter 파싱 실패 — {e['_error']}")
            continue
        etype = e.get("type")
        required = harness_lib.REQUIRED_FIELDS.get(etype)
        if required is None:
            failures.append(f"[스키마] {rel}: 알 수 없는 type {etype!r}")
            continue
        for f in required:
            if f not in e:
                failures.append(f"[스키마] {rel}: 필수 필드 누락 — {f}")
        if e.get("id") != e["_stem"]:
            failures.append(f"[스키마] {rel}: id({e.get('id')})와 파일명({e['_stem']}) 불일치")
        if etype in ("server", "k8s-cluster") and e.get("provider") not in provider_ids:
            failures.append(f"[참조] {rel}: provider {e.get('provider')!r} 없음")
        if etype == "component" and e.get("runs_on") not in host_ids:
            failures.append(f"[참조] {rel}: runs_on {e.get('runs_on')!r} 없음")
        for dep in e.get("depends_on", []) or []:
            if dep not in ids:
                failures.append(f"[참조] {rel}: depends_on {dep!r} 없음")
        for anchor in KEYS_ANCHOR_RE.findall(str(e.get("access", ""))):
            if anchor not in keys:
                failures.append(f"[참조] {rel}: keys.md#{anchor} 앵커 없음")


def check_structure(root, failures):
    """엔티티 구조 하드닝(D13) — 중복 id·conflict-copy 파일명 탐지.

    중복 id 검사는 `_error`(frontmatter 파싱 실패) 엔티티를 제외한 유효 id만 대상으로 한다 —
    파싱 실패 엔티티는 id를 신뢰할 수 없고 check_schema_and_refs가 이미 별도로 보고한다.
    conflict-copy 파일명 검사는 파싱 성공 여부와 무관하게 모든 엔티티 파일에 적용한다.
    """
    root = Path(root)
    ents = harness_lib.iter_entities(root)
    by_id = {}
    for e in ents:
        if "_error" in e:
            continue
        eid = e.get("id")
        if not eid:
            continue
        by_id.setdefault(eid, []).append(e["_path"])
    for eid in sorted(by_id):
        paths = by_id[eid]
        if len(paths) > 1:
            rels = ", ".join(str(p.relative_to(root)) for p in sorted(paths))
            failures.append(f"[구조] id '{eid}' 중복 — {rels}")
    for e in ents:
        name = e["_path"].name
        if CONFLICT_COPY_RE.search(name):
            rel = e["_path"].relative_to(root)
            failures.append(f"[구조] 충돌 사본 의심 파일: {rel}")


def check_secret_scan(root, failures):
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(
            d for d in dirnames
            if d not in SCAN_SKIP_DIRS and not os.path.islink(os.path.join(dirpath, d))
        )
        for fn in sorted(filenames):
            fp = Path(dirpath) / fn
            if fp.is_symlink():
                continue  # 심볼릭 링크는 읽기 전에 거부 — 대상을 절대 읽지 않는다
            rel = fp.relative_to(root)
            if any(part in SCAN_SKIP_DIRS for part in rel.parts):
                continue
            data = fp.read_bytes()
            if b"\x00" in data[:1024]:
                continue  # 바이너리 스킵
            text = data.decode("utf-8", errors="ignore")
            for pat, label in SECRET_PATTERNS:
                if re.search(pat, text):
                    failures.append(f"[시크릿] {rel}: {label} 패턴 검출 (secrets/ 밖 보관 금지)")


def _classify_encrypted(path):
    """secrets/ 파일이 age/SOPS 암호문 형식인지 헤더·꼬리 마커로만 판별(복호·전체 파싱·값 출력 없음).

    age는 파일 시작에 고정 헤더가 온다(head.startswith). SOPS는 sops:/mac 메타데이터가
    파일 **끝**에 붙으므로(4096B 초과 파일에서는 head만으로 보이지 않는다) head와 tail을
    모두 읽어 구조 마커 동시 존재로 판별한다(느슨한 단일 substring 금지 — 엄격 검사).
    암호학적 유효성을 주장하지 않으며, 매치된 내용을 어디에도 출력하지 않는다.
    """
    with path.open("rb") as fh:
        head = fh.read(4096)
        try:
            fh.seek(-4096, 2)          # SEEK_END — SOPS의 sops:/mac 메타데이터는 파일 끝에 온다
            tail = fh.read(4096)
        except OSError:
            tail = b""                 # 4096B 미만 파일: head가 전체
    if any(head.startswith(pfx) for pfx in AGE_PREFIXES):
        return True
    blob = head + tail
    if b"ENC[" in blob and (b"sops" in blob or b'"mac"' in blob or b"mac:" in blob):
        return True
    return False


def check_secret_policy(root, cfg, failures):
    sharing = cfg.get("sharing")
    mode = cfg.get("secrets_mode")
    if mode == "plaintext" and sharing != "local":
        failures.append(f"[정책] secrets_mode: plaintext는 sharing: local에서만 허용 (현재 sharing: {sharing})")
    sdir = Path(root) / "secrets"
    if mode == "encrypted" and sdir.is_dir():
        for dirpath, dirnames, filenames in os.walk(sdir, followlinks=False):
            # 심링크 디렉터리: 파일 심링크와 동일하게 정책 위반으로 보고한 뒤 재귀에서 제외(prune)
            for d in list(dirnames):
                dp = Path(dirpath) / d
                if os.path.islink(dp):
                    failures.append(f"[정책] secrets/{dp.relative_to(sdir)}: 심볼릭 링크는 허용하지 않는다(내용 미확인)")
            dirnames[:] = sorted(d for d in dirnames if not os.path.islink(os.path.join(dirpath, d)))
            for fn in sorted(filenames):
                p = Path(dirpath) / fn
                rel = p.relative_to(sdir)
                if p.is_symlink():
                    # 읽기 전에 거부 — 하네스 밖 링크 대상을 절대 추종하지 않는다
                    failures.append(f"[정책] secrets/{rel}: 심볼릭 링크는 허용하지 않는다(내용 미확인)")
                    continue
                if p.name == ".gitkeep":
                    continue
                if not _classify_encrypted(p):
                    failures.append(f"[정책] secrets/{rel}: age/SOPS 암호문 형식이 아님")
    if mode == "none" and sdir.is_dir():
        for dirpath, dirnames, filenames in os.walk(sdir, followlinks=False):
            dirnames[:] = sorted(d for d in dirnames if not os.path.islink(os.path.join(dirpath, d)))
            for fn in sorted(filenames):
                p = Path(dirpath) / fn
                if p.is_symlink() or p.name == ".gitkeep":
                    continue
                rel = p.relative_to(sdir)
                failures.append(f"[정책] secrets/{rel}: secrets_mode: none인데 시크릿 페이로드 파일이 있다")


def check_harness_yaml(cfg, failures):
    for k in ("sharing", "secrets_mode", "environments", "policies", "hooks"):
        if k not in cfg:
            failures.append(f"[harness.yaml] 필수 키 누락 — {k}")
    if cfg.get("sharing") not in VALID_SHARING:
        failures.append(f"[harness.yaml] 알 수 없는 sharing 값: {cfg.get('sharing')!r}")
    if cfg.get("secrets_mode") not in VALID_SECRETS_MODE:
        failures.append(f"[harness.yaml] 알 수 없는 secrets_mode 값: {cfg.get('secrets_mode')!r}")


def check_expiry(root, today, warnings):
    path = Path(root) / "access" / "keys.md"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 7 or cells[0] in ("이름", "") or set(cells[0]) <= {"-"}:
            continue
        m = DATE_RE.search(cells[6])
        if not m:
            continue
        try:
            expiry = datetime.date.fromisoformat(m.group())
        except ValueError:
            warnings.append(f"[만료] {cells[0]}: 만료일 형식이 잘못됨 ({m.group()})")
            continue
        days = (expiry - today).days
        if days < 0:
            warnings.append(f"[만료] {cells[0]}: 이미 만료됨 ({expiry})")
        elif days <= EXPIRY_WINDOW_DAYS:
            warnings.append(f"[만료] {cells[0]}: {days}일 후 만료 ({expiry})")


def run_audit(root, today):
    root = Path(root)
    failures, warnings = [], []
    try:
        cfg = harness_lib.load_harness_yaml(root / "harness.yaml")
    except (OSError, harness_lib.HarnessYamlError) as e:
        return [f"[harness.yaml] 읽기/파싱 실패 — {e}"], warnings
    check_harness_yaml(cfg, failures)
    check_schema_and_refs(root, failures)
    check_structure(root, failures)
    check_secret_scan(root, failures)
    check_secret_policy(root, cfg, failures)
    check_expiry(root, today, warnings)
    return failures, warnings


def _staged_files_in_harness(root):
    """git staged(ACM) 파일 중 하네스(root) 안에 있는 절대경로만 반환.

    git 실행파일이 없거나, root가 git 저장소가 아니거나, git 호출이 실패하면 None을
    돌려준다(호출자는 이를 '일반 audit로 폴백' 신호로 쓴다). subprocess만 쓰고 파일
    내용은 어디서도 읽거나 출력하지 않는다 — 이름(경로)만 다룬다. 어떤 예외가 나도
    크래시하지 않는다.
    """
    root = Path(root).resolve()
    try:
        top = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
        if top.returncode != 0:
            return None
        toplevel = Path(top.stdout.strip())
        diff = subprocess.run(
            ["git", "-C", str(toplevel), "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True, text=True, check=False,
        )
        if diff.returncode != 0:
            return None
    except (OSError, subprocess.SubprocessError):
        return None
    files = []
    for line in diff.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        abs_path = (toplevel / line).resolve()
        try:
            abs_path.relative_to(root)
        except ValueError:
            continue  # 하네스 밖 — staged 스캔 대상 아님
        files.append(abs_path)
    return files


def check_staged_secret_scan(root, staged_paths, failures):
    """staged 파일 중 하네스 안 텍스트 파일만 B1의 SECRET_PATTERNS로 스캔한다.

    check_secret_scan과 동일하게 secrets/ 등 SCAN_SKIP_DIRS는 제외한다(그 안은 별도
    정책 검사(check_secret_policy) 담당). 복호·매치 값 출력 없음 — 패턴 라벨만 보고.
    """
    root = Path(root)
    for fp in staged_paths:
        if fp.is_symlink() or not fp.is_file():
            continue
        rel = fp.relative_to(root)
        if any(part in SCAN_SKIP_DIRS for part in rel.parts):
            continue
        try:
            data = fp.read_bytes()
        except OSError:
            continue
        if b"\x00" in data[:1024]:
            continue  # 바이너리 스킵
        text = data.decode("utf-8", errors="ignore")
        for pat, label in SECRET_PATTERNS:
            if re.search(pat, text):
                failures.append(f"[시크릿] {rel}: {label} 패턴 검출 (secrets/ 밖 보관 금지)")


def main():
    ap = argparse.ArgumentParser(description="하네스 정합성 검증")
    ap.add_argument("--root", help="하네스 루트 (생략 시 cwd에서 상향 탐색)")
    ap.add_argument("--today", help="기준일 YYYY-MM-DD (테스트용)")
    ap.add_argument("--staged", action="store_true",
                     help="git staged 파일만 대상으로 시크릿 패턴 스캔 (pre-commit용)")
    args = ap.parse_args()
    root = Path(args.root) if args.root else harness_lib.find_harness_root()
    if root is None or not (Path(root) / "harness.yaml").is_file():
        print("하네스를 찾지 못했습니다 — 하네스 디렉터리에서 실행하거나 --root를 지정하세요.")
        return 1

    if args.staged:
        try:
            staged = _staged_files_in_harness(root)
        except Exception:
            staged = None
        if staged is None:
            print("git 저장소가 아니라 --staged를 건너뜁니다 — 일반 audit로 진행합니다.")
        else:
            failures = []
            check_staged_secret_scan(root, staged, failures)
            print(f"# audit --staged 결과 — {root} (staged {len(staged)}개 파일)")
            for f in failures:
                print(f"FAIL {f}")
            print(f"실패 {len(failures)}건")
            return 1 if failures else 0

    today = datetime.date.fromisoformat(args.today) if args.today else datetime.date.today()
    failures, warnings = run_audit(root, today)
    print(f"# audit 결과 — {root}")
    for f in failures:
        print(f"FAIL {f}")
    for w in warnings:
        print(f"WARN {w}")
    print(f"실패 {len(failures)}건 / 경고 {len(warnings)}건")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
