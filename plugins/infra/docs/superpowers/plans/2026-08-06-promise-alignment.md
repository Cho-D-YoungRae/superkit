# 약속과 실제의 일치 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 문서가 약속한 경로를 따라갔을 때 막다른 길도 조용한 거짓말도 없게 만들어, 불특정 외부에 공개 배포할 수 있는 신뢰 수준에 도달한다.

**Architecture:** 스펙 `docs/superpowers/specs/2026-08-06-promise-alignment-design.md`의 코드 5건(C1~C5)·문서 4건(D1~D4)·병합(R1)을 9개 태스크로 나눈다. 코드 변경이 스펙이 서술하는 값을 바꾸므로 **코드 → 스펙 동기화 → 문서 정합성 테스트** 순서를 지킨다. 문서 드리프트는 손으로 고치는 대신 테스트로 고정한다(신규 규약 D16).

**Tech Stack:** python3 표준 라이브러리(unittest), bash, Claude Code 플러그인(SKILL.md / hooks.json / plugin.json).

## Global Constraints

스펙과 저장소 `CLAUDE.md`에서 그대로 옮긴 전 태스크 공통 제약. 모든 태스크의 요구사항에 암묵 포함된다.

- 작업 저장소는 `/Users/choyoungrae/Projects/infra/.claude/worktrees/infra-plugin-impl`, 브랜치 `feat/infra-plugin`.
- 모든 스킬 본문·산출 문서·리포트 문구는 **한국어**. 코드 식별자·명령어는 원문 유지.
- `scripts/`·`hooks/scripts/`는 **python3 표준 라이브러리만** 사용. PyYAML 등 외부 패키지 금지(D2 결정).
- **시크릿 값 읽기·출력 금지**(원칙 1). `scripts/`는 deny 방어선 밖에서 동작하므로, `secrets/` 내용을 변수에 담더라도 stdout·stderr·예외 메시지·리포트 문자열 어디에도 싣지 않는다. 예외 보고는 `type(exc).__name__`만 쓴다.
- 모든 조작·수집 명령 예시는 `--context`/`--profile`/`--region`을 **명시**(원칙 6).
- PostToolUse hook 스크립트는 **어떤 경우에도 exit 0**(비차단, D6).
- 테스트 실행 명령은 항상 `bash tests/run_tests.sh`.
- 커밋은 태스크마다. Conventional Commits + 아래 트레일러:
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`
- 각 태스크 완료 시 `bash tests/run_tests.sh` 전체 통과를 확인한다.

---

### Task 1: C3 — 파서 오류 메시지 정정

**Files:**
- Modify: `scripts/harness_lib.py:73-79` (`parse_frontmatter`의 두 예외 분기)
- Test: `tests/test_harness_lib.py` (클래스 추가)

**Interfaces:**
- Consumes: 없음
- Produces: 없음 (메시지 문구만 변경. `FrontmatterError` 타입과 발생 조건은 불변)

**배경:** 현재 선행 공백을 만나면 `중첩 구조 미지원`을 던진다. 그러나 코드 흐름상 진짜 중첩 맵은 앞줄(`key:` 빈 값)에서 이미 다른 예외로 걸리므로, 이 분기에 도달하는 것은 사실상 들여쓰기 실수뿐인데 원인을 엉뚱하게 지목한다.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_harness_lib.py` 끝의 `if __name__ == "__main__":` 앞에 추가:

```python
class TestFrontmatterErrorMessages(unittest.TestCase):
    """오류 메시지가 진짜 원인을 지목해야 한다 (검토 P2-7)."""

    def test_leading_whitespace_names_indentation_not_nesting(self):
        text = "---\n  id: prod-db-01\n  type: server\n---\n본문\n"
        with self.assertRaises(harness_lib.FrontmatterError) as ctx:
            harness_lib.parse_frontmatter(text)
        msg = str(ctx.exception)
        self.assertIn("선행 공백", msg)
        self.assertNotIn("중첩 구조 미지원", msg)

    def test_genuine_nesting_still_names_nesting(self):
        text = "---\nid: x\npolicies:\n---\n본문\n"
        with self.assertRaises(harness_lib.FrontmatterError) as ctx:
            harness_lib.parse_frontmatter(text)
        self.assertIn("중첩 맵", str(ctx.exception))
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `python3 -m unittest tests.test_harness_lib.TestFrontmatterErrorMessages -v`
Expected: FAIL — `'선행 공백' not found in "중첩 구조 미지원: '  id: prod-db-01'"`

- [ ] **Step 3: 메시지 정정**

`scripts/harness_lib.py`에서 아래 두 줄을 각각 교체한다.

교체 전:
```python
        if line != line.lstrip(" "):
            raise FrontmatterError(f"중첩 구조 미지원: {raw!r}")
```
교체 후:
```python
        if line != line.lstrip(" "):
            raise FrontmatterError(
                f"frontmatter는 들여쓰기 없이 'key: value' 형태여야 합니다 — 선행 공백 발견: {raw!r}")
```

교체 전:
```python
        if val.strip() == "":
            raise FrontmatterError(f"빈 값/중첩 미지원: {raw!r}")
```
교체 후:
```python
        if val.strip() == "":
            raise FrontmatterError(
                f"중첩 맵은 지원하지 않습니다(엔티티 frontmatter는 플랫 구조): {raw!r}")
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `python3 -m unittest tests.test_harness_lib.TestFrontmatterErrorMessages -v`
Expected: PASS (2 tests)

- [ ] **Step 5: 전체 테스트**

Run: `bash tests/run_tests.sh`
Expected: OK — 기존 테스트 중 이 문구를 문자열로 검사하던 것이 있으면 함께 갱신한다. 확인 명령: `grep -rn "중첩 구조 미지원\|빈 값/중첩" tests/`

- [ ] **Step 6: 커밋**

```bash
git add scripts/harness_lib.py tests/test_harness_lib.py
git commit -m "fix(parser): 들여쓰기 실수를 중첩 구조 오류로 오진하던 메시지 정정 (C3)

선행 공백 분기는 사실상 들여쓰기 실수만 도달하는데 '중첩 구조 미지원'이라
말해 원인을 엉뚱하게 지목했다. 진짜 중첩은 빈 값 분기가 잡는다.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: C4 — `secrets_format` 값 검증

**Files:**
- Modify: `scripts/audit.py` (상수 추가 + `check_harness_yaml` 확장)
- Test: `tests/test_audit.py` (클래스 추가)

**Interfaces:**
- Consumes: 없음
- Produces: 없음 (`check_harness_yaml(cfg, failures)` 시그니처 불변 — 경고를 내야 하므로 `warnings` 인자를 추가한다. 아래 Step 3 참조)

**배경:** 스펙 §4.4가 키를 정의하고 템플릿이 의도값 `sops-age`를 안내하지만, 어떤 코드도 읽지 않아 `secrets_format: pgp` 같은 오설정이 통과한다.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_audit.py`의 `if __name__ == "__main__":` 앞에 추가:

```python
class TestSecretsFormat(unittest.TestCase):
    """스펙이 정의한 secrets_format이 실제로 검증되어야 한다 (검토 P2-3)."""

    BASE = ("sharing: git\nsecrets_mode: {mode}\n{fmt}"
            "secrets_recipients:\n  alice: age1aaa\n  recovery: age1rec\n"
            "environments: [prod]\npolicies:\n  mutating:\n    prod: confirm\n"
            "hooks:\n  change_reminder: true\n")

    def _run(self, mode, fmt_line):
        import tempfile
        root = Path(tempfile.mkdtemp())
        (root / "harness.yaml").write_text(
            self.BASE.format(mode=mode, fmt=fmt_line), encoding="utf-8")
        return audit.run_audit(root, TODAY)

    def test_unknown_format_fails(self):
        failures, _ = self._run("encrypted", "secrets_format: pgp\n")
        self.assertTrue(any("secrets_format" in f for f in failures), failures)

    def test_valid_format_passes(self):
        failures, _ = self._run("encrypted", "secrets_format: sops-age\n")
        self.assertEqual([f for f in failures if "secrets_format" in f], [])

    def test_missing_format_on_encrypted_warns(self):
        failures, warnings = self._run("encrypted", "")
        self.assertEqual([f for f in failures if "secrets_format" in f], [])
        self.assertTrue(any("secrets_format" in w for w in warnings), warnings)

    def test_format_on_non_encrypted_warns(self):
        failures, warnings = self._run("none", "secrets_format: sops-age\n")
        self.assertEqual([f for f in failures if "secrets_format" in f], [])
        self.assertTrue(any("secrets_format" in w for w in warnings), warnings)
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `python3 -m unittest tests.test_audit.TestSecretsFormat -v`
Expected: FAIL — `test_unknown_format_fails`에서 `secrets_format` 관련 실패가 없어 assert 실패

- [ ] **Step 3: 검증 구현**

`scripts/audit.py`의 상수 블록에 추가(`VALID_SECRETS_MODE` 줄 다음):

```python
VALID_SECRETS_FORMAT = {"sops-age"}
```

`check_harness_yaml`을 아래로 교체한다. **경고를 내야 하므로 `warnings` 인자를 추가**하고 호출부도 함께 고친다.

```python
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
```

`run_audit`의 checks 튜플에서 해당 줄을 교체:

교체 전:
```python
        ("harness.yaml", lambda: check_harness_yaml(cfg, failures)),
```
교체 후:
```python
        ("harness.yaml", lambda: check_harness_yaml(cfg, failures, warnings)),
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `python3 -m unittest tests.test_audit.TestSecretsFormat -v`
Expected: PASS (4 tests)

- [ ] **Step 5: 전체 테스트**

Run: `bash tests/run_tests.sh`
Expected: OK. `check_harness_yaml`을 직접 호출하는 기존 테스트가 있으면 인자 추가에 맞춰 고친다. 확인: `grep -rn "check_harness_yaml" tests/`

- [ ] **Step 6: 커밋**

```bash
git add scripts/audit.py tests/test_audit.py
git commit -m "feat(audit): secrets_format 값을 검증 (C4)

스펙 §4.4가 정의하고 템플릿이 sops-age를 안내하지만 어떤 코드도 읽지 않아
secrets_format: pgp 같은 오설정이 통과했다. 어휘 밖이면 실패, encrypted인데
없으면 경고, 비-encrypted인데 있으면 무시되는 키라고 경고한다.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: C1·C2 — `sync`가 확인하지 않은 것을 확인했다고 말하지 않게

이 묶음에서 가장 큰 코드 변경이다. 온프렘 fixture 추가를 동반한다.

**Files:**
- Modify: `scripts/harness_lib.py` (공용 `as_list` 추가)
- Modify: `scripts/audit.py` (`_as_list` 제거하고 `harness_lib.as_list` 사용 — DRY)
- Modify: `scripts/sync_snapshot.py` (`provider_skip_reason` 신설, `build_collect_commands`·`collect`·`diff_state` 수정)
- Create: `tests/fixtures/harness-onprem/` (온프렘 전용 fixture 5파일)
- Test: `tests/test_sync.py` (클래스 4개 추가)

**Interfaces:**
- Consumes: 없음
- Produces:
  - `harness_lib.as_list(value) -> list` — frontmatter 값을 리스트로 정규화. 스칼라는 1원소 리스트, `None`/빈 문자열은 빈 리스트.
  - `sync_snapshot.provider_skip_reason(prov: dict) -> str | None` — 자동 수집 불가 사유. 수집 가능하면 `None`.

**배경:** `diff_state`가 `if prov.get("kind") not in ("aws","gcp"): continue`로 온프렘을 통째로 삼켜, 온프렘 하네스는 4구획 전부 0건으로 나온다. 대조하지 않았는데 "문서와 실제가 일치"처럼 읽힌다. 또 aws 수집 명령에 `--region`이 없어 profile 기본 리전만 본다.

- [ ] **Step 1: 온프렘 fixture 생성**

```bash
mkdir -p tests/fixtures/harness-onprem/{providers,inventory,access,.claude}
```

`tests/fixtures/harness-onprem/harness.yaml`:
```yaml
sharing: local
secrets_mode: none
environments: [prod]
policies:
  mutating:
    prod: confirm
hooks:
  change_reminder: true
```

`tests/fixtures/harness-onprem/.claude/settings.json`:
```json
{
  "permissions": {
    "deny": [
      "Read(/secrets/**)",
      "Read(./secrets/**)"
    ]
  }
}
```

`tests/fixtures/harness-onprem/providers/onprem-idc.md`:
```markdown
---
id: onprem-idc
type: provider
kind: onprem
---

# onprem-idc

사내 IDC. 자동 수집기가 없어 sync는 "확인 불가"로 보고한다.
```

`tests/fixtures/harness-onprem/inventory/prod-web-01.md`:
```markdown
---
id: prod-web-01
type: server
env: prod
provider: onprem-idc
runtime: baremetal
purpose: 웹 서버
access: "ssh, 키: keys.md#deploy-key"
managed_by: manual
depends_on: []
---

# prod-web-01

## 사양
- arch: x86_64
```

`tests/fixtures/harness-onprem/access/keys.md`:
```markdown
# 키·자격증명 목록

| 이름 | kind | principal | fingerprint | 위치 참조 | usage | 소유자 | 생성일 | 만료·로테이션 |
|---|---|---|---|---|---|---|---|---|
| deploy-key | ssh-key | root | SHA256:FIXTUREaaaa | ~/.ssh/deploy-key | ssh -i ~/.ssh/deploy-key | ops | 2026-01-01 | - |
```

- [ ] **Step 2: 실패하는 테스트 작성**

`tests/test_sync.py`의 상수 블록에 추가(`MOCK = ...` 다음):

```python
ONPREM = PLUGIN_ROOT / "tests" / "fixtures" / "harness-onprem"
```

`if __name__ == "__main__":` 앞에 추가:

```python
class TestProviderSkipReason(unittest.TestCase):
    """자동 수집 불가 사유가 명시되어야 한다 (검토 P1-4)."""

    def test_onprem_has_no_collector(self):
        reason = sync_snapshot.provider_skip_reason({"kind": "onprem"})
        self.assertIsNotNone(reason)
        self.assertIn("자동 수집기가 없습니다", reason)

    def test_aws_without_regions(self):
        reason = sync_snapshot.provider_skip_reason({"kind": "aws", "cli_profile": "main"})
        self.assertIsNotNone(reason)
        self.assertIn("regions", reason)

    def test_aws_without_profile(self):
        reason = sync_snapshot.provider_skip_reason(
            {"kind": "aws", "regions": ["ap-northeast-2"]})
        self.assertIsNotNone(reason)
        self.assertIn("cli_profile", reason)

    def test_complete_aws_is_collectable(self):
        self.assertIsNone(sync_snapshot.provider_skip_reason(
            {"kind": "aws", "cli_profile": "main", "regions": ["ap-northeast-2"]}))

    def test_complete_gcp_is_collectable(self):
        self.assertIsNone(sync_snapshot.provider_skip_reason(
            {"kind": "gcp", "cli_profile": "gcp-prod"}))


class TestOnpremNotSilent(unittest.TestCase):
    """온프렘 하네스가 '전부 0건'으로 보고되면 안 된다 (검토 P1-4)."""

    def setUp(self):
        self.expected = sync_snapshot.build_expected(ONPREM)
        self.report = sync_snapshot.diff_state(
            self.expected, {"clusters": {}, "providers": {}})

    def test_onprem_reported_as_unverifiable(self):
        joined = "\n".join(self.report["unverifiable"])
        self.assertIn("onprem-idc", joined)
        self.assertIn("자동 수집기가 없습니다", joined)

    def test_report_is_not_all_zero(self):
        total = sum(len(v) for v in self.report.values())
        self.assertGreater(total, 0,
                           "온프렘 하네스가 4구획 전부 0건이면 조용한 거짓 안심이다")

    def test_onprem_server_is_not_reported_as_ghost(self):
        joined = "\n".join(self.report["ghost_in_docs"])
        self.assertNotIn("prod-web-01", joined,
                         "대조하지 않은 서버를 유령으로 단정하면 안 된다")


