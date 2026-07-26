# 팀 시크릿·자격증명·audit 하드닝 구현 계획 (D11~D14)

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development(권장). 태스크 단위 구현→리뷰 게이트. 스텝은 체크박스(`- [ ]`).

**Goal:** 팀 협업(git/공유드라이브) + 넓은 시크릿 관리(계정·비밀번호·외부 매니저 Vault) + audit 보안 하드닝을 구현한다. 스펙 D11~D14가 SSOT.

**Architecture:** 4개 그룹, 권장 순서 B→A1→A2→C. ① 그룹 B: `scripts/audit.py` 보안 하드닝(심링크·재귀·none 강제·엄격 헤더·conflict-copy·--staged) + 테스트. ② 그룹 A1: keys.md 자격증명 스키마 개정(kind/principal/usage) + audit 컬럼 처리 + register/lookup. ③ 그룹 A2: 신규 `secrets` 스킬(팀 라이프사이클) + harness.yaml 수신자 매니페스트 + init·audit 연동 + 외부 백엔드 references. ④ 그룹 C: README(유즈케이스·빠른시작·트러블슈팅).

**Tech Stack:** python3 stdlib unittest, SKILL.md(한국어), 엔티티/설정 템플릿.

## Global Constraints

- 스펙 D11~D14가 SSOT. 스키마를 더 바꾸려면 스펙을 먼저 갱신.
- **원칙 1**: 시크릿 **값**을 읽거나 출력·복호하지 않는다. audit은 어떤 경우에도 복호 안 함, 매치 값 미출력. 비밀번호는 argv 금지 — `sops exec-env`·`op run`·stdin만.
- **python3 표준 라이브러리만**. `harness.yaml` 로더(`parse_yaml_subset`)는 중첩 맵은 되지만 **리스트-of-맵은 안 됨** → `secrets_recipients`는 `name: age공개키` 중첩 맵.
- 커밋은 태스크마다, 한국어 Conventional Commits + `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`. 테스트는 `bash tests/run_tests.sh`.
- 스킬 편집·신규는 `tests/test_skills.py` 강제 조건 유지(frontmatter name=디렉토리, description 한 줄 스칼라 ≥80자, 본문에 "원칙"·"harness.yaml").
- audit은 `.claude/settings.json` deny가 **보안 경계가 아니라 가드레일**임을 전제(Bash/Python은 읽음) — 그래서 audit의 시크릿 스캔이 실질 방어선.

---

## 그룹 B — audit 하드닝 (D13)

### Task B1: 시크릿 스캔 하드닝 (심링크·재귀·none 강제·엄격 헤더)

**Files:**
- Modify: `scripts/audit.py` (`check_secret_scan`, `check_secret_policy`)
- Modify: `tests/test_audit.py`
- Create: `tests/fixtures/harness-bad/secrets/` 관련 파일(아래 Step에서 명시)

**Interfaces:**
- Consumes: 기존 `run_audit`, `harness_lib`.
- Produces: 하드닝된 시크릿 스캔 — 이후 A2-1의 `secrets_recipients` 정책 검사가 같은 `check_secret_policy`에 이어 붙는다.

- [ ] **Step 1: 실패 테스트 작성** — `tests/test_audit.py`에 클래스 추가:

