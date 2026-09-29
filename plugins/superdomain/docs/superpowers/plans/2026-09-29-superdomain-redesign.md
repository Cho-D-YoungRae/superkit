# superdomain 0.4.0 재설계 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 0.3.0의 스크립트·훅·governance·knowledge 기반 구현을 지우고, 스킬 4개(domain·review·adr·conventions)와 모델을 명시한 리뷰 에이전트 2개로 이루어진 0.4.0 플러그인을 만든다.

**Architecture:** 이 플러그인에는 실행 코드가 없다. 산출물은 전부 마크다운(스킬·에이전트·지식 파일)과 JSON 매니페스트다. 지식은 주제마다 파일 하나(`skills/domain/domain-guide.md`, `skills/conventions/conventions.md`)에 두고, 그 주제의 스킬은 `${CLAUDE_SKILL_DIR}`로, 리뷰 에이전트는 `${CLAUDE_PLUGIN_ROOT}`로 같은 파일을 읽는다. 스킬은 에이전트를 호출할 때 `기준 문서` 경로를 프롬프트에 함께 넘긴다. 에이전트 본문의 경로 치환을 이 환경에서 검증할 수 없어서 둔 이중 안전장치다.

**Tech Stack:** Claude Code 플러그인(SKILL.md, subagent 마크다운, `.claude-plugin/*.json`). 검증에는 `claude plugin validate`, `uv`로 띄운 PyYAML, `git grep`을 쓴다. 검증 명령은 그 자리에서 실행만 하고 저장소에 커밋하지 않는다.

**Spec:** `docs/superpowers/specs/2026-09-29-superdomain-redesign-design.md`

## Global Constraints

- 스크립트 0개. `scripts/`·`tests/`·`hooks/`·CI를 두지 않는다. 이 계획의 검증 명령은 실행만 하고 파일로 커밋하지 않는다.
- 에이전트 모델: `domain-reviewer`는 `model: opus`, `convention-reviewer`는 `model: sonnet`. 스킬은 에이전트를 호출할 때 `model`을 지정하지 않는다.
- 리뷰어는 읽기 전용이다: `tools: Read, Grep, Glob, Bash`, `disallowedTools: Agent`.
- 스킬 description에는 "언제 쓰는가"만 적고 절차를 요약하지 않는다.
- SKILL.md는 150줄 이하.
- 대상 프로젝트 산출물은 `docs/DOMAIN.md`와 `docs/adr/yyyy-MM-dd-slug.md` 둘뿐이다.
- 지식 파일: `skills/domain/domain-guide.md`, `skills/conventions/conventions.md`. 내용은 스펙 §7.1·§7.2의 블록을 글자 그대로 옮긴다.
- 모든 문서는 한국어로 쓴다. 컨벤션 예시 코드는 Kotlin이다.
- 버전은 `0.4.0`이다.
- 작업 브랜치는 `feat/superdomain-redesign`이다. push하지 않는다.
- 커밋 메시지는 Conventional Commits 접두사 + 한국어 문장이고, 마지막 줄은 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`이다.

### 에이전트 호출 계약 (Task 2·3·4가 공유)

스킬이 리뷰어에게 넘기는 프롬프트:

```
모드: 정의 검토 | 변경 검토 | 전체 점검
프로젝트 루트: <절대 경로>
DOMAIN.md: <절대 경로 | 없음>
기준 문서: <지식 파일 절대 경로>
대상: <변경을 보는 git 명령과 파일 목록 | 점검할 경로>
```

두 리뷰어가 돌려주는 형식(심각도 제목이 같아야 review 스킬이 합칠 수 있다):

```
### 지적
#### Critical
#### Important
#### Minor
- `경로:줄` 무엇이 문제인가 — 기준: <가이드의 절 | 「컨벤션 항목」> — 제안
### 질문
### 검토 범위
```

## Review Focus

- **`origin/HEAD`가 없는 저장소**: review가 기준 브랜치를 추측하지 않고 사용자에게 물어야 한다 → Task 4 검증에서 문구를 확인한다.
- **아직 추적하지 않는 새 파일**: 기본 변경 검토에서 새 파일이 빠지면 안 된다(`git ls-files --others --exclude-standard`) → Task 4 검증.
- **에이전트 본문에서 `${CLAUDE_PLUGIN_ROOT}`가 치환되지 않는 경우**: 호출하는 스킬이 `기준 문서` 경로를 넘기고, 에이전트는 그 경로를 먼저 쓴다 → Task 2·3·4 검증.
- **0.3.x 형식의 DOMAIN.md**: domain 스킬이 새 형식으로 다시 쓰자고 제안해야 한다(사용자의 기존 프로젝트가 처음 만나는 경우) → Task 2 검증.
- **대상 프로젝트 규칙과 컨벤션의 충돌**: 프로젝트 CLAUDE.md가 우선하고, 리뷰어는 그 항목을 지적하지 않는다 → Task 3 검증.

---

### Task 1: 0.3.x 구현 지우기

**Files:**
- Delete: `scripts/`, `tests/`, `hooks/`, `references/`, `.claude/skills/study/`, `.github/workflows/ci.yml`
- Delete: `skills/init/`, `skills/model/`, `skills/apply/`, `skills/sync/`, `skills/evolve/`, `skills/migrate/`
- Delete: `skills/adr/SKILL.md`, `skills/review/SKILL.md`, `agents/domain-reviewer.md` (이후 Task에서 새로 쓴다)
- Delete: `docs/superpowers/plans/`의 옛 계획 9개, `docs/superpowers/specs/`의 옛 스펙 3개 (새 스펙과 이 계획은 남긴다)
- Modify: `.gitignore` (`__pycache__/` 줄 삭제)

**Interfaces:**
- Consumes: 없음
- Produces: 0.4.0 파일만 남은 빈 바탕. 이후 Task는 `skills/`·`agents/`에 파일을 새로 만든다.

- [ ] **Step 1: 추적 파일을 지운다**

```bash
git rm -r -q scripts tests hooks references .claude/skills/study .github/workflows/ci.yml \
  skills/init skills/model skills/apply skills/sync skills/evolve skills/migrate \
  skills/adr/SKILL.md skills/review/SKILL.md agents/domain-reviewer.md \
  docs/superpowers/plans/2026-08-08-superarchitect-phase1.md \
  docs/superpowers/plans/2026-08-11-superarchitect-phase2.md \
  docs/superpowers/plans/2026-08-11-superarchitect-phase3.md \
  docs/superpowers/plans/2026-08-11-superarchitect-phase4.md \
  docs/superpowers/plans/2026-08-12-superarchitect-final.md \
  docs/superpowers/plans/2026-08-12-superarchitect-phase5.md \
  docs/superpowers/plans/2026-08-12-superarchitect-phase6.md \
  docs/superpowers/plans/2026-08-17-superdomain-refocus.md \
  docs/superpowers/plans/2026-09-28-superdomain-layout-and-fixes.md \
  docs/superpowers/specs/2026-08-08-superarchitect-plugin-design.md \
  docs/superpowers/specs/2026-08-17-superdomain-refocus-design.md \
  docs/superpowers/specs/2026-09-28-superdomain-layout-and-fixes-design.md
```

- [ ] **Step 2: 남은 캐시 디렉터리를 지운다**

`git rm` 뒤에도 무시되던 `__pycache__/`가 디스크에 남는다. `.gitignore`에서 그 줄을 지우면 추적되지 않은 파일로 보이므로 먼저 지운다. `-X`는 무시 규칙에 걸린 파일만 지우므로, `.gitignore`를 고치는 Step 3보다 **먼저** 실행해야 한다.

```bash
git clean -fdX scripts tests
```

- [ ] **Step 3: `.gitignore`를 고친다**

`.gitignore`의 전체 내용을 아래 한 줄로 바꾼다.

```
.superpowers/
```

- [ ] **Step 4: 남은 파일을 확인한다**

```bash
diff <(git ls-files | sort) <(printf '%s\n' \
  .claude-plugin/marketplace.json .claude-plugin/plugin.json .gitignore \
  CHANGELOG.md LICENSE README.md \
  docs/superpowers/plans/2026-09-29-superdomain-redesign.md \
  docs/superpowers/specs/2026-09-29-superdomain-redesign-design.md | sort) \
  && echo "OK: 남은 파일 목록 일치"
test ! -d scripts && test ! -d tests && echo "OK: scripts·tests 디렉터리 없음"
git status --short --untracked-files=all
```

Expected: `OK: 남은 파일 목록 일치`, `OK: scripts·tests 디렉터리 없음`. `git status`에는 삭제(`D`)와 `.gitignore` 수정(`M`)만 보이고 `??`는 없다.

- [ ] **Step 5: 커밋한다**

```bash
git add -A
git commit -q -F - <<'EOF'
chore: 0.3.x 구현(스크립트·테스트·훅·references·옛 스킬)을 지운다

