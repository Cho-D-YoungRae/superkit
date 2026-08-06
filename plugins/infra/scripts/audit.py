#!/usr/bin/env python3
"""하네스 정합성 검증 — 스키마·참조·시크릿 스캔·정책 조합·자격증명·키 만료·harness.yaml (stdlib 전용)."""
import argparse
import datetime
import json
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
VALID_SECRETS_FORMAT = {"sops-age"}
EXPIRY_WINDOW_DAYS = 30
# init이 심는 secrets/ 읽기 차단 규칙. 앵커 문법 차이에 대비해 두 형태를 병기한다(D3).
REQUIRED_DENY_RULES = ("Read(/secrets/**)", "Read(./secrets/**)")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
KEYS_ANCHOR_RE = re.compile(r"keys\.md#([A-Za-z0-9_.-]+)")
VALID_KEY_KINDS = {"ssh-key", "tls-cert", "api-token", "cloud", "account", "password"}
SCAN_SKIP_DIRS = {".git", "secrets", ".claude"}
CONFLICT_COPY_RE = re.compile(r"\(\d+\)\.md$|conflicted copy|conflict\b", re.I)


def _iter_credential_rows(root):
    """access/keys.md의 데이터 행(헤더·구분선 제외)을 셀 리스트로 순회한다(D12, 9컬럼).

    컬럼 수를 하드코딩하지 않는다 — 표 행인지(파이프로 시작), 헤더인지(첫 셀 '이름'),
    구분선인지(첫 셀이 '-'/':' 문자로만 구성)로만 데이터 행을 가린다. 9컬럼 스키마(이름/
    kind/principal/fingerprint/위치 참조/usage/소유자/생성일/만료·로테이션)의 나머지 컬럼
    인덱스는 이 함수가 아니라 호출자(key_names/check_credentials/check_expiry)가 고른다.
    """
    path = Path(root) / "access" / "keys.md"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue  # 표 행이 아님 — 제목·안내 문구 등 본문 텍스트
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not cells or not cells[0] or cells[0] == "이름":
            continue  # 빈 행 또는 헤더
        if set(cells[0]) <= {"-", ":"}:
            continue  # 구분선
        yield cells


def key_names(root):
    """access/keys.md 표의 '이름' 컬럼 값 집합(참조 무결성 검사용)."""
    return {cells[0] for cells in _iter_credential_rows(root)}


def _as_list(value):
    """frontmatter 값을 리스트로 정규화한다.

    파서는 `k: [a, b]`를 리스트로, `k: a`를 문자열로 돌려준다. 문자열을 그대로
    순회하면 글자 단위로 쪼개져 `depends_on 'p' 없음` 같은 엉뚱한 실패가 쏟아지므로
    단일 값은 1원소 리스트로 감싼다.
    """
    if value is None or value == "":
        return []
    return value if isinstance(value, list) else [value]


def _check_scalar_ref(entity, field, valid_ids, rel, failures):
    """단일 id를 가리켜야 하는 참조 필드를 검사한다.

    리스트가 오면 크래시 대신 스키마 오류로 보고한다 — 이 방어가 없던 시절
    `runs_on: [a, b]` 하나가 unhashable TypeError를 내며 audit 전체를 죽여서
    시크릿 스캔까지 통째로 건너뛰었다.
    """
    value = entity.get(field)
    if isinstance(value, list):
        failures.append(f"[스키마] {rel}: {field}는 단일 id여야 합니다 — 리스트가 주어짐")
        return
    if value not in valid_ids:
        failures.append(f"[참조] {rel}: {field} {value!r} 없음")


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
        if etype in ("server", "k8s-cluster"):
            _check_scalar_ref(e, "provider", provider_ids, rel, failures)
        if etype == "component":
            _check_scalar_ref(e, "runs_on", host_ids, rel, failures)
        for dep in _as_list(e.get("depends_on")):
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


