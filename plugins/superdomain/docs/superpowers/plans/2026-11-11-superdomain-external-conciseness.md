# superdomain 0.8.0 외부 정의·간결성 기준 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 도메인 가이드에 `외부`를 맡는 도메인의 기준과 간결하게 쓰는 기준을 넣고, domain 스킬·리뷰어·컨벤션을 거기에 맞춰 0.8.0으로 올린 뒤 Codex 전환본과 porting 기록에 반영한다.

**Architecture:** 이 플러그인에는 실행 코드가 없다. 산출물은 마크다운과 JSON 매니페스트다. 가이드의 문구는 스펙 §4의 인용 블록을 글자 그대로 옮기고, 스킬과 리뷰어는 스펙 §5·§6의 문장을 그 자리의 지시문으로 옮긴다. 이 계획은 어느 줄을 지우고 어디에 넣는지, 무엇으로 검사하는지를 정한다. 가이드와 리뷰어를 고친 뒤 실제 프로젝트 두 곳의 DOMAIN.md에 리뷰어를 돌려 기준이 뜻대로 움직이는지 본다.

**Tech Stack:** Claude Code 플러그인(SKILL.md, subagent 마크다운, `.claude-plugin/plugin.json`), Codex 전환본(`plugins/superdomain-codex`), 검증에 `claude plugin validate`, `python3`, `node`(`ajv`·`js-yaml`), `git`. 검사 명령은 그 자리에서 실행만 하고 파일로 남기지 않는다.

**Spec:** `plugins/superdomain/docs/superpowers/specs/2026-11-10-superdomain-external-conciseness-design.md` (근거는 같은 폴더의 `2026-11-10-superdomain-improvements-review.md`)

## Global Constraints

- **스크립트 0개.** 템플릿 파일, DOMAIN.md 파싱, 분량을 재는 스크립트를 더하지 않는다.
- **바꾸지 않는 것:** `skills/review/SKILL.md`. 가이드 「관계의 방향」의 규칙 1~4와 "관계가 어긋난다"의 한 트랜잭션 허용 조건. 가이드의 `기반 도메인` 문구와 `허용 관계 테스트` 문구(끝에 한 문장만 더한다). 리뷰어의 출력 형식과 심각도 정의, frontmatter. domain 스킬 체크리스트의 단계 수(8)와 순서.
- **용어:** "조율 계층"·"조율 컴포넌트"·"위 계층(컨트롤러 …)"은 "조합 코드"로, "외부 도메인의 복잡성"은 "외부 모델의 복잡성"으로, 칸 이름 `코드`는 `패키지`로 쓴다. 새 칸 이름은 `하위 도메인`, `알려진 어긋남`, `모든 도메인이 쓰는 별도 서비스`, `의존으로 세지 않는 코드`다. `미정` 칸은 없다.
- **분량 숫자:** 패키지 한 줄 300자, 규칙 칸 합계 500자, 한 항목 120자, 관계 설명 150자, 도메인 한 섹션 1,500자(공백 포함 글자 수, 링크 주소와 목록 기호 제외).
- **포인터 줄:** `- 도메인 정의: docs/superdomain/DOMAIN.md (도메인의 역할·관계를 바꾸는 작업 전에 읽는다. 고칠 때는 /superdomain:domain으로 고친다)`
- **문구 규칙:** 모든 문서는 한국어로 쓴다. superdomain 문서에 다른 플러그인의 이름과 특정 프로젝트의 식별자를 쓰지 않는다. `SKILL.md`는 150줄 이하.
- **버전:** 원본과 전환본 모두 `0.8.0`.
- **전환본:** `domain-guide.md`, `conventions.md`, `architecture-tests.md`는 원본과 바이트가 같아야 한다.
- **브랜치와 커밋:** 작업 브랜치는 `feat/superdomain-external-conciseness`다. 커밋 메시지는 Conventional Commits 접두사와 한국어 문장이고 범위에 플러그인 이름을 적는다. 마지막 줄은 세션의 커밋 귀속 지시를 따른다. 태스크 끝의 커밋 단계는 사용자가 커밋을 허락한 경우에만 한다. 허락이 없으면 변경을 작업 트리에 두고 다음 태스크로 간다. push와 PR은 하지 않는다.
- **`check_repository.py`:** Task 8에서 기준 상태를 다시 만들기 전까지 원본 변경을 보고하며 실패한다. 그 전의 실패는 예상된 것이다.
- **기준 상태는 `plugins/superdomain` 폴더를 파일 시스템 그대로 담는다.** 이 계획과 스펙, ADR 0.9.0의 검토서·스펙·계획도 그 안에 있다. Task 8 Step 3에서 후보 스냅샷을 뜰 때 이 폴더의 내용이 곧 커밋될 내용이어야 하고(커밋하지 않을 파일이 있으면 깨끗한 체크아웃에서 `check_repository.py`가 실패한다), 그 뒤에는 이 폴더의 어떤 파일도 고치지 않는다. 진행 표시를 이 파일에 남기려면 그 전에만 고친다.
- **다른 프로젝트는 읽기만 한다.** Task 4가 `$HOME/Projects/imstargg-v2`와 `$HOME/Projects/noguesstoday`를 읽는다. 고치지 않는다.

## Review Focus

스펙이 암시하지만 문구만 보아서는 드러나지 않는 실패다. 각 줄의 시험은 괄호 안의 태스크에 넣었다.

1. 0.7.0 형식의 DOMAIN.md(칸 이름 `코드`, `미정` 칸)를 리뷰어가 "필수 칸이 없다"고 지적한다. `패키지` 칸으로 읽고 한 번만 알려야 한다. 변경 검토와 convention-reviewer도 `코드` 칸으로 파일을 도메인에 연결해야 한다. (Task 3 Step 2, Task 5 Step 2, Task 4)
2. 글자 수를 바이트로 세어 한글 문서를 분량 초과로 지적한다. (Task 4, imstargg-v2에는 분량 지적이 없어야 한다)
3. `알려진 어긋남`에 해당하는 목록이 다른 이름의 절로 적혀 있을 때, 거기 적힌 직접 호출을 다시 지적하거나 `외부`를 더하라고 한다. (Task 4, imstargg-v2)
4. 연동만 맡는 도메인에 대한 의존을 "내부 도메인이 외부 접점 도메인에 의존한다"로 지적한다. (Task 4 Step 3, 연동 표시를 붙인 사본)
5. 전환본의 리뷰어 참고 문서에 원본의 새 검사 항목이 빠진다. (Task 7 Step 5)

---

## 시작 전 확인

- [ ] **지금 버전을 본다.**