0.4.0 재설계에 따라 검사 스크립트와 테스트, SessionStart 훅, governance·knowledge 문서,
init·model·apply·sync·evolve·migrate 스킬, 저장소 전용 study 스킬, CI, 옛 스펙·계획을
지운다. adr·review 스킬과 domain-reviewer는 이후 작업에서 새로 쓴다.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
git log --oneline -1
```

---

### Task 2: domain 스킬 · 도메인 가이드 · domain-reviewer

**Files:**
- Create: `skills/domain/domain-guide.md` (스펙 §7.1 블록을 그대로)
- Create: `skills/domain/SKILL.md`
- Create: `agents/domain-reviewer.md`

**Interfaces:**
- Consumes: Global Constraints의 "에이전트 호출 계약"
- Produces:
  - 스킬 `superdomain:domain`
  - 에이전트 `superdomain:domain-reviewer` — 모드 `정의 검토`·`변경 검토`·`전체 점검`, 출력은 호출 계약의 형식. Task 4의 review 스킬이 `변경 검토`·`전체 점검`으로 호출한다.
  - 가이드 절 이름(리뷰어가 기준으로 인용): `DOMAIN.md 형식`, `경계를 긋는 기준`, `잘못 그은 경계의 신호`, `분류 기준`, `같은 이름, 다른 모델`

- [ ] **Step 1: 가이드를 스펙에서 그대로 옮긴다**

```bash
mkdir -p skills/domain
python3 - <<'PY'
import pathlib
spec = pathlib.Path("docs/superpowers/specs/2026-09-29-superdomain-redesign-design.md").read_text(encoding="utf-8")
start = spec.index("### 7.1")
open_ = spec.index("````markdown\n", start) + len("````markdown\n")
close = spec.index("\n````\n", open_)
pathlib.Path("skills/domain/domain-guide.md").write_text(spec[open_:close] + "\n", encoding="utf-8")
PY
wc -l skills/domain/domain-guide.md
head -1 skills/domain/domain-guide.md
```

Expected: `91 skills/domain/domain-guide.md`, 첫 줄 `# 도메인 가이드`.

- [ ] **Step 2: `skills/domain/SKILL.md`를 만든다**

아래 내용을 그대로 쓴다(바깥 ```` 울타리는 빼고).

````markdown
---
name: domain
description: 프로젝트의 도메인을 처음 정의할 때, 도메인을 추가·분리·병합하거나 역할·관계를 바꿀 때, docs/DOMAIN.md가 없거나 코드와 맞지 않을 때 사용한다. "도메인 정의", "도메인 나눠줘", "바운디드 컨텍스트 정리", "DOMAIN.md" 같은 요청이 해당한다.
---

# 도메인 정의

`docs/DOMAIN.md` 한 파일에 도메인마다 역할·기능·분류·코드 위치를 적고, 도메인 사이의 관계를 표로 적는다. 사람과 Claude가 같은 도메인 그림을 보게 하는 것이 목적이다.

**핵심 원칙:** 판단은 근거와 함께 적극적으로 제안하고, 확정은 사용자가 한다. 질문은 한 번에 하나만 한다.

DOMAIN.md 형식과 경계·분류 판단 기준은 `${CLAUDE_SKILL_DIR}/domain-guide.md`에 있다.

## 체크리스트

작업 기준은 git 루트다(`git rev-parse --show-toplevel`). 아래 단계마다 할 일을 만들고 순서대로 끝낸다.

1. **맥락 파악**: `docs/DOMAIN.md`가 있으면 아래 "수정 모드"로 간다. 없으면 CLAUDE.md, README, 모듈·패키지 구조, 최근 커밋을 읽는다. 코드가 없으면 제품이 무엇을 하는지부터 묻는다.
2. **기준 읽기**: `${CLAUDE_SKILL_DIR}/domain-guide.md`를 읽는다.
3. **질문**: 한 번에 하나씩 묻는다. 가능하면 선택지를 주고 추천을 맨 앞에 둔다. 목적은 도메인의 역할·기능·경계·관계를 확정하는 것이다.
4. **도메인 목록 제안**: 후보마다 가이드의 경계 기준에 비춘 근거를 붙여 제안하고 확인받는다. 기존 코드가 있으면 패키지 구조에서 읽은 후보부터 보여 준다.
5. **섹션별 작성**: 도메인마다 역할·기능·분류·코드(선택: 규칙·하지 않는 것)를 보여 주고 확인받는다. 이어서 관계 표를 보여 주고 확인받는다.
6. **저장 후 자체 검토**: `docs/DOMAIN.md`에 쓴 뒤 domain-reviewer를 정의 검토 모드로 호출한다(아래 "자체 검토 호출"). 지적 중 무엇을 반영할지 사용자와 정해 고친다.
7. **사용자 검토**: 파일을 검토해 달라고 요청하고, 고칠 곳이 있으면 반영한다.
8. **후속 제안**
   - 도메인 분리·병합이나 경계 변경처럼 되돌리기 비싼 결정이 있었으면 `/superdomain:adr`로 기록하자고 제안한다.
   - 대상 CLAUDE.md에 DOMAIN.md 포인터가 없으면 아래 한 줄을 추가할지 묻고, 동의하면 추가한다. `@import`는 쓰지 않는다(매 세션 파일 전체를 불러온다).

     ```
     - 도메인 정의: docs/DOMAIN.md (도메인의 역할·관계를 바꾸는 작업 전에 읽는다)
     ```

## 수정 모드

1. 무엇을 바꿀지 확인한다(추가·분리·병합·이름 변경·관계 변경).
2. `${CLAUDE_SKILL_DIR}/domain-guide.md`를 읽고, 바뀌는 부분의 전·후를 나란히 보여 주고 확인받는다.
3. 반영한다.
4. 도메인을 추가·분리·병합했으면 체크리스트 6단계의 자체 검토를 한다.
5. 체크리스트 8단계의 후속 제안을 한다.

**0.3.x 형식 파일**: 기존 파일이 `## 프로젝트:`·`## 컨텍스트:`·`- 패키지:`·`### 관계` 표 같은 0.3.x 형식이면 새 형식으로 전체를 다시 쓰자고 제안한다. 옛 컨텍스트의 이름·분류·패키지·관계와 `### 근거`는 새 형식의 도메인·분류·코드·관계·역할 후보로 쓴다. `docs/superdomain/contexts/*.md`가 남아 있으면 그 불변식을 "규칙" 후보로 읽는다. 다시 쓴 뒤에는 체크리스트 5~8단계를 따른다.

## 자체 검토 호출

Agent 도구로 `superdomain:domain-reviewer`를 호출한다. `model`은 지정하지 않는다(에이전트 파일에 정해져 있다). 세션 대화는 넘기지 않고 아래만 넘긴다.

```
모드: 정의 검토
프로젝트 루트: <절대 경로>
DOMAIN.md: <절대 경로>
기준 문서: ${CLAUDE_SKILL_DIR}/domain-guide.md
```

## 하지 않는 것

- 사용자 확인 없이 DOMAIN.md를 쓰거나 고치지 않는다.
- 코드를 쓰거나 패키지·디렉터리를 만들지 않는다.
- 용어 정의를 쓰지 않는다. 용어집(superglossary)의 몫이다.
- "알아서 해 달라"는 요청에도 근거와 함께 하나를 제안하고, 동의를 받은 뒤에 적는다.
````

- [ ] **Step 3: `agents/domain-reviewer.md`를 만든다**

아래 내용을 그대로 쓴다(바깥 ```` 울타리는 빼고).

````markdown
---
name: domain-reviewer
description: 도메인 정의(docs/DOMAIN.md)나 코드 변경을 도메인 경계 관점에서 검토하는 읽기 전용 리뷰어. superdomain의 review·domain 스킬이 호출한다.
model: opus
tools: Read, Grep, Glob, Bash
disallowedTools: Agent
---

# 도메인 리뷰어

도메인 정의와 코드가 도메인 경계를 지키는지 검토한다. 코드를 고치지 않고, 근거가 있는 지적만 돌려준다.

## 시작하기 전에

1. 판단 기준을 읽는다. 호출 프롬프트에 `기준 문서` 경로가 있으면 그 파일을, 없으면 `${CLAUDE_PLUGIN_ROOT}/skills/domain/domain-guide.md`를 읽는다. 지적의 기준은 이 문서의 절이다.
2. 호출 프롬프트에서 모드(정의 검토 / 변경 검토 / 전체 점검), 프로젝트 루트, DOMAIN.md 경로, 대상을 확인한다. 모드가 없으면 변경 검토로 본다.
3. DOMAIN.md를 읽는다.

## 모드별로 보는 것

**정의 검토** — DOMAIN.md만 본다.
- 형식: 가이드의 "DOMAIN.md 형식"을 따르는가(필수 필드, key 규칙, 관계 표의 방식 값).
- 정의 품질: 역할이 한 문장인가, 기능이 역할 안에 있는가, 이름이 도메인 용어인가.
- 분리·병합 신호: 가이드의 "잘못 그은 경계의 신호" 중 문서만으로 보이는 것.
- 관계 표: 같은 쌍이 두 줄로 적히지 않았는가, 방식이 설명과 맞는가, 데이터 공유가 있는가.