class TestRegionExplicit(unittest.TestCase):
    """aws 수집 명령이 --region까지 명시해야 한다 (원칙 6, 검토 P2-2)."""

    def test_aws_command_includes_region(self):
        cmds = sync_snapshot.build_collect_commands(OK)
        aws = [" ".join(c["cmd"]) for c in cmds if c["cmd"][0] == "aws"]
        self.assertTrue(aws, "aws 수집 명령이 생성되지 않았다")
        for c in aws:
            self.assertIn("--profile main", c)
            self.assertIn("--region ap-northeast-2", c)

    def test_multi_region_emits_one_command_per_region(self):
        import shutil
        import tempfile
        root = Path(tempfile.mkdtemp()) / "h"
        shutil.copytree(OK, root)
        (root / "providers" / "aws-main.md").write_text(
            "---\nid: aws-main\ntype: provider\nkind: aws\ncli_profile: main\n"
            "regions: [ap-northeast-2, us-east-1]\n"
            'console: "https://console.aws.amazon.com"\n---\n\n# aws-main\n',
            encoding="utf-8")
        cmds = sync_snapshot.build_collect_commands(root)
        aws = [" ".join(c["cmd"]) for c in cmds if c["cmd"][0] == "aws"]
        self.assertEqual(len(aws), 2, aws)
        self.assertTrue(any("--region ap-northeast-2" in c for c in aws))
        self.assertTrue(any("--region us-east-1" in c for c in aws))


class TestPartialCollectIsUnverifiable(unittest.TestCase):
    """일부 리전만 본 것을 전부 본 것처럼 보고하면 안 된다 (검토 P1-4)."""

    def test_one_region_failure_marks_provider_unverifiable(self):
        expected = sync_snapshot.build_expected(OK)
        actual = {"clusters": {},
                  "providers": {"aws-main": {"reachable": False, "instances": ["prod-db-01"]}}}
        report = sync_snapshot.diff_state(expected, actual)
        self.assertTrue(any("aws-main" in u for u in report["unverifiable"]),
                        report["unverifiable"])
```

- [ ] **Step 3: 테스트가 실패하는지 확인**

Run: `python3 -m unittest tests.test_sync -v`
Expected: FAIL — `provider_skip_reason` 미정의(`AttributeError`), `--region` 미포함

- [ ] **Step 4: `harness_lib`에 공용 `as_list` 추가**

`scripts/harness_lib.py`의 `_scalar` 함수 정의 **다음**에 추가:

```python
def as_list(value):
    """frontmatter 값을 리스트로 정규화한다.

    파서는 `k: [a, b]`를 리스트로, `k: a`를 문자열로 돌려준다. 문자열을 그대로
    순회하면 글자 단위로 쪼개져 엉뚱한 결과가 나오므로 단일 값은 1원소 리스트로
    감싼다.
    """
    if value is None or value == "":
        return []
    return value if isinstance(value, list) else [value]
```

- [ ] **Step 5: `audit.py`의 중복 `_as_list` 제거 (DRY)**

`scripts/audit.py`에서 `_as_list` 함수 정의 전체를 삭제하고, 유일한 사용처를 교체한다.

교체 전:
```python
        for dep in _as_list(e.get("depends_on")):
```
교체 후:
```python
        for dep in harness_lib.as_list(e.get("depends_on")):
```

- [ ] **Step 6: `sync_snapshot.py`에 `provider_skip_reason` 추가**

`build_collect_commands` 함수 정의 **앞**에 추가:

```python
def provider_skip_reason(prov):
    """provider를 자동 수집할 수 없는 이유. 수집 가능하면 None.

    이 함수가 생기기 전에는 diff_state가 aws/gcp가 아닌 provider를 조용히
    건너뛰어, 온프렘 하네스가 4구획 전부 0건으로 나왔다 — 대조하지 않았는데
    문서와 실제가 일치한 것처럼 읽혔다. 스펙 §7.8이 요구하는 "확인 불가로
    구분 보고(오탐 방지)"를 이행한다.
    """
    kind = prov.get("kind")
    if kind not in ("aws", "gcp"):
        return f"{kind} provider는 자동 수집기가 없습니다 — 확인 불가(수동 확인 필요)"
    if not prov.get("cli_profile"):
        return "cli_profile 미기재 — 확인 불가"
    if kind == "aws" and not harness_lib.as_list(prov.get("regions")):
        return "regions 미기재로 리전을 특정할 수 없습니다 — 확인 불가"
    return None
```

- [ ] **Step 7: `build_collect_commands`의 provider 루프 교체**

교체 전:
```python
    for pid, p in exp["providers"].items():
        if p.get("kind") == "aws" and p.get("cli_profile"):
            cmds.append({"target": pid, "kind": "instances", "cmd": [
                "aws", "ec2", "describe-instances", "--profile", str(p["cli_profile"]),
                "--query", "Reservations[].Instances[].[Tags[?Key=='Name'].Value | [0]]",
                "--output", "text"]})
        elif p.get("kind") == "gcp" and p.get("cli_profile"):
            cmds.append({"target": pid, "kind": "instances", "cmd": [
                "gcloud", "compute", "instances", "list",
                "--configuration", str(p["cli_profile"]), "--format", "value(name)"]})
    return cmds
```
교체 후:
```python
    for pid, p in exp["providers"].items():
        if provider_skip_reason(p):
            continue  # 사유는 diff_state가 "확인 불가"로 보고한다
        if p.get("kind") == "aws":
            # 리전당 명령 하나씩 — profile 기본 리전에 암묵 의존하지 않는다(원칙 6)
            for region in harness_lib.as_list(p.get("regions")):
                cmds.append({"target": pid, "kind": "instances", "cmd": [
                    "aws", "ec2", "describe-instances",
                    "--profile", str(p["cli_profile"]), "--region", str(region),
                    "--query", "Reservations[].Instances[].[Tags[?Key=='Name'].Value | [0]]",
                    "--output", "text"]})
        else:  # gcp — instances list는 전 존을 조회하므로 리전 지정이 불필요하다
            cmds.append({"target": pid, "kind": "instances", "cmd": [
                "gcloud", "compute", "instances", "list",
                "--configuration", str(p["cli_profile"]), "--format", "value(name)"]})
    return cmds
```

- [ ] **Step 8: `collect`의 instances 분기를 누적 방식으로 교체**

한 provider가 리전 수만큼 명령을 받게 되므로 덮어쓰기가 아니라 누적해야 한다.

교체 전:
```python
        elif item["kind"] == "instances":
            names = [l.strip() for l in (r.stdout.splitlines() if ok else []) if l.strip() and l.strip() != "None"]
            actual["providers"][item["target"]] = {"reachable": ok, "instances": names}
```
교체 후:
```python
        elif item["kind"] == "instances":
            entry = actual["providers"].setdefault(
                item["target"], {"reachable": True, "instances": []})
            if ok:
                entry["instances"].extend(
                    l.strip() for l in r.stdout.splitlines()
                    if l.strip() and l.strip() != "None")
            else:
                # 한 리전이라도 실패하면 부분 결과다 — 전부 본 것처럼 보고하지 않는다
                entry["reachable"] = False
```

- [ ] **Step 9: `diff_state`의 provider 루프 앞부분 교체**

교체 전:
```python
    for pid, prov in expected["providers"].items():
        if prov.get("kind") not in ("aws", "gcp"):
            continue
        prov_actual = actual.get("providers", {}).get(pid)
```
교체 후:
```python
    for pid, prov in expected["providers"].items():
        reason = provider_skip_reason(prov)
        if reason:
            report["unverifiable"].append(f"{pid}: {reason}")
            continue
        prov_actual = actual.get("providers", {}).get(pid)