```bash
python3 - <<'PY'
import json
from pathlib import Path
assert json.loads(Path('plugins/superdomain/.claude-plugin/plugin.json').read_text())['version'] == '0.7.0'
assert json.loads(Path('plugins/superdomain-codex/plugin.json').read_text())['version'] == '0.7.0'
print('PASS')
PY
```

Expected: `PASS`. 실패하면 이미 다른 변경이 들어간 것이므로 멈추고 사용자에게 알린다.

- [ ] **브랜치를 만든다.** `main`에서 `feat/superdomain-external-conciseness`를 딴다. `plugins/superdomain/docs/superpowers/` 아래의 커밋되지 않은 설계 문서를 모두 첫 커밋으로 넣는다(0.8.0의 검토서·스펙·계획과 ADR 0.9.0의 검토서·스펙·계획, `docs(superdomain): 0.8.0·0.9.0 검토서·스펙·계획 추가`). 0.8.0 스펙이 ADR 문서에 링크를 걸고, Task 8의 기준 상태가 폴더 전체를 담기 때문이다.

---

### Task 1: `domain-guide.md`

**Files:**
- Modify: `plugins/superdomain/skills/domain/domain-guide.md`

**Interfaces:**
- Produces: 절 이름 「DOMAIN.md 형식」, 「간결하게 쓰는 기준」, 「외부 접점」, 「관계의 방향」, 「잘못 그은 경계의 신호」. Task 2·3이 이 이름으로 가리킨다.

- [ ] **Step 1: 검사를 돌려 실패를 확인한다**

```bash
python3 - <<'PY'
import re
from pathlib import Path
t = Path('plugins/superdomain/skills/domain/domain-guide.md').read_text(encoding='utf-8')
heads = re.findall(r'^## (?![a-z]).*$', t, re.M)
assert heads == ['## DOMAIN.md 형식', '## 관계', '## 간결하게 쓰는 기준', '## 경계를 긋는 기준', '## 외부 접점', '## 관계의 방향', '## 잘못 그은 경계의 신호', '## 분류 기준', '## 같은 이름, 다른 모델'], heads
for need in ['- 패키지: order-api `com.acme.order`', '처음에는 이 뼈대만 쓴다', '**실수 시험**', '**리팩터링 시험**', '**중복 시험**', '도메인 한 섹션 1,500자', '**무엇이 외부 시스템인가.**', '**어느 도메인이 맡는가.**', '(연동: <key>)', '외부 모델의 복잡성', '조합 코드', '의존으로 세지 않는 코드', '알려진 어긋남', '하위 도메인이 있으면 기능 묶음은 하위 도메인 단위로 본다', '조합 코드의 패키지는 모듈 감지에서 뺀다', '모든 도메인이 참조: <key>', 'DOMAIN.md의 "패키지"에 그렇게 적혀 있으면']:
    assert need in t, need
for gone in ['- 코드:', '**코드**', '**미정**', '조율 컴포넌트', '외부 도메인의 복잡성', '도메인 맵(mermaid)', '**개념**(선택)', '**외부**(선택)', '**규칙**(선택)', '**하지 않는 것**(선택)', '외부 시스템과 맞닿은 코드가 있는데', 'DOMAIN.md의 "코드"에']:
    assert gone not in t, gone
for keep in ['**허용 관계 테스트**(선택)', '여러 도메인이 기대는 중심 도메인은 의존받는다', '외부 접점 도메인은 내부 도메인에 의존하고, 내부 도메인은 외부 접점 도메인을 모른다', '업무 흐름이 있으면 뒤 단계가 앞 단계에 의존한다', '원자성이 꼭 필요하면 허용한다']:
    assert keep in t, keep
order = ['소개', '제목', '역할', '기능', '분류', '패키지', '외부', '규칙', '하위 도메인', '개념', '하지 않는 것', '관계', '기반 도메인', '모든 도메인이 쓰는 별도 서비스', '의존으로 세지 않는 코드', '허용 관계 테스트', '알려진 어긋남', '개념도']
pos = [t.index(f'- **{k}**') for k in order]
assert pos == sorted(pos), pos
print('PASS')
PY
```

Expected: `AssertionError`와 지금 파일의 절 제목 목록(예시 코드 블록 안의 `## 관계`도 함께 잡힌다)

- [ ] **Step 2: 「DOMAIN.md 형식」을 고친다**

- 예시 코드 블록을 스펙 §4.1의 코드 블록으로 바꾼다.
- 그 아래에 스펙 §4.1의 첫 인용 블록("처음에는 이 뼈대만 쓴다 …"와 필요할 때만 쓰는 칸 표)을 넣는다.
- 칸 설명 목록은 아래 순서로 둔다. "(지금)"은 지금 문구를 그대로 두는 항목이고, 나머지는 스펙 §4.1 둘째 인용 블록의 문구다.

  소개 → 제목(지금) → 역할(지금) → 기능 → 분류 → 패키지 → 외부 → 규칙 → 하위 도메인 → 개념 → 하지 않는 것 → 관계 → 기반 도메인(지금) → 모든 도메인이 쓰는 별도 서비스 → 의존으로 세지 않는 코드 → 허용 관계 테스트 → 알려진 어긋남 → 개념도 → "이 밖의 절이나 칸은 …"

- **관계**는 지금 문구 뒤에 스펙의 문장("방식은 관계의 종류다 …")을 잇는다. **허용 관계 테스트**는 지금 문구(머리의 "(선택)" 포함) 끝에 "조합 코드의 패키지는 모듈 감지에서 뺀다."만 더한다.
- 지금의 **코드**·**미정** 항목과 "도메인 맵(mermaid)은 선택이다 …" 줄은 지운다. **개념**·**외부**·**규칙**·**하지 않는 것** 머리의 "(선택)"은 스펙 문구대로 없어진다.

- [ ] **Step 3: 「간결하게 쓰는 기준」을 넣는다**

「DOMAIN.md 형식」 바로 뒤, 「경계를 긋는 기준」 앞에 `## 간결하게 쓰는 기준`을 만들고 스펙 §4.2의 인용 블록을 글자 그대로 옮긴다.

- [ ] **Step 4: 「외부 접점」, 「관계의 방향」, 「잘못 그은 경계의 신호」, 「같은 이름, 다른 모델」을 고친다**