**변경 검토** — DOMAIN.md의 "코드"로 변경된 파일을 도메인에 연결한 뒤 본다.
- 변경된 코드가 맞는 도메인에 있는가.
- 새로 생긴 도메인 간 의존(import·호출)이 관계 표에 있는가. import는 Grep으로 확인한다.
- 다른 도메인의 객체를 필드로 직접 참조하는가, 한 트랜잭션에서 두 도메인의 저장소를 쓰는가, 두 도메인이 같은 테이블에 쓰는가, 다른 도메인의 용어가 새어 들어오는가.
- 이 변경이 도메인의 역할 밖 기능을 더하는가(너무 커지는 신호).
- DOMAIN.md를 고쳐야 하는 변경인가(새 도메인이나 관계가 생김).

**전체 점검** — 변경 검토의 항목을 대상 전체에 적용하고, 더해서 본다.
- DOMAIN.md와 실제 구조의 어긋남: 적힌 코드 위치가 없다, DOMAIN.md에 없는 도메인처럼 보이는 패키지가 있다.
- 도메인별 크기와 응집: 가이드의 "너무 크다"·"너무 작다" 신호.

## 지키는 것

- **읽기 전용이다.** 파일을 만들거나 고치지 않는다. git은 `diff`·`log`·`show`만 쓰고, 작업 트리·인덱스·브랜치를 바꾸지 않는다.
- **근거 없이 지적하지 않는다.** 지적마다 위치(`경로:줄` 또는 DOMAIN.md의 절)와 기준(가이드의 절 이름)을 붙인다. 읽지 않은 코드에 대해 말하지 않는다. 확신이 없으면 지적이 아니라 질문으로 남긴다.
- **같은 이름, 다른 모델**: 모듈이 다른 같은 이름의 모델은 DOMAIN.md "코드"에 따로 적혀 있으면 중복으로 지적하지 않는다.
- **보고하지 않는 것**: 코딩 컨벤션(convention-reviewer의 몫), 스타일, 버그·보안 전반.
- **다른 에이전트를 띄우지 않는다.** 범위가 크면 나눠서 직접 읽고, 그렇게 했다고 "검토 범위"에 적는다.

## 출력

심각도: Critical은 고치지 않으면 버그·데이터 손상·경계 붕괴로 이어지는 것, Important는 분명한 경계 신호나 관계 표와 어긋나는 의존, Minor는 개선 제안이다.

아래 형식 하나만 돌려준다. 해당하는 지적이 없는 심각도에는 "없음"이라고 적는다.

```markdown
### 지적
#### Critical
#### Important
#### Minor
- `경로:줄` 무엇이 문제인가 — 기준: <가이드의 절> — 제안 (후속: DOMAIN.md 수정 | ADR — 해당할 때만)
### 질문
### 검토 범위
```
````

- [ ] **Step 4: 검증한다**

```bash
claude plugin validate --strict skills
claude plugin validate --strict agents
uv run --quiet --with pyyaml python3 - skills/domain/SKILL.md agents/domain-reviewer.md <<'PY'
import sys, pathlib, yaml
SKILL = set("name description when_to_use argument-hint arguments disable-model-invocation user-invocable allowed-tools disallowed-tools model effort context agent background hooks paths shell metadata license compatibility".split())
AGENT = set("name description model effort maxTurns tools disallowedTools skills memory background omitClaudeMd isolation color".split())
bad = 0
for p in map(pathlib.Path, sys.argv[1:]):
    t = p.read_text(encoding="utf-8"); skill = p.name == "SKILL.md"
    d = yaml.safe_load(t[4:t.index("\n---\n", 4)]) if t.startswith("---\n") else {}
    need = {"name", "description"} | (set() if skill else {"model"})
    errs = sorted(set(d) - (SKILL if skill else AGENT)) + [f"missing:{k}" for k in sorted(need - set(d))]
    if d.get("name") != (p.parent.name if skill else p.stem): errs.append(f"name:{d.get('name')}")
    print("FAIL" if errs else "ok", p, errs or d.get("model", "")); bad += bool(errs)
sys.exit(bad)
PY
python3 - <<'PY'
import pathlib
spec = pathlib.Path("docs/superpowers/specs/2026-09-29-superdomain-redesign-design.md").read_text(encoding="utf-8")
start = spec.index("### 7.1"); open_ = spec.index("````markdown\n", start) + 13; close = spec.index("\n````\n", open_)
print("guide matches spec:", pathlib.Path("skills/domain/domain-guide.md").read_text(encoding="utf-8") == spec[open_:close] + "\n")
PY
wc -l skills/domain/SKILL.md
grep -n 'disallowedTools: Agent' agents/domain-reviewer.md
grep -n '^model: opus$' agents/domain-reviewer.md
grep -n '0.3.x 형식' skills/domain/SKILL.md
grep -n '기준 문서: \${CLAUDE_SKILL_DIR}/domain-guide.md' skills/domain/SKILL.md
grep -n '기준 문서` 경로가 있으면 그 파일을' agents/domain-reviewer.md
grep -n '모드가 없으면 변경 검토로 본다' agents/domain-reviewer.md
```

Expected:
- 두 `validate` 모두 `✔ Validation passed`
- `ok skills/domain/SKILL.md`, `ok agents/domain-reviewer.md opus`
- `guide matches spec: True`
- SKILL.md 150줄 이하
- 나머지 `grep`은 모두 한 줄 이상 나온다.

- [ ] **Step 5: 커밋한다**

```bash
git add skills/domain agents/domain-reviewer.md
git commit -q -F - <<'EOF'
feat(domain): domain 스킬과 도메인 가이드, domain-reviewer를 추가한다

DOMAIN.md에 도메인별 역할·기능·분류·코드와 관계를 정의하는 domain 스킬, 경계·분류 판단
기준을 담은 domain-guide.md, 정의와 코드를 도메인 경계 관점에서 검토하는 읽기 전용
domain-reviewer(model: opus)를 추가한다.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
git log --oneline -1
```

---

### Task 3: conventions 스킬 · 코딩 컨벤션 · convention-reviewer

**Files:**
- Create: `skills/conventions/conventions.md` (스펙 §7.2 블록을 그대로)
- Create: `skills/conventions/SKILL.md`
- Create: `agents/convention-reviewer.md`

**Interfaces:**
- Consumes: Global Constraints의 "에이전트 호출 계약"
- Produces:
  - 스킬 `superdomain:conventions` (`paths`로 `.kt`·`.java` 작업에서만 걸린다)
  - 에이전트 `superdomain:convention-reviewer` — 모드 `변경 검토`·`전체 점검`, 출력은 호출 계약의 형식. Task 4의 review 스킬이 호출한다.
  - 컨벤션 항목 14개. 제목 끝에 `필수` 또는 `지향` 태그가 붙고, 리뷰어는 제목을 「」로 인용한다.

- [ ] **Step 1: 컨벤션을 스펙에서 그대로 옮긴다**

```bash
mkdir -p skills/conventions
python3 - <<'PY'
import pathlib
spec = pathlib.Path("docs/superpowers/specs/2026-09-29-superdomain-redesign-design.md").read_text(encoding="utf-8")
start = spec.index("### 7.2")
open_ = spec.index("````markdown\n", start) + len("````markdown\n")
close = spec.index("\n````\n", open_)
pathlib.Path("skills/conventions/conventions.md").write_text(spec[open_:close] + "\n", encoding="utf-8")
PY
wc -l skills/conventions/conventions.md
grep -c '^## ' skills/conventions/conventions.md
```

Expected: `132 skills/conventions/conventions.md`, 항목 수 `14`.

- [ ] **Step 2: `skills/conventions/SKILL.md`를 만든다**

아래 내용을 그대로 쓴다(바깥 ``` 울타리는 빼고).