```

- [ ] **Step 10: 테스트 통과 확인**

Run: `python3 -m unittest tests.test_sync -v`
Expected: PASS (신규 13 + 기존 전부)

- [ ] **Step 11: 전체 테스트**

Run: `bash tests/run_tests.sh`
Expected: OK

- [ ] **Step 12: 커밋**

```bash
git add scripts/harness_lib.py scripts/audit.py scripts/sync_snapshot.py \
        tests/test_sync.py tests/fixtures/harness-onprem
git commit -m "fix(sync): 대조하지 않은 provider를 조용히 건너뛰지 않고 확인 불가로 보고 (C1·C2)

온프렘 하네스에서 --collect를 돌리면 4구획 전부 0건이 나와 문서와 실제가
일치한 것처럼 읽혔다. 실제로는 aws/gcp가 아닌 provider를 통째로 건너뛴
것이다. provider_skip_reason으로 사유(수집기 없음/cli_profile 미기재/
regions 미기재)를 확인 불가에 담는다.

aws 수집은 provider.regions를 소비해 리전당 명령 하나씩 내보내고 결과를
누적한다. 한 리전이라도 실패하면 부분 결과이므로 확인 불가로 표기한다.
audit의 중복 _as_list는 harness_lib.as_list로 합쳤다.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: C5 — hook mutating 패턴에 서버 계열 추가

**Files:**
- Modify: `hooks/scripts/change_reminder.py` (패턴 추가 + DB 전용 판정 함수)
- Test: `tests/test_change_reminder.py` (클래스 추가)

**Interfaces:**
- Consumes: 기존 `tests/test_change_reminder.py`의 모듈 수준 헬퍼 `run_hook(cwd, command)`와 상수 `OK`
- Produces: `change_reminder.is_mutating(command: str) -> bool` — 기존 인라인 판정을 함수로 추출한 것. **내부 정리용이며 테스트는 이를 직접 호출하지 않는다** (아래 주의 참조)

**배경:** 현재 terraform·kubectl·helm·argocd 4계열뿐이라 서버 작업(ssh 경유 포함)에는 리마인드가 뜨지 않는다. PostToolUse는 절대 차단하지 않으므로 오탐 비용은 알림 한 줄이고, 미탐(기록 누락)이 더 비싸다.

**주의 — 테스트는 서브프로세스 경로로 한다.** hook은 `hooks/scripts/`에 있어 `sys.path` 밖이고, 기존 `tests/test_change_reminder.py`는 모듈을 import하지 않고 `run_hook()`으로 **서브프로세스 실행**해 stdout을 본다(CLAUDE.md의 "독립 실행형" 규약과 일치). 새 테스트도 같은 방식을 쓴다 — import를 위해 `sys.path`를 조작하면 그 규약이 흐려진다.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_change_reminder.py`의 `if __name__ == "__main__":` 앞에 추가:

```python
class TestServerSideMutating(unittest.TestCase):
    """서버 계열 mutating도 리마인드 대상이다 (검토 P2-6).

    hook을 서브프로세스로 실행해 stdout 유무로 판정한다 — 리마인드가 나가면
    hookSpecificOutput JSON이 찍히고, 아니면 아무것도 찍히지 않는다.
    """

    MUTATING = [
        "systemctl restart nginx",
        "sudo systemctl daemon-reload",
        "ssh prod-web-01 'systemctl restart nginx'",
        "apt-get install -y postgresql",
        "ssh prod-db-01 'apt install -y redis'",
        "yum remove httpd",
        "docker run -d nginx",
        "docker rm -f old-container",
        "docker compose up -d",
        "psql -h db -c 'DROP TABLE stale'",
        "mysql -e 'CREATE USER app@localhost'",
        "aws ec2 terminate-instances --instance-ids i-0abc --profile main --region ap-northeast-2",
        "aws rds modify-db-instance --db-instance-identifier prod --profile main",
    ]
    READ_ONLY = [
        "systemctl status nginx",
        "apt list --installed",
        "docker ps",
        "docker logs app",
        "psql -h db -c 'SELECT count(*) FROM users'",
        "aws ec2 describe-instances --profile main --region ap-northeast-2",
        "aws s3 list-buckets --profile main",
        "ssh prod-web-01 'df -h'",
    ]

    def _reminded(self, command):
        r = run_hook(OK, command)
        self.assertEqual(r.returncode, 0, f"hook은 항상 exit 0이어야 한다: {r.stderr}")
        return r.stdout.strip() != ""

    def test_server_side_mutating_matches(self):
        for cmd in self.MUTATING:
            with self.subTest(cmd=cmd):
                self.assertTrue(self._reminded(cmd), cmd)

    def test_read_only_does_not_match(self):
        for cmd in self.READ_ONLY:
            with self.subTest(cmd=cmd):
                self.assertFalse(self._reminded(cmd), cmd)

    def test_dry_run_still_excluded(self):
        self.assertFalse(self._reminded("kubectl apply -f x.yaml --dry-run=client"))
        self.assertFalse(self._reminded("docker compose up -d --dry-run"))

    def test_existing_four_families_still_match(self):
        for cmd in ("terraform apply", "kubectl apply -f x.yaml",
                    "helm upgrade vm vm/vm", "argocd app sync myapp"):
            with self.subTest(cmd=cmd):
                self.assertTrue(self._reminded(cmd), cmd)
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `python3 -m unittest tests.test_change_reminder.TestServerSideMutating -v`
Expected: FAIL — `test_server_side_mutating_matches`에서 `systemctl restart nginx` 등이 리마인드를 내지 않아 assert 실패

- [ ] **Step 3: 패턴 추가와 판정 함수 추출**

`hooks/scripts/change_reminder.py`의 `MUTATING` 리스트를 아래로 교체한다.

```python
MUTATING = [
    r"(?<!\S)terraform(?!\S).*(?<!\S)(apply|destroy|import|taint|untaint)(?!\S)",
    r"(?<!\S)terraform(?!\S).*(?<!\S)state(?!\S)\s+(mv|rm|push)(?!\S)",
    r"(?<!\S)kubectl(?!\S).*(?<!\S)(apply|create|delete|patch|replace|scale|edit|label|annotate|cordon|uncordon|drain|taint)(?!\S)",
    r"(?<!\S)kubectl(?!\S).*(?<!\S)rollout(?!\S)\s+(restart|undo|pause|resume)(?!\S)",
    r"(?<!\S)helm(?!\S).*(?<!\S)(install|upgrade|uninstall|rollback|delete)(?!\S)",
    r"(?<!\S)argocd(?!\S).*(?<!\S)app(?!\S)\s+(sync|delete|set|patch|rollback)(?!\S)",
    # --- 서버 계열 (C5) ---
    # 경계가 위 6개와 다르다. `(?<!\S)`는 앞 문자가 공백이어야 하는데,
    # `ssh host 'systemctl restart nginx'`에서는 앞 문자가 따옴표라 매치되지 않는다.
    # ssh 경유 작업을 덮는 것이 이 확장의 핵심이므로 단어 문자·점·하이픈만 배제해
    # 따옴표와 경로 구분자(`/usr/bin/systemctl`)를 허용한다. 하이픈을 배제한 덕분에
    # `--installed` 안의 `install`은 여전히 걸리지 않는다.
    r"(?<![\w.-])systemctl(?![\w.-]).*(?<![\w.-])(restart|stop|start|enable|disable|mask|unmask|daemon-reload)(?![\w.-])",
    r"(?<![\w.-])(apt|apt-get|yum|dnf|apk)(?![\w.-]).*(?<![\w.-])(install|remove|purge|upgrade|autoremove)(?![\w.-])",
    r"(?<![\w.-])docker(?![\w.-]).*(?<![\w.-])(run|rm|stop|start|restart|kill|exec)(?![\w.-])",
    r"(?<![\w.-])docker(?![\w.-]).*(?<![\w.-])compose(?![\w.-])\s+(up|down|restart)(?![\w.-])",
    r"(?<![\w.-])aws(?![\w.-]).*(?<![\w.-])(create|delete|update|put|modify|terminate|reboot)-[a-z-]+(?![\w.-])",
]

# DB 클라이언트는 "psql/mysql이 있고 + SQL 쓰기 키워드가 있을 때"만 매치한다.
# 하나의 정규식으로 대소문자를 섞어 처리하려면 인라인 플래그가 필요해 가독성이
# 나빠지므로 두 갈래로 나눈다. 경계는 위 서버 계열과 같은 이유로 완화한다.
DB_CLIENT_RE = re.compile(r"(?<![\w.-])(psql|mysql|mariadb)(?![\w.-])")
DB_WRITE_RE = re.compile(
    r"\b(INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|GRANT|REVOKE|TRUNCATE)\b", re.IGNORECASE)


def is_mutating(command):
    """이 명령이 변경 기록 리마인드 대상인가.

    PostToolUse는 어떤 경우에도 차단하지 않으므로(D6) 오탐 비용은 알림 한 줄이고,
    미탐(기록 누락)이 더 비싸다. 그래도 read-only 명령까지 매번 울리면 알림이
    무시되므로 제외 어휘는 지킨다.
    """
    if "--dry-run" in command:
        return False
    if DB_CLIENT_RE.search(command) and DB_WRITE_RE.search(command):
        return True
    return any(re.search(p, command) for p in MUTATING)
```