- 「외부 접점」 절 머리에 스펙 §4.3의 첫 인용 블록(무엇이 외부 시스템인가, 표, 어느 도메인이 맡는가)을 넣는다. 지금의 설명 문단과 두 복잡성은 그 뒤에 그대로 두되 "외부 도메인의 복잡성"만 "외부 모델의 복잡성"으로 바꾼다. "지키는 것"의 "외부 연동이 크면 …" 항목을 스펙 §4.3의 둘째 인용 블록으로 바꾸고, 나머지 세 항목은 그대로 둔다.
- 「관계의 방향」의 규칙 1~4는 손대지 않는다. 규칙 목록 바로 아래에 스펙 §4.4의 연동 도메인 문장을 더한다. "흐름상 내부 도메인의 일이 …" 문단을 스펙 §4.4의 조합 코드 문단으로 바꾼다.
- 「잘못 그은 경계의 신호」의 "외부 영향이 번진다" 아래 세 항목을 스펙 §4.5의 다섯 항목으로 바꾼다. "너무 크다"의 첫 항목 끝에 "하위 도메인이 있으면 기능 묶음은 하위 도메인 단위로 본다."를 더한다.
- 「같은 이름, 다른 모델」의 `DOMAIN.md의 "코드"에 그렇게 적혀 있으면`을 `DOMAIN.md의 "패키지"에 그렇게 적혀 있으면`으로 바꾼다.

- [ ] **Step 5: 검사를 다시 돌린다**

Step 1의 명령. Expected: `PASS`

- [ ] **Step 6: 커밋**

```bash
git add plugins/superdomain/skills/domain/domain-guide.md
git commit -m "feat(superdomain): 가이드에 외부를 맡는 도메인과 간결하게 쓰는 기준을 넣는다"
```

---

### Task 2: `domain/SKILL.md`

**Files:**
- Modify: `plugins/superdomain/skills/domain/SKILL.md`

**Interfaces:**
- Consumes: Task 1의 절 이름.
- Produces: 8단계의 포인터 줄(Global Constraints), 수정 모드의 단계. 0.9.0 계획이 "8단계(후속 제안)"와 "수정 모드 1번"을 가리킨다.

- [ ] **Step 1: 검사를 돌려 실패를 확인한다**

```bash
python3 - <<'PY'
import re
from pathlib import Path
t = Path('plugins/superdomain/skills/domain/SKILL.md').read_text(encoding='utf-8')
assert t.count('\n') <= 150
assert len(re.findall(r'^\d\. \*\*', t, re.M)) == 8
for need in ['역할·기능·분류·패키지', '외부 시스템과 주고받는 코드', '제품과 프로젝트의 말', '기본안', '최상위 묶음', '맡을 도메인', '어긋남 후보', '기본 뼈대', '지우는 쪽을 먼저', '6단계를 한 번 더', '고칠 때는 /superdomain:domain으로 고친다', '대화로 목록만 알린다', '기준 개념이 바뀜', '「간결하게 쓰는 기준」', '0.7.0의 형식', '리뷰어 지적을 사용자 확인 없이 반영하지 않는다', '자체 검토에 쓰는 것은 domain-reviewer 호출 하나다', '외부를 맡은 도메인이면 `외부`를 빠뜨리지 않는다', '외부를 새로 맡거나 놓으면 `외부`도 함께 고친다', '옛 줄이 있으면']:
    assert need in t, need
for gone in ['코드 위치', '역할·기능·분류·코드', '`미정`에 적는다', '개념·외부·규칙·미정', '맞닿은 도메인이면', '맞닿게 되거나', '상품 중심이냐 주문 중심이냐']:
    assert gone not in t, gone
print('PASS')
PY
```

Expected: `AssertionError: 역할·기능·분류·패키지`

- [ ] **Step 2: description과 첫 문단의 칸 이름을 고친다**

"역할·기능·분류·코드 위치"를 두 곳 모두 "역할·기능·분류·패키지"로 바꾼다.

- [ ] **Step 3: 체크리스트 1~8단계를 고친다**

스펙 §5 표의 칸에 적힌 문장을 그 단계의 지시문으로 넣는다. 표가 "지금처럼"이라고 한 부분과 표에 없는 문장(예: 5단계의 방향·기반 도메인 하위 항목, 6단계의 리뷰어 호출)은 그대로 둔다.

| 단계 | 지우는 것 | 넣는 것 |
|---|---|---|
| 1 | 없음 | 표 1행의 문장 |
| 3 | 끝 문장 "정한 것 중 핵심은 `규칙`에, 정하지 못한 것은 `미정`에 적는다." | 표 3행의 문장 전부(프로젝트의 말, 기준을 통과하는 것만 `규칙`에, 개념이 갈리는지, 그 자리에서 정한다와 기본안, 지금 정할 수 없는 것은 모아 둔다) |
| 4 | 문장 "외부 시스템을 부르거나 외부에서 호출받는 코드(외부 API 클라이언트·SDK·웹훅 수신)도 찾아, 어느 후보가 외부 접점인지 함께 보여 준다."(찾는 일은 1단계로 옮겼다) | 표 4행의 문장. 중심 후보의 예 "상품 중심이냐 주문 중심이냐"는 "주문 중심이냐 결제 중심이냐"로 바꾼다 |
| 5 | "역할·기능·분류·코드(선택: 개념·외부·규칙·미정·하지 않는 것)를 보여 주고" | "역할·기능·분류·패키지를 보여 주고"와 표 5행의 문장. "외부 시스템과 맞닿은 도메인이면 `외부`를 빠뜨리지 않는다"는 "외부를 맡은 도메인이면 `외부`를 빠뜨리지 않는다"로 바꾼다(D1). `개념` 문장과 두 하위 항목은 그대로 둔다 |
| 6 | 없음 | 표 6행의 문장 |
| 7 | 없음 | 표 7행의 문장 |
| 8 | 도메인 정의 포인터 줄 | 새 포인터 줄, "옛 줄이 있으면 바꿀지 묻는다.", 정하지 못한 정책을 알리는 두 문장 |

- [ ] **Step 4: 수정 모드와 하지 않는 것을 고친다**

- 수정 모드 1번: 괄호 안 계기에 "기준 개념이 바뀜"(스펙의 예 포함)을 더한다. 그 뒤에 스펙 §5 수정 모드 첫 항목의 둘째 문장("이때는 관계 표에서 …")과 셋째 항목(0.7.0의 형식이 남아 있으면 함께 고칠지 묻는다)을 잇는다.
- 수정 모드 2번: 첫 문장 뒤에 "고칠 때 「간결하게 쓰는 기준」을 지킨다."를 더한다. "외부 시스템과 맞닿게 되거나 떨어지면 `외부`도 함께 고친다"는 "외부를 새로 맡거나 놓으면 `외부`도 함께 고친다"로 바꾼다(D1).
- "하지 않는 것"에 스펙 §5의 세 항목을 더한다.

- [ ] **Step 5: 검사를 다시 돌린다**

Step 1의 명령과 `claude plugin validate .`. Expected: `PASS`, `✔ Validation passed`

- [ ] **Step 6: 커밋**

