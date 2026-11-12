# superdomain 0.9.0 ADR 이유 기록 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** adr 스킬과 템플릿을 "결정마다 이유·버린 안·비용을 붙인 이유의 기록" 형식으로 바꾸고, 그 변경을 Codex 전환본과 porting 기록에 반영해 0.9.0으로 올린다.

**Architecture:** 이 플러그인에는 실행 코드가 없다. 산출물은 마크다운(스킬, 템플릿, 컨벤션, README, CHANGELOG)과 JSON 매니페스트다. 문구는 스펙의 인용 블록을 글자 그대로 옮기고, 이 계획은 스펙이 정하지 않은 것(파일의 조립 순서, 지금 문구에서 남길 줄, 검사 명령, 시험 재료)을 정한다. 템플릿과 스킬의 초안을 먼저 쓰고, 하위 에이전트로 시험한 뒤 나머지 파일로 넘어간다.

**Tech Stack:** Claude Code 플러그인(SKILL.md, `.claude-plugin/plugin.json`), Codex 전환본(`plugins/superdomain-codex`), 검증에 `claude plugin validate`, `python3`, `node`(`ajv`·`js-yaml`), `git`. 검사 명령은 그 자리에서 실행만 하고 파일로 남기지 않는다.

**Spec:** `plugins/superdomain/docs/superpowers/specs/2026-11-11-superdomain-adr-reason-record-design.md` (근거인 ADR 개선 검토는 저장소에 두지 않는다)

## Global Constraints

- **전제:** 0.8.0(`2026-11-10-superdomain-external-conciseness-design.md`)이 먼저 적용돼 있어야 한다. 아래 "시작 전 확인"이 실패하면 멈춘다.
- **스크립트 0개.** 플러그인과 전환본에 스크립트, 색인 파일, 파서를 더하지 않는다.
- **바꾸지 않는 파일:** `skills/review/SKILL.md`, `agents/domain-reviewer.md`, `agents/convention-reviewer.md`, `skills/domain/domain-guide.md`.
- **바꾸지 않는 문구:** 쓰는 기준의 세 신호("되돌리는 비용이 크다.", "실제로 여러 대안 중에서 골랐다.", "나중에 누군가 \"왜?\"라고 물을 것이다.")와 "판단이 서지 않으면 쓴다.", 제안 모드의 문단, 파일 이름 `yyyy-MM-dd-slug.md`, 경로 `docs/superdomain/adr/`.
- **포인터 줄(POINTER).** 원본의 두 곳(`skills/adr/SKILL.md`, `skills/domain/SKILL.md`)에 아래 줄이 글자 그대로 들어간다. 181자다.

  ```
  - 결정 기록: docs/superdomain/adr/ (정해진 구조·정책을 바꾸는 제안을 하거나 받으면 먼저 관련 기록을 찾아 읽는다. 비싸거나 중요한 결정을 내린 작업을 마치면 /superdomain:adr로 기록할지 제안한다. 기록에는 결정마다 이유·버린 안·비용을 적고, 결정이 아닌 코드 이름과 절차는 적지 않는다)
  ```

- **분량:** 결정 블록 하나 1,000자(공백 포함, 링크 주소·목록 기호·`바뀜` 줄 제외). `skills/adr/SKILL.md`는 150줄 이하.
- **문구 규칙:** 모든 문서는 한국어로 쓴다. 예시는 일반 도메인(order, payment, coupon)으로 쓴다. superdomain 문서에 다른 플러그인의 이름과 특정 프로젝트의 식별자를 쓰지 않는다. 설계 문서를 가리킬 때는 "설계 문서"라고 한다.
- **버전:** 원본과 전환본 모두 `0.9.0`.
- **전환본:** `adr-template.md`와 `conventions.md`는 원본과 바이트가 같아야 한다.
- **브랜치와 커밋:** 작업 브랜치는 `feat/superdomain-adr-reason-record`다. 커밋 메시지는 Conventional Commits 접두사와 한국어 문장이고 범위에 플러그인 이름을 적는다. 마지막 줄은 세션의 커밋 귀속 지시를 따른다. 태스크 끝의 커밋 단계는 사용자가 커밋을 허락한 경우에만 한다. 허락이 없으면 변경을 작업 트리에 두고 다음 태스크로 간다. push와 PR은 하지 않는다.
- **`check_repository.py`:** Task 7에서 기준 상태를 다시 만들기 전까지 원본 변경을 보고하며 실패한다. 그 전의 실패는 예상된 것이다.
- **이 계획과 스펙도 원본 폴더 안에 있다.** 원본 기준 상태에 들어가므로, Task 7 Step 3에서 후보 스냅샷을 뜬 뒤에는 `plugins/superdomain` 아래의 어떤 파일도 고치지 않는다. 진행 표시를 이 파일에 남기려면 그 전에만 고치고, 그 뒤의 진행은 작업 목록으로만 추적한다.

## Review Focus

스펙이 암시하지만 문구만 보아서는 드러나지 않는 실패다. 각 줄의 시험은 괄호 안의 태스크에 넣었다.

1. 결정이 하나뿐인 기록에는 블록 제목이 없다. `바뀜` 줄이 머리에 붙어야 하는데 본문 중간에 붙을 수 있다. (Task 3 조정, 재료 가)
2. 폴더에 옛 형식 ADR이 있으면 새 ADR이 상태 줄과 범위·근거 머리를 본뜰 수 있다. (Task 3 쓰기)
3. 옛 형식 ADR의 결정이 바뀔 때 본문에 줄을 끼워 넣을 수 있다. 머리에만 달아야 한다. (Task 3 조정, 재료 다)
4. 사용자가 말하지 않은 버린 이유를 채우고 표시 없이 넘어갈 수 있다. (Task 3 쓰기)
5. 전환본에 Claude 전용 표기(`/superdomain:`, `${CLAUDE_SKILL_DIR}`, "다음 세션의 Claude")가 남을 수 있다. (Task 6 Step 6)