def check_recipients(cfg, failures):
    """secrets_recipients 수신자 매니페스트 검증 — encrypted면 recovery 수신자 필수(D11).

    `secrets_recipients`는 `name: age공개키` 중첩 맵(harness_lib.parse_yaml_subset이
    지원하는 중첩 맵 형태 — 리스트-of-맵은 지원하지 않으므로 이 형태여야 한다). 값은
    공개키뿐이라 다루지 않고, `recovery` 키가 있는지만 확인한다(개인 이탈에도 접근 보존).
    `secrets_recipients` 자체가 없거나 dict가 아니어도 동일하게 실패 처리한다.
    """
    if cfg.get("secrets_mode") != "encrypted":
        return
    recipients = cfg.get("secrets_recipients")
    if not isinstance(recipients, dict) or "recovery" not in recipients:
        failures.append(
            "[정책] secrets_mode: encrypted인데 secrets_recipients에 recovery 수신자가 없다(D11)"
        )


def check_harness_yaml(cfg, failures, warnings):
    for k in ("sharing", "secrets_mode", "environments", "policies", "hooks"):
        if k not in cfg:
            failures.append(f"[harness.yaml] 필수 키 누락 — {k}")
    if cfg.get("sharing") not in VALID_SHARING:
        failures.append(f"[harness.yaml] 알 수 없는 sharing 값: {cfg.get('sharing')!r}")
    if cfg.get("secrets_mode") not in VALID_SECRETS_MODE:
        failures.append(f"[harness.yaml] 알 수 없는 secrets_mode 값: {cfg.get('secrets_mode')!r}")

    # secrets_format — 스펙 §4.4가 정의했으나 아무도 읽지 않던 키(D16 이전 死키)
    fmt = cfg.get("secrets_format")
    encrypted = cfg.get("secrets_mode") == "encrypted"
    if fmt is not None and fmt not in VALID_SECRETS_FORMAT:
        failures.append(
            f"[harness.yaml] 알 수 없는 secrets_format 값: {fmt!r} "
            f"(허용: {', '.join(sorted(VALID_SECRETS_FORMAT))})")
    elif encrypted and fmt is None:
        warnings.append("[harness.yaml] secrets_mode: encrypted인데 secrets_format이 없습니다 "
                        "— 팀 표준 암호화 형식을 명시하세요(sops-age)")
    elif not encrypted and fmt is not None:
        warnings.append(f"[harness.yaml] secrets_mode가 encrypted가 아닌데 secrets_format이 "
                        f"있습니다 — 무시되는 키입니다({fmt!r})")


def check_credentials(root, failures):
    """access/keys.md 각 자격증명 행의 kind 어휘·위치 참조 존재를 검증한다(D12).

    값은 다루지 않는다 — kind 문자열과 위치 참조 칸이 비어 있는지/'-'인지만 본다.
    """
    for cells in _iter_credential_rows(root):
        name = cells[0]
        kind = cells[1] if len(cells) > 1 else ""
        location = cells[4] if len(cells) > 4 else ""
        if kind not in VALID_KEY_KINDS:
            failures.append(f"[키] {name}: 알 수 없는 kind '{kind}'")
        if not location or location == "-":
            failures.append(f"[키] {name}: 위치 참조 누락")


def check_expiry(root, today, warnings):
    """만료·로테이션 경고 — 항상 **마지막 컬럼**만 만료일로 취급한다(D12).

    9컬럼 스키마는 생성일과 만료·로테이션을 분리된 컬럼에 둔다. 여기서 마지막 컬럼만 보므로
    생성일을 만료일로 오인하지 않는다(구 스키마에서도 마지막 컬럼이 곧 만료 컬럼이라 동일하게
    동작한다 — 컬럼 개수에 의존하지 않는다).
    """
    for cells in _iter_credential_rows(root):
        name = cells[0]
        expiry_cell = cells[-1] if cells else ""
        if not expiry_cell or expiry_cell == "-":
            continue
        m = DATE_RE.search(expiry_cell)
        if not m:
            continue
        try:
            expiry = datetime.date.fromisoformat(m.group())
        except ValueError:
            warnings.append(f"[만료] {name}: 만료일 형식이 잘못됨 ({m.group()})")
            continue
        days = (expiry - today).days
        if days < 0:
            warnings.append(f"[만료] {name}: 이미 만료됨 ({expiry})")
        elif days <= EXPIRY_WINDOW_DAYS:
            warnings.append(f"[만료] {name}: {days}일 후 만료 ({expiry})")