```bash
git add plugins/superdomain/skills/domain/SKILL.md
git commit -m "feat(superdomain): domain 스킬이 외부를 맡을 도메인을 묻고 기본 뼈대로 시작한다"
```

---

### Task 3: `domain-reviewer.md`

**Files:**
- Modify: `plugins/superdomain/agents/domain-reviewer.md`

**Interfaces:**
- Consumes: Task 1의 절 이름과 칸 이름.

- [ ] **Step 1: 검사를 돌려 실패를 확인한다**

```bash
python3 - <<'PY'
from pathlib import Path
t = Path('plugins/superdomain/agents/domain-reviewer.md').read_text(encoding='utf-8')
for need in ['뼈대에 없는 절·칸', '`패키지` 칸으로 읽고', '분량 예산', '유니코드 문자 수', '(연동: <key>)', '의존으로 세지 않는 코드:', '`알려진 어긋남`에 적힌 것은 다시 지적하지 않는다', '절 이름이 달라도', '의존받는 도메인의 상태·타입·공개 조회 동작이 바뀌면', '`규칙`에 적힌 값이 코드와 다른가', '가이드가 요구하지 않는 내용을 DOMAIN.md에 더하자는 제안', '프로젝트의 말', 'DOMAIN.md의 "패키지"(0.7.0 형식의 문서면 "코드")로', 'DOMAIN.md "패키지"에', '`패키지`에 적힌 위치가 없다', '주고받는 것이 적혀 있는가']:
    assert need in t, need
for gone in ['DOMAIN.md의 "코드"', 'DOMAIN.md "코드"', '적힌 코드 위치가 없다', '조율 계층', '외부와 맞닿을 것 같은데', '외부 시스템과 맞닿은 코드가 있는데']:
    assert gone not in t, gone
for keep in ['model: opus', '#### Critical', '심각도: Critical은']:
    assert keep in t, keep
print('PASS')
PY
```

Expected: `AssertionError: 뼈대에 없는 절·칸`

- [ ] **Step 2: 모드별 항목을 고친다**

스펙 §6의 문장을 해당 모드의 항목으로 넣는다. "잇는다"는 지금 문장을 두고 뒤에 붙이는 것이다.

정의 검토:

- 형식: 지금 문장 뒤에 스펙 §6 정의 검토 첫 항목의 문장을 잇는다.
- 정의 품질: 지금 문장 뒤에 스펙 셋째 항목(`개념`의 하위 구성 예외)과 둘째 항목(간결성 검사)을 차례로 잇는다.
- 분리·병합 신호: 그대로 둔다.
- 외부: "적힌 것이 우리가 운영하는 인프라가 아닌 외부 시스템인가"를 "적힌 것이 가이드의 판별에 맞는 외부 시스템인가"로 바꾸고 "주고받는 것이 적혀 있는가"는 둔다. 뒤 문장("역할·기능으로 보아 외부와 맞닿을 것 같은데 …")은 스펙 넷째 항목의 나머지 문장으로 바꾼다.
- 관계 표: 지금 문장 뒤에 스펙 다섯째 항목의 문장을 잇는다.

변경 검토:

- 머리 문장의 `DOMAIN.md의 "코드"로`를 `DOMAIN.md의 "패키지"(0.7.0 형식의 문서면 "코드")로`로 바꾼다.
- 의존 항목의 마지막 문장("어느 도메인에도 속하지 않는 조율 계층(컨트롤러 등)이 …")을 스펙 변경 검토 첫 항목(조합 코드)의 문장으로 바꾼다.
- 외부 항목을 스펙 둘째 항목의 문장으로 바꾼다. 끝의 `(가이드의 "외부 접점")`은 둔다.
- 외부 항목 뒤에 스펙의 새 항목 둘과 `알려진 어긋남` 항목을 더한다.

전체 점검:

- 첫 항목의 "적힌 코드 위치가 없다"를 "`패키지`에 적힌 위치가 없다"로 바꾸고, "외부 시스템과 맞닿은 코드가 있는데 그 도메인의 `외부`에 없다"는 지운다.
- 첫 항목 아래에 스펙 전체 점검의 세 항목을 더한다.

- [ ] **Step 3: 지키는 것을 고친다**

- "같은 이름, 다른 모델"의 `DOMAIN.md "코드"에` → `DOMAIN.md "패키지"에`.
- "보고하지 않는 것"에 스펙 §6의 문장("가이드가 요구하지 않는 내용을 DOMAIN.md에 더하자는 제안. 알려야 할 사실은 질문으로 남긴다")을 더한다.
- "근거 없이 지적하지 않는다" 뒤에 두 항목을 더한다: 모순을 지적할 때 제안은 한쪽을 지우는 쪽을 먼저 낸다. 지적과 질문은 프로젝트의 말로 쓰고, `기준:`에는 가이드의 절 이름을 적으며, 본문에 가이드 용어를 쓰면 한 구절로 풀어 쓴다.

- [ ] **Step 4: 검사를 다시 돌린다**

Step 1의 명령과 `claude plugin validate .`. Expected: `PASS`, `✔ Validation passed`

- [ ] **Step 5: 커밋**

```bash
git add plugins/superdomain/agents/domain-reviewer.md
git commit -m "feat(superdomain): domain-reviewer가 간결성과 외부를 맡은 도메인을 본다"
```

---

### Task 4: 두 프로젝트로 기준 확인

스펙 §10의 확인이다. 두 프로젝트를 읽기만 하고, 산출물은 `${TMPDIR:-/tmp}/superdomain-080` 아래에 둔다(셸 변수는 명령 사이에 남지 않으므로 명령마다 `T`를 다시 정한다).

**Files:**
- Modify: Task 1·3의 두 파일(기대와 다를 때만), 스펙 §2·§4·§6(숫자나 문구를 바꿨을 때만)
- Modify: `plugins/superdomain/docs/superpowers/specs/2026-11-10-superdomain-external-conciseness-design.md` (끝에 `## 11. 기준 확인 결과` 절)

**Interfaces:**
- Consumes: Task 1의 가이드, Task 3의 리뷰어.

- [ ] **Step 1: 리뷰어를 돌린다**

프로젝트마다 한 번씩 실행한다(백그라운드, 제한 10분).

```bash
T="${TMPDIR:-/tmp}/superdomain-080"; mkdir -p "$T"; R=$(git rev-parse --show-toplevel)
(cd "$HOME/Projects/imstargg-v2" && claude --plugin-dir "$R/plugins/superdomain" -p "/superdomain:review domain 전체") > "$T/imstargg.md"
(cd "$HOME/Projects/noguesstoday" && claude --plugin-dir "$R/plugins/superdomain" -p "/superdomain:review domain 전체") > "$T/noguesstoday.md"
```