`main()`의 판정 부분을 교체한다.

교체 전:
```python
        if "--dry-run" in command:
            return
        if not any(re.search(p, command) for p in MUTATING):
            return
```
교체 후:
```python
        if not is_mutating(command):
            return
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `python3 -m unittest tests.test_change_reminder -v`
Expected: PASS (신규 4 + 기존 15)

`aws s3 list-buckets`가 read-only로 판정되는지 특히 확인한다 — `list-buckets`는 `(create|delete|...)-` 접두에 걸리지 않아야 한다.

- [ ] **Step 5: 전체 테스트**

Run: `bash tests/run_tests.sh`
Expected: OK

- [ ] **Step 6: 커밋**

```bash
git add hooks/scripts/change_reminder.py tests/test_change_reminder.py
git commit -m "feat(hook): mutating 패턴에 서버 계열 추가 (C5)

terraform·kubectl·helm·argocd 4계열뿐이라 ssh·apt·docker·DB·클라우드 CLI
작업에는 기록 리마인드가 뜨지 않았다. systemctl·패키지 관리자·docker·
psql/mysql 쓰기·aws 변경 동사 접두를 추가한다. ssh <host> '<명령>'은 전체
문자열이 매치 대상이라 자동으로 커버된다.

판정을 is_mutating()으로 추출해 테스트가 직접 호출한다. --dry-run 전역
제외는 유지하고 read-only 어휘는 매치되지 않음을 테스트로 고정한다.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: D1 — `secrets` 스킬에 신규 시크릿 생성·최초 암호화 절 추가

**Files:**
- Modify: `skills/secrets/SKILL.md` (§6 신설, 기존 §6~§8 → §7~§9 재번호, 상호참조 3곳 수정)
- Modify: `skills/init/SKILL.md:129` (인계 문구가 실재하는 절을 가리키게)
- Test: `tests/test_skills.py` (검사 추가)

**Interfaces:**
- Consumes: 없음
- Produces: 없음

**배경:** `init`이 "`secrets` 스킬로 넘어가 `.sops.yaml` 생성과 초기 암호화를 진행하라"고 인계하는데, 그 스킬은 수신자 관리와 **기존** 암호문 편집만 다룬다. 문서를 따라가면 막다른 길이고, 그 틈을 메우는 가장 쉬운 방법이 평문 파일을 잠깐 두는 것이라 원칙 위반을 유도한다.

**주의:** `skills/secrets/` 이하는 Read 도구가 권한 정책상 거부될 수 있다. 그때는 `git show HEAD:skills/secrets/SKILL.md`로 읽고, 편집은 Write 도구로 전체를 다시 쓴다.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_skills.py`의 `if __name__ == "__main__":` 앞에 추가:

```python
class TestHandoffPathsResolve(unittest.TestCase):
    """문서가 가리키는 곳에 실제로 그 절이 있어야 한다 (검토 P1-6)."""

    def _read(self, rel):
        import subprocess
        p = PLUGIN_ROOT / rel
        try:
            return p.read_text(encoding="utf-8")
        except (OSError, PermissionError):
            out = subprocess.run(["git", "-C", str(PLUGIN_ROOT), "show", f"HEAD:{rel}"],
                                 capture_output=True, text=True, check=True)
            return out.stdout

    def test_secrets_skill_has_initial_encryption_section(self):
        body = self._read("skills/secrets/SKILL.md")
        self.assertIn("신규 시크릿 생성", body,
                      "init이 인계하는 초기 암호화 절이 secrets 스킬에 없다")
        self.assertIn(".sops.yaml", body)

    def test_init_handoff_names_the_section(self):
        body = self._read("skills/init/SKILL.md")
        self.assertIn("신규 시크릿 생성", body,
                      "init의 인계 문구가 실재하는 절 이름을 가리키지 않는다")
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `python3 -m unittest tests.test_skills.TestHandoffPathsResolve -v`
Expected: FAIL — `'신규 시크릿 생성' not found`

- [ ] **Step 3: `skills/secrets/SKILL.md`에 새 절 삽입**

기존 `## 6. 편집·재암호화` **바로 앞**에 아래 절을 삽입한다.

```markdown
## 6. 신규 시크릿 생성·최초 암호화

`init`이 `secrets_mode: encrypted`로 하네스를 만들면 `harness.yaml`의 수신자 매니페스트만
준비된 상태다. 실제 암호화는 여기서 시작한다. **클로드는 시크릿 값을 만들지도 보지도
않는다**(원칙 1) — 아래 명령은 사용자가 자기 터미널에서 직접 실행한다.

### 6.1 `.sops.yaml` 생성

하네스 루트에 `.sops.yaml`을 만들고 `harness.yaml`의 `secrets_recipients` 공개키를 옮겨
적는다. **경로별로 규칙을 나눈다** — 단일 키가 침해됐을 때 노출 범위를 그 경로로 묶기
위해서다(NIST SP 800-57 Part 1 Rev.5의 "단일 키 침해가 최대한 적은 데이터만 침해하도록"
권고).

```yaml
creation_rules:
  - path_regex: secrets/prod/.*
    age: age1prodaaaa...,age1recovery...
  - path_regex: secrets/.*
    age: age1alice...,age1bob...,age1recovery...
```

`recovery` 수신자는 **모든 규칙에** 포함한다(§5). 빠지면 개인 이탈 시 복호 불능이 되고
`audit`가 실패로 잡는다.

### 6.2 최초 암호화

값 자체는 사용자가 만든다. 클로드는 값을 생성하지 않는다 — 생성하는 순간 값이 컨텍스트에
들어오기 때문이다.

```bash
# 사용자가 자기 터미널에서 실행한다
sops secrets/prod/db-app.env      # 편집기가 열리고, 저장하면 암호문으로 기록된다
```

클로드는 이 명령을 **대신 실행하거나 출력을 캡처하지 않는다**(§2 공통 규약과 동일).
암호화가 끝나면 `audit`로 형식을 확인한다: 하네스에서 "하네스 점검해줘".

### 6.3 생성 방향 end-to-end 체인

"DB 계정을 추가한다" 같은 요청은 여러 스킬에 걸친다. 각 단계의 소관은 이렇다.

| 단계 | 소관 | 비고 |
|---|---|---|
| 1. DB에 계정 생성 | 사용자 | `CREATE USER`/`GRANT`는 사용자가 실행한다. 값이 argv에 남지 않게 주의 |
| 2. `access/keys.md`에 행 추가 | `register` | `kind: account`/`password`, 값이 아니라 **위치 참조**만 |
| 3. `secrets/` 암호문 최초 생성 | 사용자 (§6.2) | 클로드는 경로와 명령만 안내한다 |
| 4. 접속 검증 | `ops` | `usage` 컬럼의 참조 실행 레시피로 확인한다 |
| 5. 변경 기록 | `change` | 롤백 방법(계정 회수 절차) 필수 |

`secrets_mode: none`으로 외부 매니저(Vault·1Password 등)를 쓰는 하네스는 이 절 대신 §9의
백엔드 참조를 따른다 — 값 생성·보관은 그 매니저의 몫이다.
```