```python
class TestAuditHardening(unittest.TestCase):
    def _root(self, files, harness="sharing: local\nsecrets_mode: encrypted\nenvironments: [prod]\npolicies:\n  mutating:\n    prod: confirm\nhooks:\n  change_reminder: true\n"):
        import tempfile
        d = tempfile.mkdtemp()
        root = Path(d)
        (root / "harness.yaml").write_text(harness, encoding="utf-8")
        (root / "secrets").mkdir()
        for rel, content in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                p.write_bytes(content)
            else:
                p.write_text(content, encoding="utf-8")
        return root

    def test_symlink_in_secrets_rejected_not_followed(self):
        root = self._root({})
        target = root.parent / "outside-secret.txt"
        target.write_text("AKIAIOSFODNN7EXAMPLE\n", encoding="utf-8")
        (root / "secrets" / "link.age").symlink_to(target)
        failures = []
        import audit
        audit.check_secret_policy(root, {"sharing": "local", "secrets_mode": "encrypted"}, failures)
        joined = "\n".join(failures)
        self.assertIn("link.age", joined)           # 심링크가 보고되고
        self.assertIn("심볼릭 링크", joined)          # 링크로 분류
        self.assertNotIn("AKIA", joined)             # 대상 내용은 절대 안 읽음

    def test_nested_encrypted_file_checked(self):
        # secrets/ 하위 디렉터리의 비암호문도 잡는다(재귀)
        root = self._root({"secrets/team/plain.txt": b"not encrypted at all\n"})
        failures = []
        import audit
        audit.check_secret_policy(root, {"sharing": "local", "secrets_mode": "encrypted"}, failures)
        self.assertTrue(any("plain.txt" in f and "암호문 형식이 아님" in f for f in failures))

    def test_strict_header_rejects_loose_substring(self):
        # 'sops'가 파일 중간에 있을 뿐 유효 암호문 아님 → 엄격 검사로 실패
        root = self._root({"secrets/fake.age": b"hello sops world not encrypted\n"})
        failures = []
        import audit
        audit.check_secret_policy(root, {"sharing": "local", "secrets_mode": "encrypted"}, failures)
        self.assertTrue(any("fake.age" in f for f in failures))

    def test_valid_age_and_sops_pass(self):
        root = self._root({
            "secrets/ok.age": b"age-encryption.org/v1\n-> X25519 abc\n--- def\n",
            "secrets/ok.sops.yaml": b"data: ENC[AES256_GCM,data:xx]\nsops:\n    mac: ENC[AES256_GCM,data:yy]\n",
        })
        failures = []
        import audit
        audit.check_secret_policy(root, {"sharing": "local", "secrets_mode": "encrypted"}, failures)
        self.assertEqual([f for f in failures if "ok.age" in f or "ok.sops.yaml" in f], [])

    def test_secrets_mode_none_forbids_payload(self):
        root = self._root({"secrets/leftover.age": b"age-encryption.org/v1\n"})
        failures = []
        import audit
        audit.check_secret_policy(root, {"sharing": "local", "secrets_mode": "none"}, failures)
        self.assertTrue(any("leftover.age" in f and "secrets_mode: none" in f for f in failures))
```

- [ ] **Step 2: RED 확인** — `bash tests/run_tests.sh 2>&1 | tail -8` → 신규 5개 FAIL(현재 로직: glob 직속 자식만, 느슨한 substring, none 미강제, 심링크 미거부).

- [ ] **Step 3: `scripts/audit.py` 구현** — `check_secret_policy`를 아래 사양으로 개정(실제 파일을 읽어 기존 함수 교체):

  - `encrypted` 분기: `sdir.glob("*")` → `sdir.rglob("*")`(재귀). 각 항목:
    - `p.is_symlink()`면 `failures.append(f"[정책] secrets/{p.relative_to(sdir)}: 심볼릭 링크는 허용하지 않는다(내용 미확인)")` 후 **읽지 않고** continue.
    - `p.name == ".gitkeep"` 또는 `not p.is_file()`이면 continue.
    - `_classify_encrypted(p)` 호출로 형식 판별. 미인식이면 `failures.append(f"[정책] secrets/{p.relative_to(sdir)}: age/SOPS 암호문 형식이 아님")`.
  - 신규 헬퍼 `_classify_encrypted(path) -> bool`(모듈 함수): 첫 4096바이트만 읽어(헤더/구조 마커 판별, 복호·전체 파싱 안 함):
    ```python
    AGE_PREFIXES = (b"age-encryption.org/v1", b"-----BEGIN AGE ENCRYPTED FILE-----")
    def _classify_encrypted(path):
        with path.open("rb") as fh:
            head = fh.read(4096)
        if any(head.startswith(pfx) for pfx in AGE_PREFIXES):
            return True
        # SOPS: 구조 마커 동시 존재(암호학적 검증 아님, 값 미출력)
        if b"sops" in head and (b"ENC[" in head or b'"mac"' in head or b"mac:" in head):
            return True
        return False
    ```
  - `none` 강제(신규 분기, `check_secret_policy` 안): `mode == "none"`이면 `secrets/`를 rglob해 `.gitkeep`·심링크·디렉터리 아닌 **실제 파일이 하나라도 있으면** `failures.append(f"[정책] secrets/{rel}: secrets_mode: none인데 시크릿 페이로드 파일이 있다")`.
  - `check_secret_scan`(secrets/ **밖** 평문 스캔)에도 심링크 가드 추가: 루프에서 `path.is_symlink()`면 continue(대상을 읽지 않음). 기존 SCAN_SKIP_DIRS·바이너리 스킵·패턴 매칭은 유지.

