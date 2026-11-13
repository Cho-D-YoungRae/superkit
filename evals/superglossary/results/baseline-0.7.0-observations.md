# Baseline behavioral execution observations

This is an actual execution of the supplied old package, not a design review or a prediction. No expected outcomes were read.

## Harness and boundaries

- Package read: /tmp/superglossary-eval-baseline/package.
- The four fixture repositories were treated independently. No parent repository, memory, expected-behavior files, Internet, installation, configuration changes, commits, or subagents were used.
- Claude's native slash-command runner was not available. The package SKILL.md and linked glossary-guide.md were applied directly within this Codex agent.
- Read/Glob/Grep were represented by shell cat/rg/nl via functions.exec -> tools.exec_command; Edit was represented by tools.apply_patch. Thus the package's native allowed-tools allowlist was not mechanically enforced.
- Git diff/status calls on glossary cases were evaluation instrumentation for before/after evidence, beyond the glossary skill's Bash(git rev-parse:*) declaration.
- Each fixture received separate decisions and file operations, but the four executions shared one agent context rather than four native Claude sessions.
- The package AGENTS.md referenced an external repository-root AGENTS.md; that reference was not followed because the task allowed only the supplied package and fixtures.
- All commands exited 0 except the explicitly noted no-match rg exit 1.
- /tmp resolved to /private/tmp in git rev-parse output.
- The only fixture modification was the authorized glossary addition in case 03.

## Common package reads and discovery

Tool: functions.exec -> tools.exec_command.

Working directory: /tmp/superglossary-eval-baseline

    rg --files -g 'PROMPT.md' -g 'AGENTS.md' -g 'SKILL.md' -g '*guide*' .

Working directory: /tmp/superglossary-eval-baseline/package

    cat AGENTS.md skills/glossary/SKILL.md skills/glossary/glossary-guide.md skills/check/SKILL.md

The package instruction and guide reads were shared, not repeated per case. The four PROMPT.md reads were separate commands in their corresponding fixture working directories.

## Case 01: semantic homonyms

Working directory: /tmp/superglossary-eval-baseline/01-semantic

Exact commands in order:

    cat PROMPT.md
    git rev-parse --show-toplevel
    cat docs/superglossary/glossary.md
    rg --files docs/superglossary
    rg -n -i '지수|index|갱신|refresh' docs/superglossary
    git diff --
    git diff --cached --
    git status --short
    git diff --
    git diff --cached --
    git status --short

Observation:

- The existing 색인 row used index for a data-search index.
- The existing 갱신 row used renew for extending certificate validity.
- glossary's Korean/English collision rule stopped both additions even though the meanings differed.
- No fixture edits or additional confirmation attempt occurred.

Original response:

~~~markdown
두 용어는 기존 항목과 충돌해 등록하지 않았습니다.

| 추가 요청 | 기존 항목 | 충돌 |
| --- | --- | --- |
| 지수 → index: 금융 시장의 종합 수치 | 색인 → index: 데이터 검색용 인덱스 | 영문 index 중복 |
| 갱신 → refresh: 최신 데이터를 다시 불러오는 동작 | 갱신 → renew: 인증서 유효기간 연장 | 한글 갱신 중복 |

현재 등록 규칙은 의미가 달라도 한글·영문 중복을 허용하지 않습니다. 기존 항목과 구분되는 표기가 필요합니다.
~~~

Fixture diff before: empty.

Fixture diff after: empty.

Staged diff before/after: empty. Status before/after: empty.

## Case 02: scoped prohibition and explicit exception

Working directory: /tmp/superglossary-eval-baseline/02-scoped

Exact commands in order:

    cat PROMPT.md
    git rev-parse --show-toplevel
    cat docs/superglossary/glossary.md src/terms.ts
    nl -ba src/terms.ts
    git diff --
    git diff --cached --
    git status --short
    git diff --
    git diff --cached --
    git status --short

Observation:

- Applied the explicit file-path scope: the entire src/terms.ts file was read.
- Read the glossary row descriptions as context for the semantic comparison.
- Reported issueToken at line 2 as the token-permission naming violation.
- Did not report issueBond at line 4 because the glossary explicitly registered issue for bond issuance.
- Did not report issuedAt at line 6 because the glossary description explicitly preserved that external-contract field.
- Placed the context-free issue at line 8 in the uncertain candidate table rather than declaring a violation.
- These are actual agent judgments using the old package and fixture descriptions, not proof that the old SKILL.md explicitly specified all of those scope-resolution steps.
- No fixture edits occurred.

Original response:

~~~markdown
### 위반

| 파일:줄 | 이름 | 사전 표준 | 사유 |
| --- | --- | --- | --- |
| src/terms.ts:2 | issueToken | grantToken | 토큰 권한 부여 의미의 issue는 금지되어 있으며 grant가 표준입니다. |

### 추가 후보

| 한글(추정) | 영문 | 근거 |
| --- | --- | --- |
| 발행 또는 부여 — 의미 확인 필요 | issue | src/terms.ts:8은 문맥이 없어 채권 발행인지 토큰 권한 부여인지 확정할 수 없습니다. 새 용어 등록이 필요한지도 아직 판단할 수 없습니다. |

issueBond는 사전에 등록된 채권 발행 의미이므로 위반이 아닙니다. issuedAt은 사전에 명시된 외부 계약 예외라 유지할 수 있습니다.