---

## 시작 전 확인

- [ ] **0.8.0이 적용돼 있는지 본다.**

```bash
python3 - <<'PY'
import json
from pathlib import Path
assert json.loads(Path('plugins/superdomain/.claude-plugin/plugin.json').read_text())['version'] == '0.8.0'
assert json.loads(Path('plugins/superdomain-codex/plugin.json').read_text())['version'] == '0.8.0'
assert '역할·기능·분류·패키지·규칙·관계' in Path('plugins/superdomain/skills/adr/SKILL.md').read_text(encoding='utf-8')
print('PASS')
PY
```

Expected: `PASS`. 실패하면 0.8.0을 먼저 구현해야 하므로 멈추고 사용자에게 알린다.

- [ ] **브랜치를 만든다.** `main`에서 `feat/superdomain-adr-reason-record`를 딴다. 스펙·검토서·이 계획이 아직 커밋되지 않았으면 첫 커밋으로 넣는다(`docs(superdomain): ADR 0.9.0 검토서·스펙·계획 추가`).

---

### Task 1: `adr-template.md` 새 판

**Files:**
- Modify: `plugins/superdomain/skills/adr/adr-template.md` (전체를 다시 쓴다)

**Interfaces:**
- Produces: 절 제목 `## 형식`, `## 예시`, `## 결정이 바뀌었을 때`, `## 적지 않는 것`, `## 분량`. Task 2의 스킬이 "템플릿 '결정이 바뀌었을 때'"와 "적지 않는 것과 분량은 템플릿을 따른다"로 이 절들을 가리킨다.

- [ ] **Step 1: 검사를 돌려 실패를 확인한다**

```bash
python3 - <<'PY'
import re
from pathlib import Path
t = Path('plugins/superdomain/skills/adr/adr-template.md').read_text(encoding='utf-8')
for h in ['## 형식', '## 예시', '## 결정이 바뀌었을 때', '## 적지 않는 것', '## 분량']:
    assert h in t, h
for gone in ['proposed', 'accepted', 'superseded', '## 상태']:
    assert gone not in t, gone
ex = t.split('## 예시')[1].split('```markdown')[1].split('```')[0]
blocks = re.split(r'^## ', ex, flags=re.M)[1:]
assert len(blocks) == 2
for b in blocks:
    lines = [re.sub(r'\]\([^)]*\)', ']', re.sub(r'^- ', '', l)) for l in b.split('\n') if l.strip() and not l.startswith('- 바뀜')]
    assert len('\n'.join(lines)) <= 1000
print('PASS')
PY
```

Expected: `AssertionError: ## 형식`

- [ ] **Step 2: 파일을 다시 쓴다**

아래 순서로 조립한다. 스펙의 인용 블록은 줄 머리의 `> `를 빼고 글자 그대로 옮긴다.

| 자리 | 내용 |
|---|---|
| `# ADR 템플릿` 아래 | "ADR은 결정을 내린 때의 이유를 남기는 기록이다. 지금 따를 규칙은 DOMAIN.md와 지침 파일에 있고, 여기에는 저장소 다른 곳에 없는 것(이유, 버린 안, 받아들인 비용, 바뀐 관계)만 적는다." |
| `## 형식` | 스펙 §4.1의 첫 코드 블록, 이어서 칸 설명 일곱 항목 |
| `## 예시` | 스펙 §4.1의 둘째 코드 블록(주문 취소) |
| `## 결정이 바뀌었을 때` | 스펙 §4.2의 다섯 항목 |
| `## 적지 않는 것` | 스펙 §4.3의 표 |
| `## 분량` | 스펙 §4.4의 문단 |

지금 파일의 `## 상태` 표, 머리 링크 설명, 옛 템플릿 블록은 모두 지운다.

- [ ] **Step 3: 검사를 다시 돌린다**

Step 1의 명령. Expected: `PASS`

- [ ] **Step 4: 커밋**

```bash
git add plugins/superdomain/skills/adr/adr-template.md
git commit -m "feat(superdomain): ADR 템플릿을 결정 블록과 적지 않는 것으로 다시 쓴다"
```

---

### Task 2: `adr/SKILL.md` 새 판

**Files:**
- Modify: `plugins/superdomain/skills/adr/SKILL.md` (전체를 다시 쓴다)

**Interfaces:**
- Consumes: Task 1의 절 제목.
- Produces: 모드 이름 `신규`·`바꿈`·`제안`, 절 번호 1~6, POINTER. Task 4·6이 POINTER와 "5절 찾아 읽기"를 가리킨다.

- [ ] **Step 1: 검사를 돌려 실패를 확인한다**

```bash
python3 - <<'PY'
import re
from pathlib import Path
t = Path('plugins/superdomain/skills/adr/SKILL.md').read_text(encoding='utf-8')
assert t.count('\n') <= 150
heads = re.findall(r'^## .*$', t, re.M)
assert heads == ['## 1. 모드', '## 2. 신규', '## 3. 바꿈', '## 4. 고쳐도 되는 것', '## 5. 찾아 읽기', '## 6. 후속 제안', '## 하지 않는 것'], heads
for keep in ['되돌리는 비용이 크다.', '실제로 여러 대안 중에서 골랐다.', '나중에 누군가 "왜?"라고 물을 것이다.', '판단이 서지 않으면 쓴다.', '역할·기능·분류·패키지·규칙·관계', '이유와 버린 안은 ADR에 둔다']:
    assert keep in t, keep
for gone in ['proposed', 'accepted', 'superseded', '승인', '부분 조정', '40~60줄', '한 번에 하나씩', '상태 규칙']:
    assert gone not in t, gone
p = [l.strip() for l in t.split('\n') if l.strip().startswith('- 결정 기록:')]
assert len(p) == 1 and len(p[0]) == 181, (len(p), [len(x) for x in p])
assert '쓰지 않는 예' in t and '기록해 둔 결정이 바뀌었을 때' in t.split('---')[1]
print('PASS')
PY
```