- [ ] **Step 4: GREEN 확인** — `bash tests/run_tests.sh 2>&1 | tail -6` → 전체 통과(기존 56 + 신규 5 = 61), skip 0, ResourceWarning 없음.

- [ ] **Step 5: 커밋**
```bash
git add scripts/audit.py tests/test_audit.py
git commit -m "feat: audit 시크릿 스캔 하드닝 — 심링크 거부·재귀·none 강제·엄격 헤더(D13)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task B2: 구조 하드닝(중복 id·conflict-copy) + `--staged` 모드

**Files:**
- Modify: `scripts/audit.py` (`check_schema_and_refs` 또는 신규 `check_structure`, `main`)
- Modify: `tests/test_audit.py`

**Interfaces:**
- Consumes: B1의 audit.py.
- Produces: `python3 scripts/audit.py --staged` (git staged 파일만 대상). pre-commit 훅용.

- [ ] **Step 1: 실패 테스트** — `tests/test_audit.py`에 추가:

```python
class TestAuditStructure(unittest.TestCase):
    def test_conflict_copy_filename_flagged(self):
        import tempfile, datetime
        d = tempfile.mkdtemp(); root = Path(d)
        (root / "harness.yaml").write_text("sharing: shared-drive\nsecrets_mode: none\nenvironments: [prod]\npolicies:\n  mutating:\n    prod: confirm\nhooks:\n  change_reminder: true\n", encoding="utf-8")
        (root / "inventory").mkdir()
        (root / "inventory" / "prod-db-01 (1).md").write_text("---\nid: prod-db-01\ntype: server\nenv: prod\nprovider: p\nruntime: ec2\npurpose: x\naccess: y\nmanaged_by: manual\n---\n", encoding="utf-8")
        import audit
        failures, _ = audit.run_audit(root, datetime.date(2026,7,22))
        self.assertTrue(any("conflict" in f.lower() or "충돌 사본" in f for f in failures))

    def test_duplicate_id_flagged(self):
        import tempfile, datetime
        d = tempfile.mkdtemp(); root = Path(d)
        (root / "harness.yaml").write_text("sharing: local\nsecrets_mode: none\nenvironments: [prod]\npolicies:\n  mutating:\n    prod: confirm\nhooks:\n  change_reminder: true\n", encoding="utf-8")
        (root / "inventory").mkdir(); (root / "providers").mkdir()
        body = "---\nid: dup\ntype: server\nenv: prod\nprovider: p\nruntime: ec2\npurpose: x\naccess: y\nmanaged_by: manual\n---\n"
        (root / "inventory" / "dup.md").write_text(body, encoding="utf-8")
        (root / "providers" / "dup.md").write_text("---\nid: dup\ntype: provider\nkind: aws\n---\n", encoding="utf-8")
        import audit
        failures, _ = audit.run_audit(root, datetime.date(2026,7,22))
        self.assertTrue(any("중복" in f and "dup" in f for f in failures))
```

`--staged`는 git 의존이라 단위 테스트에서 실제 git 없이 검증이 어렵다 → CLI 인자 파싱만 확인:

```python
class TestAuditStagedFlag(unittest.TestCase):
    def test_staged_flag_parses(self):
        import subprocess, sys
        script = str(PLUGIN_ROOT / "scripts" / "audit.py")
        # --staged를 git 아닌 디렉터리에서 실행하면 "git 저장소 아님" 안내 후 비크래시(exit 0 또는 1)
        r = subprocess.run([sys.executable, script, "--root", str(OK), "--staged"], capture_output=True, text=True)
        self.assertIn(r.returncode, (0, 1))
        self.assertNotIn("Traceback", r.stderr)