- [ ] **Step 4: 뒤따르는 절 재번호와 상호참조 수정**

같은 파일에서 아래를 순서대로 바꾼다.

| 위치 | 변경 전 | 변경 후 |
|---|---|---|
| 헤더 | `## 6. 편집·재암호화` | `## 7. 편집·재암호화` |
| 헤더 | `## 7. 공유 드라이브 주의` | `## 8. 공유 드라이브 주의` |
| 헤더 | `## 8. 외부 백엔드는 별도 참조` | `## 9. 외부 백엔드는 별도 참조` |
| §1 본문 | `캡처하지 않는다(§6)` | `캡처하지 않는다(§7)` |
| §2 본문 | `§8의 백엔드 참조만 해당된다` | `§9의 백엔드 참조만 해당된다` |
| §4 본문 | `§6(편집·재암호화)을` | `§7(편집·재암호화)을` |

확인 명령: `git show HEAD:skills/secrets/SKILL.md | grep -nE "^## |§[0-9]"` 로 변경 전 위치를 먼저 확보한 뒤 편집한다.

- [ ] **Step 5: `init`의 인계 문구를 실재하는 절로 연결**

`skills/init/SKILL.md`에서 교체한다.

교체 전:
```
암호화가 동작하지 않는다 — `secrets` 스킬로 넘어가 `.sops.yaml` 생성과 초기 암호화를
진행하라고 안내한다(이 스킬은 골격(harness.yaml의 수신자 매니페스트)만 준비하며, 실제
`.sops.yaml`·암호화 파일 생성이나 시크릿 값 생성은 하지 않는다).
```
교체 후:
```
암호화가 동작하지 않는다 — `secrets` 스킬 **§6(신규 시크릿 생성·최초 암호화)**로 넘어가
`.sops.yaml` 생성과 최초 암호화를 진행하라고 안내한다(이 스킬은 골격(harness.yaml의
수신자 매니페스트)만 준비하며, 실제 `.sops.yaml`·암호화 파일 생성이나 시크릿 값 생성은
하지 않는다).
```

- [ ] **Step 6: 테스트 통과 확인**

Run: `python3 -m unittest tests.test_skills -v`
Expected: PASS

- [ ] **Step 7: 전체 테스트 + 원칙 1 회귀 확인**

Run: `bash tests/run_tests.sh`
Expected: OK — 특히 `test_secret_containment.py`가 통과해야 한다(새 절이 값 출력을 유도하지 않는지).

- [ ] **Step 8: 커밋**

```bash
git add skills/secrets/SKILL.md skills/init/SKILL.md tests/test_skills.py
git commit -m "feat(secrets): 신규 시크릿 생성·최초 암호화 절 추가로 끊긴 인계 복구 (D1)

init은 'secrets 스킬로 넘어가 .sops.yaml 생성과 초기 암호화를 진행하라'고
인계하는데 그 스킬에는 해당 절이 없었다. 문서를 따라가면 막다른 길이고,
그 틈을 메우는 가장 쉬운 방법이 평문 파일을 잠깐 두는 것이라 원칙 위반을
유도하는 구조였다.

.sops.yaml creation_rules(경로별 분리 — NIST SP 800-57 권고), 최초 암호화,
DB 계정 추가 같은 생성 방향의 end-to-end 소관표를 담는다. 클로드는 값을
만들지도 보지도 않고 사용자가 실행할 명령만 안내한다.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: D3 — 스펙 상세 절을 완료 시점 상태로 동기화

**Files:**
- Modify: `docs/superpowers/specs/2026-07-19-infra-plugin-design.md` (§1·§5·§7·§8.1·§12)

**Interfaces:**
- Consumes: Task 1~5의 결과 (fixture 수·audit 검사 항목·hook 패턴·테스트 구성이 이 태스크가 서술할 값이다)
- Produces: Task 7이 검사할 D 결정표와 수치

**배경:** 스펙은 D 결정표(§2)만 D15까지 진화했고 상세 절은 D9 시점이다. **동기화 대상은 "현재"가 아니라 "Task 1~5 완료 후" 상태다.**

- [ ] **Step 1: 실제 값 수집**

```bash
echo "스킬: $(ls -d skills/*/ | wc -l)종"
echo "fixture: $(ls -d tests/fixtures/harness-*/ | wc -l)종 — $(ls -d tests/fixtures/harness-*/ | xargs -n1 basename | tr '\n' ' ')"
echo "audit 검사 함수: $(grep -c '^def check_' scripts/audit.py)개"
echo "테스트 파일: $(ls tests/test_*.py | xargs -n1 basename | tr '\n' ' ')"
bash tests/run_tests.sh 2>&1 | tail -3
```

이 출력값을 아래 단계에서 그대로 쓴다.

- [ ] **Step 2: §1 스킬 수 정정**

`§1 목표와 배경`의 "스킬 9종"을 Step 1에서 확인한 실제 수("스킬 10종")로 바꾸고, 스킬 이름 나열에 `secrets`를 추가한다.

- [ ] **Step 3: §5 플러그인 구조 트리 갱신**

트리에 아래를 추가한다.

- `skills/secrets/SKILL.md`와 `skills/secrets/references/backends.md`
- `templates/settings.local.json` (D15)
- `tests/fixtures/harness-off/`, `tests/fixtures/harness-onprem/`
- `tests/test_secret_containment.py`, `tests/test_docs_consistency.py`(Task 7에서 생성)

- [ ] **Step 4: §7에 `secrets` 스킬 명세 절 신설**

`§7.9 audit` 다음에 `### 7.10 secrets — 팀 시크릿 라이프사이클`을 추가한다. 담을 내용:

```markdown
### 7.10 secrets — 팀 시크릿 라이프사이클

적용 원칙: 1, 2, 8. `sharing`이 공유이고 `secrets_mode: encrypted`인 하네스에서만 동작한다
(`none`이면 외부 백엔드 참조로 위임하고, `plaintext`는 공유 조합 자체가 금지다).

- **신규 생성·최초 암호화**: `.sops.yaml` creation_rules를 경로별로 나눠 작성하고(단일 키
  침해 범위 축소), 최초 암호화는 사용자가 자기 터미널에서 `sops <파일>`로 수행한다.
  클로드는 값을 생성하지도 출력하지도 않는다(원칙 1).
- **온보딩**: `secrets_recipients`에 팀원 age 공개키를 추가하고 `sops updatekeys`로 재키잉.
- **오프보딩**: 수신자 제거 → 재키잉 → **하위 자격증명 로테이션**의 3단계가 모두 필수다.
  암호문에서 지워도 이미 본 값은 회수되지 않기 때문이다.
- **복구 수신자**: 조직 복구 수신자를 모든 creation_rule에 포함한다. 없으면 audit 실패(D11).
- **편집·재암호화**: 기존 암호문 수정도 사용자 터미널에서 `sops <파일>`로 한다.
- **외부 백엔드**: `op://`·`vault://`·`aws-secretsmanager://` 참조는 resolve하지 않고
  형식과 사용 명령만 다룬다(D14). 상세는 `references/backends.md`.