Expected: `AssertionError`와 지금 파일의 절 제목 목록

- [ ] **Step 2: 파일을 다시 쓴다**

frontmatter는 이렇게 둔다.

```
---
name: adr
description: 비싸거나 중요한 결정을 docs/superdomain/adr/에 ADR(결정 기록)로 남긴다. 되돌리기 비싸거나, 여러 대안 중에서 골랐거나, 나중에 누군가 "왜?"라고 물을 결정을 내렸을 때, 작업을 마쳤는데 그런 결정이 있었을 때(기록 제안), 기록해 둔 결정이 바뀌었을 때, 정해진 것을 바꾸기 전에 관련 기록을 찾아볼 때 사용한다. "ADR 써줘", "결정 기록", "왜 이렇게 했는지 남겨줘", "이 결정 바뀌었어", "전에 왜 이렇게 정했지" 같은 요청이 해당한다.
---
```

본문은 아래 순서로 조립한다. "지금 파일"은 0.8.0을 적용한 뒤의 `SKILL.md`다.

| 자리 | 내용 |
|---|---|
| `# 결정 기록 (ADR)` 아래 | 스펙 §5.1의 두 인용 문단. 이어서 "작업 기준은 git 루트다(`git rev-parse --show-toplevel`). 템플릿은 `${CLAUDE_SKILL_DIR}/adr-template.md`에 있으니 쓰기 전에 읽는다." |
| `## 1. 모드` | 스펙 §5.2의 표. 지금 파일의 "**제안**: …" 문단을 그대로. 그 아래 "바꾸려는 결정에 이미 `바뀜` 줄과 새 기록 링크가 있거나 기록에 `대체됨` 줄이 있으면, 링크를 따라가 지금 유효한 기록의 결정을 대상으로 한다." |
| `## 2. 신규` | "먼저 `docs/superdomain/adr/`의 기존 기록을 훑는다(5절). 기록해 둔 결정을 바꾸는 것이면 신규가 아니라 바꿈을 제안한다. 같은 주제의 기록이 있어도 결정을 새로 더하는 것이면 바꿈이 아니라 새 기록으로 쓴다." 지금 파일의 1번 항목(세 신호와 그 아래 문장)을 그대로. 1번 안에 스펙 §5.3의 예시 인용 블록을 들여 쓴다. 스펙 §5.3의 2~9번. 절 끝에 "형식을 따로 정하는 것은 지침 파일뿐이다. 지침 파일이 ADR 형식을 정했으면 그것을 따른다. 폴더의 옛 기록이나 ADR에 적힌 형식 결정은 본으로 삼지 않는다." |
| `## 3. 바꿈` | 스펙 §5.4의 다섯 항목 |
| `## 4. 고쳐도 되는 것` | 스펙 §5.5의 세 항목 |
| `## 5. 찾아 읽기` | 스펙 §5.6의 문단과 네 항목 |
| `## 6. 후속 제안` | 지금 파일의 첫 항목을 그대로. 포인터 줄 항목은 지금 문구에서 코드 블록의 줄만 POINTER로 바꾸고, 항목 끝에 "옛 줄이 있으면 새 줄로 바꿀지 묻는다."를 더한다 |
| `## 하지 않는 것` | 스펙 §5.7의 여섯 항목 |

지금 파일의 `## 3. 승인`, `## 4. 대체`, `## 5. 부분 조정`과 인터뷰 표는 지운다.

- [ ] **Step 3: 검사를 다시 돌린다**

Step 1의 명령. Expected: `PASS`

- [ ] **Step 4: 매니페스트 검사**

Run: `claude plugin validate .`
Expected: `✔ Validation passed`

- [ ] **Step 5: 커밋**

```bash
git add plugins/superdomain/skills/adr/SKILL.md
git commit -m "feat(superdomain): adr 스킬을 신규·바꿈·제안과 찾아 읽기로 다시 쓴다"
```

---

### Task 3: 구현 전 시험

스펙 §8의 네 시험이다. 재료와 산출물은 `${TMPDIR:-/tmp}/superdomain-090` 아래에 두고 저장소에 넣지 않는다(셸 변수는 명령 사이에 남지 않으므로 명령마다 `T`를 다시 정한다). 시험 대상 에이전트에게는 통과 기준을 알려 주지 않는다. 시험마다 새 하위 에이전트를 쓴다.

**Files:**
- Modify: `plugins/superdomain/docs/superpowers/specs/2026-11-11-superdomain-adr-reason-record-design.md` (끝에 `## 11. 구현 전 시험 결과` 절을 더한다)
- Modify: Task 1·2의 두 파일(시험이 실패했을 때만)

**Interfaces:**
- Consumes: Task 1·2의 두 파일.
- Produces: 스펙 §11의 결과 표. 리뷰어 짝 검사를 다시 정해야 하는지의 판정.

- [ ] **Step 1: 재료를 만든다**

`$T/project/docs/superdomain/adr/` 아래에 셋을 둔다.

재료 가(결정 하나, 새 형식) `2026-02-03-no-retry-on-payment-call.md`:

```markdown
# 결제 호출은 클라이언트에서 재시도하지 않는다

- 날짜: 2026-02-03
- 지금 규칙이 있는 곳: 지침 파일의 "외부 호출" 절

PG 호출이 실패하면 주문을 결제 대기로 두고 사용자가 다시 시도한다.
- 이유: 응답을 받지 못한 요청이 PG에서 승인됐을 수 있어, 다시 보내면 이중 결제가 된다.
- 버린 안: 3회까지 자동 재시도 — PG가 멱등 키를 지원하지 않는다
- 비용: 일시적인 장애에도 사용자가 다시 눌러야 한다
```

재료 나(결정 둘, 새 형식) `2026-03-11-cancel-before-shipping-and-refund-by-payment.md`: 템플릿 `## 예시`의 블록에서 `- 바뀜` 줄만 뺀 것.

재료 다(옛 형식): `~/Projects/noguesstoday/docs/superdomain/adr/2026-10-12-no-client-retry.md`를 그대로 복사한다(읽기만 한다).

`$T/project/AGENTS.md`에는 POINTER 한 줄만 둔다. `$T/plugin/`에 Task 1·2의 두 파일을 복사한다.

- [ ] **Step 2: 조정 시험**

조건은 둘이다. **스킬 조건**은 에이전트에게 `$T/plugin/SKILL.md`를 따르라고 한다. **포인터 조건**은 따르라고 하지 않고, 세션에 쓸 수 있는 스킬 목록으로 `adr`의 description과 파일 위치만 알려 준다. 조건마다 `$T/project`의 사본에서 아래 넷을 차례로 시킨다(에이전트 2개).

| 변경 | 요청 |
|---|---|
| 뒤집힘 | "PG가 멱등 키를 지원하게 돼서 결제 호출을 2회까지 자동으로 재시도하기로 했어. 기록해 줘." |
| 좁혀짐 | "주문 취소를 배송 시작 전까지가 아니라 출고 지시 전까지만 받기로 했어. 새 ADR까지는 필요 없어." |
| 이름만 바뀜 | "`RefundService`를 `RefundExecutor`로 이름을 바꿨어. 문서도 맞춰 줘." |
| 옛 형식 | 재료 다의 번호 결정 하나를 골라 "이 결정을 <반대 내용>으로 바꾸기로 했어. 기록해 줘." |

통과 기준(사본의 `git diff`와 파일을 직접 읽어 판정한다):

- 뒤집힘: 재료 가의 **머리**에 `- 바뀜(날짜): …` 줄이 있고 새 파일 링크가 달렸다(결정이 하나뿐인 기록에는 `대체됨`을 쓰지 않는다). 새 파일의 `버린 안`에 재료 가의 링크와 "따르다가 버렸다"가 있다. 재료 가의 다른 줄은 그대로다.
- 좁혀짐: 재료 나의 `## 1.` 제목 **바로 아래**에 링크 없는 `바뀜` 줄이 있다. 새 파일은 없다. 다른 줄은 그대로다.
- 이름만 바뀜: `docs/superdomain/adr/` 아래의 어느 파일도 바뀌지 않았다.
- 옛 형식: 재료 다의 **머리**에 결정 번호와 "무엇이 무엇으로"가 적힌 줄이 더해졌다. 첫 `## ` 뒤의 본문은 한 글자도 바뀌지 않았다.

- [ ] **Step 3: 블록만 읽기 시험**

1. 에이전트 하나가 `~/Projects/noguesstoday/docs/superdomain/adr/`의 `2026-10-12-no-client-retry.md`, `2026-10-19-market-indicator-boundary.md`, `2026-10-20-instrument-surrogate-identity-and-identifier-table.md`를 템플릿 형식으로 옮겨 `$T/converted/`에 쓴다. 원문에 있는 내용만 쓰고 문제는 보지 않는다.
2. 다른 에이전트 하나가 원문 셋을 읽고 ADR마다 문제 다섯을 낸다(결정 2, 버린 안 2, 상태·조정 1). 문항마다 정답 요지, 근거 줄, 해당하는 결정 번호를 적는다.
3. ADR마다 에이전트 둘이 답한다. 하나는 옮긴 파일 전체를 읽고, 하나는 문항마다 해당 결정 블록(`## N.`부터 다음 `## ` 앞까지)만 받는다. 문서에 없으면 "문서에 없음"이라고 답하게 한다.
4. 정답 키와 견줘 정답·부분·오답·없다고 답함으로 채점한다.

통과 기준: 블록만 받은 답에 오답이 없다. 머리(`정하지 않은 것`, `대체됨`)에만 있는 내용 때문에 갈린 문항 수를 따로 센다.

- [ ] **Step 4: 판단 시험**

에이전트 하나에게 `$T/plugin/SKILL.md`를 주고 아래 여섯을 ADR로 쓸지 판단하게 한다.

1. "회원 식별자를 이메일에서 내부 번호로 바꾸고 기존 데이터를 옮겼다."
2. "알림 발송을 주문 처리와 같은 트랜잭션에서 하지 않고 큐로 넘기기로 했다. 같은 트랜잭션 안에서 보내는 안, 스케줄러가 주기적으로 훑는 안과 견줬다."
3. "환율을 유료 공급사 대신 중앙은행 공시값으로 받기로 했다. 실시간 값은 포기했다."
4. "PG 호출의 읽기 타임아웃을 5초에서 8초로 올렸다."
5. "주문 목록 조회에서 한 번에 가져오는 크기를 지정했다. 그 조회 메서드에만 해당한다."
6. "주문 번호는 날짜와 일련번호로 만든다. 다른 안은 견주지 않았고 치르는 비용도 없다."

통과 기준: 1~3은 쓴다고 판단한다. 3을 "예시 표에 없으니 쓰지 않는다"고 하지 않는다. 4는 코드와 설정, 5는 코드 주석, 6은 DOMAIN.md `규칙`이나 지침 파일의 한 줄을 대신 남길 곳으로 말한다.