```markdown
---
name: conventions
description: Kotlin·Java(Spring·JPA) 코드에서 도메인 모델·서비스·리포지토리·엔티티·테스트를 작성하거나 고칠 때 사용한다.
paths: ["**/*.kt", "**/*.java"]
---

# 코딩 컨벤션 적용

도메인 로직이 드러나고 테스트하기 쉬운 코드를 처음부터 쓰기 위해, 코드를 쓰기 전에 컨벤션을 읽고 따른다. `/superdomain:review`의 convention-reviewer도 같은 문서를 기준으로 쓴다.

## 적용 방법

1. 코드를 쓰거나 고치기 전에 `${CLAUDE_SKILL_DIR}/conventions.md`를 읽는다.
2. 대상 프로젝트의 CLAUDE.md(루트와 모듈)를 확인한다. 컨벤션과 충돌하는 규칙은 프로젝트 규칙을 따른다.
3. `docs/DOMAIN.md`가 있으면 지금 고치는 코드가 어느 도메인인지, 그 분류가 무엇인지 본다. 분류가 generic인 도메인이나 어드민·워커·배치처럼 도메인 로직이 얇은 곳에서는 「JPA는 인프라에 둔다」의 예외를 쓸 수 있다.
4. 코드를 쓴다.
   - `필수` 규칙에서 벗어나야 하면 그 이유를 사용자에게 말한다.
   - `지향` 규칙은 가능한 한 따른다.

## 기존 코드가 컨벤션과 다를 때

- 이번 변경 범위에서만 컨벤션을 따른다. 기존 코드와 섞여 어색해지면 그 사실을 알린다.
- 범위 밖의 넓은 정리는 하지 않고 제안만 한다.

## 하지 않는 것

- 컨벤션을 이유로 요청받지 않은 리팩터링을 하지 않는다.
- 프로젝트 규칙보다 컨벤션을 앞세우지 않는다.
```

- [ ] **Step 3: `agents/convention-reviewer.md`를 만든다**

아래 내용을 그대로 쓴다(바깥 ```` 울타리는 빼고).

````markdown
---
name: convention-reviewer
description: Kotlin·Java 코드를 superdomain 코딩 컨벤션 기준으로 검토하는 읽기 전용 리뷰어. superdomain의 review 스킬이 호출한다.
model: sonnet
tools: Read, Grep, Glob, Bash
disallowedTools: Agent
---

# 컨벤션 리뷰어

Kotlin·Java 코드가 코딩 컨벤션을 따르는지 검토한다. 코드를 고치지 않고, 근거가 있는 지적만 돌려준다.

## 시작하기 전에

1. 기준을 읽는다. 호출 프롬프트에 `기준 문서` 경로가 있으면 그 파일을, 없으면 `${CLAUDE_PLUGIN_ROOT}/skills/conventions/conventions.md`를 읽는다.
2. 대상 프로젝트의 CLAUDE.md(루트와 대상 모듈)를 읽는다. 컨벤션과 충돌하는 규칙은 프로젝트 규칙을 따르고, 그 항목은 지적하지 않는다.
3. `docs/DOMAIN.md`가 있으면 도메인별 분류와 코드 위치를 읽는다. 분류가 generic인 도메인과 어드민·워커·배치 모듈에는 「JPA는 인프라에 둔다」의 예외를 적용한다.
4. 호출 프롬프트에서 모드(변경 검토 / 전체 점검)와 대상을 확인한다. 모드가 없으면 변경 검토로 본다.

## 보는 범위

- **변경 검토**: 변경된 `.kt`·`.java` 파일의 변경된 줄과, 그 줄이 속한 선언(클래스·함수)만 본다. 변경 밖의 기존 위반은 보고하지 않는다.
- **전체 점검**: 도메인·application 패키지부터 읽고, 가능한 만큼 넓힌다. 읽은 범위를 "검토 범위"에 적는다.

## 심각도

- `필수` 규칙 위반 → Important
- `지향` 규칙 미준수 → Minor
- 위반이 실제 결함으로 이어질 때만 Critical (예: 도메인 검증을 거치지 않아 잘못된 상태가 저장될 수 있다)

## 지키는 것

- **읽기 전용이다.** 파일을 만들거나 고치지 않는다. git은 `diff`·`log`·`show`만 쓴다.
- **근거 없이 지적하지 않는다.** 지적마다 위치(`경로:줄`)와 컨벤션 항목 이름(예: 「현재 시각은 Clock에서 얻는다」)을 붙인다. 확신이 없으면 질문으로 남긴다.
- **보고하지 않는 것**: 도메인 경계(domain-reviewer의 몫), 컨벤션에 없는 스타일 취향, 버그·보안 전반.
- **다른 에이전트를 띄우지 않는다.**

## 출력

아래 형식 하나만 돌려준다. 해당하는 지적이 없는 심각도에는 "없음"이라고 적는다.

```markdown
### 지적
#### Critical
#### Important
#### Minor
- `경로:줄` 무엇이 문제인가 — 기준: 「컨벤션 항목」 — 제안 (필요하면 짧은 코드)
### 질문
### 검토 범위
```
````

- [ ] **Step 4: 검증한다**

```bash
claude plugin validate --strict skills
claude plugin validate --strict agents
uv run --quiet --with pyyaml python3 - skills/conventions/SKILL.md agents/convention-reviewer.md <<'PY'
import sys, pathlib, yaml
SKILL = set("name description when_to_use argument-hint arguments disable-model-invocation user-invocable allowed-tools disallowed-tools model effort context agent background hooks paths shell metadata license compatibility".split())
AGENT = set("name description model effort maxTurns tools disallowedTools skills memory background omitClaudeMd isolation color".split())
bad = 0
for p in map(pathlib.Path, sys.argv[1:]):
    t = p.read_text(encoding="utf-8"); skill = p.name == "SKILL.md"
    d = yaml.safe_load(t[4:t.index("\n---\n", 4)]) if t.startswith("---\n") else {}
    need = {"name", "description"} | (set() if skill else {"model"})
    errs = sorted(set(d) - (SKILL if skill else AGENT)) + [f"missing:{k}" for k in sorted(need - set(d))]
    if d.get("name") != (p.parent.name if skill else p.stem): errs.append(f"name:{d.get('name')}")
    print("FAIL" if errs else "ok", p, errs or d.get("model", "")); bad += bool(errs)
sys.exit(bad)
PY
python3 - <<'PY'
import pathlib
spec = pathlib.Path("docs/superpowers/specs/2026-09-29-superdomain-redesign-design.md").read_text(encoding="utf-8")
start = spec.index("### 7.2"); open_ = spec.index("````markdown\n", start) + 13; close = spec.index("\n````\n", open_)
print("conventions matches spec:", pathlib.Path("skills/conventions/conventions.md").read_text(encoding="utf-8") == spec[open_:close] + "\n")
PY
grep '^## ' skills/conventions/conventions.md | grep -vcE '`(필수|지향)`'
grep -n '^paths:' skills/conventions/SKILL.md
grep -n '^model: sonnet$' agents/convention-reviewer.md
grep -n 'disallowedTools: Agent' agents/convention-reviewer.md
grep -n '프로젝트 규칙을 따르' skills/conventions/SKILL.md agents/convention-reviewer.md
grep -n '기준 문서` 경로가 있으면 그 파일을' agents/convention-reviewer.md
grep -n '모드가 없으면 변경 검토로 본다' agents/convention-reviewer.md
```

Expected:
- 두 `validate` 모두 `✔ Validation passed`
- `ok skills/conventions/SKILL.md`, `ok agents/convention-reviewer.md sonnet`
- `conventions matches spec: True`
- 강도 태그가 없는 항목 수 `0`
- 나머지 `grep`은 모두 한 줄 이상 나온다(`프로젝트 규칙을 따르`는 두 파일 모두에서).

- [ ] **Step 5: 커밋한다**

```bash
git add skills/conventions agents/convention-reviewer.md
git commit -q -F - <<'EOF'
feat(conventions): 코딩 컨벤션과 conventions 스킬, convention-reviewer를 추가한다