```

- [ ] **Step 2: RED 확인** — 신규 3개 FAIL.

- [ ] **Step 3: 구현**
  - 신규 `check_structure(root, failures)`: `iter_entities`로 모은 엔티티에서 ① 같은 `id`가 2개 이상 파일에 나오면 `failures.append(f"[구조] id '{eid}' 중복 — {경로들}")` ② 파일명이 conflict-copy 패턴(`re.search(r"\(\d+\)\.md$|conflicted copy|conflict\b", name, re.I)`)이면 `failures.append(f"[구조] 충돌 사본 의심 파일: {rel}")`. `run_audit`에서 호출(스키마 검사와 함께).
  - `main`에 `--staged` 플래그: git `git diff --cached --name-only --diff-filter=ACM`로 staged 파일 목록을 얻어, 그 중 하네스 안 텍스트 파일만 시크릿 패턴 스캔(B1의 SECRET_PATTERNS 재사용)한다. git이 없거나 저장소가 아니면 "git 저장소가 아니라 --staged를 건너뜁니다" 출력 후 일반 audit로 폴백. subprocess 사용, 복호·값 출력 없음.

- [ ] **Step 4: GREEN** — 전체 통과(61 + 3 = 64).

- [ ] **Step 5: 커밋**
```bash
git add scripts/audit.py tests/test_audit.py
git commit -m "feat: audit 구조 하드닝(중복 id·conflict-copy) + --staged 모드(D13)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## 그룹 A1 — 자격증명 스키마 (D12·D14)

### Task A1-1: keys.md 스키마 개정 + audit 컬럼 처리 + fixture

**Files:**
- Modify: `templates/keys.md`
- Modify: `scripts/audit.py` (`key_names`, `check_expiry`, 신규 kind 검증)
- Modify: `tests/fixtures/harness-ok/access/keys.md`, `tests/fixtures/harness-bad/access/keys.md`
- Modify: `tests/test_audit.py`

**Interfaces:**
- Consumes: B2까지의 audit.py.
- Produces: 9컬럼 keys.md 스키마(이름/kind/principal/fingerprint/위치참조/usage/소유자/생성일/만료·로테이션). `key_names`는 컬럼0(이름) 기준 유지, `check_expiry`는 **마지막 컬럼(만료·로테이션)**에서만 날짜 추출(생성일 오인 방지). A1-2 register/lookup이 이 스키마로 행을 쓴다.

- [ ] **Step 1: 실패 테스트** — 기존 fixture를 새 스키마로 바꾸면 `check_expiry`(현재 cells[6] 고정)가 깨진다. 먼저 fixture를 9컬럼으로 갱신하고, 새 검증 테스트를 추가:

`tests/fixtures/harness-ok/access/keys.md` (9컬럼 — 생성일과 만료·로테이션 분리):
```markdown
# 키·인증서·자격증명 목록

**값은 절대 이 파일에 적지 않는다 — 위치 참조만** (원칙 1·2, D12).

| 이름 | kind | principal | fingerprint | 위치 참조 | usage | 소유자 | 생성일 | 만료·로테이션 |
|------|------|-----------|-------------|-----------|-------|--------|--------|---------------|
| deploy-key | ssh-key | - | SHA256:abc | ~/.ssh/deploy-key | `ssh -i ~/.ssh/deploy-key` | 담당자 | 2026-01-01 | - |
| vm-token | api-token | - | - | secrets/vm-token.age | `sops exec-env` | 담당자 | 2026-01-01 | 2030-01-01 |
| pg-app | password | app | - | secrets/pg-app.age | `sops exec-env secrets/pg-app.age 'psql'` | 담당자 | 2026-01-01 | 2027-01-01 |
```

`harness-bad/access/keys.md`도 9컬럼으로 갱신하되, **잘못된 kind**(예: `superkey`) 행 1개를 넣어 kind 검증 실패를 유발. 만료 임박 행(old-cert, --today 기준 30일 내)은 **마지막 컬럼(만료·로테이션)**에 날짜를 두고 생성일 컬럼엔 다른 날짜를 둬 "생성일 오인 없음"도 함께 검증되게 한다.

