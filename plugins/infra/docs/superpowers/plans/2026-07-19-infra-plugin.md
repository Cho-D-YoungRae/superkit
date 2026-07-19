# infra 플러그인 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 인프라 하네스(인벤토리·변경기록·직접 제어)를 구성·운영하는 Claude Code 플러그인 `infra`를 스펙(docs/superpowers/specs/2026-07-19-infra-plugin-design.md)대로 구현한다.

**Architecture:** 저장소 루트 = 플러그인 루트. 산출물은 ① 스킬 9종(SKILL.md, 한국어) ② 하네스 템플릿 11종 ③ python3 stdlib 전용 검증 스크립트(harness_lib/audit/sync) ④ PostToolUse hook. 스크립트를 먼저 TDD로 만들고(스펙 §13 순서에서 앞당김 — init이 audit를 호출하기 때문), 스킬 문서는 test_skills.py로 frontmatter·필수 요소를 자동 검증한다.

**Tech Stack:** Claude Code plugin (plugin.json / SKILL.md / hooks.json), python3 표준 라이브러리(unittest), bash.

## Global Constraints

스펙에서 그대로 옮긴 전 태스크 공통 제약. 모든 태스크의 요구사항에 암묵 포함된다.

- 모든 스킬 본문·산출 문서·리포트 문구는 **한국어**. 코드 식별자·명령어는 원문 유지.
- 스크립트는 **python3 표준 라이브러리만** 사용. PyYAML 등 외부 패키지 금지 (스펙 D2).
- **시크릿 값 읽기·출력 금지**: `~/.aws/credentials`·kubeconfig raw·`secrets/` 내용을 읽는 코드·절차를 만들지 않는다. 메타데이터 명령(`aws configure list-profiles`, `kubectl config get-contexts`, `ssh-keygen -lf`)만 (원칙 1).
- 모든 조작 명령 예시는 `--context`/`--profile`/`--kube-context` **명시** (원칙 6).
- 컴포넌트 디렉토리를 `.claude-plugin/` 안에 두지 않는다 — 그 안에는 `plugin.json`만.
- 스킬·hook에서 플러그인 파일 접근은 `${CLAUDE_PLUGIN_ROOT}` 기준 경로.
- PostToolUse hook 스크립트는 **어떤 경우에도 exit 0** (비차단, 스펙 D6).
- secrets deny 규칙은 `Read(/secrets/**)`와 `Read(./secrets/**)` **병기** (스펙 D3).
- SKILL.md frontmatter `description`은 한국어 3요소(① 역할 한 문장 — 인프라 도메인 어휘 우선 ② 트리거 발화 예시 ③ 인접 스킬 경계)를 **한 줄 스칼라**로 작성한다(자체 파서 검증 단순화 — 스펙 §6.1의 `>-` 표기는 내용 예시일 뿐 표기 규약이 아님).
- 커밋은 태스크마다. Conventional Commits(`feat:`/`test:`/`docs:`) + 아래 트레일러:
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`
- 테스트 실행 명령은 항상 `bash tests/run_tests.sh` (Task 3에서 생성).

---

### Task 1: 플러그인 매니페스트

**Files:**
- Create: `.claude-plugin/plugin.json`

**Interfaces:**
- Consumes: 없음
- Produces: 플러그인 이름 `infra` — 이후 모든 스킬이 `/infra:<name>`으로 노출되는 근거.

- [ ] **Step 1: plugin.json 작성**

```json
{
  "name": "infra",
  "version": "0.1.0",
  "description": "인프라 하네스(인벤토리·변경기록·직접 제어) 플러그인 — init/register/lookup/connect/ops/change/decide/sync/audit",
  "author": {
    "name": "Youngrae Cho"
  }
}
```

- [ ] **Step 2: JSON 유효성 확인**

Run: `python3 -c "import json; print(json.load(open('.claude-plugin/plugin.json'))['name'])"`
Expected: `infra`

- [ ] **Step 3: 커밋**

```bash
git add .claude-plugin/plugin.json
git commit -m "feat: 플러그인 매니페스트 추가

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: 하네스 템플릿 11종

**Files:**
- Create: `templates/provider.md`, `templates/server.md`, `templates/k8s-cluster.md`, `templates/component.md`, `templates/keys.md`, `templates/change.md`, `templates/adr.md`, `templates/harness.yaml`, `templates/harness-CLAUDE.md`, `templates/settings.json`, `templates/gitignore`

**Interfaces:**
- Consumes: 없음
- Produces: init 스킬(Task 7)이 복사·치환하는 템플릿. 치환 변수는 `{{변수명}}` 스타일이며 기계 치환이 아니라 init 실행 시 클로드가 값을 채운다. Task 3 fixture는 이 frontmatter 구조를 그대로 따른다.

- [ ] **Step 1: 엔티티 템플릿 4종 작성**

`templates/provider.md`:

````markdown
---
id: {{id}}
type: provider
kind: {{kind}}                 # aws | gcp | onprem | ...
cli_profile: {{cli_profile}}   # aws --profile / gcloud configuration 이름 (온프렘이면 이 줄 삭제)
regions: []                    # 예: [ap-northeast-2]
console: "{{console}}"         # 콘솔/관리 UI URL (없으면 이 줄 삭제)
---

# {{id}}

<!-- 계정 구조, 결제, 네트워크 대역, 주의사항을 자유 서술 -->
````

`templates/server.md`:

````markdown
---
id: {{id}}
type: server
env: {{env}}
provider: {{provider}}
runtime: {{runtime}}           # ec2 | vm | baremetal | ...
purpose: "{{purpose}}"
access: "{{access}}"           # 예: "ssh, 키: keys.md#deploy-key"
managed_by: {{managed_by}}     # terraform://org/repo//module 경로 또는 manual
depends_on: []
---

# {{id}}

<!-- 히스토리·주의사항 자유 서술 -->
````

`templates/k8s-cluster.md`:

````markdown
---
id: {{id}}
type: k8s-cluster
env: {{env}}
provider: {{provider}}
context: {{context}}           # kubectl context 이름
access_recipe: "{{access_recipe}}"   # 로컬 접근 재구성 명령. 온프렘은 위치·방법만 기술, 파일 내용 저장 금지
managed_by: {{managed_by}}
---

# {{id}}

<!-- 노드 구성, 버전, 업그레이드 이력 등 자유 서술 -->
````

`templates/component.md`:

````markdown
---
id: {{id}}
type: component
category: {{category}}         # gitops | monitoring | db | ingress | ...
runs_on: {{runs_on}}           # server 또는 k8s-cluster id
namespace: {{namespace}}       # k8s가 아니면 이 줄 삭제
endpoint: "{{endpoint}}"       # 없으면 이 줄 삭제
installed_by: {{installed_by}} # helm://<repo>/<chart>@<ver> | manifest 경로 | apt | docker 등
access: "{{access}}"           # 예: "PromQL API, 토큰: keys.md#vm-token"
---

# {{id}}

<!-- 설정 위치, 대시보드, 주의사항 자유 서술 -->
````

- [ ] **Step 2: keys.md·change.md·adr.md 템플릿 작성**

`templates/keys.md`:

````markdown
# 키·인증서 목록

**값은 절대 이 파일에 적지 않는다 — 위치 참조만** (원칙 1·2). TLS 인증서 만료도 여기서 추적한다.
`access:` 필드의 `keys.md#<이름>` 앵커는 아래 표의 "이름" 컬럼과 일치해야 한다(audit가 검사).

| 이름 | 종류 | fingerprint | 위치 참조 | 소유자 | 생성일 | 만료/로테이션 |
|------|------|-------------|-----------|--------|--------|---------------|
| deploy-key | ssh | SHA256:예시 | ~/.ssh/deploy-key | 담당자 | 2026-01-01 | - |
````

`templates/change.md`:

````markdown
---
date: {{date}}
targets: [{{targets}}]
---

# {{title}}

## 변경 내용

## 사유
<!-- 배경. 관련 ADR이 있으면 링크: ../../decisions/ADR-NNNN-slug.md -->

## 실행 명령/방법
<!-- 실제 실행한 명령을 --context/--profile 포함 그대로 기록 -->

## 결과·검증

## 롤백 방법 (필수)
<!-- 비워두지 말 것 — change 스킬이 반드시 채우도록 요구한다 -->
````

`templates/adr.md`:

````markdown
# ADR-{{number}}: {{title}}

- 상태: {{status}}   <!-- 제안됨 | 승인됨 | 폐기됨 | 대체됨 -->
- 날짜: {{date}}

## 맥락

## 결정

## 고려한 대안

## 결과

## 관련 기록
<!-- 관련 change: ../changes/YYYY/MM-DD-slug.md -->
````

- [ ] **Step 3: harness.yaml·harness-CLAUDE.md·settings.json·gitignore 템플릿 작성**

`templates/harness.yaml`:

```yaml
# 인프라 하네스 설정 — infra 플러그인 스킬이 읽는 정책 데이터 (원칙 8)
sharing: {{sharing}}            # local | git | shared-drive
secrets_mode: {{secrets_mode}}  # none(참조만) | plaintext(local에서만 유효) | encrypted(age/SOPS)
environments: [{{environments}}]
iac:
  repos: []
  # repos:
  #   - terraform://github.com/org/infra-tf
policies:
  mutating:                     # 환경별 mutating 정책: confirm | allow (미정의 env는 confirm — D4)
    prod: confirm
hooks:
  change_reminder: true
```

`templates/harness-CLAUDE.md`:

````markdown
# 인프라 하네스

이 저장소는 인프라의 지식(인벤토리)·기록(변경/의사결정)·조작(진입점)을 담는 **중앙 하네스**다.
infra 플러그인 스킬(init/register/lookup/connect/ops/change/decide/sync/audit)이 이 저장소를 읽고 쓴다.
이 저장소는 IP·토폴로지·접근 정보가 담긴 민감 문서다 — **외부 비공개 필수**.

