#!/usr/bin/env python3
"""하네스 정합성 검증 — 스키마·참조·시크릿 스캔·정책 조합·키 만료·harness.yaml (stdlib 전용)."""
import argparse
import datetime
import re
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
ENC_MAGICS = (b"age-encryption.org/v1", b"-----BEGIN AGE ENCRYPTED FILE-----", b"sops", b"ENC[")
VALID_SHARING = {"local", "git", "shared-drive"}
VALID_SECRETS_MODE = {"none", "plaintext", "encrypted"}
EXPIRY_WINDOW_DAYS = 30
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
KEYS_ANCHOR_RE = re.compile(r"keys\.md#([A-Za-z0-9_.-]+)")
SCAN_SKIP_DIRS = {".git", "secrets", ".claude"}


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
    ids = {e.get("id") for e in ents if "id" in e}
    provider_ids = {e["id"] for e in ents if e.get("type") == "provider"}
    host_ids = {e["id"] for e in ents if e.get("type") in ("server", "k8s-cluster")}
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


def check_secret_scan(root, failures):
    for path in sorted(Path(root).rglob("*")):
        if not path.is_file():
            continue
        if any(part in SCAN_SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        data = path.read_bytes()
        if b"\x00" in data[:1024]:
            continue  # 바이너리 스킵
        text = data.decode("utf-8", errors="ignore")
        for pat, label in SECRET_PATTERNS:
            if re.search(pat, text):
                failures.append(f"[시크릿] {path.relative_to(root)}: {label} 패턴 검출 (secrets/ 밖 보관 금지)")


def check_secret_policy(root, cfg, failures):
    sharing = cfg.get("sharing")
    mode = cfg.get("secrets_mode")
    if mode == "plaintext" and sharing != "local":
        failures.append(f"[정책] secrets_mode: plaintext는 sharing: local에서만 허용 (현재 sharing: {sharing})")
    if mode == "encrypted":
        sdir = Path(root) / "secrets"
        for p in sorted(sdir.glob("*")) if sdir.is_dir() else []:
            if p.name == ".gitkeep" or not p.is_file():
                continue
            with p.open("rb") as fh:
                head = fh.read(512)  # 헤더 판별용 — 내용은 출력하지 않는다
            if not any(m in head for m in ENC_MAGICS):
                failures.append(f"[정책] secrets/{p.name}: age/SOPS 암호문 형식이 아님")


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
        expiry = datetime.date.fromisoformat(m.group())
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
    check_secret_scan(root, failures)
    check_secret_policy(root, cfg, failures)
    check_expiry(root, today, warnings)
    return failures, warnings


def main():
    ap = argparse.ArgumentParser(description="하네스 정합성 검증")
    ap.add_argument("--root", help="하네스 루트 (생략 시 cwd에서 상향 탐색)")
    ap.add_argument("--today", help="기준일 YYYY-MM-DD (테스트용)")
    args = ap.parse_args()
    root = Path(args.root) if args.root else harness_lib.find_harness_root()
    if root is None or not (Path(root) / "harness.yaml").is_file():
        print("하네스를 찾지 못했습니다 — 하네스 디렉터리에서 실행하거나 --root를 지정하세요.")
        return 1
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