`tests/test_audit.py`에 추가:
```python
class TestCredentialSchema(unittest.TestCase):
    def test_ok_keys_pass(self):
        import datetime
        failures, _ = audit.run_audit(OK, datetime.date(2026, 7, 22))
        self.assertEqual([f for f in failures if "[키]" in f], [])

    def test_bad_kind_flagged(self):
        import datetime
        failures, _ = audit.run_audit(BAD, datetime.date(2026, 7, 22))
        self.assertTrue(any("superkey" in f for f in failures))

    def test_expiry_still_detected_new_schema(self):
        import datetime
        _, warnings = audit.run_audit(BAD, datetime.date(2026, 7, 22))
        self.assertTrue(any("old-cert" in w for w in warnings))
```

- [ ] **Step 2: RED 확인** — `check_expiry`가 새 컬럼 위치를 못 읽어 `test_expiry_still_detected_new_schema` FAIL, kind 검증 없어 `test_bad_kind_flagged` FAIL.

- [ ] **Step 3: 구현**
  - `templates/keys.md`를 9컬럼 헤더로 교체(위 fixture와 동일 구조 + 안내 문구, D12 참조).
  - `audit.py` `key_names(root)`: 컬럼 수 하드코딩(`len(cells) >= 7`)을 완화 — 표 데이터 행(구분선·헤더 제외)의 **컬럼0**을 이름으로 수집. 헤더 판별은 `cells[0] == "이름"`, 구분선은 `set(cells[0]) <= {"-", ":"}`.
  - 신규 `check_credentials(root, failures)`: keys.md 각 데이터 행의 `kind`(컬럼1)가 `{ssh-key,tls-cert,api-token,cloud,account,password}`에 없으면 `failures.append(f"[키] {이름}: 알 수 없는 kind '{kind}'")`. 위치 참조(컬럼4)가 빈칸이면 `failures.append(f"[키] {이름}: 위치 참조 누락")`. `run_audit`에서 호출.
  - `check_expiry`: 만료 날짜를 **마지막 컬럼(만료·로테이션, `cells[-1]`)**에서만 `DATE_RE`로 추출(생성일 컬럼은 보지 않아 오인 방지). `-`·빈칸이면 스킵. 무효 날짜 try/except는 유지(기존 하드닝).

- [ ] **Step 4: GREEN** — 전체 통과(64 + 3 = 67). 기존 `test_ok_harness_passes`·`test_expiry_warning`도 새 fixture로 통과.

- [ ] **Step 5: 커밋**
```bash
git add templates/keys.md scripts/audit.py tests/fixtures/ tests/test_audit.py
git commit -m "feat: keys.md 자격증명 스키마 개정(kind/principal/usage) + audit 검증(D12)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task A1-2: register·lookup 자격증명 반영

**Files:**
- Modify: `skills/register/SKILL.md`
- Modify: `skills/lookup/SKILL.md`

**Interfaces:**
- Consumes: A1-1의 9컬럼 keys.md 스키마.
- Produces: register가 계정·비밀번호·외부참조 행을 쓰고, lookup이 usage 기반 참조 실행 레시피로 답한다.

- [ ] **Step 1: register §3 key 등록 절차 개정** — `skills/register/SKILL.md`의 §3.4(key는 keys.md 표에 행 추가) 부분을 개정. 반드시 담을 내용:
  - keys.md는 9컬럼(이름/kind/principal/fingerprint/위치참조/usage/소유자/생성일/만료·로테이션, D12). kind는 `ssh-key|tls-cert|api-token|cloud|account|password`.
  - **비밀번호·계정 등록 시**: principal(계정명)을 받고, 값은 절대 keys.md에 안 적고 위치 참조만. usage 컬럼에 안전한 사용법을 적되 **argv 금지** — `sops exec-env <파일> '<명령>'`·`op run -- <명령>`·stdin. SSH 비밀번호 로그인은 키 인증을 권하고 `sshpass`를 쓰지 않는다(불가피하면 그 제약을 usage에 명시).
  - **외부 매니저 참조(D14)**: 위치 참조 스킴 `op://`·`vault://`·`aws-secretsmanager://`·`secrets/…`를 그대로 위치 참조에 적는다. 참조는 불투명 — register는 값을 조회하지 않는다.

