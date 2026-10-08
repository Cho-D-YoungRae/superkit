# superglossary 0.7.0 LLM 용어집 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** superglossary를 JSON·생성물·Python CLI 없이, LLM이 `docs/superglossary/*.md`를 직접 읽고 고치는 플러그인(스킬 `glossary`·`check`, 에이전트 `glossary-scanner`)으로 바꾼다.

**Architecture:** 산출물은 사용자 프로젝트의 md 표다. 스킬 본문은 짧게 두고 형식·규칙·분리 절차는 `skills/glossary/glossary-guide.md`에 둔다(`${CLAUDE_SKILL_DIR}`로 참조). 검증은 단위 테스트 대신 `claude plugin validate`와 임시 픽스처에서 돌리는 시나리오 eval이다.

**Tech Stack:** Claude Code 플러그인(스킬·서브에이전트 md), git, bash(픽스처 생성만)

**Spec:** `plugins/superglossary/docs/superpowers/specs/2026-10-07-llm-glossary-design.md`

## Global Constraints

- 용어집 경로: `docs/superglossary/glossary.md`, 분리 뒤 `docs/superglossary/<도메인>.md` (spec D1)
- 표 열: `| 한글 | 영문 | 축약 | 금지 | 설명 |`, 한글 가나다순 (spec D2)
- 포인터 줄(문구 그대로): `- 용어 사전: docs/superglossary/glossary.md (이름을 짓기 전에 읽는다. 없는 단어는 /superglossary:glossary로 추가한다)`
- 분리 제안 기준: 용어 300개 초과, 제안만 한다 (spec D5)
- 스크립트를 두지 않는다. 플러그인은 `plugins/superglossary/` 밖을 참조하지 않는다
- 스킬 문체: superdomain 스킬과 같은 해라체("~한다"), 이유를 함께 적고 대문자 MUST를 쓰지 않는다(skill-creator 권고). description은 spec §5 초안을 그대로 쓴다
- 커밋: Conventional Commits + 한국어, 범위 `superglossary`, 끝에 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`
- 버전 0.7.0은 `plugin.json` 한 곳에만 적는다

## Review Focus

1. 지침 파일이 `CLAUDE.md` 계열인 프로젝트 — 포인터 줄을 `AGENTS.md`가 아니라 그 파일에 제안해야 한다 (Task 4 시나리오 S4)
2. 이미 분리된 용어집 — index의 코드 범위로 도메인 파일을 골라 거기에 추가하고, 공통 용어는 공통 표에서 재사용해야 한다 (Task 4 시나리오 S5)
3. 설명에 `|`가 든 용어 — 표가 깨지지 않게 `\|`로 써야 한다 (Task 1 guide 문구 + grep)
4. git 저장소 밖에서 실행 — `git rev-parse`가 실패하면 현재 디렉터리를 기준으로 삼아야 한다 (Task 1·2 SKILL.md 문구 + grep)
5. 기존 단어 조합만으로 지을 수 있는 이름 — 아무것도 추가하지 않아야 한다 (Task 4 시나리오 S1의 `일시` 재사용)

---

### Task 1: `glossary` 스킬과 `glossary-scanner` 에이전트

**Files:**
- Create: `plugins/superglossary/skills/glossary/SKILL.md`
- Create: `plugins/superglossary/skills/glossary/glossary-guide.md`
- Modify (전체 다시 씀): `plugins/superglossary/agents/glossary-scanner.md`

**Interfaces:**
- Produces: 스킬 호출명 `/superglossary:glossary`; 에이전트 호출명 `superglossary:glossary-scanner`, 입력 블록 형식:
  ```
  프로젝트 루트: <절대 경로>
  용어집: <절대 경로>/docs/superglossary/glossary.md
  기준 문서: ${CLAUDE_SKILL_DIR}/glossary-guide.md
  ```
  (superdomain `domain` 스킬의 "자체 검토 호출"과 같은 방식 — 세션 대화는 넘기지 않는다)

- [ ] **Step 1: `glossary-guide.md` 작성** — 세 절로 쓴다. ① 형식: spec §3의 분리 전 템플릿(기본 용어 셋 포함)과 분리 후 `glossary.md`(규칙 → `## 도메인` index 표 → `## 공통 용어`) 및 도메인 파일(`# <도메인> 용어` + 표) 템플릿, 셀 안의 `|`는 `\|`로 쓴다는 줄. ② 등록 규칙: spec §4 전체(예시 표, 확정 주체, 충돌 조건, 금지 단어 단위). ③ 분리 절차: 도메인 후보 제안(도메인 정의 문서가 있으면 그 이름) → 사용자 확인 → 도메인 파일 생성 → 공통 용어 판정(여러 도메인이 쓰는 단어) → index 작성(코드 범위 포함) → 원래 표에서 옮긴 행 제거.