noguesstoday 결과의 `기준:`에 「간결하게 쓰는 기준」이 한 번도 없으면 설치된 0.7.0이 돈 것이다. 그때와 명령이 실패할 때는 하위 에이전트 하나에게 `agents/domain-reviewer.md`의 본문을 지침으로 주고 호출 프롬프트(모드: 전체 점검, 프로젝트 루트, DOMAIN.md 경로, 기준 문서: 이 저장소의 `domain-guide.md` 절대 경로, 대상: 프로젝트 전체)로 같은 일을 시킨다. 어느 방법을 썼는지 결과에 적는다.

- [ ] **Step 2: 기대와 견준다**

스펙 §10 표의 두 행이 통과 기준이다. 항목마다 "기대대로 / 다르다"를 적는다. 프로젝트의 DOMAIN.md가 2026-11-10 뒤에 바뀌었으면(`git log -1 --format=%cs -- docs/superdomain/DOMAIN.md`) 바뀐 곳에 해당하는 항목은 그 문서에 맞춰 읽고, 그렇게 했다고 결과에 적는다.

| 대상 | 반드시 없어야 하는 지적 | 반드시 있어야 하는 지적 |
|---|---|---|
| imstargg-v2 | 분량 예산 초과. `패키지` 칸이 없다. renewal·statistics의 공식 API 직접 호출(이미 적어 둔 어긋남). `외부`를 더하라는 제안 | 옛 칸 이름 `코드`(문서에 한 번), statistics의 `미정` 칸, 클래스 이름(QueryComposer), 코드의 enum 표기, "(이벤트는 아직 구현 전)", 뼈대 밖 절과 줄. 모두 Minor |
| noguesstoday | `패키지` 칸이 없다 | 세 도메인의 규칙 칸·섹션 분량, market·provider의 `코드` 줄 분량, 두 문단인 소개, 옛 칸 이름 `코드`(한 번), 클래스·라이브러리 이름과 아키텍처 테스트 번호, 같은 외부가 연동 표시 없이 두 도메인에 적힌 것, 허용 목록 밖의 관계 방식 값 |

- [ ] **Step 3: 연동 표시를 사본으로 시험한다**

지금 noguesstoday 문서에는 `(연동: <key>)`가 없어 Review Focus 4가 걸릴 조건이 없다. 사본을 만들어 본다.

1. noguesstoday의 DOMAIN.md를 `$T/DOMAIN-linked.md`로 복사하고, market·indicator의 `외부` 하위 목록 줄마다 끝에 ` (연동: provider)`를 붙인다. 다른 줄은 건드리지 않는다.
2. 하위 에이전트 하나에게 `agents/domain-reviewer.md`의 본문을 지침으로 주고 호출 프롬프트(모드: 정의 검토, 프로젝트 루트: noguesstoday, DOMAIN.md: 사본의 절대 경로, 기준 문서: 가이드의 절대 경로)를 넘긴다. 통과 기준은 알려 주지 않는다.

Expected: "같은 외부가 연동 표시 없이 두 도메인에 적혔다"는 지적이 없다. market·indicator가 provider에 의존하는 줄을 방향이 어긋났다고 지적하지 않는다. 허용 목록 밖의 관계 방식 값은 그대로 지적한다.

- [ ] **Step 4: 다르면 고친다**

가이드나 리뷰어의 문구를 고치고 그 대상만 다시 돌린다. 스펙 §4·§6의 해당 문구도 같은 문구로 고친다. 분량 숫자를 바꿔야 하면 스펙 §2의 기본값과 §4.2, Global Constraints의 숫자를 함께 고치고 사용자에게 알린다. 세 번 고쳐도 기대와 다른 항목은 더 고치지 않고 결과에 적는다.

- [ ] **Step 5: 결과를 스펙에 적는다**

스펙 끝에 `## 11. 기준 확인 결과`를 더한다. 대상(두 프로젝트와 연동 사본)별로 기대대로 나온 항목 수, 다른 항목과 고친 문구, 쓴 방법을 표로 적는다.

- [ ] **Step 6: 커밋**

```bash
git add plugins/superdomain/docs/superpowers/specs/2026-11-10-superdomain-external-conciseness-design.md plugins/superdomain/skills/domain/domain-guide.md plugins/superdomain/agents/domain-reviewer.md
git commit -m "docs(superdomain): 두 프로젝트로 본 기준 확인 결과를 스펙에 적는다"
```

---

### Task 5: 컨벤션 쪽 문서, adr 스킬, README

**Files:**
- Modify: `plugins/superdomain/skills/conventions/conventions.md` (머리말, 「도메인 사이 의존은 한 방향으로만 둔다」, 「외부 응답과 오류는 경계에서 우리 타입으로 바꾼다」)
- Modify: `plugins/superdomain/skills/conventions/SKILL.md` (3단계의 첫 경우)
- Modify: `plugins/superdomain/agents/convention-reviewer.md` (시작 3단계, 보고하지 않는 것)
- Modify: `plugins/superdomain/skills/conventions/architecture-tests.md` (「모듈 감지」)
- Modify: `plugins/superdomain/skills/adr/SKILL.md` (6절 첫 항목)
- Modify: `plugins/superdomain/README.md` (산출물 표의 DOMAIN.md 행)

**Interfaces:**
- Produces: `adr/SKILL.md` 6절의 문장. 0.9.0 계획의 "시작 전 확인"과 Task 2 검사가 "역할·기능·분류·패키지·규칙·관계"와 "이유와 버린 안은 ADR에 둔다"를 찾는다.

- [ ] **Step 1: 검사를 돌려 실패를 확인한다**

```bash
python3 - <<'PY'
from pathlib import Path
P = Path('plugins/superdomain')
c = (P / 'skills/conventions/conventions.md').read_text(encoding='utf-8')
s = (P / 'skills/conventions/SKILL.md').read_text(encoding='utf-8')
r = (P / 'agents/convention-reviewer.md').read_text(encoding='utf-8')
a = (P / 'skills/conventions/architecture-tests.md').read_text(encoding='utf-8')
d = (P / 'skills/adr/SKILL.md').read_text(encoding='utf-8')
m = (P / 'README.md').read_text(encoding='utf-8')
assert '"외부 자원"은 우리 프로세스 밖의 자원이다.' in c and '조합 코드는 도메인 패키지 밖에 둔다' in c and '외부 모델의 복잡성' in c
assert '지금 고치는 도메인이 맡지 않은 외부 시스템과 직접 주고받게 될 때' in s and '(연동: <key>)' in s and '조합 코드' in s
assert '분류와 패키지를 읽는다' in r and '조합 코드' in r
assert '조합 코드를 둔 패키지도 역할 패키지로 보고 모듈에서 뺀다' in a and '의존으로 세지 않는 코드:' in a
assert '역할·기능·분류·패키지·규칙·관계' in d and '이유와 버린 안은 ADR에 둔다' in d
assert '역할·기능·분류·패키지(필요할 때: 외부·규칙·하위 도메인·개념·하지 않는 것·알려진 어긋남)' in m
for t in (c, s, r):
    for gone in ['조율', '위 계층(컨트롤러', '외부 도메인의 복잡성']:
        assert gone not in t, gone
print('PASS')
PY
```