def _deny_rules_in(path):
    """설정 파일에서 permissions.deny 목록을 읽는다.

    파일이 없거나 JSON이 깨졌으면 None(=확인 불가), 정상이면 규칙 문자열 집합을
    돌려준다. 이 파일에는 시크릿 값이 들어갈 자리가 없고 우리가 읽는 것은
    permissions.deny 목록뿐이므로, 내용은 어디에도 출력하지 않는다.
    """
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    deny = data.get("permissions", {}).get("deny", []) if isinstance(data.get("permissions"), dict) else []
    return {r for r in deny if isinstance(r, str)}


def check_deny_rules(root, cfg, failures, warnings):
    """secrets/ 읽기 차단 설정이 실제로 남아 있는지 확인한다.

    두 가지를 본다.

    1. **드리프트**: `init`이 심은 `.claude/settings.json`을 사용자가 지우거나 편집하면
       차단은 조용히 사라진다. 플러그인은 자기 `permissions`를 배포할 수 없어서
       (플러그인 settings.json은 `agent`·`subagentStatusLine` 키만 지원) 업데이트로
       복구할 수도 없다. 그래서 드리프트 감지는 audit의 책임이다.

    2. **하위 디렉터리 구멍**: `.claude/settings.json`은 cwd의 `.claude/`에서만, 부모
       폴백 없이 로드된다. 반면 하네스 발견은 상향 탐색이라(D1) 하네스 하위 디렉터리에서
       연 세션은 **스킬은 동작하는데 차단은 없는** 상태가 된다.
       `.claude/settings.local.json`은 git 저장소 루트에서 로드되므로 이 구멍을 메운다.

    `secrets_mode: none`인 하네스는 지킬 로컬 값이 없으므로 경고로만 다룬다.
    """
    mode = str(cfg.get("secrets_mode", "")).strip()
    has_local_secrets = mode in ("plaintext", "encrypted")
    report = failures if has_local_secrets else warnings
    label = "[보호]"

    settings = Path(root) / ".claude" / "settings.json"
    rules = _deny_rules_in(settings)
    if rules is None:
        report.append(f"{label} .claude/settings.json이 없거나 읽을 수 없습니다 — "
                      "secrets/ 읽기 차단이 걸려 있지 않습니다(init을 다시 실행하세요)")
    else:
        missing = [r for r in REQUIRED_DENY_RULES if r not in rules]
        if missing:
            report.append(f"{label} .claude/settings.json의 deny 규칙 누락 — {', '.join(missing)}")

    # 하위 디렉터리 세션 보호: git 하네스만 settings.local.json으로 메울 수 있다.
    if (Path(root) / ".git").exists():
        local_rules = _deny_rules_in(Path(root) / ".claude" / "settings.local.json")
        if local_rules is None or any(r not in local_rules for r in REQUIRED_DENY_RULES):
            report.append(
                f"{label} .claude/settings.local.json에 deny 규칙이 없습니다 — "
                "하네스 하위 디렉터리에서 연 세션은 secrets/ 차단을 받지 못합니다"
                "(settings.json은 부모 폴백 없이 cwd에서만 로드됩니다)")
    elif has_local_secrets:
        warnings.append(
            f"{label} git 저장소가 아니라 하위 디렉터리 세션을 보호할 수 없습니다 — "
            "세션은 하네스 루트에서 여세요")


def _run_check(name, fn, failures, debug=False):
    """검사 하나를 예외 격리해 실행한다.

    한 검사가 죽어도 나머지는 계속 돌아야 한다 — 특히 시크릿 스캔이 다른 검사의
    버그 때문에 건너뛰어지면, 사용자는 `실패 0건`을 보고 안전하다고 믿게 된다.

    예외 **메시지는 싣지 않고 타입만** 보고한다(원칙 1). 디코딩·파싱 계열 예외는
    메시지에 파일 내용 조각을 담을 수 있어서, 진단 편의보다 값 비유출을 우선한다.
    상세가 필요하면 `--debug`로 재실행해 원래 트레이스백을 본다.
    """
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — 어떤 검사도 전체를 죽이지 못하게 한다
        if debug:
            raise
        failures.append(
            f"[내부오류] {name} 검사가 {type(exc).__name__}로 중단됐습니다 "
            "(나머지 검사는 계속 수행). 상세는 --debug로 재실행하세요."
        )