- [ ] **Step 2: lookup §2 자격증명 응답 개정** — `skills/lookup/SKILL.md`에 추가. 반드시 담을 내용:
  - 키·토큰·비밀번호를 물으면 **값이 아니라** keys.md의 위치 참조 + **usage 컬럼의 참조 실행 레시피**로 답한다(원칙 1). 비밀번호는 argv에 넣는 형태를 절대 제시하지 않고 `sops exec-env`·`op run`·stdin 형태만.
  - 외부 매니저 참조(`op://`·`vault://`·`aws-secretsmanager://`)면 그 백엔드의 참조 실행 명령(`op run`, `vault kv get`, `aws secretsmanager get-secret-value` + 명시적 profile/region/namespace)을 안내하되 값을 조회·출력하지 않는다. 상세 백엔드 관례는 `secrets` 스킬 references를 가리킨다.

- [ ] **Step 3: GREEN** — `bash tests/run_tests.sh` 전체 통과(test_skills 유지).
- [ ] **Step 4: 자체 점검** — `grep -nE "sshpass|파이프.*비밀번호|echo .*password" skills/register/SKILL.md skills/lookup/SKILL.md` → 매치가 "금지" 부정 문맥인지 확인.
- [ ] **Step 5: 커밋**
```bash
git add skills/register/SKILL.md skills/lookup/SKILL.md
git commit -m "feat: register·lookup 자격증명(계정·비밀번호·외부참조) 반영(D12·D14)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## 그룹 A2 — 팀 시크릿 스킬 (D11)

### Task A2-1: harness.yaml 수신자 매니페스트 + audit 정책 + init 연동

**Files:**
- Modify: `templates/harness.yaml`
- Modify: `scripts/audit.py` (`check_secret_policy` 또는 `check_harness_yaml`)
- Modify: `skills/init/SKILL.md`
- Modify: `tests/test_audit.py`, `tests/fixtures/`(필요 시)

**Interfaces:**
- Consumes: B1의 `check_secret_policy`, `harness_lib.parse_yaml_subset`(중첩 맵 지원).
- Produces: `secrets_recipients` 검증(encrypted면 recovery 필수). A2-2의 `secrets` 스킬이 이 매니페스트를 읽어 `.sops.yaml`을 만든다.

- [ ] **Step 1: 실패 테스트** — `tests/test_audit.py`:
```python
class TestRecipients(unittest.TestCase):
    def _root(self, harness):
        import tempfile
        d = tempfile.mkdtemp(); root = Path(d)
        (root / "harness.yaml").write_text(harness, encoding="utf-8")
        return root

    def test_encrypted_requires_recovery_recipient(self):
        import datetime
        h = "sharing: git\nsecrets_mode: encrypted\nsecrets_format: sops-age\nsecrets_recipients:\n  alice: age1aaa\nenvironments: [prod]\npolicies:\n  mutating:\n    prod: confirm\nhooks:\n  change_reminder: true\n"
        failures, _ = audit.run_audit(self._root(h), datetime.date(2026,7,22))
        self.assertTrue(any("recovery" in f for f in failures))

    def test_encrypted_with_recovery_passes_recipient_check(self):
        import datetime
        h = "sharing: git\nsecrets_mode: encrypted\nsecrets_format: sops-age\nsecrets_recipients:\n  alice: age1aaa\n  recovery: age1rec\nenvironments: [prod]\npolicies:\n  mutating:\n    prod: confirm\nhooks:\n  change_reminder: true\n"
        failures, _ = audit.run_audit(self._root(h), datetime.date(2026,7,22))
        self.assertEqual([f for f in failures if "recovery" in f or "recipient" in f], [])
```

- [ ] **Step 2: RED 확인** — recovery 검증 없어 첫 테스트 FAIL.

- [ ] **Step 3: 구현**
  - `check_secret_policy`(또는 신규 `check_recipients`)에: `mode == "encrypted"`면 `cfg.get("secrets_recipients")`가 dict이고 `recovery` 키가 있어야 함. 없으면 `failures.append("[정책] secrets_mode: encrypted인데 secrets_recipients에 recovery 수신자가 없다(D11)")`. `secrets_recipients` 자체가 없으면 같은 실패.
  - `templates/harness.yaml`: `secrets_format`·`secrets_recipients` 주석 블록 추가(스펙 §4.4와 동일, encrypted일 때만 채움 안내).
  - `skills/init/SKILL.md`: §4 인터뷰에서 `secrets_mode: encrypted` 선택 시 팀원 age 공개키 + **recovery 수신자**를 물어 `secrets_recipients`를 채우고, `secrets` 스킬로 `.sops.yaml` 생성·초기 암호화를 안내한다(값은 안 만들고 골격만). age 공개키는 비밀이 아님을 명시.

- [ ] **Step 4: GREEN** — 전체 통과(67 + 2 = 69).
- [ ] **Step 5: 커밋**
```bash
git add templates/harness.yaml scripts/audit.py skills/init/SKILL.md tests/test_audit.py
git commit -m "feat: harness.yaml secrets_recipients + audit recovery 검증 + init 연동(D11)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task A2-2: 신규 `secrets` 스킬 + 외부 백엔드 references