Expected: `AssertionError`

- [ ] **Step 2: 여섯 파일을 고친다**

스펙 §7의 항목을 하나씩 반영한다.

- `conventions.md` 머리말의 "외부 자원" 줄을 스펙 §7의 인용 문단으로 바꾼다. 목록 기호 `- `는 그대로 둔다.
- `conventions.md` 「도메인 사이 의존은 한 방향으로만 둔다」의 "어느 도메인에도 속하지 않는 위 계층(컨트롤러나 조율 컴포넌트)이"를 "어느 도메인에도 속하지 않는 조합 코드(여러 도메인을 묶는 컨트롤러, 조회 조합, 배치 Job 구성)가"로 바꾸고, 그 항목 끝에 "조합 코드는 도메인 패키지 밖에 둔다."를 더한다.
- `conventions.md` 「외부 응답과 오류는 …」의 "외부 도메인의 복잡성"을 "외부 모델의 복잡성"으로 바꾼다.
- `conventions/SKILL.md` 3단계의 첫 경우를 아래 두 경우로 바꾼다(첫 경우의 마지막 문장은 지금 그대로다. 문구는 전체 리뷰 뒤 스펙 §7과 함께 고쳤다).

  ```
     - 지금 고치는 도메인이 맡지 않은 외부 시스템과 직접 주고받게 될 때(부르거나 외부의 호출·웹훅을 받는다): 그 외부를 맡은 도메인이 주고받게 하자고 제안한다. 내부 도메인은 외부 접점 도메인을 부르지 않으므로, 순서가 필요하면 어느 도메인에도 속하지 않는 조합 코드가 차례로 부르게 한다. 맡을 도메인이 없으면 `/superdomain:domain`으로 `외부`를 더하거나 도메인을 새로 정하자고 제안한다.
     - 지금 고치는 도메인의 `외부`에 `(연동: <key>)`로 적힌 외부 시스템과 주고받게 될 때: 직접 부르지 않고 그 연동 도메인을 부르게 한다(연동 도메인은 그 표시를 쓴 도메인에게서 의존받는다).
  ```

- `convention-reviewer.md` 시작 3단계의 "도메인별 분류와 코드 위치를 읽는다"를 "도메인별 분류와 패키지를 읽는다(0.7.0 형식의 문서면 `코드` 칸이 패키지다)"로, "보고하지 않는 것"의 "조율 계층(컨트롤러 등)"을 "조합 코드"로 바꾼다.
- `architecture-tests.md` 「모듈 감지」의 목록 끝에 "조합 코드를 둔 패키지도 역할 패키지로 보고 모듈에서 뺀다. DOMAIN.md의 `의존으로 세지 않는 코드:`와 같은 위치여야 한다."를 더한다.
- `adr/SKILL.md` 6절 첫 항목을 "결정이 도메인 정의(역할·기능·분류·패키지·규칙·관계)를 바꾸면 `/superdomain:domain`으로 DOMAIN.md를 고치자고 안내한다. DOMAIN.md에는 결론 한 문장만 반영하고(필요하면 규칙 끝에 ADR 링크 하나), 이유와 버린 안은 ADR에 둔다. DOMAIN.md는 이 스킬이 직접 고치지 않는다."로 바꾼다.
- `README.md` 산출물 표의 DOMAIN.md 행 설명을 "도메인별 역할·기능·분류·패키지(필요할 때: 외부·규칙·하위 도메인·개념·하지 않는 것·알려진 어긋남)와 도메인 간 관계"로 바꾼다.

- [ ] **Step 3: 검사를 다시 돌린다**

Step 1의 명령과 `claude plugin validate .`. Expected: `PASS`, `✔ Validation passed`

- [ ] **Step 4: 커밋**

```bash
git add plugins/superdomain/skills/conventions plugins/superdomain/agents/convention-reviewer.md plugins/superdomain/skills/adr/SKILL.md plugins/superdomain/README.md
git commit -m "feat(superdomain): 컨벤션과 리뷰어의 용어를 조합 코드와 외부를 맡은 도메인으로 맞춘다"
```

---

### Task 6: CHANGELOG와 버전

**Files:**
- Modify: `plugins/superdomain/CHANGELOG.md` (0.7.0 절 위에 0.8.0 절)
- Modify: `plugins/superdomain/.claude-plugin/plugin.json` (`version`)

- [ ] **Step 1: 검사를 돌려 실패를 확인한다**

```bash
python3 - <<'PY'
import json
from pathlib import Path
P = Path('plugins/superdomain')
assert json.loads((P / '.claude-plugin/plugin.json').read_text())['version'] == '0.8.0'
c = (P / 'CHANGELOG.md').read_text(encoding='utf-8')
s = c.split('## 0.8.0')[1].split('## 0.7.0')[0]
for h in ['### Added', '### Changed', '### Removed', '### 이행']:
    assert h in s, h
assert s.split('### 이행')[1].count('\n- ') == 7
print('PASS')
PY
```

Expected: `AssertionError`

- [ ] **Step 2: CHANGELOG에 0.8.0 절을 쓴다**

제목은 `## 0.8.0 — <오늘 날짜>`다(`date +%F`). 첫 문단: "`외부`를 어느 도메인에 적는지와 DOMAIN.md를 간결하게 쓰는 기준을 정했고, DOMAIN.md의 형식을 기본 뼈대와 필요할 때만 쓰는 칸으로 나눴다."

| 절 | 항목 |
|---|---|
| `### Added` | 가이드 「간결하게 쓰는 기준」(시험 셋, 적지 않는 것, 분량). 외부 시스템의 판별과 맡는 도메인. 칸 `하위 도메인`, `알려진 어긋남`, `모든 도메인이 쓰는 별도 서비스`, `의존으로 세지 않는 코드`, `외부`의 `(연동: <key>)`. 개념도. domain-reviewer의 간결성 검사와 변경 검토 두 항목 |
| `### Changed` | 칸 이름 `코드` → `패키지`. `외부`는 맡은 도메인 하나에만. "조율 계층" → "조합 코드". domain 스킬(최상위 묶음을 먼저 묻는다, 기본 뼈대로 시작한다, 지적은 지우는 쪽을 먼저, 포인터 줄). 컨벤션 머리말의 "외부 자원" |
| `### Removed` | `미정` 칸. 도메인 맵 |
| `### 이행` | 스펙 §9의 이행 안내 일곱 항목을 글자 그대로 |