- [ ] **Step 5: 쓰기 시험**

에이전트 하나에게 `$T/project`의 사본(옛 형식 재료 다가 폴더에 있다)과 `$T/plugin/`을 주고, 아래 대화를 방금 끝난 논의로 주면서 ADR 초안과 승인 화면에 보일 글을 쓰게 한다.

```
사용자: 주문을 취소할 때 쓴 쿠폰을 어떻게 할지 정하자.
Claude: 세 가지가 있습니다. 항상 되돌린다, 유효기간이 남았을 때만 되돌린다, 되돌리지 않는다.
사용자: 유효기간이 남았을 때만 되돌리자. 항상 되돌리면 만료된 쿠폰이 살아나서 안 돼. 만료 직전에 쓴 고객은 취소하면 쿠폰을 잃는데 그건 받아들이자.
Claude: 되돌리는 일은 coupon이 하고 order는 취소 이벤트만 내면 될까요?
사용자: 응, 그렇게.
Claude: CouponRestoreHandler가 order_cancelled 이벤트를 받아 처리하고, 실패하면 3회 재시도하게 하겠습니다.
사용자: 좋아. 그리고 쿠폰 코드는 대문자로 저장하자.
```

통과 기준:

- 새 형식이다. 상태 줄과 범위·근거 머리가 없다(옛 형식 재료를 본뜨지 않았다).
- `CouponRestoreHandler`, `order_cancelled`, "3회"가 초안에 없다.
- "되돌리지 않는다"는 버린 안의 이유를 지어내지 않았다. 사용자에게 묻거나, 채운 문장으로 요지에 따로 나온다.
- "coupon이 되돌리고 order는 이벤트만 낸다"는 버린 안도 비용도 없으므로 블록으로 서지 않았다.
- "쿠폰 코드는 대문자로 저장"은 ADR에 블록으로 들어가지 않았다.
- 승인 화면의 글이 결정문 목록과 채운 문장을 먼저 보이고 전문을 그 아래에 둔다. 블록이 1,000자 이하다.

- [ ] **Step 6: 실패한 시험을 고친다**

스펙 §8 표의 "실패하면" 칸을 따른다. 템플릿이나 스킬의 문구를 고쳤으면 스펙 §4·§5의 해당 인용 블록도 같은 문구로 고치고, 실패한 시험만 다시 한다. 포인터 조건에서만 실패한 조정 시험은 문구를 고치지 않고 결과를 적는다.

- [ ] **Step 7: 결과를 스펙에 적는다**

스펙 끝에 `## 11. 구현 전 시험 결과`를 더한다. 시험·조건별로 통과 여부, 실패한 항목, 고친 문구를 표로 적는다. 포인터 조건의 조정 시험이 실패했으면 "리뷰어 짝 검사를 다시 정한다"를 적고 사용자에게 알린다.

- [ ] **Step 8: 커밋**

```bash
git add plugins/superdomain/docs/superpowers/specs/2026-11-11-superdomain-adr-reason-record-design.md plugins/superdomain/skills/adr
git commit -m "docs(superdomain): ADR 새 형식의 구현 전 시험 결과를 스펙에 적는다"
```

---

### Task 4: domain 스킬, 컨벤션, README

**Files:**
- Modify: `plugins/superdomain/skills/domain/SKILL.md` (8단계의 포인터 줄, 수정 모드 1번)
- Modify: `plugins/superdomain/skills/conventions/conventions.md` (「아키텍처 규칙은 테스트로 강제한다」의 한 항목, 「자명하지 않은 규칙은 KDoc으로 남긴다」의 끝)
- Modify: `plugins/superdomain/README.md` (스킬 표의 adr 행, 산출물 표의 ADR 행)

**Interfaces:**
- Consumes: POINTER.

- [ ] **Step 1: 검사를 돌려 실패를 확인한다**

```bash
python3 - <<'PY'
from pathlib import Path
P = Path('plugins/superdomain')
d = (P / 'skills/domain/SKILL.md').read_text(encoding='utf-8')
c = (P / 'skills/conventions/conventions.md').read_text(encoding='utf-8')
r = (P / 'README.md').read_text(encoding='utf-8')
p = [l.strip() for l in d.split('\n') if l.strip().startswith('- 결정 기록:')]
assert len(p) == 1 and len(p[0]) == 181
assert '관련 기록을 찾아 읽고, 버린 안을 되살리는 변경이면 사용자에게 알린다' in d
assert '이유를 남긴다(KDoc·주석·ADR)' not in c
assert '날짜가 아니라 파일 이름으로 적고' in c and 'KDoc에는 그 파일 이름을 적는다' in c
assert 'ADR을 승인·대체할 때' not in r and '기록해 둔 결정이 바뀌었을 때' in r
assert '결정 기록(결정마다 이유·버린 안·받아들인 비용)' in r
print('PASS')
PY
```

Expected: `AssertionError`

- [ ] **Step 2: `domain/SKILL.md`를 고친다**

- 8단계 코드 블록의 `- 결정 기록: …` 줄을 POINTER로 바꾼다(들여쓰기는 그대로).
- 8단계의 "옛 줄이 있으면 바꿀지 묻는다"가 도메인 정의 줄만 가리키면 두 줄 모두를 가리키게 고친다.
- 수정 모드 1번 끝에 더한다: "규칙·관계를 바꾸는 변경이면 `docs/superdomain/adr/`에서 관련 기록을 찾아 읽고, 버린 안을 되살리는 변경이면 사용자에게 알린다."

- [ ] **Step 3: `conventions.md`를 고친다**