## 핵심 규약

- 시크릿 값은 어떤 파일에도 적지 않는다. 위치 참조만(access/keys.md). 사용은 참조 실행
  (`ssh -i <경로>`, `${VAR}`, `sops exec-env`, `op run`)만 (원칙 1).
- `secrets/`는 읽기 금지 구역이다(.claude/settings.json의 deny). 보관 정책은 harness.yaml의
  sharing·secrets_mode를 따른다 (원칙 2).
- 조작 명령은 항상 엔티티에 기록된 `--context`/`--profile`을 명시한다 (원칙 6).
- mutating 작업 후에는 changes/에 기록을 남긴다 — 롤백 방법 필수 (원칙 7·9).
- 상태의 SSOT는 실제 인프라·terraform state·config 레포다. 하네스는 색인·맥락·진입점만 담는다 (원칙 4).

## 스킬 사용

자연어로 요청하면 된다: "prod DB 어떻게 붙어?"(lookup) · "이 클러스터 파드 상태 봐줘"(ops) ·
"방금 작업 기록 남겨줘"(change) · "문서랑 실제 상태 맞아?"(sync) · "하네스 점검해줘"(audit) ·
"서버 등록해줘"(register) · "kubeconfig 다시 잡아줘"(connect).

## 하네스 변경 이력

- {{date}}: init으로 생성
````

`templates/settings.json`:

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

`templates/gitignore` — 주의: gitignore는 디렉토리 자체(`secrets/`)를 무시하면 내부 재포함(`!`)이 불가능하므로, encrypted 모드 전환을 고려해 `secrets/*` 패턴을 쓴다:

```
# secrets/ — 시크릿 값 보관 구역 (원칙 2)
# 기본: 전부 비공유. sharing: git + secrets_mode: encrypted라면 init이
# 아래 재포함 줄의 주석을 해제해 암호문(.age/.sops.yaml)만 커밋되게 한다.
secrets/*
# !secrets/*.age
# !secrets/*.sops.yaml
```

- [ ] **Step 4: 검증**

Run: `ls templates/ | wc -l && python3 -c "import json; json.load(open('templates/settings.json')); print('settings.json OK')"`
Expected: `11` 그리고 `settings.json OK`

- [ ] **Step 5: 커밋**

```bash
git add templates/
git commit -m "feat: 하네스 템플릿 11종 추가

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: harness_lib(탐색·파서) + 테스트 기반 + 정상 fixture

**Files:**
- Create: `scripts/harness_lib.py`
- Create: `tests/run_tests.sh`
- Create: `tests/test_harness_lib.py`
- Create: `tests/fixtures/harness-ok/` (하위 전체)

**Interfaces:**
- Consumes: Task 2의 frontmatter 구조.
- Produces (이후 Task 4·5·7이 사용):
  - `harness_lib.find_harness_root(start: str|Path|None) -> Path|None` — start(기본 cwd)에서 루트 방향으로 `harness.yaml` 상향 탐색.
  - `harness_lib.FrontmatterError(Exception)`, `harness_lib.HarnessYamlError(Exception)`
  - `harness_lib.parse_frontmatter(text: str) -> dict` — 플랫 전용(`key: value`, `[a, b]`, 따옴표, `#` 주석). 중첩·빈 값·구분자 누락은 `FrontmatterError`.
  - `harness_lib.parse_yaml_subset(text: str) -> dict` — harness.yaml용 YAML 서브셋(중첩 맵, `- ` 리스트, 인라인 리스트, true/false).
  - `harness_lib.load_harness_yaml(path: Path) -> dict`
  - `harness_lib.iter_entities(root: Path) -> list[dict]` — `providers/`·`inventory/` 재귀 스캔. 각 dict에 `_path`(Path)·`_stem`(str) 추가, 파싱 실패 시 `_error`(str).
  - `harness_lib.REQUIRED_FIELDS: dict[str, list[str]]` — type별 필수 필드.
  - fixture `tests/fixtures/harness-ok/` — 이후 태스크의 통과 케이스.
  - `bash tests/run_tests.sh` — 전 태스크 공통 테스트 러너.

- [ ] **Step 1: 정상 fixture 작성**

다음 파일들을 생성한다 (frontmatter는 Task 2 템플릿 구조를 값 채워 사용):

`tests/fixtures/harness-ok/harness.yaml`:

```yaml
sharing: local
secrets_mode: plaintext
environments: [prod, dev]
iac:
  repos:
    - terraform://github.com/example/infra-tf
policies:
  mutating:
    prod: confirm
    dev: allow
hooks:
  change_reminder: true
```

`tests/fixtures/harness-ok/providers/aws-main.md`:

```markdown
---
id: aws-main
type: provider
kind: aws
cli_profile: main
regions: [ap-northeast-2]
console: "https://console.aws.amazon.com"
---

# aws-main
```

`tests/fixtures/harness-ok/inventory/prod-db-01.md`:

```markdown
---
id: prod-db-01
type: server
env: prod
provider: aws-main
runtime: ec2
purpose: "PostgreSQL 단독 DB 서버"
access: "ssh, 키: keys.md#deploy-key"
managed_by: manual
depends_on: []
---

# prod-db-01
```

`tests/fixtures/harness-ok/inventory/prod-k8s.md`:

```markdown
---
id: prod-k8s
type: k8s-cluster
env: prod
provider: aws-main
context: prod-k8s
access_recipe: "aws eks update-kubeconfig --name prod --profile main --alias prod-k8s"
managed_by: manual
---

# prod-k8s
```

`tests/fixtures/harness-ok/inventory/components/victoria-metrics.md`:

```markdown
---
id: victoria-metrics
type: component
category: monitoring
runs_on: prod-k8s
namespace: monitoring
endpoint: "https://vm.internal.example.com"
installed_by: helm://vm/victoria-metrics-single@0.x
access: "PromQL API, 토큰: keys.md#vm-token"
---

# victoria-metrics
```

`tests/fixtures/harness-ok/access/keys.md`:

```markdown
# 키·인증서 목록

| 이름 | 종류 | fingerprint | 위치 참조 | 소유자 | 생성일 | 만료/로테이션 |
|------|------|-------------|-----------|--------|--------|---------------|
| deploy-key | ssh | SHA256:abc | ~/.ssh/deploy-key | 담당자 | 2026-01-01 | - |
| vm-token | api-token | - | secrets/vm-token.txt | 담당자 | 2026-01-01 | 2030-01-01 |
```

추가로 빈 구조 유지용: `tests/fixtures/harness-ok/secrets/vm-token.txt`(내용: `dummy-not-a-real-token`), `tests/fixtures/harness-ok/changes/.gitkeep`, `tests/fixtures/harness-ok/decisions/.gitkeep`.

- [ ] **Step 2: 실패하는 테스트 작성**

`tests/test_harness_lib.py`:

```python
import sys
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import harness_lib  # noqa: E402

OK = PLUGIN_ROOT / "tests" / "fixtures" / "harness-ok"


class TestFindHarnessRoot(unittest.TestCase):
    def test_finds_from_subdir(self):
        self.assertEqual(harness_lib.find_harness_root(OK / "inventory" / "components"), OK)

    def test_none_outside(self):
        self.assertIsNone(harness_lib.find_harness_root("/"))


class TestParseFrontmatter(unittest.TestCase):
    def test_parses_server(self):
        fm = harness_lib.parse_frontmatter((OK / "inventory" / "prod-db-01.md").read_text(encoding="utf-8"))
        self.assertEqual(fm["id"], "prod-db-01")
        self.assertEqual(fm["type"], "server")
        self.assertEqual(fm["depends_on"], [])
        self.assertEqual(fm["purpose"], "PostgreSQL 단독 DB 서버")

    def test_inline_list(self):
        fm = harness_lib.parse_frontmatter((OK / "providers" / "aws-main.md").read_text(encoding="utf-8"))
        self.assertEqual(fm["regions"], ["ap-northeast-2"])

    def test_rejects_missing_delim(self):
        with self.assertRaises(harness_lib.FrontmatterError):
            harness_lib.parse_frontmatter("id: x\n")

    def test_rejects_nested(self):
        with self.assertRaises(harness_lib.FrontmatterError):
            harness_lib.parse_frontmatter("---\nparent:\n  child: 1\n---\n")


class TestParseYamlSubset(unittest.TestCase):
    def test_harness_yaml(self):
        data = harness_lib.load_harness_yaml(OK / "harness.yaml")
        self.assertEqual(data["sharing"], "local")
        self.assertEqual(data["environments"], ["prod", "dev"])
        self.assertEqual(data["iac"]["repos"], ["terraform://github.com/example/infra-tf"])
        self.assertEqual(data["policies"]["mutating"]["prod"], "confirm")
        self.assertIs(data["hooks"]["change_reminder"], True)


class TestIterEntities(unittest.TestCase):
    def test_collects_all(self):
        ents = harness_lib.iter_entities(OK)
        ids = sorted(e["_stem"] for e in ents)
        self.assertEqual(ids, ["aws-main", "prod-db-01", "prod-k8s", "victoria-metrics"])
        for e in ents:
            self.assertNotIn("_error", e)


if __name__ == "__main__":
    unittest.main()
```

`tests/run_tests.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

- [ ] **Step 3: 테스트가 실패하는지 확인**

Run: `chmod +x tests/run_tests.sh && bash tests/run_tests.sh`
Expected: FAIL — `ModuleNotFoundError: No module named 'harness_lib'`

- [ ] **Step 4: harness_lib.py 구현**

`scripts/harness_lib.py`:

```python
"""infra 하네스 공용 유틸 — 상향 탐색, frontmatter/harness.yaml 파서 (python3 stdlib 전용)."""
from pathlib import Path

FM_DELIM = "---"
ENTITY_DIRS = ("providers", "inventory")