- [ ] **Step 3: 버전을 올린다**

`plugins/superdomain/.claude-plugin/plugin.json`의 `"version"`을 `"0.8.0"`으로 바꾼다.

- [ ] **Step 4: 검사를 다시 돌린다**

Step 1의 명령과 `claude plugin validate .`. Expected: `PASS`, `✔ Validation passed`

- [ ] **Step 5: 커밋**

```bash
git add plugins/superdomain/CHANGELOG.md plugins/superdomain/.claude-plugin/plugin.json
git commit -m "chore(superdomain): 0.8.0 CHANGELOG와 버전"
```

---

### Task 7: Codex 전환본

절차는 `.agents/skills/claude-to-codex/SKILL.md`를 따른다. 쓰기 전에 원본·전환본·`porting/superdomain/decisions.md`를 함께 읽는다.

**Files:**
- Modify: `plugins/superdomain-codex/skills/domain/domain-guide.md`, `skills/conventions/conventions.md`, `skills/conventions/architecture-tests.md` (원본을 복사)
- Modify: `plugins/superdomain-codex/skills/domain/SKILL.md`, `skills/conventions/SKILL.md`, `skills/adr/SKILL.md`
- Modify: `plugins/superdomain-codex/skills/review/references/domain-reviewer.md`, `skills/review/references/convention-reviewer.md`
- Modify: `plugins/superdomain-codex/README.md`, `plugins/superdomain-codex/plugin.json`

**Interfaces:**
- Consumes: Task 1~6의 원본 파일.
- Produces: Task 8이 스냅샷으로 뜨는 전환본 상태.

- [ ] **Step 1: 세 파일을 복사한다**

```bash
for f in skills/domain/domain-guide.md skills/conventions/conventions.md skills/conventions/architecture-tests.md; do cp "plugins/superdomain/$f" "plugins/superdomain-codex/$f"; done
```

- [ ] **Step 2: 스킬 세 개를 합친다**

원본에서 바뀐 문장을 전환본의 같은 자리에 같은 문장으로 넣는다. 전환본의 변형은 그대로 둔다: `${CLAUDE_SKILL_DIR}/…` 대신 상대 링크, `/superdomain:<이름>` 대신 "superdomain의 <이름> 스킬"(링크가 있던 자리는 링크), "Claude" 대신 "Codex", 리뷰어 호출 방식. 포인터 줄은 "고칠 때는 superdomain의 domain 스킬로 고친다"로 끝난다.

- [ ] **Step 3: 리뷰어 참고 문서 둘을 합친다**

`agents/domain-reviewer.md`와 `agents/convention-reviewer.md`에서 바뀐 항목을 `skills/review/references/`의 같은 이름 파일에 같은 문장으로 넣는다. 전환본의 변형("Grep" 대신 "읽기 전용 검색(rg 등)", frontmatter 없음, 실행 계약 문단)은 그대로 둔다.

- [ ] **Step 4: `README.md`와 `plugin.json`을 고친다**

기반 버전 **0.7.0**을 **0.8.0**으로, `plugin.json`의 `"version"`을 `"0.8.0"`으로 바꾼다. 전환본 README에는 DOMAIN.md의 칸을 나열한 곳이 없으므로 그 밖은 고치지 않는다.

- [ ] **Step 5: 검사한다**

```bash
for f in skills/domain/domain-guide.md skills/conventions/conventions.md skills/conventions/architecture-tests.md; do cmp "plugins/superdomain/$f" "plugins/superdomain-codex/$f"; done
python3 - <<'PY'
import json
from pathlib import Path
O, C = Path('plugins/superdomain'), Path('plugins/superdomain-codex')
pairs = {
 'agents/domain-reviewer.md': 'skills/review/references/domain-reviewer.md',
 'agents/convention-reviewer.md': 'skills/review/references/convention-reviewer.md',
 'skills/domain/SKILL.md': 'skills/domain/SKILL.md',
 'skills/conventions/SKILL.md': 'skills/conventions/SKILL.md',
}
marks = {
 'agents/domain-reviewer.md': ['뼈대에 없는 절·칸', '`패키지` 칸으로 읽고', '분량 예산', '유니코드 문자 수', '의존으로 세지 않는 코드:', '절 이름이 달라도', '`규칙`에 적힌 값이 코드와 다른가', '가이드가 요구하지 않는 내용을 DOMAIN.md에 더하자는 제안', '프로젝트의 말', 'DOMAIN.md의 "패키지"(0.7.0 형식의 문서면 "코드")로', '`패키지`에 적힌 위치가 없다'],
 'agents/convention-reviewer.md': ['분류와 패키지를 읽는다', '조합 코드'],
 'skills/domain/SKILL.md': ['역할·기능·분류·패키지', '최상위 묶음', '맡을 도메인', '어긋남 후보', '기본 뼈대', '6단계를 한 번 더', '대화로 목록만 알린다', '기준 개념이 바뀜', '0.7.0의 형식', '외부를 맡은 도메인이면 `외부`를 빠뜨리지 않는다'],
 'skills/conventions/SKILL.md': ['지금 고치는 도메인이 맡지 않은 외부 시스템과 직접 주고받게 될 때', '조합 코드'],
}
for o, c in pairs.items():
    ot, ct = (O / o).read_text(encoding='utf-8'), (C / c).read_text(encoding='utf-8')
    for m in marks[o]:
        assert m in ot and m in ct, (c, m)
    for gone in ['/superdomain:', '${CLAUDE_SKILL_DIR}', '${CLAUDE_PLUGIN_ROOT}', '조율', '`미정`에 적는다', '맞닿은 도메인이면', '맞닿을 것 같은데']:
        assert gone not in ct, (c, gone)
a = (C / 'skills/adr/SKILL.md').read_text(encoding='utf-8')
assert '역할·기능·분류·패키지·규칙·관계' in a and '이유와 버린 안은 ADR에 둔다' in a
assert json.loads((C / 'plugin.json').read_text())['version'] == '0.8.0'
assert '**0.8.0**' in (C / 'README.md').read_text(encoding='utf-8')
print('PASS')
PY
D=$(mktemp -d) && npm install --prefix "$D" --ignore-scripts --no-audit --no-fund --no-package-lock ajv@8.18.0 js-yaml@4.1.1 >/dev/null \
  && curl --fail --silent --show-error https://agent-plugins.org/schemas/1.0.0/plugin.schema.json --output "$D/plugin.schema.json" \
  && NODE_PATH="$D/node_modules" node porting/superdomain/validate.cjs plugins/superdomain-codex "$D/plugin.schema.json"
```