- "규칙에 예외를 더하거나 규칙을 지우는 변경에는 이유를 남긴다(KDoc·주석·ADR)."을 스펙 §6의 인용 문단 세 문장으로 바꾼다. 같은 줄의 뒤 문장("테스트를 통과시키려고 …")은 그대로 둔다.
- 「자명하지 않은 규칙은 KDoc으로 남긴다」의 본문 끝에 더한다: "여러 클래스에 걸친 결정이면 이유는 ADR에 두고 KDoc에는 그 파일 이름을 적는다."

- [ ] **Step 4: `README.md`를 고친다**

- 스킬 표의 adr 행 설명: "비싸거나 중요한 결정을 기록하거나, 기록해 둔 결정이 바뀌었을 때, 정해진 것을 바꾸기 전에 관련 기록을 찾을 때. 작업을 마칠 때 기록할 결정이 있으면 먼저 제안한다"
- 산출물 표의 ADR 행 설명: "결정 기록(결정마다 이유·버린 안·받아들인 비용)"

- [ ] **Step 5: 검사를 다시 돌린다**

Step 1의 명령. Expected: `PASS`

- [ ] **Step 6: 커밋**

```bash
git add plugins/superdomain/skills/domain/SKILL.md plugins/superdomain/skills/conventions/conventions.md plugins/superdomain/README.md
git commit -m "feat(superdomain): 포인터 줄에 읽는 때를 더하고 이유를 남기는 자리를 가른다"
```

---

### Task 5: CHANGELOG와 버전

**Files:**
- Modify: `plugins/superdomain/CHANGELOG.md` (0.8.0 절 위에 0.9.0 절)
- Modify: `plugins/superdomain/.claude-plugin/plugin.json` (`version`)

- [ ] **Step 1: 검사를 돌려 실패를 확인한다**

```bash
python3 - <<'PY'
import json
from pathlib import Path
P = Path('plugins/superdomain')
assert json.loads((P / '.claude-plugin/plugin.json').read_text())['version'] == '0.9.0'
c = (P / 'CHANGELOG.md').read_text(encoding='utf-8')
s = c.split('## 0.9.0')[1].split('## 0.8.0')[0]
for h in ['### Changed', '### Removed', '### 이행']:
    assert h in s, h
assert s.split('### 이행')[1].count('\n- ') == 6
print('PASS')
PY
```

Expected: `AssertionError` 또는 `IndexError`

- [ ] **Step 2: CHANGELOG에 0.9.0 절을 쓴다**

제목은 `## 0.9.0 — <오늘 날짜>`다(`date +%F`). 첫 문단: "ADR을 결정을 내린 때의 이유를 남기는 기록으로 다시 정했다. 저장소 다른 곳에 있는 것은 적지 않고, 결정마다 이유·버린 안·받아들인 비용을 붙인다."

| 절 | 항목 |
|---|---|
| `### Changed` | 템플릿(머리 네 줄, 결정 블록, 적지 않는 것, 글자 수 분량). adr 스킬(모드가 신규·바꿈·제안, 쓰는 예와 쓰지 않는 예, 초안 한 번, 요지를 먼저 보이는 확정, 찾아 읽기). 포인터 줄(읽는 때와 쓰기 규칙). 컨벤션(이유를 남기는 자리, ADR은 파일 이름으로 가리킨다). domain 스킬 수정 모드(관련 기록 읽기) |
| `### Removed` | 상태(`proposed`·`accepted`·`superseded`)와 승인 모드. 부분 조정과 대체 모드(`바뀜` 줄로 합침). 한 번에 하나씩 묻는 인터뷰. "한 ADR에 결정 하나". "한 화면(40~60줄)" |
| `### 이행` | 스펙 §9의 이행 안내 여섯 항목을 글자 그대로 |

- [ ] **Step 3: 버전을 올린다**

`plugins/superdomain/.claude-plugin/plugin.json`의 `"version"`을 `"0.9.0"`으로 바꾼다.

- [ ] **Step 4: 검사를 다시 돌린다**

Step 1의 명령과 `claude plugin validate .`. Expected: `PASS`, `✔ Validation passed`

- [ ] **Step 5: 커밋**

```bash
git add plugins/superdomain/CHANGELOG.md plugins/superdomain/.claude-plugin/plugin.json
git commit -m "chore(superdomain): 0.9.0 CHANGELOG와 버전"
```

---

### Task 6: Codex 전환본

절차는 `.agents/skills/claude-to-codex/SKILL.md`를 따른다. 쓰기 전에 원본·전환본·`porting/superdomain/decisions.md`를 함께 읽는다.

**Files:**
- Modify: `plugins/superdomain-codex/skills/adr/adr-template.md`, `plugins/superdomain-codex/skills/conventions/conventions.md` (원본을 복사)
- Modify: `plugins/superdomain-codex/skills/adr/SKILL.md`, `plugins/superdomain-codex/skills/adr/agents/openai.yaml`
- Modify: `plugins/superdomain-codex/skills/domain/SKILL.md`
- Modify: `plugins/superdomain-codex/README.md`, `plugins/superdomain-codex/plugin.json`

**Interfaces:**
- Consumes: Task 1~5의 원본 파일.
- Produces: Task 7이 스냅샷으로 뜨는 전환본 상태.

- [ ] **Step 1: 두 파일을 복사한다**

```bash
cp plugins/superdomain/skills/adr/adr-template.md plugins/superdomain-codex/skills/adr/adr-template.md
cp plugins/superdomain/skills/conventions/conventions.md plugins/superdomain-codex/skills/conventions/conventions.md
```

- [ ] **Step 2: `skills/adr/SKILL.md`를 합친다**

원본의 새 `SKILL.md`를 바탕으로 전환본의 변형 다섯을 다시 입힌다.