- [ ] **Step 2: `SKILL.md` 작성** — frontmatter는 `name: glossary`와 spec §5의 `description`·`argument-hint`·`allowed-tools`를 그대로. 본문은 spec §5의 다섯 단계(찾기·추가·수정·삭제·생성·분리)와 포인터 줄 규칙, "하지 않는 것"을 쓰고, 상세는 `${CLAUDE_SKILL_DIR}/glossary-guide.md`를 가리킨다. 찾기 단계에 "git 저장소가 아니면 현재 디렉터리를 기준으로 삼는다"를 넣는다. 생성 단계의 scanner 호출은 Interfaces의 입력 블록을 그대로 보여 준다. 본문은 80줄 안팎으로 유지한다(이름을 지을 때마다 불릴 수 있다).

- [ ] **Step 3: `glossary-scanner.md` 다시 쓰기** — frontmatter `name: glossary-scanner`, `model: sonnet`, `tools: Read, Grep, Glob`, description은 "기존 코드베이스에서 용어 후보(단어 단위)와 혼용(영문 변형·빈도)을 찾는 에이전트. superglossary의 glossary 스킬이 용어집을 만들 때 부른다". 본문은 spec §5 scanner 절(입력, 작업, 출력 세 표, 표준 선정은 사용자 몫). 등록 규칙은 입력의 기준 문서를 읽어 따른다고 적는다. lint·Bash 언급은 넣지 않는다.

- [ ] **Step 4: 검증**

Run:
```bash
cd /Users/chodyoungrae/Projects/superkit && claude plugin validate . \
 && grep -c "이름을 짓기 전에 읽는다. 없는 단어는 /superglossary:glossary로 추가한다" plugins/superglossary/skills/glossary/SKILL.md \
 && grep -c '300' plugins/superglossary/skills/glossary/SKILL.md \
 && grep -c 'git 저장소가 아니면' plugins/superglossary/skills/glossary/SKILL.md \
 && grep -c '\\|' plugins/superglossary/skills/glossary/glossary-guide.md \
 && ! grep -nE 'lint|glossary\.py|Bash' plugins/superglossary/agents/glossary-scanner.md \
 && wc -l plugins/superglossary/skills/glossary/SKILL.md
```
Expected: validate 통과, 각 grep 1 이상, scanner에 lint·glossary.py·Bash 없음, SKILL.md 100줄 이하.

- [ ] **Step 5: Commit**

```bash
git add plugins/superglossary/skills/glossary plugins/superglossary/agents/glossary-scanner.md
git commit -m "feat(superglossary): md 용어집을 관리하는 glossary 스킬을 추가한다"
```

### Task 2: `check` 스킬 다시 쓰기

**Files:**
- Modify (전체 다시 씀): `plugins/superglossary/skills/check/SKILL.md`

**Interfaces:**
- Consumes: Task 1의 용어집 형식(index의 `코드 범위` 열, `## 공통 용어`), 추가 후보를 넘길 곳 `/superglossary:glossary`

- [ ] **Step 1: `SKILL.md` 작성** — frontmatter는 `name: check`와 spec §5의 `description`·`argument-hint`·`allowed-tools`를 그대로. 본문은 spec §5 check 흐름 다섯 단계와 두 보고 표의 열을 그대로 쓴다. 대상 결정의 명령은 `git diff --name-only`(unstaged), `git diff --cached --name-only`(staged), `git ls-files --others --exclude-standard`(untracked)이고 삭제된 파일은 뺀다. 커밋 범위가 주어지면 `git diff <범위>`를 본다. 용어집 형식(분리 여부·index·코드 범위)은 형식을 다시 적지 않고 `${CLAUDE_SKILL_DIR}/../glossary/glossary-guide.md`를 읽게 한다(형식의 출처를 하나로 둔다). git 저장소가 아니면 경로 인자가 필요하다고 안내하고 끝낸다.

- [ ] **Step 2: 검증**

Run:
```bash
cd /Users/chodyoungrae/Projects/superkit && claude plugin validate . \
 && ! grep -nE 'lint|glossary\.py|check-analyzer|\.claude/superglossary' plugins/superglossary/skills/check/SKILL.md \
 && grep -c 'docs/superglossary' plugins/superglossary/skills/check/SKILL.md
```
Expected: validate 통과, 옛 CLI·에이전트 언급 없음, 새 경로 1 이상.

- [ ] **Step 3: Commit**

```bash
git add plugins/superglossary/skills/check/SKILL.md
git commit -m "feat(superglossary): check가 변경분을 md 용어집과 대조한다"
```

### Task 3: CLI·테스트·옛 스킬 제거와 문서·버전