Expected: `cmp` 세 번이 아무것도 출력하지 않고, `PASS`, `validate.cjs`가 오류 없이 끝난다.

- [ ] **Step 6: 커밋**

```bash
git add plugins/superdomain-codex
git commit -m "feat(superdomain-codex): 원본 0.8.0의 외부 정의와 간결성 기준을 반영한다"
```

---

### Task 8: porting 기록, 독립 리뷰, 기준 상태

**Files:**
- Modify: `porting/superdomain/decisions.md` (끝에 0.8.0 절)
- Modify: `porting/superdomain/review.md` (끝에 리뷰 절)
- Modify: `porting/superdomain/source-state.json`, `porting/superdomain/target-state.json`

**Interfaces:**
- Consumes: Task 1~7의 모든 파일.

- [ ] **Step 1: `decisions.md` 끝에 `## <오늘 날짜>: 원본 0.8.0 반영`을 쓴다**

"2026-10-11: 원본 0.7.0 반영" 절과 같은 짜임으로 쓴다. 원본에서 바뀐 파일 목록, 아래 대응표, 메모 세 줄(스킬 진입점·인자·호출 흐름·권한·트리거 경로는 그대로다. 관리 파일은 18개 그대로다. 리뷰어의 판단 기준과 스킬의 질문 절차가 바뀌므로 독립 리뷰를 받는다)을 넣는다.

| 원본 | 전환본 | 처리 |
|---|---|---|
| `skills/domain/domain-guide.md` | 같은 위치 | copy |
| `skills/conventions/conventions.md`, `architecture-tests.md` | 같은 위치 | copy |
| `skills/domain/SKILL.md`, `skills/conventions/SKILL.md`, `skills/adr/SKILL.md` | 같은 위치 | adapt (문장 동일, 전환본의 변형 유지) |
| `agents/domain-reviewer.md`, `agents/convention-reviewer.md` | `skills/review/references/` | adapt |
| `.claude-plugin/plugin.json` 버전 | `plugin.json`, README 기반 버전 | adapt |
| `README.md`, `CHANGELOG.md`, 설계 문서 | 없음 | omit |

- [ ] **Step 2: 대응표의 옛 서술을 맞춘다**

`decisions.md` 앞쪽의 컴포넌트 대응표와 남은 런타임 검증에서 0.8.0으로 틀려진 서술(칸 이름, 외부 접점, 조율 계층)이 있으면 고친다. 없으면 건너뛴다.

- [ ] **Step 3: 후보 스냅샷을 뜬다**

```bash
D="${TMPDIR:-/tmp}/superdomain-080"; mkdir -p "$D"
python3 .agents/skills/claude-to-codex/scripts/tree_state.py snapshot plugins/superdomain > "$D/source-candidate.json"
python3 .agents/skills/claude-to-codex/scripts/tree_state.py snapshot plugins/superdomain-codex --paths-file porting/superdomain/managed-paths.json > "$D/target-candidate.json"
shasum -a 256 "$D"/*.json
```

- [ ] **Step 4: 독립 리뷰를 받는다**

새 컨텍스트의 리뷰어(하위 에이전트, 읽기 전용, 추가 위임 없음)에게 원본 0.8.0의 바뀐 파일, 전환본의 바뀐 파일, `decisions.md`의 새 절, 두 후보 파일을 준다. 볼 것은 넷이다. 원본에서 바뀐 판단 기준과 절차가 전환본에 빠짐없이 있는가. Claude 전용 표기가 새로 들어가지 않았는가. 전환본의 상대 링크가 풀리는가. 후보 스냅샷이 지금 파일과 같은가. must_fix가 있으면 고치고 후보를 다시 떠서 재검토를 받는다.

- [ ] **Step 5: 리뷰를 기록한다**

`review.md` 끝에 `## <오늘 날짜>: 0.8.0 반영의 독립 리뷰`를 더한다. 판정, 검토 범위, 지적과 조치 표, 리뷰한 후보의 SHA-256을 적는다. `decisions.md`의 새 절에는 판정 한 줄과 검증 결과를 적는다.

- [ ] **Step 6: 기준 상태를 확정한다**

```bash
D="${TMPDIR:-/tmp}/superdomain-080"
python3 .agents/skills/claude-to-codex/scripts/tree_state.py compare "$D/source-candidate.json" plugins/superdomain
python3 .agents/skills/claude-to-codex/scripts/tree_state.py compare "$D/target-candidate.json" plugins/superdomain-codex
python3 .agents/skills/claude-to-codex/scripts/tree_state.py snapshot plugins/superdomain > porting/superdomain/source-state.json
python3 .agents/skills/claude-to-codex/scripts/tree_state.py snapshot plugins/superdomain-codex --paths-file porting/superdomain/managed-paths.json > porting/superdomain/target-state.json
python3 porting/superdomain/check_repository.py
```

Expected: 두 `compare`의 `added`·`modified`·`removed`가 비어 있고, 마지막 줄이 `PASS: platform catalogs, package identity, reviewed source/target baselines, managed paths`다. 원본 폴더는 Step 3 뒤로 바뀌지 않았어야 한다.

- [ ] **Step 7: 커밋**

```bash
git add porting/superdomain
git commit -m "docs(superdomain-codex): 0.8.0 전환 결정과 독립 리뷰를 기록하고 기준 상태를 갱신한다"
```

---

### Task 9: 마지막 검증

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
git grep -n -E "조율 계층|조율 컴포넌트|외부 도메인의 복잡성|도메인 맵|코드 위치" -- plugins/superdomain plugins/superdomain-codex ':!plugins/superdomain/docs' ':!plugins/superdomain/CHANGELOG.md'
git grep -n -E '^- 코드:|\*\*코드\*\*|\*\*미정\*\*|개념·외부·규칙·미정|DOMAIN\.md(의)? "코드"|맞닿은 도메인이면|맞닿게 되거나' -- plugins/superdomain/skills plugins/superdomain/agents plugins/superdomain-codex/skills
```

Expected: 둘 다 결과가 없다. CHANGELOG의 과거 항목과 0.8.0 이행 안내, 설계 문서에는 남아 있어도 된다. 리뷰어가 0.7.0 형식을 읽는 법을 적은 문장의 `` `코드` ``와 `` `미정` ``은 위 패턴에 걸리지 않는다.

- [ ] **Step 3: 보고한다**

바뀐 파일, 기준 확인 결과(스펙 §11), 리뷰 판정, 통과한 검사를 사용자에게 알린다. push와 PR, 태그는 사용자가 요청할 때만 한다. 이어서 0.9.0 계획(`2026-11-11-superdomain-adr-reason-record.md`)을 시작할 수 있다고 알린다.