도메인 로직이 드러나고 테스트하기 쉬운 코드를 위한 컨벤션 14개(필수·지향)와, Kotlin·Java
작업에서 이를 적용하는 conventions 스킬, 같은 문서를 기준으로 검토하는 읽기 전용
convention-reviewer(model: sonnet)를 추가한다.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
git log --oneline -1
```

---

### Task 4: review 스킬

**Files:**
- Create: `skills/review/SKILL.md`

**Interfaces:**
- Consumes:
  - `superdomain:domain-reviewer` (Task 2) — 모드 `변경 검토`·`전체 점검`, 기준 문서 `${CLAUDE_PLUGIN_ROOT}/skills/domain/domain-guide.md`
  - `superdomain:convention-reviewer` (Task 3) — 모드 `변경 검토`·`전체 점검`, 기준 문서 `${CLAUDE_PLUGIN_ROOT}/skills/conventions/conventions.md`
  - 두 리뷰어의 출력 형식(Global Constraints의 호출 계약)
- Produces: 스킬 `superdomain:review` — 인자 `[domain|code] [경로 | 커밋 범위 | 전체]`

인자 해석: 인자가 없거나 커밋 범위면 변경 검토, 경로나 `전체`면 전체 점검이다. 경로는 "그 경로 아래 파일의 전체 점검"으로 해석한다(스펙은 경로를 인자로 받는다고만 정했다).

- [ ] **Step 1: `skills/review/SKILL.md`를 만든다**

아래 내용을 그대로 쓴다(바깥 ```` 울타리는 빼고).

````markdown
---
name: review
description: 커밋·PR 전에 변경이 도메인 정의(docs/DOMAIN.md)와 코딩 컨벤션을 따르는지 검토할 때, 도메인이 너무 커지거나 경계가 흐려지지 않았는지 점검할 때 사용한다. "도메인 리뷰", "컨벤션 리뷰", "superdomain 리뷰" 같은 요청이 해당한다. 버그·보안 중심의 일반 코드 리뷰에는 쓰지 않는다.
argument-hint: "[domain|code] [경로 | 커밋 범위 | 전체]"
---

# 도메인·컨벤션 리뷰

변경을 두 관점에서 본다. 도메인 경계는 `superdomain:domain-reviewer`가, 코딩 컨벤션은 `superdomain:convention-reviewer`가 맡는다. 이 스킬은 대상을 정하고, 두 리뷰어를 동시에 띄우고, 결과를 한 리포트로 합친다.

**핵심 원칙:** 판정은 리뷰어가 한다. 이 스킬이 diff를 직접 읽고 판정하지 않는다. 코드는 사용자가 요청할 때만 고친다.

## 1. 대상 결정

작업 기준은 git 루트다(`git rev-parse --show-toplevel`). 인자(`$ARGUMENTS`)를 해석한다.

| 인자 | 모드 | 대상 |
|---|---|---|
| 없음 | 변경 검토 | 기준 브랜치와의 merge-base 이후의 모든 변경(커밋된 것 + 커밋하지 않은 것) |
| 커밋 범위(`A..B`) | 변경 검토 | 그 범위의 변경 |
| 경로 | 전체 점검 | 그 경로 아래 파일 |
| `전체` | 전체 점검 | 프로젝트 전체 |

기준 브랜치와 변경 목록은 이렇게 구한다.

```bash
git symbolic-ref --quiet --short refs/remotes/origin/HEAD   # 기준 브랜치 (예: origin/main)
git merge-base HEAD <기준 브랜치>                            # BASE
git diff --name-only <BASE>                                  # 추적 중인 파일의 변경 (커밋 + 작업 트리)
git ls-files --others --exclude-standard                     # 아직 추적하지 않는 새 파일
```

- `origin/HEAD`가 없으면 기준 브랜치를 추측하지 말고 사용자에게 묻는다.
- 변경 검토인데 변경이 없으면 알리고 끝낸다.

## 2. 관점 결정

- 인자에 `domain`이 있으면 도메인만, `code`가 있으면 컨벤션만, 없으면 둘 다 본다.
- `docs/DOMAIN.md`가 없으면 도메인 리뷰를 건너뛰고 `/superdomain:domain`을 안내한다.
- 대상에 `.kt`·`.java` 파일이 없으면 컨벤션 리뷰를 건너뛰고 그 사실을 알린다.
- 두 관점이 모두 건너뛰어지면 이유를 알리고 끝낸다.

## 3. 리뷰어 호출

두 리뷰어를 **한 메시지에서 동시에** Agent 도구로 호출한다. `model`은 지정하지 않는다(에이전트 파일에 정해져 있다). 세션 대화는 넘기지 않고 아래만 넘긴다.

`superdomain:domain-reviewer`:

```
모드: 변경 검토 | 전체 점검
프로젝트 루트: <절대 경로>
DOMAIN.md: <절대 경로>
기준 문서: ${CLAUDE_PLUGIN_ROOT}/skills/domain/domain-guide.md
대상: <변경을 보는 git 명령과 파일 목록, 또는 점검할 경로>
```

`superdomain:convention-reviewer`:

```
모드: 변경 검토 | 전체 점검
프로젝트 루트: <절대 경로>
DOMAIN.md: <절대 경로 | 없음>
기준 문서: ${CLAUDE_PLUGIN_ROOT}/skills/conventions/conventions.md
대상: <변경을 보는 git 명령과 .kt·.java 파일 목록, 또는 점검할 경로>
```

## 4. 합치기

- 심각도 순(Critical → Important → Minor)으로 모은다.
- 같은 위치의 같은 문제는 하나로 합치고 기준을 둘 다 적는다.
- 두 리뷰어의 판단이 충돌하면 둘 다 보여 준다.
- 위치나 기준이 없는 지적은 빼고, 뺐다는 사실을 적는다.

## 5. 보고와 후속

```markdown
## 리뷰 결과 — <대상 요약>
### Critical
### Important
### Minor
- [도메인|컨벤션] `경로:줄` 문제 — 기준 — 제안
### 질문
### 검토 범위
(건너뛴 관점과 그 이유를 포함한다)
```

- 코드 수정은 사용자가 요청할 때만 한다. 요청받으면 Critical부터 고친다.
- 리뷰어의 지적이 틀렸다고 보이면 근거와 함께 그렇게 말한다. 그대로 따르지 않는다.
- DOMAIN.md를 고쳐야 하면 `/superdomain:domain`을, 결정을 남겨야 하면 `/superdomain:adr`을 안내한다.

## 하지 않는 것

- 자동으로 코드를 고치지 않는다.
- 리뷰 결과를 파일로 저장하지 않는다.
- 리뷰어의 모델을 지정하거나 덮어쓰지 않는다.
````

- [ ] **Step 2: 검증한다**

```bash
claude plugin validate --strict skills
uv run --quiet --with pyyaml python3 - skills/review/SKILL.md <<'PY'
import sys, pathlib, yaml
SKILL = set("name description when_to_use argument-hint arguments disable-model-invocation user-invocable allowed-tools disallowed-tools model effort context agent background hooks paths shell metadata license compatibility".split())
AGENT = set("name description model effort maxTurns tools disallowedTools skills memory background omitClaudeMd isolation color".split())
bad = 0
for p in map(pathlib.Path, sys.argv[1:]):
    t = p.read_text(encoding="utf-8"); skill = p.name == "SKILL.md"
    d = yaml.safe_load(t[4:t.index("\n---\n", 4)]) if t.startswith("---\n") else {}
    need = {"name", "description"} | (set() if skill else {"model"})
    errs = sorted(set(d) - (SKILL if skill else AGENT)) + [f"missing:{k}" for k in sorted(need - set(d))]
    if d.get("name") != (p.parent.name if skill else p.stem): errs.append(f"name:{d.get('name')}")
    print("FAIL" if errs else "ok", p, errs or d.get("model", "")); bad += bool(errs)
sys.exit(bad)
PY
wc -l skills/review/SKILL.md
grep -cE 'superdomain:(domain|convention)-reviewer' skills/review/SKILL.md
grep -c '^기준 문서: ' skills/review/SKILL.md
test -f skills/domain/domain-guide.md && test -f skills/conventions/conventions.md && echo "기준 문서 파일 있음"
grep -n 'ls-files --others --exclude-standard' skills/review/SKILL.md
grep -n 'origin/HEAD`가 없으면 기준 브랜치를 추측하지 말고' skills/review/SKILL.md
grep -n '두 관점이 모두 건너뛰어지면' skills/review/SKILL.md
grep -n '버그·보안 중심의 일반 코드 리뷰에는 쓰지 않는다' skills/review/SKILL.md
```

Expected:
- `✔ Validation passed`
- `ok skills/review/SKILL.md`
- SKILL.md 150줄 이하
- 에이전트 이름 언급 `3` 이상, `기준 문서:` 줄 `2`
- `기준 문서 파일 있음`
- 나머지 `grep`은 모두 한 줄 이상 나온다.

- [ ] **Step 3: 커밋한다**

```bash
git add skills/review
git commit -q -F - <<'EOF'
feat(review): 두 리뷰어를 병렬로 호출하는 review 스킬을 새로 쓴다

대상(변경 검토·전체 점검)과 관점(domain·code)을 정하고, domain-reviewer와
convention-reviewer를 동시에 호출해 한 리포트로 합친다. 코드는 사용자가 요청할 때만 고친다.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
git log --oneline -1
```

---

### Task 5: adr 스킬 · 템플릿

**Files:**
- Create: `skills/adr/SKILL.md`
- Create: `skills/adr/adr-template.md`

**Interfaces:**
- Consumes: 없음 (결정이 도메인 정의를 바꾸면 `/superdomain:domain`을 안내만 한다)
- Produces: 스킬 `superdomain:adr` — 파일 `docs/adr/yyyy-MM-dd-slug.md`, 상태 `proposed`·`accepted`·`superseded`, 머리 링크 `대체함:`·`대체됨:`·`조정됨:`

- [ ] **Step 1: `skills/adr/adr-template.md`를 만든다**

아래 내용을 그대로 쓴다(바깥 ```` 울타리는 빼고).

````markdown
# ADR 템플릿

## 상태

| 상태 | 뜻 | 다음 |
|---|---|---|
| `proposed` | 초안이다. 아직 확정되지 않았다 | 승인되면 `accepted` |
| `accepted` | 유효한 결정이다. 본문은 고치지 않는다 | 전면 무효가 되면 `superseded` |
| `superseded` | 다른 ADR로 대체되었다. `대체됨:` 링크를 따라간다 | — |

머리(메타데이터)에 쓰는 링크:

- `- 대체함: [<파일명>](<파일명>)` — 이 ADR이 대체한 옛 ADR (새 ADR에 쓴다)
- `- 대체됨: [<파일명>](<파일명>)` — 이 ADR을 대체한 새 ADR (옛 ADR에 쓴다)
- `- 조정됨: [<파일명>](<파일명>)` — 이 ADR의 일부를 조정한 ADR (옛 ADR에 쓴다, 여러 줄 가능)

## 템플릿

```markdown
# <결정을 한 문장으로 — 명사구가 아니라 결정문으로>