**Files:**
- Delete: `plugins/superglossary/{templates,bin,tests,scripts}/`, `plugins/superglossary/skills/{init,add}/`, `plugins/superglossary/agents/check-analyzer.md`, `plugins/superglossary/docs/superpowers/specs/2026-06-20-glossary-feature-design.md`, `.../specs/2026-07-09-usability-improvements-design.md`, `.../plans/2026-06-20-glossary-feature.md`, `.../plans/2026-07-09-usability-improvements.md`, `.github/workflows/superglossary.yml`
- Modify: `plugins/superglossary/.claude-plugin/plugin.json`, `plugins/superglossary/README.md`(다시 씀), `plugins/superglossary/AGENTS.md`(다시 씀), `plugins/superglossary/CHANGELOG.md`, `AGENTS.md`(루트), `CONTRIBUTING.md`

- [ ] **Step 1: 삭제** — 위 Delete 목록을 `git rm -r`로 지운다.

- [ ] **Step 2: `plugin.json`** — `version`을 `"0.7.0"`, `description`을 `"프로젝트 용어사전을 md로 관리하고 일관된 이름 짓기를 돕는 Claude Code 플러그인"`으로.

- [ ] **Step 3: 플러그인 `AGENTS.md` 다시 쓰기** — superdomain처럼 짧게: 무엇인지 한 줄, 구조(`skills/glossary/`·`skills/check/`·`agents/glossary-scanner.md`·`docs/superpowers/`), 규칙(스크립트를 두지 않는다, 용어집 형식·규칙의 출처는 `skills/glossary/glossary-guide.md` 하나, 버전은 `plugin.json`에만), 검증(`claude plugin validate .`, `claude --plugin-dir .`). 사용자 프로젝트 지침 파일 규칙은 루트 AGENTS.md를 따른다고 적는다.

- [ ] **Step 4: `README.md` 다시 쓰기** — 절: 소개(문제: 같은 개념의 다른 번역), 핵심 개념(단어별 등록과 영문 기준 예외 — `매도호가 → ask` 예시, 축약어 통제, 금지 단어), 설치(기존 명령 유지), 빠른 시작(`/superglossary:glossary` → 생성·포인터 줄, 작업 중 자율 추가, `/superglossary:check`), 구성 요소 표(스킬 2·에이전트 1), 파일 형식(분리 전·후 트리, 300개 기준), 0.6.0에서 옮기기(CHANGELOG 0.7.0 항목을 가리키는 한 줄), 출처(김영한 강의 문단 그대로), 라이선스.

- [ ] **Step 5: `CHANGELOG.md`** — `## [Unreleased]` 아래에 `## [0.7.0] - 2026-10-07` 항목. Changed(BREAKING): 용어집이 `docs/superglossary/*.md`로, 스킬이 `glossary`·`check`로, 지침 파일은 `@import` 블록 대신 포인터 줄. Removed: `glossary.json`·`core.md`·`terms.md`, CLI(`glossary.py`·`bin/superglossary`), `lint`, `init`·`add` 스킬, `check-analyzer`, `bump_version.py`. 옮기는 방법 세 단계: ① `.claude/superglossary/glossary.json`의 용어를 `/superglossary:glossary`로 `docs/superglossary/glossary.md`에 옮겨 달라고 요청 ② 지침 파일의 `<!-- superglossary:begin -->`…`<!-- superglossary:end -->` 블록을 지우고 포인터 줄을 넣는다 ③ `.claude/superglossary/`를 지운다.

- [ ] **Step 6: 루트 문서** — `AGENTS.md`에서 "superglossary는 `plugins/superglossary/scripts/bump_version.py`로…" 줄과 `python3 -m unittest discover -s plugins/superglossary/tests` 코드 블록을 지운다. `CONTRIBUTING.md`의 개발·검증 블록에서 같은 unittest 줄을, 릴리즈 절차 1번에서 "superglossary는 `python3 plugins/superglossary/scripts/bump_version.py <version>`을, " 부분을 지운다(superrelease 안내는 남긴다).

- [ ] **Step 7: 검증**

Run:
```bash
cd /Users/chodyoungrae/Projects/superkit && claude plugin validate . \
 && ! grep -rnE 'glossary\.py|bump_version|core\.md|terms\.md|glossary\.json|check-analyzer|superglossary:(init|add)([^a-z]|$)|plugins/superglossary/tests' \
      AGENTS.md CONTRIBUTING.md README.md .github plugins/superglossary --exclude=CHANGELOG.md --exclude-dir=specs --exclude-dir=plans \
 && ls plugins/superglossary
```
Expected: validate 통과, 남은 참조 없음, 디렉터리에 `.claude-plugin agents skills docs AGENTS.md CHANGELOG.md LICENSE README.md`만.