REQUIRED_FIELDS = {
    "provider": ["id", "type", "kind"],
    "server": ["id", "type", "env", "provider", "runtime", "purpose", "access", "managed_by"],
    "k8s-cluster": ["id", "type", "env", "provider", "context", "access_recipe", "managed_by"],
    "component": ["id", "type", "category", "runs_on", "installed_by"],
}


class FrontmatterError(Exception):
    pass


class HarnessYamlError(Exception):
    pass


def find_harness_root(start=None):
    cur = Path(start or Path.cwd()).resolve()
    for p in [cur, *cur.parents]:
        if (p / "harness.yaml").is_file():
            return p
    return None


def _strip_comment(line):
    out, quote = [], None
    for i, ch in enumerate(line):
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch in ('"', "'"):
            quote = ch
            out.append(ch)
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            break
        else:
            out.append(ch)
    return "".join(out).rstrip()


def _scalar(s):
    s = s.strip()
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        return [] if not inner else [_scalar(x) for x in inner.split(",")]
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        return s[1:-1]
    if s == "true":
        return True
    if s == "false":
        return False
    return s


def parse_frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != FM_DELIM:
        raise FrontmatterError("frontmatter 시작(---)이 없음")
    fm = {}
    for raw in lines[1:]:
        if raw.strip() == FM_DELIM:
            return fm
        line = _strip_comment(raw)
        if not line.strip():
            continue
        if line != line.lstrip(" "):
            raise FrontmatterError(f"중첩 구조 미지원: {raw!r}")
        if ":" not in line:
            raise FrontmatterError(f"지원하지 않는 구문: {raw!r}")
        key, _, val = line.partition(":")
        if val.strip() == "":
            raise FrontmatterError(f"빈 값/중첩 미지원: {raw!r}")
        fm[key.strip()] = _scalar(val)
    raise FrontmatterError("frontmatter 종료(---)가 없음")


def parse_yaml_subset(text):
    """harness.yaml용 YAML 서브셋 파서 — 중첩 맵, '- ' 리스트, 인라인 [a, b], 스칼라."""
    root = {}
    # stack 원소: [indent, container, parent, key_in_parent]
    stack = [[-1, root, None, None]]
    for raw in text.splitlines():
        line = _strip_comment(raw)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        body = line.strip()
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        top = stack[-1]
        container = top[1]
        if body.startswith("- "):
            if isinstance(container, dict):
                if container:
                    raise HarnessYamlError(f"리스트 위치 오류: {raw!r}")
                new_list = []
                top[2][top[3]] = new_list  # 빈 dict 자리에 리스트로 교체
                top[1] = new_list
                container = new_list
            container.append(_scalar(body[2:]))
        elif ":" in body:
            if not isinstance(container, dict):
                raise HarnessYamlError(f"맵 위치 오류: {raw!r}")
            key, _, val = body.partition(":")
            key, val = key.strip(), val.strip()
            if val == "":
                child = {}
                container[key] = child
                stack.append([indent, child, container, key])
            else:
                container[key] = _scalar(val)
        else:
            raise HarnessYamlError(f"지원하지 않는 구문: {raw!r}")
    return root


def load_harness_yaml(path):
    return parse_yaml_subset(Path(path).read_text(encoding="utf-8"))


def iter_entities(root):
    out = []
    for d in ENTITY_DIRS:
        base = Path(root) / d
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.md")):
            try:
                fm = parse_frontmatter(path.read_text(encoding="utf-8"))
            except FrontmatterError as e:
                fm = {"_error": str(e)}
            fm["_path"] = path
            fm["_stem"] = path.stem
            out.append(fm)
    return out
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `bash tests/run_tests.sh`
Expected: PASS (전체 OK, 실패 0)

- [ ] **Step 6: 커밋**

```bash
git add scripts/harness_lib.py tests/
git commit -m "feat: harness_lib 파서·탐색 유틸과 테스트 기반 추가

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: 오염 fixture + audit.py

**Files:**
- Create: `scripts/audit.py`
- Create: `tests/fixtures/harness-bad/` (하위 전체)
- Test: `tests/test_audit.py`

**Interfaces:**
- Consumes: `harness_lib`(Task 3 전체), fixture 2종.
- Produces (Task 7·11의 스킬이 호출):
  - CLI: `python3 scripts/audit.py [--root PATH] [--today YYYY-MM-DD]` — root 생략 시 cwd에서 상향 탐색. 사람이 읽는 한국어 리포트를 stdout에 출력. **실패 있으면 exit 1, 경고만 있으면 exit 0**.
  - 함수(테스트·재사용용): `run_audit(root: Path, today: datetime.date) -> tuple[list[str], list[str]]` — `(failures, warnings)`.

- [ ] **Step 1: 오염 fixture 작성**

스펙 완료 기준 9를 재현하는 fixture. **주의: AKIA 문자열은 가짜 예시이며 fixture에만 존재해야 한다.**

`tests/fixtures/harness-bad/harness.yaml` — 무효 정책 조합(sharing ≠ local + plaintext):

```yaml
sharing: shared-drive
secrets_mode: plaintext
environments: [prod]
policies:
  mutating:
    prod: confirm
hooks:
  change_reminder: true
```

`tests/fixtures/harness-bad/providers/aws-main.md` — Task 3의 harness-ok와 동일 내용 복사.

`tests/fixtures/harness-bad/inventory/ghost-server.md` — 깨진 참조(provider) + id-파일명 불일치 + 필수 필드 누락(runtime 없음):

```markdown
---
id: ghost-01
type: server
env: prod
provider: no-such-provider
purpose: "참조가 깨진 서버"
access: "ssh, 키: keys.md#no-such-key"
managed_by: manual
---

# ghost-01
```

`tests/fixtures/harness-bad/notes.md` — secrets/ 밖 시크릿 패턴(가짜 값):

```markdown
# 메모

aws_access_key_id = AKIA1234567890ABCDEF
```

`tests/fixtures/harness-bad/access/keys.md` — 만료 임박 키(--today 2026-07-19 기준 13일 뒤):

```markdown
# 키·인증서 목록

| 이름 | 종류 | fingerprint | 위치 참조 | 소유자 | 생성일 | 만료/로테이션 |
|------|------|-------------|-----------|--------|--------|---------------|
| old-cert | tls-cert | - | secrets/old-cert.pem | 담당자 | 2025-08-01 | 2026-08-01 |
```

`tests/fixtures/harness-bad/secrets/plain.txt`(내용: `dummy`) — encrypted 검사가 아닌 plaintext 조합 실패 확인용.

- [ ] **Step 2: 실패하는 테스트 작성**

`tests/test_audit.py`:

```python
import datetime
import subprocess
import sys
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import audit  # noqa: E402

OK = PLUGIN_ROOT / "tests" / "fixtures" / "harness-ok"
BAD = PLUGIN_ROOT / "tests" / "fixtures" / "harness-bad"
TODAY = datetime.date(2026, 7, 19)


class TestAuditOk(unittest.TestCase):
    def test_ok_harness_passes(self):
        failures, warnings = audit.run_audit(OK, TODAY)
        self.assertEqual(failures, [])


class TestAuditBad(unittest.TestCase):
    def setUp(self):
        self.failures, self.warnings = audit.run_audit(BAD, TODAY)
        self.joined = "\n".join(self.failures)
        self.warn_joined = "\n".join(self.warnings)

    def test_secret_pattern_detected(self):
        self.assertIn("AKIA", self.joined)
        self.assertIn("notes.md", self.joined)

    def test_invalid_policy_combo(self):
        self.assertIn("plaintext", self.joined)
        self.assertIn("shared-drive", self.joined)

    def test_broken_reference(self):
        self.assertIn("no-such-provider", self.joined)
        self.assertIn("no-such-key", self.joined)

    def test_id_mismatch_and_missing_field(self):
        self.assertIn("ghost", self.joined)   # id-파일명 불일치
        self.assertIn("runtime", self.joined)  # 필수 필드 누락

    def test_expiry_warning(self):
        self.assertIn("old-cert", self.warn_joined)