**Files:**
- Create: `skills/secrets/SKILL.md`
- Create: `skills/secrets/references/backends.md`
- Modify: `tests/test_skills.py` (SKILLS에 `secrets` 추가)
- Modify: `.claude-plugin/plugin.json`(스킬 수 문구가 있으면) / README는 그룹 C에서

**Interfaces:**
- Consumes: A2-1의 `secrets_recipients`, A1의 keys.md usage 스킴.
- Produces: 팀 시크릿 라이프사이클 스킬(9종 → 10종). lookup이 외부 백엔드 상세를 이 references로 위임.

- [ ] **Step 1: test_skills SKILLS 확장** — `SKILLS = [..., "audit", "secrets"]`. `bash tests/run_tests.sh` → RED(`secrets: SKILL.md 없음`).

- [ ] **Step 2: `skills/secrets/SKILL.md` 작성** — frontmatter:
```yaml
---
name: secrets
description: 팀 하네스의 암호화 시크릿(SOPS+age) 라이프사이클을 관리한다 — 팀원 온보딩(수신자 추가·재키잉), 오프보딩(수신자 제거·재키잉·자격증명 로테이션), 복구 수신자, 시크릿 편집·재암호화. "팀원 추가해줘", "나간 사람 시크릿 회수해줘", "시크릿 로테이션" 같은 요청에 사용. 값 조회·위치는 lookup, 정합성 검사는 audit.
---
```
본문 필수 요소:
- 적용 원칙 1·2(값 미출력·복호 결과 미노출, 공유 모드 종속), 8(정책은 harness.yaml). 공통 규약(harness.yaml 상향 탐색).
- **온보딩**: `harness.yaml`의 `secrets_recipients`에 새 팀원 age 공개키 추가 → `.sops.yaml` 재생성 → `sops updatekeys`로 전 시크릿 재키잉. 공개키는 비밀 아님.
- **오프보딩**(3단계 필수): ① `secrets_recipients`에서 제거 + `.sops.yaml` 갱신 + `sops updatekeys` ② **하위 자격증명 로테이션**(구버전 암호문은 이전 키로 복호 가능 — 재키잉만으론 불충분, 로테이션이 진짜 회수) ③ 로테이션을 `changes/`에 기록. 히스토리 재작성은 일상 회수 수단이 아니라 인시던트 대응 전용임을 명시.
- **복구 수신자**: 항상 조직 복구 수신자를 포함(개인 이탈에도 접근 보존). 공유 개인키 금지.
- **편집·재암호화**: `sops <파일>`로 편집(복호 결과를 컨텍스트로 가져오지 않음), 평문을 stdout·로그·기록에 남기지 않는다.
- **공유 드라이브 주의**: 암호문을 단일 작성자/읽기 위주로 취급(동시 편집 시 conflict-copy — audit B2가 탐지).
- **백엔드 위임**: 외부 매니저(Vault 등)는 `references/backends.md` 참조.

- [ ] **Step 3: `skills/secrets/references/backends.md` 작성** — 외부 시크릿 백엔드별 참조 실행 관례(D14). 각 스킴: 위치 참조 형식 + 사용 명령(값 미출력):
  - `secrets/…` (로컬 age/SOPS): `sops exec-env secrets/x.age '<명령>'`.
  - `op://` (1Password): `op run -- <명령>` / `op read op://vault/item/field`(값을 env로만).
  - `vault://` (HashiCorp Vault): `vault kv get -mount=<mount> <path>` — `VAULT_ADDR`/`VAULT_NAMESPACE` 명시, 값을 env/파일로만.
  - `aws-secretsmanager://`: `aws secretsmanager get-secret-value --secret-id <id> --profile <p> --region <r> --query SecretString`.
  - 공통: argv에 값 금지, 참조 실행만. 참조는 불투명 — audit/lookup은 resolve 안 함. 전역 `secrets_backend` 없음(참조별 백엔드).