- [ ] **Step 8: Commit**

```bash
git add -A plugins/superglossary AGENTS.md CONTRIBUTING.md .github/workflows
git commit -m "feat(superglossary)!: CLI·JSON·lint를 걷어 내고 0.7.0으로 올린다"
```

### Task 4: 시나리오 eval

**Files:**
- Create (저장소 밖, 커밋하지 않음): `/tmp/superglossary-eval/S1`…`S5/`
- Modify (실패 시에만): Task 1·2의 스킬 파일

**Interfaces:**
- Consumes: Task 1·2의 스킬 파일(서브에이전트에게 SKILL.md 경로를 준다)

- [ ] **Step 1: 픽스처 생성** — 각 디렉터리에서 `git init`, 아래 상태로 만든 뒤 첫 커밋까지 한다(S3은 변경을 커밋하지 않은 채 둔다). `기본 셋` = spec §3 템플릿 그대로.
  - S1: `AGENTS.md`(포인터 줄 포함), `docs/superglossary/glossary.md`(기본 셋), `src/Execution.kt`(빈 data class)
  - S2: S1과 같되 표에 `| 용어N | termN |  |  | 설명 |`(N=1..300, bash `seq`로 생성)을 더한다
  - S3: 기본 셋 + `| 회원 | member |  | customer | 서비스 가입자 |`, 커밋 뒤 `src/Order.kt`에 `val customerId: Long` 과 `val regDt: String`을 추가(커밋하지 않음)
  - S4: `CLAUDE.md`(빈 제목 한 줄)와 `src/Member.kt`만, 용어집 없음
  - S5: 분리된 용어집 — `glossary.md`(규칙, `## 도메인` 표에 `| 주문 | order.md | src/order/** | 주문 |`, `## 공통 용어`에 기본 셋), `order.md`(`| 주문 | order |  |  | 구매 요청 |`), `src/order/Order.kt`

- [ ] **Step 2: 서브에이전트 실행** — 다섯 개를 한 번에 띄운다. 프롬프트 공통부: "작업 디렉터리 `<S 경로>`. 스킬 `<SKILL.md 절대 경로>`를 읽고 따른다(`${CLAUDE_SKILL_DIR}`는 그 SKILL.md가 있는 디렉터리다). 사용자에게 물어야 하는 지점에 오면 멈추고, 할 질문을 최종 보고에 그대로 적는다. 마지막에 바꾼 파일 목록을 적는다."
  - S1(glossary): "src/Execution.kt에 매도호가, 체결수량, 체결일시 필드를 추가해줘"
  - S2(glossary): "src/Execution.kt에 체결 필드를 추가해줘"
  - S3(check): "/superglossary:check"
  - S4(glossary): "용어집 만들어줘"
  - S5(glossary): "src/order/Order.kt에 취소일시 필드를 추가해줘"

- [ ] **Step 3: 판정** — 픽스처의 `git status`/`git diff`와 보고를 보고 판정한다.
  - S1: `체결`·`수량` 행이 추가됨, `체결수량`·`매도호가체결` 행 없음, `일시` 행 그대로(중복 없음), 보고에 `매도호가`를 한 항목(`ask` 계열)으로 둘지 묻는 질문, `용어 등록:` 알림 줄
  - S2: 표가 304행(생성 300 + 기본 셋 3 + `체결` 1), `docs/superglossary/`에 새 파일 없음, 보고에 분리 제안
  - S3: 보고에 `customer`(표준 `member`)와 `reg`(미등록 축약) 둘 다, `src/Order.kt`의 diff가 eval 전과 같음
  - S4: `docs/superglossary/glossary.md`가 기본 셋 3행으로 생성, `CLAUDE.md` 변경 없음, 보고에 스캔 여부 질문 또는 `CLAUDE.md`를 대상으로 한 포인터 줄 제안(`AGENTS.md` 아님)
  - S5: `취소` 행이 `order.md`에 추가되고 `glossary.md`의 공통 표는 그대로, `일시` 재사용

- [ ] **Step 4: 실패 처리** — 실패한 시나리오마다 원인을 스킬 문구에서 찾아 고치고(특정 예시에 맞춘 땜질 대신 이유를 설명하는 쪽으로) 그 시나리오만 픽스처를 새로 만들어 다시 돌린다. 두 번 고쳐도 실패하면 멈추고 사용자에게 보고한다. 모두 통과하면 결과 표(시나리오 | 판정 | 근거 한 줄)를 채팅에 남긴다.

- [ ] **Step 5: Commit (고친 경우만)**

```bash
git add plugins/superglossary/skills
git commit -m "fix(superglossary): eval에서 드러난 스킬 지시를 고친다"
```