- 상태: proposed
- 날짜: YYYY-MM-DD
- 관련: <도메인 이름 / 다른 ADR 파일명 — 없으면 이 줄을 지운다>

## 문제 상황

무엇이 결정을 강제했는가. 제약, 요구, 관측된 문제를 사실 위주로 쓴다.
이 결정을 모르는 사람이 읽고 "그래서 결정이 필요했겠다"까지 이해할 만큼만.

## 결정

무엇을 하기로 했는가. 한 문단, 능동태, 단정형으로.
"~하는 것을 고려한다"가 아니라 "~한다".

## 근거

왜 이 선택인가.

**검토한 대안**

| 대안 | 기각 이유 |
|---|---|
| <대안 A> | <왜 고르지 않았는가> |

## 결과

**긍정적**
- <이 결정으로 좋아지는 것>

**부정적**
- <이 결정이 만드는 비용·제약·위험>

**후속 작업**
- <코드·문서에 반영해야 할 것 — 없으면 "없음">
```
````

- [ ] **Step 2: `skills/adr/SKILL.md`를 만든다**

아래 내용을 그대로 쓴다(바깥 ``` 울타리는 빼고).

```markdown
---
name: adr
description: 되돌리기 비싼 기술·도메인 결정을 내렸거나 그 결정을 기록으로 남겨야 할 때, 기존 ADR을 승인하거나 대체할 때 사용한다. "ADR 써줘", "결정 기록", "ADR 승인", "ADR 대체" 같은 요청이 해당한다.
---

# 결정 기록 (ADR)

되돌리기 비싼 결정을 `docs/adr/yyyy-MM-dd-slug.md`에 남긴다. 다음 사람(다음 세션의 Claude 포함)이 "왜 이렇게 했지?"에 답을 찾을 수 있게 하는 것이 목적이다.

**핵심 원칙:** 사실만 적는다. 검토하지 않은 대안이나 사용자가 말하지 않은 이유를 지어내지 않는다.

작업 기준은 git 루트다(`git rev-parse --show-toplevel`). 템플릿과 상태 규칙은 `${CLAUDE_SKILL_DIR}/adr-template.md`에 있으니 쓰기 전에 읽는다.

## 1. 모드

| 요청 | 모드 |
|---|---|
| 새 결정을 기록한다 | 신규 |
| `proposed` ADR을 확정한다 | 승인 |
| 옛 결정을 전면 무효로 하고 새 결정으로 바꾼다 | 대체 |
| 옛 결정의 일부만 바꾼다 | 부분 조정 |

대체인지 부분 조정인지 애매하면 근거와 함께 하나를 제안하고 확인받는다. 옛 ADR이 이미 `superseded`면 `대체됨:` 링크를 따라가 현재 유효한 ADR을 대상으로 다시 판단한다.

## 2. 신규

1. **쓸 결정인가 판단한다.** 셋 중 하나라도 해당하면 쓴다.
   - 되돌리는 비용이 크다.
   - 실제로 여러 대안 중에서 골랐다.
   - 나중에 누군가 "왜?"라고 물을 것이다.

   해당하지 않으면 쓰지 않고 이유를 말한다. 판단이 서지 않으면 쓴다.
2. **한 ADR에 결정 하나.** 인터뷰 중 결정이 둘로 갈라지면 문서도 둘로 나눈다.
3. **인터뷰한다.** 한 번에 하나씩 묻고, 받은 답을 바로 초안에 반영해 보여 준다. 대화나 코드에서 본 것을 근거로 초안 문장을 먼저 제안해도 되지만 확정은 사용자가 한다.

   | 항목 | 묻는 것 | 실패 신호 |
   |---|---|---|
   | 제목 | 이 결정을 한 문장 결정문으로 | "인증 방식 검토" 같은 명사구 |
   | 문제 상황 | 무엇이 이 결정을 강제했는가 | 배경이 본문의 절반을 넘는다 |
   | 결정 | 무엇을 하기로 했는가 | "~를 고려한다" |
   | 검토한 대안 | 실제로 오간 대안과 기각 이유 | 아래 4번 |
   | 결과 | 긍정 / 부정 / 후속 작업 | 부정 칸이 비었다 |

4. **검토한 대안**: 사용자가 말한 대안, 또는 제안한 대안 중 사용자가 "그것도 봤다"고 확인한 것만 적는다. 기각 이유도 사용자에게서 받는다. 대안이 없으면 표 대신 "검토한 대안 없음."이라고 쓰고, ADR로 쓸 결정이 맞는지 다시 확인한다.
5. **부정적 결과가 비면 한 번 더 묻는다.** 그래도 없다고 하면 사용자의 답을 그대로 적는다. 없는 대가를 지어내지 않는다.
6. **분량은 한 화면(40~60줄)이다.** 넘치는 배경은 다른 문서로 보내고 링크한다.
7. **파일을 쓴다.** 이름은 `docs/adr/<오늘 날짜>-<slug>.md`다(날짜는 `date +%F`, slug는 영문 소문자와 하이픈). 같은 이름이 있으면 slug를 바꾼다. 상태는 `proposed`로 시작한다.

## 3. 승인

확인받고 `- 상태: proposed`를 `- 상태: accepted`로 바꾼다. 본문은 고치지 않는다.

## 4. 대체

- 새 ADR을 쓴다. 상태는 확인받고 `accepted`로 쓰며, 머리에 `- 대체함: [<옛 파일명>](<옛 파일명>)`을 단다.
- 옛 ADR의 상태를 `superseded`로 바꾸고, 머리에 `- 대체됨: [<새 파일명>](<새 파일명>)`을 단다.
- **옛 ADR의 본문은 한 글자도 고치지 않는다.** 머리(메타데이터)만 고친다.
- 한쪽 링크만 걸고 끝내지 않는다. 어느 문서에 먼저 도착해도 현재 유효한 결정에 닿아야 한다.

## 5. 부분 조정

- 새 ADR 본문에 "<옛 파일명>의 X 부분을 조정한다"고 쓴다.
- 옛 ADR은 `accepted`로 두고, 머리에 `- 조정됨: [<새 파일명>](<새 파일명>)`을 한 줄 더한다. 조정이 쌓이면 줄을 나열한다.

## 6. 도메인 정의와의 연결

결정이 도메인의 역할·경계·관계를 바꾸면 `/superdomain:domain`으로 DOMAIN.md를 고치자고 안내한다. DOMAIN.md는 이 스킬이 직접 고치지 않는다.

## 하지 않는 것

- 검토하지 않은 대안, 사용자가 말하지 않은 기각 이유, 없는 부정적 결과를 지어내지 않는다.
- 확인 없이 상태를 바꾸지 않는다.
- `accepted`·`superseded` ADR의 본문을 고치지 않는다.
```

- [ ] **Step 3: 검증한다**

```bash
claude plugin validate --strict skills
uv run --quiet --with pyyaml python3 - skills/adr/SKILL.md <<'PY'
import sys, pathlib, yaml
SKILL = set("name description when_to_use argument-hint arguments disable-model-invocation user-invocable allowed-tools disallowed-tools model effort context agent background hooks paths shell metadata license compatibility".split())
AGENT = set("name description model effort maxTurns tools disallowedTools skills memory background omitClaudeMd isolation color".split())
bad = 0
for p in map(pathlib.Path, sys.argv[1:]):
    t = p.read_text(encoding="utf-8"); skill = p.name == "SKILL.md"
    d = yaml.safe_load(t[4:t.index("\n---\n", 4)]) if t.startswith("---\n") else {}
    need = {"name", "description"} | (set() if skill else {"model"})
    errs = sorted(set(d) - (SKILL if skill else AGENT)) + [f"missing:{k}" for k in sorted(need - set(d))]
    if d.get("name") != (p.parent.name if skill else p.stem): errs.append(f"name:{d.get('name')}")
    print("FAIL" if errs else "ok", p, errs or d.get("model", "")); bad += bool(errs)
sys.exit(bad)
PY
wc -l skills/adr/SKILL.md
grep -n 'CLAUDE_SKILL_DIR}/adr-template.md' skills/adr/SKILL.md
grep -c '^- 상태: proposed$' skills/adr/adr-template.md
```

Expected:
- `✔ Validation passed`
- `ok skills/adr/SKILL.md`
- SKILL.md 150줄 이하
- 템플릿 경로 `grep`이 한 줄 나오고, 템플릿의 `- 상태: proposed` 줄 수는 `1`

- [ ] **Step 4: 커밋한다**