- [ ] **Step 4: GREEN** — 전체 통과(69, test_skills가 secrets 검증). test_skills의 references 검사가 ops 전용이면 secrets references는 별도 검사 불필요하나, 파일 존재는 확인.

- [ ] **Step 5: 커밋**
```bash
git add skills/secrets/ tests/test_skills.py
git commit -m "feat: 팀 시크릿 라이프사이클 secrets 스킬 + 외부 백엔드 references(D11·D14)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## 그룹 C — README 문서화

### Task C1: README 유즈케이스·빠른 시작·트러블슈팅

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: 앞 그룹 전체.
- Produces: 없음(말단).

- [ ] **Step 1: §5 유즈케이스에 신규 시나리오 4개 추가**
  - **비밀번호·서버 계정 관리** — register로 keys.md에 `password`/`account` 행(값은 secrets/ 또는 외부, usage에 `sops exec-env`), lookup이 참조 실행 레시피로 답. argv 금지.
  - **외부 시크릿 매니저(Vault·1Password) 사용** — 위치 참조를 `vault://`·`op://`로 두고 `secrets_mode: none`, 사용은 `op run`·`vault kv get`. 하네스는 참조만.
  - **새 팀원 온보딩** — `secrets` 스킬이 age 공개키를 `secrets_recipients`에 추가하고 `sops updatekeys` 재키잉.
  - **팀원 오프보딩** — `secrets` 스킬이 수신자 제거+재키잉+**자격증명 로테이션**+기록. 복구 수신자로 접근 보존.

- [ ] **Step 2: 최상단에 "빠른 시작"(3줄) 추가** — §1 앞 또는 개요 직후:
```markdown
## 빠른 시작

​```bash
mkdir ~/infra-workspace && cd ~/infra-workspace
claude --plugin-dir /path/to/infra
# 대화창: "인프라 하네스 만들어줘" → 이후 자연어로 등록·조회·조작
​```
```

- [ ] **Step 3: 트러블슈팅 섹션 추가** — 자주 겪는 문제:
  - "하네스를 못 찾음" → 하네스 디렉터리(harness.yaml 있는 곳)에서 세션을 열거나 init.
  - "공유 + 평문 audit 실패" → `secrets_mode: encrypted`로 전환(`secrets` 스킬).
  - "sops: no key could decrypt" → 내 age 개인키가 `secrets_recipients`에 없음 → 팀원에게 온보딩 요청.
  - "secrets/ 를 Read 못 함" → 정상(deny 가드레일). 값은 참조 실행으로.

- [ ] **Step 4: 스킬 표·구조·엔티티 모델 갱신** — §7 스킬 표에 `secrets` 행 추가(9종→10종), §2 keys.md 컬럼 설명을 D12 스키마로, 안전성 FAQ에 "비밀번호는 어떻게?"·"팀원이 나가면?" 문답 추가, 하네스 구조 트리에 `secrets_recipients`(harness.yaml 주석) 반영. 목차·"스킬 9종"→"10종" 문구 일괄 갱신.

- [ ] **Step 5: 검증·커밋** — 내부 링크·목차 앵커 확인, `bash tests/run_tests.sh` 통과.
```bash
git add README.md
git commit -m "docs: README 팀 시크릿·자격증명·Vault 유즈케이스 + 빠른 시작·트러블슈팅

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## 스펙 커버리지 매핑 (self-review)

| 스펙 | 태스크 |
|---|---|
| D13 audit 하드닝(심링크·재귀·none·헤더) | B1 |
| D13 구조(중복·conflict-copy)·--staged | B2 |
| D12 keys.md 스키마·audit 검증 | A1-1 |
| D12·D14 register·lookup 자격증명·외부참조 | A1-2 |
| D11 수신자 매니페스트·audit·init | A2-1 |
| D11 secrets 스킬 / D14 백엔드 references | A2-2 |
| 유즈케이스·문서화(전 D) | C1 |