인접 경계: 키 **메타데이터** 등록은 register, 위치·사용법 조회는 lookup, 값 사용은 ops의
참조 실행이다. 이 스킬은 암호문 파일과 수신자 집합의 라이프사이클만 담당한다.
```

- [ ] **Step 5: §8.1 audit 검사 항목표 갱신**

표를 Step 1에서 센 실제 검사 함수에 맞춘다. 최소한 아래 행이 있어야 한다: 스키마·참조 무결성 / 구조(중복 id·conflict-copy, D13) / 시크릿 스캔 / 시크릿 정책 / 수신자(recovery 필수, D11) / 자격증명(kind 어휘·위치 참조, D12) / **보호 설정(settings.json·settings.local.json 드리프트, D15)** / 만료 경고 / harness.yaml(**secrets_format 포함, C4**) / `--staged` 모드(D13).

- [ ] **Step 6: §12 검증 계획·완료 기준 갱신**

- fixture 목록을 실제 4종(`harness-ok`·`harness-bad`·`harness-off`·`harness-onprem`)으로
- 테스트 파일 목록과 총 테스트 수를 Step 1의 실측값으로
- 자동 검증 항목에 "시크릿 봉쇄 카나리 회귀", "문서 정합성"을 추가

- [ ] **Step 7: 스펙 자체 점검**

Run: `grep -nE "스킬 9종|fixture 2개|D1~D9" docs/superpowers/specs/2026-07-19-infra-plugin-design.md`
Expected: 출력 없음 (스테일 표기가 남아 있지 않다)

- [ ] **Step 8: 전체 테스트**

Run: `bash tests/run_tests.sh`
Expected: OK

- [ ] **Step 9: 커밋**

```bash
git add docs/superpowers/specs/2026-07-19-infra-plugin-design.md
git commit -m "docs(spec): 상세 절을 D15와 현재 구현에 동기화 (D3)

스펙은 D 결정표만 D15까지 진화했고 §1·§5·§7·§8.1·§12는 D9 시점에 멈춰
있었다. 특히 §7에 secrets 스킬 명세 절이 없어 스펙만으로는 그 스킬의
절차를 알 수 없었다.

스킬 수·fixture 목록·audit 검사 항목·테스트 구성을 실측값으로 맞추고
§7.10 secrets 명세를 신설한다.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 7: D2 — 문서 정합성을 테스트로 고정 (D16)

**Files:**
- Create: `tests/test_docs_consistency.py`
- Modify: `docs/superpowers/specs/2026-07-19-infra-plugin-design.md` (D16 행 추가)
- Modify: `CLAUDE.md` (스킬 수·D 범위·plan 목록)

**Interfaces:**
- Consumes: Task 6이 갱신한 스펙 D 결정표
- Produces: 없음

**배경:** 수치를 손으로 고쳐도 재발한다 — P0 작업 중에도 테스트 수와 D 범위가 다시 어긋나 손으로 고쳤다. **D16 추가·`CLAUDE.md` 갱신·테스트 추가 셋이 같은 커밋에서 함께 움직여야 한다.** 하나라도 빠지면 새 테스트가 곧바로 실패하는데, 이는 결함이 아니라 이 규약이 의도한 작동이다.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_docs_consistency.py` 생성:

```python
"""문서가 코드 구조를 수치로 언급하면 그 정합성을 강제한다 (D16).

손으로 고치는 것만으로는 재발한다 — 실제로 P0 작업 중에 테스트 수와 D 범위가
다시 어긋나 사람이 고쳤다. 사람 규율에 맡기지 않고 테스트로 고정한다.
"""
import re
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_MD = PLUGIN_ROOT / "CLAUDE.md"
README = PLUGIN_ROOT / "README.md"
SPEC = PLUGIN_ROOT / "docs" / "superpowers" / "specs" / "2026-07-19-infra-plugin-design.md"
PLANS_DIR = PLUGIN_ROOT / "docs" / "superpowers" / "plans"


def actual_skill_count():
    return len([p for p in (PLUGIN_ROOT / "skills").iterdir() if (p / "SKILL.md").is_file()])


class TestSkillCount(unittest.TestCase):
    """'스킬 N종' 표기가 **모두** 실제 수와 같아야 한다.

    첫 등장만 검사하면 뒤쪽에 다른 수치가 남아도 통과한다 — 드리프트를 막는 게
    목적이므로 findall로 전부 본다.
    """

    def _assert_all_match(self, path, label):
        found = [int(x) for x in re.findall(r"스킬\s*(\d+)종",
                                            path.read_text(encoding="utf-8"))]
        self.assertTrue(found, f"{label}에 '스킬 N종' 표기가 없다")
        actual = actual_skill_count()
        self.assertEqual(set(found), {actual},
                         f"{label}의 표기 {found}가 실제 {actual}종과 다르다")

    def test_claude_md_matches_reality(self):
        self._assert_all_match(CLAUDE_MD, "CLAUDE.md")

    def test_readme_matches_reality(self):
        self._assert_all_match(README, "README.md")


class TestDecisionRange(unittest.TestCase):
    def test_claude_md_d_range_matches_spec(self):
        nums = [int(x) for x in re.findall(
            r"^\| D(\d+) \|", SPEC.read_text(encoding="utf-8"), re.MULTILINE)]
        self.assertTrue(nums, "스펙에서 D 결정표 행을 찾지 못했다")
        m = re.search(r"결정\s*D1~D(\d+)", CLAUDE_MD.read_text(encoding="utf-8"))
        self.assertIsNotNone(m, "CLAUDE.md에 '결정 D1~DN' 표기가 없다")
        self.assertEqual(int(m.group(1)), max(nums))


class TestPlanList(unittest.TestCase):
    def test_claude_md_lists_every_plan(self):
        listed = set(re.findall(r"docs/superpowers/plans/([\w.-]+\.md)",
                                CLAUDE_MD.read_text(encoding="utf-8")))
        actual = {p.name for p in PLANS_DIR.glob("*.md")}
        self.assertEqual(listed, actual)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `python3 -m unittest tests.test_docs_consistency -v`
Expected: FAIL 3건 — 스킬 수(9 vs 10), D 범위(15 vs 16 예정), plan 목록(1개 vs 4개)

- [ ] **Step 3: 스펙에 D16 추가**

`docs/superpowers/specs/2026-07-19-infra-plugin-design.md`의 `| D15 |` 행 **다음**에 삽입:

```
| D16 | 문서 수치의 정합성은 테스트로 강제 | 문서(`CLAUDE.md`·`README.md`)가 스킬 수·결정 범위·계획 문서 목록처럼 코드 구조를 수치나 목록으로 언급하면, 그 정합성을 `tests/test_docs_consistency.py`가 검사한다. 손으로 고치는 규율만으로는 재발하기 때문이다(P0 작업 중 실제로 재발). 구조를 바꾸는 변경은 문서와 테스트를 같은 커밋에서 함께 갱신한다. |
```

- [ ] **Step 4: `CLAUDE.md` 갱신**

세 곳을 고친다.

| 변경 전 | 변경 후 |
|---|---|
| `스킬 9종.` | `스킬 10종.` |
| `결정 D1~D15.` | `결정 D1~D16.` |
| plan 1개만 열거 | 아래 4개 전부 열거 |

plan 목록 교체 후:
```markdown
- `docs/superpowers/plans/2026-07-19-infra-plugin.md` — 태스크별 구현 계획.
- `docs/superpowers/plans/2026-07-21-server-body-info.md` — D10 서버 본문 정보.
- `docs/superpowers/plans/2026-07-22-team-secrets.md` — D11~D14 팀 시크릿.
- `docs/superpowers/plans/2026-08-06-promise-alignment.md` — 약속과 실제의 일치(이 계획).
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `python3 -m unittest tests.test_docs_consistency -v`
Expected: PASS (4 tests)

- [ ] **Step 6: 전체 테스트**

Run: `bash tests/run_tests.sh`
Expected: OK

- [ ] **Step 7: 커밋**

```bash
git add tests/test_docs_consistency.py CLAUDE.md \
        docs/superpowers/specs/2026-07-19-infra-plugin-design.md
git commit -m "test: 문서 수치 정합성을 테스트로 강제 (D2, 신규 규약 D16)