| 원본 | 전환본 |
|---|---|
| "다음 세션의 Claude다" | "다음 세션의 Codex다" |
| "템플릿은 `${CLAUDE_SKILL_DIR}/adr-template.md`에 있으니" | "템플릿은 [adr-template.md](adr-template.md)에 있으니". 다음 문단에 지금 전환본의 "이 문서의 상대 링크는 Codex가 제공한 실제 `SKILL.md` 위치를 기준으로 …" 문단을 그대로 둔다 |
| `/superdomain:domain` (2절 7번, 6절) | "superdomain의 [domain 스킬](../domain/SKILL.md)" |
| 6절 포인터 항목의 대상 지침 파일 설명 | 지금 전환본의 문구를 그대로 둔다 |
| POINTER의 "/superdomain:adr로" | "superdomain의 adr 스킬로" |

- [ ] **Step 3: `skills/adr/agents/openai.yaml`을 고친다**

`short_description`을 "중요한 결정의 이유를 ADR로 남기고, 바뀐 결정을 표시하고, 관련 기록을 찾습니다"로 바꾼다.

- [ ] **Step 4: `skills/domain/SKILL.md`를 고친다**

Task 4 Step 2의 세 가지를 같은 문장으로 넣는다. 포인터 줄은 Step 2의 전환본 줄과 글자가 같아야 한다.

- [ ] **Step 5: `README.md`와 `plugin.json`을 고친다**

- 기반 버전 **0.8.0**을 **0.9.0**으로.
- 스킬 표의 adr 행 동작: "신규·바꿈과 기록 제안, 관련 기록 찾기"
- 산출물의 ADR 줄: "`docs/superdomain/adr/yyyy-MM-dd-slug.md`: adr이 확인받은 사실과 결정만 기록한다. 병합된 기록의 문장은 보존하고 바뀐 결정에는 `바뀜` 줄을 단다."
- `plugin.json`의 `"version"`을 `"0.9.0"`으로.

- [ ] **Step 6: 검사한다**

```bash
cmp plugins/superdomain/skills/adr/adr-template.md plugins/superdomain-codex/skills/adr/adr-template.md
cmp plugins/superdomain/skills/conventions/conventions.md plugins/superdomain-codex/skills/conventions/conventions.md
python3 - <<'PY'
import json, re
from pathlib import Path
C = Path('plugins/superdomain-codex')
a = (C / 'skills/adr/SKILL.md').read_text(encoding='utf-8')
d = (C / 'skills/domain/SKILL.md').read_text(encoding='utf-8')
for gone in ['/superdomain:', '${CLAUDE_SKILL_DIR}', '다음 세션의 Claude', 'proposed', 'superseded', '승인', '부분 조정']:
    assert gone not in a, gone
pa = [l.strip() for l in a.split('\n') if l.strip().startswith('- 결정 기록:')]
pd = [l.strip() for l in d.split('\n') if l.strip().startswith('- 결정 기록:')]
assert len(pa) == 1 and pa == pd and 'superdomain의 adr 스킬로' in pa[0]
assert json.loads((C / 'plugin.json').read_text())['version'] == '0.9.0'
assert '**0.9.0**' in (C / 'README.md').read_text(encoding='utf-8')
assert '승인' not in (C / 'skills/adr/agents/openai.yaml').read_text(encoding='utf-8')
print('PASS')
PY
D=$(mktemp -d) && npm install --prefix "$D" --ignore-scripts --no-audit --no-fund --no-package-lock ajv@8.18.0 js-yaml@4.1.1 >/dev/null \
  && curl --fail --silent --show-error https://agent-plugins.org/schemas/1.0.0/plugin.schema.json --output "$D/plugin.schema.json" \
  && NODE_PATH="$D/node_modules" node porting/superdomain/validate.cjs plugins/superdomain-codex "$D/plugin.schema.json"
```

Expected: `cmp` 두 번이 아무것도 출력하지 않고, `PASS`, `validate.cjs`가 오류 없이 끝난다.

- [ ] **Step 7: 커밋**

```bash
git add plugins/superdomain-codex
git commit -m "feat(superdomain-codex): 원본 0.9.0의 ADR 형식을 반영한다"
```

---

### Task 7: porting 기록, 독립 리뷰, 기준 상태

**Files:**
- Modify: `porting/superdomain/decisions.md` (대응표의 세 줄, 끝에 0.9.0 절)
- Modify: `porting/superdomain/review.md` (끝에 리뷰 절)
- Modify: `porting/superdomain/source-state.json`, `porting/superdomain/target-state.json`

**Interfaces:**
- Consumes: Task 1~6의 모든 파일.

- [ ] **Step 1: `decisions.md`의 옛 서술을 고친다**

- 컴포넌트 대응표의 `skills/adr/SKILL.md` 행 보존 조건: "신규/바꿈/제안과 찾아 읽기, 사실 확인, 병합된 기록의 문장 보존, `바뀜` 줄과 새 기록의 짝, 포인터 동의"
- `사용자 프로젝트 출력` 행의 "기존 ADR 본문 보존"을 "병합된 ADR의 문장 보존(바뀐 결정에는 `바뀜` 줄만 더한다)"으로.
- 남은 런타임 검증 5번의 "ADR 신규·승인·대체·부분 조정에서 동의·본문 보존·양방향 링크"를 "ADR 신규·바꿈에서 동의·문장 보존·`바뀜` 줄과 새 기록의 짝"으로.

- [ ] **Step 2: `decisions.md` 끝에 `## <오늘 날짜>: 원본 0.9.0 반영`을 쓴다**