def run_audit(root, today, debug=False):
    root = Path(root)
    failures, warnings = [], []
    try:
        cfg = harness_lib.load_harness_yaml(root / "harness.yaml")
    except (OSError, harness_lib.HarnessYamlError) as e:
        return [f"[harness.yaml] 읽기/파싱 실패 — {e}"], warnings
    checks = (
        ("harness.yaml", lambda: check_harness_yaml(cfg, failures, warnings)),
        ("스키마·참조", lambda: check_schema_and_refs(root, failures)),
        ("구조", lambda: check_structure(root, failures)),
        ("시크릿 스캔", lambda: check_secret_scan(root, failures)),
        ("시크릿 정책", lambda: check_secret_policy(root, cfg, failures)),
        ("수신자", lambda: check_recipients(cfg, failures)),
        ("자격증명", lambda: check_credentials(root, failures)),
        ("보호 설정", lambda: check_deny_rules(root, cfg, failures, warnings)),
        ("만료", lambda: check_expiry(root, today, warnings)),
    )
    for name, fn in checks:
        _run_check(name, fn, failures, debug)
    return failures, warnings


def _staged_files_in_harness(root):
    """git staged(ACM) 파일 중 하네스(root) 안에 있는 절대경로만 반환.

    git 실행파일이 없거나, root가 git 저장소가 아니거나, git 호출이 실패하면 None을
    돌려준다(호출자는 이를 '일반 audit로 폴백' 신호로 쓴다). subprocess만 쓰고 파일
    내용은 어디서도 읽거나 출력하지 않는다 — 이름(경로)만 다룬다. 어떤 예외가 나도
    크래시하지 않는다.

    diff는 `-z`로 NUL 구분 출력을 받아 **바이트로** 캡처한다 — `-z` 없이 텍스트로 받으면
    core.quotePath(기본 true) 때문에 한글 등 비-ASCII 파일명이 따옴표+8진수 이스케이프로
    감싸져 나와 실제 경로와 달라지고, 결국 뒤에서 조용히 스킵(미탐)된다. `-z` 출력은
    이스케이프 없이 원문 그대로 NUL로만 구분되므로 바이트 split 후 디코딩하면 안전하다.
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
            ["git", "-C", str(toplevel), "diff", "--cached", "--name-only", "-z", "--diff-filter=ACM"],
            capture_output=True, check=False,  # text=False — 바이트로 캡처(따옴표·이스케이프 없음)
        )
        if diff.returncode != 0:
            return None
    except (OSError, subprocess.SubprocessError):
        return None
    files = []
    for name in diff.stdout.split(b"\0"):
        if not name:
            continue
        rel = name.decode("utf-8")
        abs_path = (toplevel / rel).resolve()
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

    root는 반드시 .resolve()로 정규화한다 — staged_paths(_staged_files_in_harness가
    돌려주는 절대경로)는 이미 .resolve()된 값인데, main이 넘기는 root는 미resolve
    상태일 수 있다(예: --root가 심링크를 경유). 여기서 맞춰주지 않으면 root에 심링크
    구성요소가 있을 때 fp.relative_to(root)가 ValueError로 크래시한다(D13).
    """
    root = Path(root).resolve()
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
    ap.add_argument("--debug", action="store_true",
                     help="검사 내부 오류를 감추지 않고 트레이스백을 그대로 띄운다")
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
    failures, warnings = run_audit(root, today, debug=args.debug)
    print(f"# audit 결과 — {root}")
    for f in failures:
        print(f"FAIL {f}")
    for w in warnings:
        print(f"WARN {w}")
    print(f"실패 {len(failures)}건 / 경고 {len(warnings)}건")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