CLAUDE.md의 스킬 수·D 범위·plan 목록이 반복해서 스테일해졌다. P0 작업
중에도 테스트 수와 D 범위가 다시 어긋나 사람이 고쳤다. 사람 규율에
맡기지 않고 테스트로 고정한다.

D16을 스펙에 추가하고, 그 D16 때문에 CLAUDE.md의 D 범위도 함께 올라간다
— 규약과 검사가 같은 커밋에서 움직이는 것이 의도한 작동이다.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 8: D4 — 공개 준비 문서와 `init` 보완 제안

**Files:**
- Modify: `README.md` (§3 설치, §11 트러블슈팅, §12 기여, 신규 마이그레이션 절)
- Modify: `skills/init/SKILL.md` (기존-하네스 분기에 보호 설정 보완 제안)

**Interfaces:**
- Consumes: 없음
- Produces: 없음

- [ ] **Step 1: README §3 설치를 정식 경로로 재작성**

현재 `### 개발 모드`로 소개된 부분을 아래로 교체한다.

```markdown
### 설치

```bash
git clone <저장소 URL> ~/infra-plugin
cd ~/infra-workspace          # 하네스로 쓸 디렉터리(없으면 mkdir로 만든다)
claude --plugin-dir ~/infra-plugin
```

`--plugin-dir`에는 `.claude-plugin/plugin.json`이 있는 저장소 루트의 절대 경로를 준다.
같은 이름의 설치된 플러그인이 있어도 `--plugin-dir`로 띄운 쪽이 우선한다.

marketplace 배포는 아직 제공하지 않는다 — 위 경로가 현재의 정식 설치 방법이다.

> **언어**: 스킬 본문과 산출 문서는 한국어다. 영어권 사용자 대응(i18n)은 별도 작업으로
> 예정돼 있으며, 그 전까지는 한국어를 읽을 수 있는 환경을 전제한다.
```

- [ ] **Step 2: README에 마이그레이션 절 추가**

§11 트러블슈팅 앞에 신설한다.

```markdown
## 마이그레이션

### 기존 하네스에 보호 설정 보강 (D15)

`.claude/settings.local.json`이 없는 기존 git 하네스는 `audit`가 실패로 보고한다. 하네스
하위 디렉터리에서 연 세션이 `secrets/` 차단을 받지 못하기 때문이다(`settings.json`은 부모
폴백 없이 cwd에서만 로드된다).

하네스에서 **"하네스 점검해줘"**라고 말하면 `audit`가 누락을 짚고 `init`이 보완을 제안한다.
직접 처리하려면 `.claude/settings.json`과 같은 내용으로 `.claude/settings.local.json`을
만들면 된다. `sharing: git` 하네스라면 이 파일을 **커밋한다** — 이름은 `local`이지만 팀
전체가 같은 보호를 받게 하려는 의도적 선택이며, `.gitignore`에 넣지 않는다.
```

- [ ] **Step 3: README §12 기여 문서에 열람 마찰 기록**

```markdown
### 기여자 주의 — `skills/secrets/` 열람

`Read(secrets/**)` 계열 deny 규칙을 쓰는 환경에서 **플러그인 저장소가 세션 cwd 아래에
있으면** `skills/secrets/` 이하 문서가 차단된다. deny 규칙이 앵커 아래 임의 깊이의
`secrets` 디렉터리를 매치하기 때문이다(문서화된 동작).

이때는 git 경유로 읽는다: `git show HEAD:skills/secrets/SKILL.md`

실사용자에게는 발생하지 않는다 — 사용자의 cwd는 하네스이고 플러그인은
`~/.claude/plugins/…`나 clone 경로에 있어 앵커 밖이기 때문이다.
```

- [ ] **Step 4: `init`의 기존-하네스 분기에 보완 제안 추가**

`skills/init/SKILL.md`의 §1(기존 하네스 감지 → 감사/확장 모드) 절에 추가한다.

```markdown
감사 결과에 `[보호]` 실패·경고가 있으면 **보완을 제안한다**. 특히 `.claude/settings.local.json`
누락은 D15가 도입한 항목이라 그 이전에 만든 하네스에는 없다. `settings.local.json` 템플릿을
복사해 만들 것을 제안하고, `sharing: git`이면 커밋 대상에 포함해야 함을 함께 안내한다
(`.gitignore`에 넣지 않는다). 사용자 확인 없이 파일을 만들지 않는다.
```

- [ ] **Step 5: 문서 정합성 테스트 통과 확인**

Run: `python3 -m unittest tests.test_docs_consistency -v`
Expected: PASS — README의 "스킬 10종" 표기가 유지되어야 한다

- [ ] **Step 6: 전체 테스트**

Run: `bash tests/run_tests.sh`
Expected: OK

- [ ] **Step 7: 커밋**

```bash
git add README.md skills/init/SKILL.md
git commit -m "docs: 공개 설치 경로·마이그레이션·기여자 마찰 문서화 (D4)

낯선 사용자가 README만으로 설치하고 첫 하네스를 만들 수 있게 한다.
clone + --plugin-dir를 '개발 모드'가 아니라 정식 설치 경로로 다시 쓰고,
i18n이 아직 안 됐음을 전제로 명시한다.

D15로 audit이 실패하게 된 기존 하네스의 마이그레이션 절차를 추가하고,
init의 기존-하네스 분기가 보호 설정 보완을 제안하게 한다. 기여자만 겪는
skills/secrets 열람 마찰과 git 경유 우회도 기록한다.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 9: R1 — `main` 병합

**Files:**
- 없음 (git 작업)

**Interfaces:**
- Consumes: Task 1~8 전부
- Produces: `main`이 실질 SSOT가 된다

- [ ] **Step 1: 최종 전체 테스트**

```bash
bash tests/run_tests.sh
```
Expected: OK, 실패 0

- [ ] **Step 2: 작업 트리 청결 확인**

```bash
git status --porcelain
```
Expected: 출력 없음(`.context/` 같은 untracked 제외)

- [ ] **Step 3: 병합 대상 확인**

```bash
git log main..HEAD --oneline | wc -l
git log main..HEAD --oneline | head -20
```
Expected: 이 계획의 커밋들을 포함한 목록. 사용자에게 보여주고 병합 승인을 받는다.

- [ ] **Step 4: 병합**

```bash
cd /Users/choyoungrae/Projects/infra
git merge --no-ff feat/infra-plugin -m "Merge feat/infra-plugin: infra 플러그인 + 검토·신뢰 확보

스킬 10종, 검증 스크립트, hook, 검토 보고서, 그리고 공개 배포 전 신뢰
확보 작업(P0 4건 + 약속과 실제의 일치 묶음)을 main에 반영한다.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

- [ ] **Step 5: 병합 후 검증**

```bash
cd /Users/choyoungrae/Projects/infra
bash tests/run_tests.sh
git log --oneline -3
```
Expected: 테스트 OK, 병합 커밋이 보인다

---

## 부록: 스펙 커버리지 확인

| 스펙 항목 | 태스크 |
|---|---|
| C1 sync 확인 불가 세분화 | Task 3 |
| C2 `--region` 명시 | Task 3 |
| C3 파서 메시지 정정 | Task 1 |
| C4 `secrets_format` 검증 | Task 2 |
| C5 hook 패턴 확장 | Task 4 |
| D1 신규 암호화 절 | Task 5 |
| D2 문서 정합성 + D16 | Task 7 |
| D3 스펙 동기화 | Task 6 |
| D4 공개 준비 문서 | Task 8 |
| R1 main 병합 | Task 9 |
| 완료 기준 1 (막다른 길 없음) | Task 5 (+ Task 8 마이그레이션) |
| 완료 기준 2 (확인 불가 구분 보고) | Task 3 |
| 완료 기준 3 (`--region` 명시) | Task 3 |
| 완료 기준 4 (테스트 통과 + 회귀) | 전 태스크의 마지막 단계 |
| 완료 기준 5 (병합 + README 설치) | Task 8, Task 9 |