class TestAuditCli(unittest.TestCase):
    def test_exit_codes(self):
        script = str(PLUGIN_ROOT / "scripts" / "audit.py")
        ok = subprocess.run([sys.executable, script, "--root", str(OK), "--today", "2026-07-19"],
                            capture_output=True, text=True)
        bad = subprocess.run([sys.executable, script, "--root", str(BAD), "--today", "2026-07-19"],
                             capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        self.assertEqual(bad.returncode, 1, bad.stdout + bad.stderr)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: 테스트가 실패하는지 확인**

Run: `bash tests/run_tests.sh`
Expected: FAIL — `ModuleNotFoundError: No module named 'audit'`

- [ ] **Step 4: audit.py 구현**

`scripts/audit.py` — 핵심 구조 (검사 6종은 스펙 §8.1 표와 1:1):

```python
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
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
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
            head = p.open("rb").read(512)  # 헤더 판별용 — 내용은 출력하지 않는다
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
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `bash tests/run_tests.sh`
Expected: PASS (test_harness_lib + test_audit 전체 OK)

- [ ] **Step 6: 커밋**

```bash
git add scripts/audit.py tests/fixtures/harness-bad/ tests/test_audit.py
git commit -m "feat: audit 정합성 검증 스크립트와 오염 fixture 추가

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: sync_snapshot.py

**Files:**
- Create: `scripts/sync_snapshot.py`
- Test: `tests/test_sync.py`
- Create: `tests/fixtures/mock-actual.json`

**Interfaces:**
- Consumes: `harness_lib.iter_entities`, `harness_lib.find_harness_root`, fixture `harness-ok`.
- Produces (Task 11 sync 스킬이 호출):
  - CLI 3모드: `python3 scripts/sync_snapshot.py [--root PATH]` (dry — 기대 스냅샷 + 수집 명령 목록 출력) / `--collect` (수집 명령을 subprocess로 실행 후 대조) / `--mock-actual FILE.json` (수집 대신 파일 주입 — 테스트용).
  - 함수: `build_expected(root) -> dict`, `build_collect_commands(root) -> list[dict]` (각 `{"target": id, "kind": str, "cmd": list[str]}`), `parse_installed_by(value) -> tuple[str, str, str|None]` (`(method, ref, version)`), `diff_state(expected, actual) -> dict` (키: `missing_in_docs`, `ghost_in_docs`, `version_mismatch`, `unverifiable` — 각 한국어 문자열 리스트).
  - actual JSON 스키마: `{"clusters": {"<id>": {"reachable": bool, "helm_releases": [{"name","namespace","chart"}]}}, "providers": {"<id>": {"reachable": bool, "instances": ["<Name태그>", ...]}}}`
  - 대조 규약(구현·문서 공통 가정): helm 릴리스 이름 == 컴포넌트 id, EC2 Name 태그 == 서버 id. 이 규약은 sync SKILL.md(Task 11)와 register SKILL.md(Task 8)에도 명시해 등록 시 지키게 한다.

- [ ] **Step 1: mock fixture 작성**

`tests/fixtures/mock-actual.json` — harness-ok 대비 ① 문서에 없는 릴리스 `argocd`(누락) ② 문서의 victoria-metrics는 버전 불일치(installed_by `@0.x` ↔ chart `victoria-metrics-single-1.2.0`) ③ 문서의 prod-db-01은 실측에 없음(유령) ④ aws-main은 reachable:

```json
{
  "clusters": {
    "prod-k8s": {
      "reachable": true,
      "helm_releases": [
        {"name": "victoria-metrics", "namespace": "monitoring", "chart": "victoria-metrics-single-1.2.0"},
        {"name": "argocd", "namespace": "argocd", "chart": "argo-cd-5.51.6"}
      ]
    }
  },
  "providers": {
    "aws-main": {
      "reachable": true,
      "instances": ["prod-app-01"]
    }
  }
}
```

- [ ] **Step 2: 실패하는 테스트 작성**

`tests/test_sync.py`:

```python
import json
import sys
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import sync_snapshot  # noqa: E402

OK = PLUGIN_ROOT / "tests" / "fixtures" / "harness-ok"
MOCK = PLUGIN_ROOT / "tests" / "fixtures" / "mock-actual.json"


class TestParseInstalledBy(unittest.TestCase):
    def test_helm(self):
        self.assertEqual(sync_snapshot.parse_installed_by("helm://vm/victoria-metrics-single@0.x"),
                         ("helm", "vm/victoria-metrics-single", "0.x"))

    def test_non_helm(self):
        self.assertEqual(sync_snapshot.parse_installed_by("apt"), ("apt", "", None))


class TestCollectCommands(unittest.TestCase):
    def test_context_profile_explicit(self):
        cmds = sync_snapshot.build_collect_commands(OK)
        flat = [" ".join(c["cmd"]) for c in cmds]
        self.assertTrue(any("--kube-context prod-k8s" in c for c in flat))
        self.assertTrue(any("--context prod-k8s" in c for c in flat))
        self.assertTrue(any("--profile main" in c for c in flat))
        for c in cmds:  # read-only 보증: mutating 동사가 없어야 한다
            joined = " ".join(c["cmd"])
            for bad in ("apply", "delete", "upgrade", "install", "scale"):
                self.assertNotIn(bad, joined)


class TestDiff(unittest.TestCase):
    def setUp(self):
        expected = sync_snapshot.build_expected(OK)
        actual = json.loads(MOCK.read_text(encoding="utf-8"))
        self.report = sync_snapshot.diff_state(expected, actual)

    def test_missing_in_docs(self):
        self.assertTrue(any("argocd" in x for x in self.report["missing_in_docs"]))
        self.assertTrue(any("prod-app-01" in x for x in self.report["missing_in_docs"]))

    def test_ghost_in_docs(self):
        self.assertTrue(any("prod-db-01" in x for x in self.report["ghost_in_docs"]))

    def test_version_mismatch(self):
        self.assertTrue(any("victoria-metrics" in x for x in self.report["version_mismatch"]))

    def test_no_unverifiable_when_reachable(self):
        self.assertEqual(self.report["unverifiable"], [])


class TestUnverifiable(unittest.TestCase):
    def test_unreachable_reported(self):
        expected = sync_snapshot.build_expected(OK)
        report = sync_snapshot.diff_state(expected, {"clusters": {}, "providers": {}})
        self.assertTrue(any("prod-k8s" in x for x in report["unverifiable"]))
        self.assertTrue(any("aws-main" in x for x in report["unverifiable"]))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: 테스트가 실패하는지 확인**

Run: `bash tests/run_tests.sh`
Expected: FAIL — `ModuleNotFoundError: No module named 'sync_snapshot'`

- [ ] **Step 4: sync_snapshot.py 구현**

`scripts/sync_snapshot.py` 핵심 로직 (전체 파일로 작성):

```python
#!/usr/bin/env python3
"""인벤토리 문서 vs 실제 상태 대조 — read-only 수집만 수행 (stdlib 전용)."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_lib  # noqa: E402

CHART_VER_RE = re.compile(r"^(?P<name>.+)-(?P<ver>\d[\w.]*)$")


def parse_installed_by(value):
    value = str(value)
    if value.startswith("helm://"):
        body = value[len("helm://"):]
        ref, _, ver = body.partition("@")
        return ("helm", ref, ver or None)
    method = value.split("://")[0].split()[0] if value else ""
    return (method, "", None)


def build_expected(root):
    ents = harness_lib.iter_entities(root)
    exp = {"servers": {}, "clusters": {}, "components": {}, "providers": {}}
    for e in ents:
        if "_error" in e:
            continue
        t = e.get("type")
        if t == "provider":
            exp["providers"][e["id"]] = e
        elif t == "server":
            exp["servers"][e["id"]] = e
        elif t == "k8s-cluster":
            exp["clusters"][e["id"]] = e
        elif t == "component":
            exp["components"][e["id"]] = e
    return exp


def build_collect_commands(root):
    exp = build_expected(root)
    cmds = []
    for cid, c in exp["clusters"].items():
        ctx = c.get("context")
        cmds.append({"target": cid, "kind": "nodes",
                     "cmd": ["kubectl", "--context", ctx, "get", "nodes", "-o", "name"]})
        cmds.append({"target": cid, "kind": "helm-releases",
                     "cmd": ["helm", "--kube-context", ctx, "list", "-A", "-o", "json"]})
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


def collect(root):
    actual = {"clusters": {}, "providers": {}}
    for item in build_collect_commands(root):
        try:
            r = subprocess.run(item["cmd"], capture_output=True, text=True, timeout=60)
            ok = r.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            ok, r = False, None
        if item["kind"] == "nodes":
            actual["clusters"].setdefault(item["target"], {"reachable": False, "helm_releases": []})
            actual["clusters"][item["target"]]["reachable"] = ok
        elif item["kind"] == "helm-releases":
            entry = actual["clusters"].setdefault(item["target"], {"reachable": False, "helm_releases": []})
            if ok:
                try:
                    rels = json.loads(r.stdout or "[]")
                    entry["helm_releases"] = [
                        {"name": x.get("name"), "namespace": x.get("namespace"), "chart": x.get("chart")}
                        for x in rels]
                except json.JSONDecodeError:
                    pass
        elif item["kind"] == "instances":
            names = [l.strip() for l in (r.stdout.splitlines() if ok else []) if l.strip() and l.strip() != "None"]
            actual["providers"][item["target"]] = {"reachable": ok, "instances": names}
    return actual


def _version_matches(expected_ver, actual_ver):
    if expected_ver is None:
        return True
    if "x" in expected_ver or "*" in expected_ver:
        prefix = expected_ver.replace("*", "x").split("x")[0]
        return actual_ver.startswith(prefix)
    return expected_ver == actual_ver


def diff_state(expected, actual):
    report = {"missing_in_docs": [], "ghost_in_docs": [], "version_mismatch": [], "unverifiable": []}
    # 클러스터·컴포넌트(helm) 대조
    for cid in expected["clusters"]:
        cluster_actual = actual.get("clusters", {}).get(cid)
        if not cluster_actual or not cluster_actual.get("reachable"):
            report["unverifiable"].append(f"{cid}: 클러스터 수집 실패 — 확인 불가")
            continue
        releases = {r["name"]: r for r in cluster_actual.get("helm_releases", [])}
        doc_components = {c_id: c for c_id, c in expected["components"].items() if c.get("runs_on") == cid}
        for rname, rel in releases.items():
            if rname not in doc_components:
                report["missing_in_docs"].append(f"{cid}: helm 릴리스 {rname} ({rel.get('chart')}) — 문서에 없음")
        for c_id, comp in doc_components.items():
            method, ref, ver = parse_installed_by(comp.get("installed_by", ""))
            if method != "helm":
                continue
            if c_id not in releases:
                report["ghost_in_docs"].append(f"{cid}: 컴포넌트 {c_id} — 실측에 없음")
                continue
            m = CHART_VER_RE.match(releases[c_id].get("chart") or "")
            if m and not _version_matches(ver, m.group("ver")):
                report["version_mismatch"].append(
                    f"{c_id}: 문서 {comp.get('installed_by')} vs 실측 {releases[c_id]['chart']}")
    # provider 인스턴스 대조 (Name 태그 = 문서 서버 id 가정)
    for pid, prov in expected["providers"].items():
        if prov.get("kind") not in ("aws", "gcp"):
            continue
        prov_actual = actual.get("providers", {}).get(pid)
        if not prov_actual or not prov_actual.get("reachable"):
            report["unverifiable"].append(f"{pid}: provider 수집 실패 — 확인 불가")
            continue
        instances = set(prov_actual.get("instances", []))
        doc_servers = {s_id for s_id, s in expected["servers"].items() if s.get("provider") == pid}
        for name in sorted(instances - doc_servers):
            report["missing_in_docs"].append(f"{pid}: 인스턴스 {name} — 문서에 없음")
        for s_id in sorted(doc_servers - instances):
            report["ghost_in_docs"].append(f"{pid}: 서버 {s_id} — 실측에 없음")
    return report


def main():
    ap = argparse.ArgumentParser(description="인벤토리 vs 실제 상태 drift 대조")
    ap.add_argument("--root")
    ap.add_argument("--collect", action="store_true", help="수집 명령을 실제 실행 (read-only)")
    ap.add_argument("--mock-actual", help="수집 대신 JSON 파일 주입 (테스트용)")
    args = ap.parse_args()
    root = Path(args.root) if args.root else harness_lib.find_harness_root()
    if root is None:
        print("하네스를 찾지 못했습니다 — 하네스 디렉터리에서 실행하거나 --root를 지정하세요.")
        return 1
    expected = build_expected(root)
    if args.mock_actual:
        actual = json.loads(Path(args.mock_actual).read_text(encoding="utf-8"))
    elif args.collect:
        actual = collect(root)
    else:  # dry: 수집 명령만 보여준다
        print("# 수집 명령 (read-only)")
        for item in build_collect_commands(root):
            print(f"[{item['target']}/{item['kind']}] {' '.join(item['cmd'])}")
        return 0
    report = diff_state(expected, actual)
    print(f"# sync 결과 — {root}")
    for key, title in (("missing_in_docs", "실제에만 있음(문서 누락)"), ("ghost_in_docs", "문서에만 있음(유령)"),
                       ("version_mismatch", "버전 불일치"), ("unverifiable", "확인 불가")):
        print(f"## {title}: {len(report[key])}건")
        for line in report[key]:
            print(f"- {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `bash tests/run_tests.sh`
Expected: PASS

- [ ] **Step 6: 커밋**

```bash
git add scripts/sync_snapshot.py tests/test_sync.py tests/fixtures/mock-actual.json
git commit -m "feat: sync drift 대조 스크립트 추가

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: PostToolUse hook

**Files:**
- Create: `hooks/hooks.json`
- Create: `hooks/scripts/change_reminder.py`
- Create: `tests/fixtures/harness-off/harness.yaml`
- Test: `tests/test_change_reminder.py`

**Interfaces:**
- Consumes: fixture `harness-ok`(change_reminder: true). 추가로 이 태스크에서 `tests/fixtures/harness-off/`(change_reminder: false인 harness.yaml 1파일) 생성.
- Produces: PostToolUse(Bash) hook. stdin JSON(`cwd`, `tool_input.command`) → mutating이면 stdout에 `hookSpecificOutput.additionalContext` JSON, 아니면 무출력. **항상 exit 0**. `change_reminder.py`는 harness_lib를 import하지 않는 독립 실행형(플러그인 배포 경로 문제 회피).

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/fixtures/harness-off/harness.yaml`:

```yaml
sharing: local
secrets_mode: none
environments: [prod]
policies:
  mutating:
    prod: confirm
hooks:
  change_reminder: false
```

`tests/test_change_reminder.py`:

```python
import json
import subprocess
import sys
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = PLUGIN_ROOT / "hooks" / "scripts" / "change_reminder.py"
OK = PLUGIN_ROOT / "tests" / "fixtures" / "harness-ok"
OFF = PLUGIN_ROOT / "tests" / "fixtures" / "harness-off"


def run_hook(cwd, command, raw=None):
    payload = raw if raw is not None else json.dumps(
        {"hook_event_name": "PostToolUse", "cwd": str(cwd), "tool_name": "Bash",
         "tool_input": {"command": command}})
    return subprocess.run([sys.executable, str(SCRIPT)], input=payload,
                          capture_output=True, text=True)


class TestChangeReminder(unittest.TestCase):
    def assert_reminded(self, r):
        self.assertEqual(r.returncode, 0)
        out = json.loads(r.stdout)
        self.assertIn("change", out["hookSpecificOutput"]["additionalContext"])

    def assert_silent(self, r):
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "")

    def test_kubectl_apply_reminds(self):
        self.assert_reminded(run_hook(OK, "kubectl --context prod-k8s apply -f d.yaml"))

    def test_helm_upgrade_reminds(self):
        self.assert_reminded(run_hook(OK, "helm --kube-context prod-k8s upgrade vm vm/victoria-metrics-single"))

    def test_rollout_restart_reminds(self):
        self.assert_reminded(run_hook(OK, "kubectl --context prod-k8s rollout restart deploy/api"))

    def test_terraform_apply_reminds(self):
        self.assert_reminded(run_hook(OK, "terraform apply -auto-approve"))

    def test_argocd_sync_reminds(self):
        self.assert_reminded(run_hook(OK, "argocd app sync my-app"))

    def test_readonly_silent(self):
        self.assert_silent(run_hook(OK, "kubectl --context prod-k8s get pods -A"))

    def test_rollout_status_silent(self):
        self.assert_silent(run_hook(OK, "kubectl --context prod-k8s rollout status deploy/api"))

    def test_dry_run_silent(self):
        self.assert_silent(run_hook(OK, "kubectl --context prod-k8s apply --dry-run=client -f d.yaml"))

    def test_reminder_off_silent(self):
        self.assert_silent(run_hook(OFF, "kubectl --context prod-k8s apply -f d.yaml"))

    def test_outside_harness_silent(self):
        self.assert_silent(run_hook("/", "kubectl apply -f d.yaml"))

    def test_broken_stdin_exit0(self):
        self.assert_silent(run_hook(OK, "", raw="not-json"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `bash tests/run_tests.sh`
Expected: FAIL — change_reminder 케이스들이 `FileNotFoundError`(스크립트 없음)로 실패

- [ ] **Step 3: hook 구현**

`hooks/hooks.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/change_reminder.py"
          }
        ]
      }
    ]
  }
}
```

`hooks/scripts/change_reminder.py`:

```python
#!/usr/bin/env python3
"""PostToolUse(Bash) hook — mutating 인프라 명령 실행 후 변경 기록 리마인드.

독립 실행형(다른 모듈 import 없음). 어떤 경우에도 exit 0 (비차단 — 스펙 D6).
"""
import json
import re
import sys
from pathlib import Path

MUTATING = [
    r"\bterraform\s+.*\b(apply|destroy|import|taint|untaint)\b",
    r"\bterraform\s+.*\bstate\s+(mv|rm|push)\b",
    r"\bkubectl\b.*\b(apply|create|delete|patch|replace|scale|edit|label|annotate|cordon|uncordon|drain|taint)\b",
    r"\bkubectl\b.*\brollout\s+(restart|undo|pause|resume)\b",
    r"\bhelm\b.*\b(install|upgrade|uninstall|rollback)\b",
    r"\bhelm\s+delete\b",
    r"\bargocd\s+app\s+(sync|delete|set|patch|rollback)\b",
]
REMINDER = ("방금 mutating 인프라 명령이 실행되었습니다. "
            "changes/에 변경 기록을 남기세요 — change 스킬 (/infra:change). 롤백 방법 필수.")


def find_harness_root(start):
    cur = Path(start).resolve()
    for p in [cur, *cur.parents]:
        if (p / "harness.yaml").is_file():
            return p
    return None


def reminder_enabled(root):
    # 간이 판독: harness.yaml 전체에서 change_reminder 값만 읽는다 (독립 실행형 유지)
    try:
        text = (root / "harness.yaml").read_text(encoding="utf-8")
    except OSError:
        return True
    m = re.search(r"^\s*change_reminder\s*:\s*(true|false)\b", text, re.MULTILINE)
    return m is None or m.group(1) == "true"


def main():
    try:
        data = json.load(sys.stdin)
        command = str(data.get("tool_input", {}).get("command", ""))
        cwd = data.get("cwd") or "."
        if "--dry-run" in command:
            return
        if not any(re.search(p, command) for p in MUTATING):
            return
        root = find_harness_root(cwd)
        if root is None or not reminder_enabled(root):
            return
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": REMINDER,
            }
        }, ensure_ascii=False))
    except Exception:
        pass  # 어떤 오류도 세션에 영향 주지 않는다


if __name__ == "__main__":
    main()
    sys.exit(0)
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `bash tests/run_tests.sh`
Expected: PASS (test_change_reminder 11케이스 포함 전체 OK)

- [ ] **Step 5: 커밋**

```bash
git add hooks/ tests/test_change_reminder.py tests/fixtures/harness-off/
git commit -m "feat: mutating 변경기록 리마인드 hook 추가

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 7: 스킬 검증 테스트 + init SKILL.md

**Files:**
- Create: `skills/init/SKILL.md`
- Test: `tests/test_skills.py`

**Interfaces:**
- Consumes: `harness_lib.parse_frontmatter`, `templates/`(Task 2), `scripts/audit.py`(Task 4).
- Produces: `tests/test_skills.py`의 `SKILLS` 리스트 — 이후 태스크(8~11)는 이 리스트에 스킬 이름을 추가하는 것으로 실패 테스트를 만든다.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_skills.py`:

```python
import sys
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import harness_lib  # noqa: E402

# 태스크 진행에 따라 스킬 이름을 추가한다 (Task 8: register, lookup / Task 9: change, decide
# / Task 10: connect, ops / Task 11: sync, audit)
SKILLS = ["init"]


class TestSkills(unittest.TestCase):
    def _skill_path(self, name):
        return PLUGIN_ROOT / "skills" / name / "SKILL.md"

    def test_skill_files_exist(self):
        for name in SKILLS:
            self.assertTrue(self._skill_path(name).is_file(), f"{name}: SKILL.md 없음")

    def test_frontmatter_name_and_description(self):
        for name in SKILLS:
            fm = harness_lib.parse_frontmatter(self._skill_path(name).read_text(encoding="utf-8"))
            self.assertEqual(fm.get("name"), name)
            desc = str(fm.get("description", ""))
            self.assertGreaterEqual(len(desc), 80, f"{name}: description이 3요소를 담기에 너무 짧음")

    def test_principles_and_harness_discovery_mentioned(self):
        for name in SKILLS:
            body = self._skill_path(name).read_text(encoding="utf-8")
            self.assertIn("원칙", body, f"{name}: 적용 원칙 명시 없음")
            self.assertIn("harness.yaml", body, f"{name}: 하네스 발견 규약 언급 없음")


class TestOpsReferences(unittest.TestCase):
    def test_references_exist_when_ops_added(self):
        if "ops" not in SKILLS:
            self.skipTest("ops 미구현")
        for ref in ("kubectl", "argocd", "prometheus", "helm"):
            p = PLUGIN_ROOT / "skills" / "ops" / "references" / f"{ref}.md"
            self.assertTrue(p.is_file(), f"references/{ref}.md 없음")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `bash tests/run_tests.sh`
Expected: FAIL — `init: SKILL.md 없음`

- [ ] **Step 3: skills/init/SKILL.md 작성**

frontmatter는 아래 전문을 그대로 사용한다:

```yaml
---
name: init
description: 인프라 하네스 저장소(서버·k8s·컴포넌트 인벤토리 + 변경기록 + 정책)를 새로 스캐폴딩하거나 기존 하네스를 점검·확장한다. "인프라 하네스 만들어줘", "인프라 관리 시작하고 싶어", "하네스 초기화" 같은 요청에 사용. 로컬 CLI를 스캔해 확인 인터뷰 후 골격만 생성한다. 개별 서버·컴포넌트 등록은 register, 정합성 검증만 원하면 audit.
---
```

본문(한국어)에 반드시 포함할 요소 — 스펙 §7.1의 6단계를 이 순서대로 절차화한다:

1. **적용 원칙** 섹션: 원칙 1(시크릿 값 미독취 — credentials·kubeconfig raw 읽기 금지, 메타데이터 명령만), 2(sharing별 시크릿 저장 규칙), 3(묻기 전에 스캔), 8(정책은 harness.yaml 데이터로).
2. **기존 하네스 감지**: cwd에서 상향 탐색으로 harness.yaml 발견 시 → 새로 만들지 않고 `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audit.py --root <발견경로>` 실행 후 구조 점검·누락 보완(빠진 디렉토리·템플릿) 제안으로 전환.
3. **자동 발견** — 아래 명령만 사용(각 CLI는 `command -v <cli>`로 존재 확인 후):
   - `aws configure list-profiles` / `gcloud config configurations list` / `kubectl config get-contexts -o name` / `ssh-keygen -lf <파일>` (`~/.ssh/*.pub` 각각) / terraform·ansible·docker·helm·argocd는 설치 여부만.
   - **금지 명령 명시**: `cat ~/.aws/credentials`, `cat ~/.kube/config` 등 raw 파일 읽기.
4. **확인 인터뷰**: AskUserQuestion으로 한 턴에 2~3개씩 — ① 발견된 profile/context 중 관리 대상 선택 ② 미발견 provider(온프렘 등) 수동 추가 여부 ③ sharing(local/git/shared-drive) + secrets_mode — 원칙 2의 유효 조합만 선택지로 제시(shared 계열이면 plaintext 옵션 제외) ④ environments 목록 ⑤ IaC 레포 등록 ⑥ change_reminder 활성화.
5. **스캐폴딩**: `${CLAUDE_PLUGIN_ROOT}/templates/`에서 복사·치환 — 디렉토리(providers/ inventory/components/ access/ changes/ decisions/ runbooks/), 선택된 provider마다 provider.md, harness.yaml, CLAUDE.md(harness-CLAUDE.md 템플릿), `.claude/settings.json`(settings.json 템플릿 그대로 — deny 병기), `.gitignore`(gitignore 템플릿; encrypted 모드면 재포함 줄 주석 해제), secrets_mode ≠ none이면 `secrets/` 생성, `decisions/ADR-0001-harness-init.md`(adr.md 템플릿 — 인터뷰 결정·근거 기록). `configs/`는 만들지 않는다(원칙 5 — 필요 시점에 생성).
6. **마무리**: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audit.py --root <하네스>` 1회 실행, 결과 보고 후 "서버·컴포넌트는 register로 등록하세요" 안내. 전수 등록을 강요하지 않는다.
7. **에러 처리**: CLI 부재 시 해당 provider 발견을 건너뛰고 수동 추가 안내.

- [ ] **Step 4: 테스트 통과 확인**

Run: `bash tests/run_tests.sh`
Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add skills/init/ tests/test_skills.py
git commit -m "feat: init 스킬 추가

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 8: register + lookup SKILL.md

**Files:**
- Create: `skills/register/SKILL.md`, `skills/lookup/SKILL.md`
- Modify: `tests/test_skills.py` (SKILLS 리스트)

**Interfaces:**
- Consumes: `templates/`의 엔티티 템플릿, `harness_lib` 규약(id=파일명), Task 7의 SKILLS 리스트.
- Produces: 없음 (말단 스킬).

- [ ] **Step 1: 실패 테스트 — SKILLS 확장**

`tests/test_skills.py`의 리스트를 다음으로 수정:

```python
SKILLS = ["init", "register", "lookup"]
```

Run: `bash tests/run_tests.sh`
Expected: FAIL — `register: SKILL.md 없음`

- [ ] **Step 2: skills/register/SKILL.md 작성**

frontmatter 전문:

```yaml
---
name: register
description: 인프라 하네스 인벤토리에 서버·k8s 클러스터·컴포넌트·provider·키 메타데이터를 등록해 엔티티 파일을 만든다. "이 서버 등록해줘", "클러스터 추가해줘", 서버 목록·스프레드시트를 붙여넣는 일괄 등록 요청에 사용. 스캔으로 후보를 먼저 제안한다. 등록된 것 조회는 lookup, 하네스 골격 생성은 init, 문서-실제 대조는 sync.
---
```

본문 필수 요소:

1. **적용 원칙**: 1(키는 위치 참조만 기록), 3(묻기 전에 스캔), 5(managed_by는 엔티티별).
2. **공통 규약**: harness.yaml 상향 탐색, 미발견 시 init 안내 후 중단.
3. **대화형 모드**: type 선택(server/k8s-cluster/component/provider/key) → `${CLAUDE_PLUGIN_ROOT}/templates/<type>.md` 골격으로 필수 필드 인터뷰(AskUserQuestion 2~3개씩) → id=파일명 규칙으로 `providers/` 또는 `inventory/`(component는 `inventory/components/`)에 생성. key는 `access/keys.md` 표에 행 추가.
4. **스캔 우선**: k8s-cluster 등록 직후 `helm --kube-context <c> list -A`와 `kubectl --context <c> get ns`로 컴포넌트 후보를 표로 제안. server 등록 시 access에 ssh가 있으면(사용자 동의 후) `ssh -i <키경로> <호스트> 'systemctl list-units --type=service --state=running; docker ps --format {{.Names}}'` 스캔 제안 — 키 경로는 keys.md 참조로 조립.
5. **일괄 모드**: 붙여넣은 텍스트에서 (id, env, purpose, provider, runtime 등) 열 추정 → 파싱 결과를 초안 표로 제시 → 사용자 확인 후 일괄 생성 → 요약 보고.
6. **검증**: env가 harness.yaml environments에 없으면 추가 여부 확인. 생성 후 `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audit.py` 실행 권고.
7. **명명 규약**: sync 대조를 위해 컴포넌트 id는 helm 릴리스 이름과, 서버 id는 클라우드 Name 태그와 일치시키도록 안내(불일치 시 sync에서 유령/누락으로 보고됨을 설명).
8. **MCP 구성(스펙 §4.3)**: 컴포넌트 접근에 MCP를 쓰는 경우 `.mcp.json`은 하네스에 보관하되 토큰 등 값은 `${VAR}` 환경변수 참조로만 쓰고 값 자체는 secrets 정책(원칙 2)을 따르게 안내.

- [ ] **Step 3: skills/lookup/SKILL.md 작성**

frontmatter 전문:

```yaml
---
name: lookup
description: 인프라 하네스(서버·k8s 클러스터·컴포넌트·키 인벤토리)에서 접속 방법·위치·구성 정보를 조회해 답한다. "prod DB 어떻게 붙어?", "argocd 어디 떠 있어?", "vm 토큰 어디 있어?" 같은 질문에 사용. 키·토큰은 값이 아니라 위치 참조와 사용 명령만 답한다. 명령 실행은 ops, 로컬 접근 재구성은 connect, 새 엔티티 등록은 register.
---
```

본문 필수 요소:

1. **적용 원칙**: 1(값 대신 위치 참조 + 사용 명령 — 예: "vm 토큰은 `secrets/vm-token.txt`에 있고 `curl -H "Authorization: Bearer ${VM_TOKEN}"` 형태로 사용, `VM_TOKEN=$(cat ...)` 같은 값 노출 지시는 금지"), 4(하네스는 색인 — 실제 상태 질문이면 ops로 확인 제안).
2. **절차**: 질의 키워드로 `providers/`·`inventory/`·`access/keys.md` grep → 엔티티 frontmatter + provider의 cli_profile/context + keys 참조를 조합해 응답. 접근 방법 질문이면 실행 가능한 명령 형태(`ssh -i ~/.ssh/deploy-key ec2-user@...`, `kubectl --context prod-k8s ...`)로 제시.
3. **에러 처리**: 깨진 참조는 경고와 함께 가능한 범위로 응답하고 audit 권고. 해당 엔티티가 없으면 register 안내.

- [ ] **Step 4: 테스트 통과 확인**

Run: `bash tests/run_tests.sh`
Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add skills/register/ skills/lookup/ tests/test_skills.py
git commit -m "feat: register·lookup 스킬 추가

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 9: change + decide SKILL.md

**Files:**
- Create: `skills/change/SKILL.md`, `skills/decide/SKILL.md`
- Modify: `tests/test_skills.py`

**Interfaces:**
- Consumes: `templates/change.md`, `templates/adr.md`, SKILLS 리스트.
- Produces: change 절차 — Task 10의 ops가 "mutating 완료 후 change 절차 수행"으로 참조.

- [ ] **Step 1: 실패 테스트 — SKILLS 확장**

```python
SKILLS = ["init", "register", "lookup", "change", "decide"]
```

Run: `bash tests/run_tests.sh`
Expected: FAIL — `change: SKILL.md 없음`

- [ ] **Step 2: skills/change/SKILL.md 작성**

frontmatter 전문:

```yaml
---
name: change
description: 인프라 변경 내역을 하네스 changes/에 날짜 기반 기록으로 남긴다. "방금 작업 기록 남겨줘", mutating 작업(kubectl apply, helm upgrade, terraform apply 등) 직후, hook의 변경기록 리마인드가 떴을 때 사용. 대화 맥락에서 대상·명령·결과를 자동으로 채우고 롤백 방법을 반드시 확인한다. 기술 의사결정 기록은 decide, 명령 실행 자체는 ops.
---
```

본문 필수 요소:

1. **적용 원칙**: 8, 9(기록은 작업의 부산물 — ops 파이프라인·hook에서 유도됨), changes/가 변경 이력의 SSOT.
2. **절차**: `${CLAUDE_PLUGIN_ROOT}/templates/change.md` 기반으로 `changes/YYYY/MM-DD-slug.md` 생성(연도 디렉토리 자동 생성, slug는 변경 내용 요약 kebab-case). 대화 맥락에서 date/targets(엔티티 id)/변경 내용/실행 명령(--context·--profile 포함 그대로)/결과를 자동 채움. **롤백 방법이 비어 있으면 반드시 사용자에게 묻고, 답을 받기 전에 완료 처리하지 않는다.**
3. **append-only**: 기존 change 파일은 수정하지 않는다. 정정도 새 기록으로.
4. 같은 날 같은 slug 충돌 시 `-2` 접미사.

- [ ] **Step 3: skills/decide/SKILL.md 작성**

frontmatter 전문:

```yaml
---
name: decide
description: 인프라 기술 의사결정을 ADR로 하네스 decisions/에 기록한다. "이 결정 ADR로 남겨줘", "DB 이중화 방식 결정한 거 문서화해줘"처럼 구조·기술 선택을 남길 때 사용. 상태·맥락·결정·대안·결과를 채우고 관련 change 기록과 상호 링크한다. 개별 변경 작업의 실행 기록은 change.
---
```

본문 필수 요소: 원칙 9 / `decisions/` 스캔으로 최대 번호+1 → `ADR-NNNN-slug.md`(4자리 0패딩) / `templates/adr.md` 채움 / 관련 change가 대화에 있으면 "관련 기록"에 상대 경로 링크 + 해당 change 파일에도 ADR 링크 추가 제안.

- [ ] **Step 4: 테스트 통과 확인**

Run: `bash tests/run_tests.sh`
Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add skills/change/ skills/decide/ tests/test_skills.py
git commit -m "feat: change·decide 스킬 추가

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 10: connect + ops SKILL.md + references 4종

**Files:**
- Create: `skills/connect/SKILL.md`, `skills/ops/SKILL.md`
- Create: `skills/ops/references/kubectl.md`, `skills/ops/references/argocd.md`, `skills/ops/references/prometheus.md`, `skills/ops/references/helm.md`
- Modify: `tests/test_skills.py`

**Interfaces:**
- Consumes: change 절차(Task 9), harness.yaml `policies.mutating`, SKILLS 리스트.
- Produces: 없음 (말단 스킬).

- [ ] **Step 1: 실패 테스트 — SKILLS 확장**

```python
SKILLS = ["init", "register", "lookup", "change", "decide", "connect", "ops"]
```

Run: `bash tests/run_tests.sh`
Expected: FAIL — `connect: SKILL.md 없음` 및 `references/kubectl.md 없음`

- [ ] **Step 2: skills/connect/SKILL.md 작성**

frontmatter 전문:

```yaml
---
name: connect
description: 하네스에 기록된 access_recipe를 실행해 k8s 클러스터·서버의 로컬 접근을 재구성한다. "이 클러스터 kubeconfig 잡아줘", "접속 설정 다시 해줘", 새 머신 세팅이나 자격 만료 후 접근 복구에 사용. 실행 전 레시피를 보여주고 진행한다. 접속 방법이 뭔지 묻는 질문은 lookup, 구성된 접근으로 명령 실행은 ops.
---
```

본문 필수 요소: 원칙 1(레시피 실행은 자격증명 생성 도구 위임 — kubeconfig 내용을 읽지 않음)·3·6 / 절차: 엔티티의 `access_recipe` 표시 → 사용자 확인 → 실행 → 검증(`kubectl --context <c> get nodes` 등 read-only) / 온프렘 레시피(파일 복사형)는 절차 안내만 하고 kubeconfig 내용을 컨텍스트로 가져오지 않는다 / CLI 부재 시 설치 안내.

- [ ] **Step 3: skills/ops/SKILL.md 작성**

frontmatter 전문:

```yaml
---
name: ops
description: 하네스 엔티티(서버·k8s 클러스터·컴포넌트)를 대상으로 kubectl·helm·argocd·PromQL·클라우드 CLI 명령을 context/profile 명시로 실행한다. "이 클러스터 프로메테우스 버전 확인해줘", "파드 상태 봐줘", "디플로이 재시작해줘" 같은 실제 조회·조작 요청에 사용. read-only는 즉시, mutating은 env 정책에 따라 승인 후 실행하고 변경 기록 초안을 남긴다. 위치·접속법 질문만이면 lookup, 접근 자체가 안 되면 connect.
---
```

본문 필수 요소 — 스펙 §7.5 파이프라인 그대로:

1. **적용 원칙**: 1, 4, 6, 7, 8, 9.
2. **대상 해석**: 요청에서 엔티티 id 식별(모호하면 lookup 방식으로 후보 제시) → server는 provider의 cli_profile + access, k8s-cluster는 context, component는 runs_on 체인을 따라 env·context/profile 해석(스펙 D5) + endpoint/access.
3. **read/mutating 분류**: 분류 기준은 references의 도구별 표를 따른다. 애매하면 mutating으로 취급.
4. **정책 적용**: harness.yaml `policies.mutating.<env>` — `allow`면 진행, `confirm`이면 AskUserQuestion으로 대상 id·env·전체 명령을 보여주고 승인. **env가 정책에 없으면 confirm**(스펙 D4).
5. **실행**: 모든 명령에 `--context`/`--kube-context`/`--profile` 명시. 시크릿 필요 시 참조 실행만(`ssh -i <경로>`, `${VAR}`, `sops exec-env <파일> '<명령>'`, `op run -- <명령>`) — 값을 echo·cat 하는 형태 금지.
6. **검증**: mutating 후 rollout status·헬스체크 등 대응 read-only 명령.
7. **기록**: mutating 완료(성공·실패 모두) 시 change 스킬 절차로 초안 자동 생성.
8. **references 로드**: kubectl 작업 전 `references/kubectl.md`, helm은 `references/helm.md`, argocd는 `references/argocd.md`, PromQL/victoria-metrics는 `references/prometheus.md`를 읽는다.

- [ ] **Step 4: references 4종 작성**

각 파일은 ① read-only/mutating 분류표 ② context/profile 명시 형태 ③ 참조 실행 예시 ④ 검증 명령을 담는다. 다음 내용을 기반으로 작성:

`references/kubectl.md`:

````markdown
# kubectl 조작 지식 (ops용)

모든 명령에 `--context <엔티티의 context>`를 명시한다. 현재 컨텍스트 의존 금지 (원칙 6).

## read-only (즉시 실행)
get, describe, logs, top, events, api-resources, `rollout status`, `rollout history`, `auth can-i`

## mutating (정책 승인 파이프라인)
apply, create, delete, patch, replace, scale, edit, label, annotate, cordon, uncordon, drain, taint,
`rollout restart|undo|pause|resume`, exec(대상 상태를 바꿀 수 있으므로 mutating 취급)

## 예시
- 조회: `kubectl --context prod-k8s -n monitoring get pods`
- 변경: `kubectl --context prod-k8s -n app rollout restart deploy/api`
- 검증: `kubectl --context prod-k8s -n app rollout status deploy/api --timeout=120s`

## 주의
- `--dry-run=client|server`는 read-only 취급이지만 결과 확인 용도로만.
- 컴포넌트의 namespace는 엔티티 frontmatter의 `namespace:`를 사용한다.
````

`references/helm.md`:

````markdown
# helm 조작 지식 (ops용)

모든 명령에 `--kube-context <엔티티의 context>`를 명시한다 (원칙 6).

## read-only
list, status, get(values|manifest|notes), history, show, search, template(렌더만)

## mutating
install, upgrade, uninstall, rollback

## 예시
- 버전 확인: `helm --kube-context prod-k8s list -A` (installed_by와 대조)
- 업그레이드: `helm --kube-context prod-k8s -n monitoring upgrade vm vm/victoria-metrics-single --version 0.9.1`
- 검증: `helm --kube-context prod-k8s -n monitoring status vm` + 해당 파드 rollout status

## 주의
- upgrade 전 `helm ... get values`로 현재 값 확인, `--reuse-values` 여부를 사용자와 확인.
- 값 파일에 시크릿이 필요하면 `sops exec-env` 또는 `--set-file <경로>` 참조 실행만.
````

`references/argocd.md`:

````markdown
# argocd 조작 지식 (ops용)

서버 지정: 컴포넌트 엔티티의 `endpoint`를 `--server <endpoint>`로 명시 (원칙 6).
인증(원칙 1 — 값 노출 금지): `--auth-token ${ARGOCD_AUTH_TOKEN}` 환경변수 참조,
또는 토큰 없이 kubectl 자격 재사용: `--port-forward --port-forward-namespace argocd --kube-context <c>`
(port-forward 모드에서도 컨텍스트를 명시한다 — 원칙 6).

## read-only
app list, app get, app history, app diff, proj list, cluster list

## mutating
app sync, app delete, app set, app patch, app rollback

## 예시
- 조회: `argocd --server argocd.example.com --auth-token ${ARGOCD_AUTH_TOKEN} app list`
- 동기화: `argocd --server argocd.example.com --auth-token ${ARGOCD_AUTH_TOKEN} app sync my-app`
- 검증: `argocd ... app get my-app` (Health/Sync 상태 확인)
````

`references/prometheus.md`:

````markdown
# prometheus / victoria-metrics 조작 지식 (ops용)

엔드포인트는 컴포넌트 엔티티의 `endpoint`, 토큰은 keys.md 참조 위치에서 환경변수로만 (원칙 1).

## read-only (PromQL API — 전부 read-only)
- 즉시 쿼리: `curl -sf -H "Authorization: Bearer ${VM_TOKEN}" "${ENDPOINT}/api/v1/query?query=up"`
- 범위 쿼리: `.../api/v1/query_range?query=...&start=...&end=...&step=...`
- 메타: `/api/v1/labels`, `/api/v1/label/<name>/values`, `/api/v1/targets`(prometheus),
  victoria-metrics 상태: `/metrics`, vmui: `${ENDPOINT}/vmui`

## mutating
v0.1 범위에서는 없음 — admin API(tsdb delete 등)는 ops로 실행하지 않고 runbook으로 안내한다.

## 주의
- 토큰 값을 명령에 직접 붙여넣지 않는다. `VM_TOKEN` 환경변수가 없으면 사용자에게
  `export VM_TOKEN=$(...)` 준비를 요청하되 그 실행은 사용자가 한다.
- 버전 확인: `curl -sf "${ENDPOINT}/api/v1/status/buildinfo"` (victoria-metrics도 호환 제공)
````

- [ ] **Step 5: 테스트 통과 확인**

Run: `bash tests/run_tests.sh`
Expected: PASS (TestOpsReferences 포함)

- [ ] **Step 6: 커밋**

```bash
git add skills/connect/ skills/ops/ tests/test_skills.py
git commit -m "feat: connect·ops 스킬과 도구 references 추가

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 11: sync + audit SKILL.md

**Files:**
- Create: `skills/sync/SKILL.md`, `skills/audit/SKILL.md`
- Modify: `tests/test_skills.py`

**Interfaces:**
- Consumes: `scripts/sync_snapshot.py` CLI(Task 5), `scripts/audit.py` CLI(Task 4), SKILLS 리스트.
- Produces: 없음 (말단 스킬 — 전체 9종 완성).

- [ ] **Step 1: 실패 테스트 — SKILLS 확장**

```python
SKILLS = ["init", "register", "lookup", "change", "decide", "connect", "ops", "sync", "audit"]
```

Run: `bash tests/run_tests.sh`
Expected: FAIL — `sync: SKILL.md 없음`

- [ ] **Step 2: skills/sync/SKILL.md 작성**

frontmatter 전문:

```yaml
---
name: sync
description: 하네스 인벤토리 문서와 실제 인프라 상태(클라우드 인스턴스·k8s 노드·helm 릴리스)를 read-only로 대조해 drift(문서 누락·유령 항목·버전 불일치)를 보고한다. "문서랑 실제 상태 맞는지 확인해줘", "인벤토리 최신이야?", 정기 점검 요청에 사용. 자동 수정하지 않고 확인받은 항목만 문서에 반영한다. 문서 자체의 정합성 검사는 audit, 개별 조작은 ops.
---
```

본문 필수 요소: 원칙 1·3·4·6 / 절차: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sync_snapshot.py --root <하네스>` (dry)로 수집 명령을 먼저 보여주고 → 사용자 확인 후 `--collect` 실행(read-only만, --profile/--context 명시됨) → 4구획 리포트(누락/유령/버전 불일치/확인 불가) 보고 → **자동 수정 금지**: 반영할 항목을 사용자와 하나씩 확인해 인벤토리 문서 갱신(신규는 register 절차, 유령은 삭제 대신 본문에 사유 기록 제안) / 확인 불가 항목은 connect로 접근 복구 제안 / 대조 명명 규약(helm 릴리스 이름 == 컴포넌트 id, Name 태그 == 서버 id — Task 5 규약) 불일치가 의심되면 오탐 가능성을 함께 알림.

- [ ] **Step 3: skills/audit/SKILL.md 작성**

frontmatter 전문:

```yaml
---
name: audit
description: 하네스 문서 자체의 정합성 — 스키마 필수 필드, id-파일명 일치, 엔티티 참조 무결성, secrets/ 밖 시크릿 패턴 유출, sharing·secrets_mode 정책 조합, 키·인증서 만료 임박 — 을 검증한다. "하네스 점검해줘", "시크릿 유출 없나 확인해줘", init·register 직후 확인에 사용. 실제 인프라와의 대조는 sync, 문제 수정 자체는 각 스킬(register 등)로.
---
```

본문 필수 요소: 원칙 1·2·8 / 절차: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audit.py --root <하네스>` 실행 → FAIL/WARN을 항목별로 해설하고 수정 방법 제안(깨진 참조 → register/문서 수정, 시크릿 검출 → 값 제거·위치 참조로 교체·해당 키 로테이션 권고, 정책 위반 → harness.yaml 수정 또는 암호화 전환 안내) / exit 1이면 "실패" 상태임을 명확히 보고 / 시크릿 검출 시 **검출된 값 자체를 재출력하지 않는다** — 파일·패턴 종류만 언급.

- [ ] **Step 4: 테스트 통과 확인**

Run: `bash tests/run_tests.sh`
Expected: PASS (SKILLS 9종 전체)

- [ ] **Step 5: 커밋**

```bash
git add skills/sync/ skills/audit/ tests/test_skills.py
git commit -m "feat: sync·audit 스킬 추가

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 12: README + 수동 검증 체크리스트 + 최종 점검

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: 전체 산출물.
- Produces: 설치·사용 문서, 스펙 §12 수동 시나리오 체크리스트.

- [ ] **Step 1: README.md 작성**

포함 요소 (한국어):

1. 개요: 플러그인 목적(지식·기록·조작), 플러그인 vs 하네스 인스턴스 구분, 하네스는 중앙 1개.
2. 설치: `claude --plugin-dir /path/to/infra` (개발), marketplace 등록 시 `/plugin` 안내. 개발 루프: `/reload-plugins`.
3. 시작하기: 하네스로 쓸 빈 디렉토리에서 세션 열기 → "인프라 하네스 만들어줘"(init) → register로 등록 → 이후 자연어 사용 예시 표(발화 → 스킬 9종 매핑).
4. 불변 원칙 요약(특히 원칙 1·2)과 하네스 발견 규약(하네스 안에서만 동작 — 스펙 D1).
5. 스킬 표: 이름 / 역할 한 줄 / 대표 발화.
6. 테스트: `bash tests/run_tests.sh`.
7. **수동 검증 체크리스트** — 스펙 §12의 수동 시나리오를 체크박스로: (1) 빈 디렉토리 init 자동 발견·스캐폴딩 (2) sharing/secrets_mode 질문·기록·모드별 구성 (3) 전 과정 raw 자격증명 미독취 (4) secrets/ Read 차단 + `ssh -i`·`${VAR}` 참조 실행 정상 (5) register 대화형 3종 + 일괄 (6) lookup "prod DB 접속 방법" (7) ops read 즉시/prod mutating 승인/change 초안/--context·--profile 명시 (8) sync 실환경 diff (10) hook 리마인드 on/off 스모크 (11) 자연어 3종("prod DB 어떻게 접속해?"→lookup, "이 클러스터 프로메테우스 버전 확인해줘"→ops, "방금 작업 기록 남겨줘"→change) 자동 선택.

- [ ] **Step 2: 최종 점검**

Run: `bash tests/run_tests.sh && ls .claude-plugin/plugin.json hooks/hooks.json && ls skills/*/SKILL.md | wc -l`
Expected: 테스트 전체 PASS, 두 파일 존재, `9`

Run: `git status --short`
Expected: `M README.md`만 표시 (그 외 미커밋 변경 없음)

- [ ] **Step 3: 커밋**

```bash
git add README.md
git commit -m "docs: README와 수동 검증 체크리스트 추가

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## 스펙 커버리지 매핑 (self-review용)

| 스펙 항목 | 태스크 |
|-----------|--------|
| §2 D1~D9 | D1: 전 스킬·hook 본문 / D2: 3~5 / D3: 2(템플릿)·7(init) / D4: 10(ops) / D5: 10 / D6: 6 / D7: 7~11 description / D8: 3~6 / D9: 1 |
| §3 원칙 1~10 | 각 SKILL.md "적용 원칙" 섹션(7~11), 스크립트 설계(3~6) |
| §4 스키마 | 2(템플릿), 3(fixture·REQUIRED_FIELDS) |
| §5 플러그인 구조 | 1~11 전체 |
| §6 공통 규약 | 7~11 각 SKILL.md 공통 요소 |
| §7 스킬 9종 | 7(init), 8(register·lookup), 9(change·decide), 10(connect·ops), 11(sync·audit) |
| §8 scripts | 3(harness_lib), 4(audit), 5(sync) |
| §9 hooks | 6 |
| §10 templates | 2 |
| §11 에러 처리 | 각 스킬 본문 + 스크립트 main |
| §12 검증 | 3~6(자동), 12(수동 체크리스트) |