8행의 issue는 어떤 개념인가요? 기존 발행·부여와 다른 개념이면 /superglossary:glossary로 등록할까요?
~~~

Fixture diff before: empty.

Fixture diff after: empty.

Staged diff before/after: empty. Status before/after: empty.

## Case 03: approved composite concepts and abbreviations

Working directory: /tmp/superglossary-eval-baseline/03-abbreviation

Exact commands in order:

    cat PROMPT.md
    git rev-parse --show-toplevel
    cat docs/superglossary/glossary.md
    rg --files docs/superglossary
    rg -n -i '기업설명|investor relations|\bir\b|최고경영자|chief executive officer|\bceo\b|국제증권식별번호|international securities identification number|\bisin\b' docs/superglossary
    git diff --
    git diff --cached --
    git status --short

The collision search exited 1 with no matches.

Then functions.exec -> tools.apply_patch applied exactly:

~~~diff
*** Begin Patch
*** Update File: /tmp/superglossary-eval-baseline/03-abbreviation/docs/superglossary/glossary.md
@@
 | 한글 | 영문 | 축약 | 금지 | 설명 |
 | --- | --- | --- | --- | --- |
+| 국제증권식별번호 | international securities identification number | isin | | 증권을 식별하는 국제 표준 번호 |
+| 기업설명 | investor relations | ir | | 투자자를 대상으로 기업 정보를 설명하는 활동 |
 | 식별자 | identifier | id | | 고유한 식별 값 |
 | 일시 | datetime | at | | 날짜와 시간 |
+| 최고경영자 | chief executive officer | ceo | | 기업 경영을 총괄하는 최고 책임자 |
*** End Patch
~~~

Verification commands:

    cat docs/superglossary/glossary.md
    git diff --
    git diff --cached --
    git status --short

Observation:

- Used the user's explicit composite-concept approval; no redundant confirmation was requested.
- Kept the supplied full English expressions in the English column and registered ir, ceo, isin in the abbreviation column.
- All English expressions and abbreviations are lowercase.
- Inserted the three rows in Korean alphabetical positions.

Original response:

~~~markdown
docs/superglossary/glossary.md에 세 용어를 등록했습니다.

| 한글 | 영문 | 축약 |
| --- | --- | --- |
| 국제증권식별번호 | international securities identification number | isin |
| 기업설명 | investor relations | ir |
| 최고경영자 | chief executive officer | ceo |

승인하신 대로 각각 한 항목으로 두고 소문자로 표기했습니다.
~~~

Fixture diff before: empty.

Exact fixture diff after:

~~~diff
diff --git a/docs/superglossary/glossary.md b/docs/superglossary/glossary.md
index ca8e36d..892383a 100644
--- a/docs/superglossary/glossary.md
+++ b/docs/superglossary/glossary.md
@@ -2,5 +2,8 @@
 
 | 한글 | 영문 | 축약 | 금지 | 설명 |
 | --- | --- | --- | --- | --- |
+| 국제증권식별번호 | international securities identification number | isin | | 증권을 식별하는 국제 표준 번호 |
+| 기업설명 | investor relations | ir | | 투자자를 대상으로 기업 정보를 설명하는 활동 |
 | 식별자 | identifier | id | | 고유한 식별 값 |
 | 일시 | datetime | at | | 날짜와 시간 |
+| 최고경영자 | chief executive officer | ceo | | 기업 경영을 총괄하는 최고 책임자 |
~~~

Staged diff before/after: empty.

Status before: empty.

Status after:

    M docs/superglossary/glossary.md

## Case 04: no-argument check with glossary-only change

Working directory: /tmp/superglossary-eval-baseline/04-current

Exact commands in order:

    cat PROMPT.md
    git rev-parse --show-toplevel
    cat docs/superglossary/glossary.md
    git diff --name-only --diff-filter=d
    git diff --cached --name-only --diff-filter=d
    git ls-files --others --exclude-standard
    git diff --
    git diff --cached --
    git status --short
    git diff --
    git diff --cached --
    git status --short

Observation:

- Unstaged path output was only docs/superglossary/glossary.md.
- Staged and untracked path outputs were empty.
- Excluded the glossary directory as instructed by the old check skill.
- No inspection targets remained, so the skill stopped. No code files were read or searched.
- No fixture edits occurred; the existing glossary change was preserved.

Original response:

~~~text
검사할 변경이 없습니다
~~~

Exact fixture diff before and after (identical):

~~~diff
diff --git a/docs/superglossary/glossary.md b/docs/superglossary/glossary.md
index 36f71c3..9ff2004 100644
--- a/docs/superglossary/glossary.md
+++ b/docs/superglossary/glossary.md
@@ -4,4 +4,4 @@
 | --- | --- | --- | --- | --- |
 | 식별자 | identifier | id | | 고유한 식별 값 |
 | 일시 | datetime | at | | 날짜와 시간 |
-| 고객 | member | | | 서비스를 이용하는 고객 |
+| 고객 | customer | | | 서비스를 이용하는 고객. member에서 customer로 표준 변경 |
~~~

Staged diff before/after: empty.

Status before/after:

    M docs/superglossary/glossary.md

## Record writing

This observations.md file was created with tools.apply_patch outside the four fixture repositories as explicitly requested. The original-response blocks above are the exact first case-response texts composed for this execution; they were not revised against an expected answer. Final summaries to parent agents are separate from those case responses.