"2026-10-11: 원본 0.7.0 반영" 절과 같은 짜임으로 쓴다. 원본에서 바뀐 파일 목록, 아래 대응표, 메모 세 줄(진입점·인자·권한·트리거 경로는 그대로다. 관리 파일은 18개 그대로다. 스킬의 동작이 바뀌므로 독립 리뷰를 받는다)을 넣는다.

| 원본 | 전환본 | 처리 |
|---|---|---|
| `skills/adr/adr-template.md` | 같은 위치 | copy |
| `skills/conventions/conventions.md` | 같은 위치 | copy |
| `skills/adr/SKILL.md` | 같은 위치 | adapt (Task 6 Step 2의 변형 다섯) |
| `skills/domain/SKILL.md` 포인터 줄·수정 모드 | 같은 위치 | adapt |
| adr 스킬의 설명 | `skills/adr/agents/openai.yaml` | adapt |
| `.claude-plugin/plugin.json` 버전 | `plugin.json`, README 기반 버전 | adapt |
| `README.md`, `CHANGELOG.md`, 설계 문서 | 없음 | omit |

- [ ] **Step 3: 후보 스냅샷을 뜬다**

```bash
D="${TMPDIR:-/tmp}/superdomain-090"; mkdir -p "$D"
python3 .agents/skills/claude-to-codex/scripts/tree_state.py snapshot plugins/superdomain > "$D/source-candidate.json"
python3 .agents/skills/claude-to-codex/scripts/tree_state.py snapshot plugins/superdomain-codex --paths-file porting/superdomain/managed-paths.json > "$D/target-candidate.json"
shasum -a 256 "$D"/*.json
```

- [ ] **Step 4: 독립 리뷰를 받는다**

새 컨텍스트의 리뷰어(하위 에이전트, 읽기 전용, 추가 위임 없음)에게 원본 0.9.0의 바뀐 파일, 전환본의 바뀐 파일, `decisions.md`의 새 절, 두 후보 파일을 준다. 볼 것은 넷이다. 원본의 동작(모드, 확정 절차, 문장 보존, `바뀜` 줄)이 전환본에 그대로 있는가. Claude 전용 표기가 남지 않았는가. 전환본의 상대 링크가 풀리는가. 후보 스냅샷이 지금 파일과 같은가. must_fix가 있으면 고치고 후보를 다시 떠서 재검토를 받는다.

- [ ] **Step 5: 리뷰를 기록한다**

`review.md` 끝에 `## <오늘 날짜>: 0.9.0 반영의 독립 리뷰`를 더한다. 판정, 검토 범위, 지적과 조치 표, 리뷰한 후보의 SHA-256을 적는다. `decisions.md`의 새 절에는 판정 한 줄과 검증 결과를 적는다.

- [ ] **Step 6: 기준 상태를 확정한다**

리뷰한 후보와 지금 파일이 같은지 확인한 뒤 옮긴다.

```bash
D="${TMPDIR:-/tmp}/superdomain-090"
python3 .agents/skills/claude-to-codex/scripts/tree_state.py compare "$D/target-candidate.json" plugins/superdomain-codex
python3 .agents/skills/claude-to-codex/scripts/tree_state.py snapshot plugins/superdomain > porting/superdomain/source-state.json
python3 .agents/skills/claude-to-codex/scripts/tree_state.py snapshot plugins/superdomain-codex --paths-file porting/superdomain/managed-paths.json > porting/superdomain/target-state.json
python3 porting/superdomain/check_repository.py
```

Expected: `compare`의 `modified`·`removed`가 비어 있고, 마지막 줄이 `PASS: platform catalogs, package identity, reviewed source/target baselines, managed paths`다. 원본 폴더는 Step 3 뒤로 바뀌지 않았어야 한다(`git status --short plugins/superdomain`이 Step 3 때와 같다).

- [ ] **Step 7: 커밋**

```bash
git add porting/superdomain
git commit -m "docs(superdomain-codex): 0.9.0 전환 결정과 독립 리뷰를 기록하고 기준 상태를 갱신한다"
```

---

### Task 8: 마지막 검증

**Files:** 없음(검사만 한다)

- [ ] **Step 1: 저장소 검사**

```bash
claude plugin validate .
python3 porting/superdomain/check_repository.py
python3 porting/superdomain/check_git_scopes.py
python3 -m unittest discover -s .agents/skills/claude-to-codex/tests -q
```

Expected: 넷 모두 통과.

- [ ] **Step 2: 남은 옛 말을 찾는다**

```bash
git grep -n -E "proposed|accepted|superseded|부분 조정|40~60줄|한 번에 하나씩|승인" -- plugins/superdomain/skills/adr plugins/superdomain-codex/skills/adr
git grep -n -E "accepted|superseded|승인·대체|부분 조정" -- plugins/superdomain/README.md plugins/superdomain-codex/README.md
```

Expected: 둘 다 결과가 없다. 검색은 adr 스킬 폴더와 두 README로 좁혔다. "한 번에 하나씩"과 "승인"은 domain 스킬과 가이드의 예시에 다른 뜻으로 남아 있고, CHANGELOG와 설계 문서에도 남아 있어도 된다.

- [ ] **Step 3: 포인터 줄 네 곳을 견준다**

```bash
git grep -h -F -- "- 결정 기록: docs/superdomain/adr/" plugins/superdomain/skills plugins/superdomain-codex/skills | sed 's/^ *//' | sort | uniq -c
```

Expected: 두 줄이 나오고 각각 2회다. 원본 줄은 181자이고, 두 줄의 차이는 "/superdomain:adr로"와 "superdomain의 adr 스킬로"뿐이다.

- [ ] **Step 4: 보고한다**

바뀐 파일, 시험 결과(스펙 §11), 리뷰 판정, 통과한 검사를 사용자에게 알린다. push와 PR, 태그는 사용자가 요청할 때만 한다.