```bash
git add skills/adr
git commit -q -F - <<'EOF'
feat(adr): adr 스킬과 템플릿을 새로 쓴다

기술·도메인 결정을 docs/adr/yyyy-MM-dd-slug.md에 MADR 형식으로 남긴다. 쓸 결정인지 판단,
한 ADR에 결정 하나, 실제로 검토한 대안만 적기, 대체 시 양방향 링크 규율을 유지한다.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
git log --oneline -1
```

---

### Task 6: 매니페스트 · README · CHANGELOG · 최종 검증

**Files:**
- Modify: `.claude-plugin/plugin.json` (전체 교체)
- Modify: `.claude-plugin/marketplace.json` (전체 교체)
- Modify: `README.md` (전체 교체)
- Modify: `CHANGELOG.md` (머리말과 `## 0.3.0` 사이에 0.4.0 항목 삽입)

**Interfaces:**
- Consumes: Task 2~5가 만든 스킬 4개(`domain`·`review`·`adr`·`conventions`)와 에이전트 2개(`domain-reviewer`·`convention-reviewer`)의 이름·모델·경로
- Produces: 0.4.0 배포 메타데이터와 문서

- [ ] **Step 1: `.claude-plugin/plugin.json`을 바꾼다**

파일 전체를 아래로 바꾼다.

```json
{
  "name": "superdomain",
  "version": "0.4.0",
  "description": "도메인 정의(DOMAIN.md), 도메인·코딩 컨벤션 리뷰, ADR로 도메인 로직이 드러나는 코드를 돕는다",
  "author": {
    "name": "Cho-D-YoungRae",
    "email": "yrc9229@gmail.com",
    "url": "https://github.com/Cho-D-YoungRae"
  },
  "homepage": "https://github.com/Cho-D-YoungRae/superdomain",
  "repository": "https://github.com/Cho-D-YoungRae/superdomain",
  "license": "MIT",
  "keywords": [
    "ddd",
    "domain-driven-design",
    "bounded-context",
    "code-review",
    "conventions",
    "adr",
    "kotlin",
    "spring",
    "korean"
  ]
}
```

- [ ] **Step 2: `.claude-plugin/marketplace.json`을 바꾼다**

파일 전체를 아래로 바꾼다.

```json
{
  "name": "superdomain",
  "owner": {
    "name": "Cho-D-YoungRae",
    "email": "yrc9229@gmail.com",
    "url": "https://github.com/Cho-D-YoungRae"
  },
  "metadata": {
    "description": "superdomain 배포용 Claude Code 마켓플레이스 — 저장소 자체가 플러그인이자 마켓플레이스다"
  },
  "plugins": [
    {
      "name": "superdomain",
      "source": "./",
      "description": "도메인 정의(DOMAIN.md), 도메인·코딩 컨벤션 리뷰, ADR로 도메인 로직이 드러나는 코드를 돕는다",
      "keywords": [
        "ddd",
        "domain-driven-design",
        "bounded-context",
        "code-review",
        "conventions",
        "adr",
        "kotlin",
        "spring",
        "korean"
      ],
      "category": "workflow"
    }
  ]
}
```

- [ ] **Step 3: `README.md`를 바꾼다**

파일 전체를 아래로 바꾼다(바깥 ```` 울타리는 빼고).

````markdown
# superdomain

도메인 로직이 드러나는 코드를 돕는 Claude Code 플러그인.

- 도메인마다 역할·기능·관계를 `docs/DOMAIN.md` 한 파일에 정의한다.
- 변경이 도메인 정의와 코딩 컨벤션을 따르는지 리뷰한다.
- 되돌리기 비싼 결정을 ADR로 남긴다.

아키텍처를 문서로 정하지 않는다. 대신 코드가 권장 방식(코딩 컨벤션)을 따르는지 리뷰로 확인한다. 스크립트가 없어서 Claude Code 말고는 설치할 것이 없다.

## 설치

Claude Code 세션 안에서:

```
/plugin marketplace add Cho-D-YoungRae/superdomain
/plugin install superdomain@superdomain
```

터미널에서:

```bash
claude plugin marketplace add Cho-D-YoungRae/superdomain
```

```bash
claude plugin install superdomain@superdomain
```

## 스킬

| 스킬 | 언제 쓰나 |
|---|---|
| `/superdomain:domain` | 도메인을 처음 정의하거나, 도메인을 추가·분리·병합하거나, 역할·관계를 바꿀 때 |
| `/superdomain:review` | 커밋·PR 전에 변경이 도메인 정의와 코딩 컨벤션을 따르는지 볼 때, 도메인이 너무 커지지 않았는지 점검할 때 |
| `/superdomain:adr` | 되돌리기 비싼 기술·도메인 결정을 기록하거나, ADR을 승인·대체할 때 |
| `/superdomain:conventions` | Kotlin·Java 코드를 쓸 때 코딩 컨벤션을 적용한다. `.kt`·`.java` 작업에서 자동으로 걸린다 |

`review`의 인자는 `[domain|code] [경로 | 커밋 범위 | 전체]`다. 인자가 없으면 현재 브랜치의 변경과 커밋하지 않은 변경을 두 관점으로 모두 본다.

## 에이전트

| 에이전트 | 모델 | 하는 일 |
|---|---|---|
| `domain-reviewer` | opus | 도메인 정의와 코드를 도메인 경계 관점에서 검토한다. domain·review 스킬이 호출한다 |
| `convention-reviewer` | sonnet | Kotlin·Java 코드를 코딩 컨벤션 기준으로 검토한다. review 스킬이 호출한다 |

둘 다 읽기 전용이고, 모델은 에이전트 파일에서만 정한다.

## 대상 프로젝트에 생기는 파일

| 경로 | 무엇 |
|---|---|
| `docs/DOMAIN.md` | 도메인별 역할·기능·분류·코드 위치와 도메인 간 관계 |
| `docs/adr/yyyy-MM-dd-slug.md` | 결정 기록 |

`domain` 스킬은 동의를 받아 대상 CLAUDE.md에 DOMAIN.md를 가리키는 한 줄을 추가할 수 있다.

## 언어 범위

도메인 정의·도메인 리뷰·ADR은 언어와 무관하다. 코딩 컨벤션과 컨벤션 리뷰는 Kotlin·Java(Spring·JPA) 전용이다. 대상 프로젝트의 CLAUDE.md에 다른 규칙이 있으면 그 규칙이 우선한다. 컨벤션이 맞지 않는 프로젝트에서는 그 프로젝트에서 플러그인을 끈다.

## 0.3.x에서 올라왔다면

산출물 위치와 형식이 바뀌었다. [CHANGELOG](CHANGELOG.md)의 0.4.0 이행 절차를 따른다.

## 저장소 구조

```
.claude-plugin/          plugin.json, marketplace.json — 이 저장소가 플러그인이자 마켓플레이스다
skills/
  domain/                SKILL.md, domain-guide.md (DOMAIN.md 형식과 경계·분류 판단 기준)
  review/                SKILL.md
  adr/                   SKILL.md, adr-template.md
  conventions/           SKILL.md, conventions.md (코딩 컨벤션)
agents/                  domain-reviewer.md, convention-reviewer.md
docs/superpowers/        설계 스펙과 구현 계획
```

지식 파일(`domain-guide.md`, `conventions.md`)은 주제마다 하나이고, 해당 스킬과 리뷰 에이전트가 같은 파일을 읽는다.

## 로컬 개발

```bash
claude --plugin-dir /path/to/superdomain
```

스킬은 `/superdomain:<스킬명>`으로 노출된다. SKILL.md 본문은 바로 반영되지만, `plugin.json`이나 에이전트를 고쳤다면 `/reload-plugins`가 필요하다.

구조 검증:

```bash
claude plugin validate --strict .claude-plugin/plugin.json
```

```bash
claude plugin validate --strict skills
```

```bash
claude plugin validate --strict agents
```
````

- [ ] **Step 4: `CHANGELOG.md`에 0.4.0 항목을 넣는다**

`CHANGELOG.md`의 머리말 문단("이 플러그인의 버전은 … 담을 수 있다.")과 `## 0.3.0 — 2026-09-29` 제목 사이에 아래 내용을 넣는다. 기존 0.3.0 이하 내용은 그대로 둔다(바깥 ```` 울타리는 빼고).

````markdown
## 0.4.0 — 2026-09-29

플러그인을 도메인 정의·리뷰·ADR에 집중하도록 다시 설계했다. 설계는
`docs/superpowers/specs/2026-09-29-superdomain-redesign-design.md`에 있다.

### Breaking

- 스킬이 `domain`·`review`·`adr`·`conventions` 넷으로 바뀌었다. `init`·`model`·`apply`·`sync`·`evolve`·`migrate`는 없어졌다.
- 산출물은 `docs/DOMAIN.md`와 `docs/adr/` 둘뿐이다. `docs/superdomain/`의 `summary.md`·`contexts/`·`state/`·`conventions/`는 더 이상 쓰지 않는다.
- DOMAIN.md 형식이 바뀌었다. 도메인마다 역할·기능·분류·코드(선택: 규칙·하지 않는 것)를 적고, 관계는 `도메인 | 의존 대상 | 방식 | 설명` 표로 적는다. 파서가 없으므로 형식은 사람과 Claude가 읽기 위한 것이다.
- 검사 스크립트(`parse_domain.py`·`check_imports.py`·`check_invariants.py`·`collect_signals.py`·`layout.py`·`build_index.py`)와 SessionStart 훅이 없어졌다. 도메인 경계와 코딩 컨벤션은 `review` 스킬의 리뷰 에이전트가 확인한다. python3가 더 이상 필요 없다.
- `references/`(governance·knowledge)가 없어졌다. 필요한 기준은 `skills/domain/domain-guide.md`와 `skills/conventions/conventions.md`로 옮겼다.

### Added

- `conventions` 스킬과 코딩 컨벤션 문서. Kotlin·Java(Spring·JPA) 코드를 쓸 때 적용한다.
- `convention-reviewer` 에이전트(`model: sonnet`). `domain-reviewer`는 새로 썼다(`model: opus`).
- `review`가 두 리뷰어를 병렬로 호출해 한 리포트로 합친다. 인자는 `[domain|code] [경로 | 커밋 범위 | 전체]`다.

### 이행 절차 (0.3.x → 0.4.0)

1. `git mv docs/superdomain/DOMAIN.md docs/DOMAIN.md`
2. `/superdomain:domain`으로 새 형식으로 다시 쓴다. 옛 `docs/superdomain/contexts/*.md`의 불변식 중 핵심은 도메인의 "규칙"으로 옮긴다.
3. `git mv docs/superdomain/adr docs/adr`. ADR 안의 `../DOMAIN.md` 링크는 옮긴 뒤에도 그대로 맞는다.
4. `docs/superdomain/`의 나머지(`summary.md`, `contexts/`, `state/`, `conventions/`)를 지운다. `conventions/`의 팀 규약은 프로젝트 CLAUDE.md로 옮긴다.
5. CLAUDE.md 등에서 `docs/superdomain/`을 가리키는 참조를 찾아 고친다.

   ```bash
   git grep -n 'docs/superdomain/'
   ```

````

(삽입 뒤 `## 0.4.0` 항목의 마지막 줄과 `## 0.3.0` 제목 사이에는 빈 줄 하나가 있어야 한다.)

- [ ] **Step 5: 전체를 검증한다**

```bash
python3 -c "import json; [json.load(open(p, encoding='utf-8')) for p in ('.claude-plugin/plugin.json', '.claude-plugin/marketplace.json')]; print('json ok')"
claude plugin validate --strict .claude-plugin/plugin.json
claude plugin validate --strict .claude-plugin/marketplace.json
claude plugin validate --strict skills
claude plugin validate --strict agents
uv run --quiet --with pyyaml python3 - skills/*/SKILL.md agents/*.md <<'PY'
import sys, pathlib, yaml
SKILL = set("name description when_to_use argument-hint arguments disable-model-invocation user-invocable allowed-tools disallowed-tools model effort context agent background hooks paths shell metadata license compatibility".split())
AGENT = set("name description model effort maxTurns tools disallowedTools skills memory background omitClaudeMd isolation color".split())
bad = 0
for p in map(pathlib.Path, sys.argv[1:]):
    t = p.read_text(encoding="utf-8"); skill = p.name == "SKILL.md"
    d = yaml.safe_load(t[4:t.index("\n---\n", 4)]) if t.startswith("---\n") else {}
    need = {"name", "description"} | (set() if skill else {"model"})
    errs = sorted(set(d) - (SKILL if skill else AGENT)) + [f"missing:{k}" for k in sorted(need - set(d))]
    if d.get("name") != (p.parent.name if skill else p.stem): errs.append(f"name:{d.get('name')}")
    print("FAIL" if errs else "ok", p, errs or d.get("model", "")); bad += bool(errs)
sys.exit(bad)
PY
wc -l skills/*/SKILL.md
git grep -nE 'check_imports|check_invariants|parse_domain|collect_signals|layout\.py|build_index|session_summary|summary\.md|references/|/superdomain:(init|model|apply|sync|evolve|migrate)' -- . ':!CHANGELOG.md' ':!docs/superpowers/' || echo "stale refs: 0"
git grep -n 'docs/superdomain' -- . ':!CHANGELOG.md' ':!docs/superpowers/' ':!skills/domain/SKILL.md' || echo "old layout refs: 0"
diff <(git ls-files | sort) <(printf '%s\n' \
  .claude-plugin/marketplace.json .claude-plugin/plugin.json .gitignore \
  CHANGELOG.md LICENSE README.md \
  agents/convention-reviewer.md agents/domain-reviewer.md \
  docs/superpowers/plans/2026-09-29-superdomain-redesign.md \
  docs/superpowers/specs/2026-09-29-superdomain-redesign-design.md \
  skills/adr/SKILL.md skills/adr/adr-template.md \
  skills/conventions/SKILL.md skills/conventions/conventions.md \
  skills/domain/SKILL.md skills/domain/domain-guide.md \
  skills/review/SKILL.md | sort) \
  && echo "OK: 최종 파일 17개 일치"
```

Expected:
- `json ok`, 네 `validate` 모두 `✔ Validation passed`
- `ok`가 6줄(스킬 4, 에이전트 2 — 에이전트 줄 끝에 `opus`·`sonnet`)
- 모든 SKILL.md가 150줄 이하
- `stale refs: 0`, `old layout refs: 0`
- `OK: 최종 파일 17개 일치`

- [ ] **Step 6: 커밋한다**

```bash
git add .claude-plugin README.md CHANGELOG.md
git commit -q -F - <<'EOF'
docs: 0.4.0 매니페스트·README·CHANGELOG를 갱신한다

버전을 0.4.0으로 올리고 description·keywords를 새 방향에 맞춘다. README를 스킬 4개·에이전트
2개 기준으로 다시 쓰고, CHANGELOG에 0.4.0 변경과 0.3.x 이행 절차를 적는다.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
git log --oneline -1
```

---

## 구현 후 사용자가 직접 확인할 것

**이 절은 구현 작업이 아니다.** Task 6 구현자는 이 절을 실행하지 않는다. 컨트롤러가 최종 보고에서 사용자에게 안내한다.

이 환경에서는 headless `claude -p`의 인증이 만료되어 플러그인을 실제로 띄워 볼 수 없다. 아래는 스펙 §9의 2~6번이고, 구현이 끝난 뒤 사용자가 직접 확인한다.

1. `claude --plugin-dir /Users/choyoungrae/Projects/superdomain`로 띄워 스킬 4개(`/superdomain:domain`·`review`·`adr`·`conventions`)와 에이전트 2개가 잡히는지 본다.
2. 리뷰어가 지식 파일을 실제로 읽는지, 지정한 모델(opus·sonnet)로 도는지 본다.
3. `conventions` 스킬이 Kotlin·Java 파일을 다룰 때만 걸리는지 본다.
4. imstargg에서 `/superdomain:review`를 돌려 두 리뷰어가 병렬로 돌고 한 리포트로 합쳐지는지 본다.
5. 연습 저장소에서 `/superdomain:domain`으로 DOMAIN.md를 만들고 정의 검토가 도는지 본다.

## 구현 중 바뀐 것

실행 중 리뷰에서 나온 판정으로 아래는 위 Task 블록과 다르게 구현됐다. 기준은 스펙이고, 이유는 각 커밋 메시지에 있다.

- Task 2: domain SKILL.md 1단계는 모드와 상관없이 맥락을 먼저 읽는다(스펙 §5.1). — 5c6c869
- Task 3: convention-reviewer는 「다른 도메인은 ID로 참조한다」를 검토한다. 제외 범위는 도메인 귀속·관계 표 정합·DOMAIN.md 수정 판단뿐이다. 검증 grep 패턴은 '프로젝트 규칙을 따'가 맞다. — 8ec66c8
- Task 4: 경로 인자는 전체 점검이 아니라 기본 변경을 그 경로로 거르는 조건이다(스펙 §5.2). 리뷰어에게는 리뷰어가 실행할 수 있는 `git diff` 명령과 상태(새 파일·삭제됨)를 붙인 파일 목록을 넘긴다. — 4ef57e6
- Task 6: README의 로컬 개발 안내는 "SKILL.md를 포함해 플러그인 파일을 고쳤다면 `/reload-plugins`로 반영한다"이고, 구조 검증에 marketplace.json이 들어간다. — 1a766da
- 최종 리뷰: 0.3.x 배치를 만난 domain·review의 이행 안내, 리뷰어 git 명령의 `-C <프로젝트 루트>`, 부분 조정 ADR의 상태, ADR 링크 표기 `[<파일명>](<파일명>.md)` 등을 반영했다.
