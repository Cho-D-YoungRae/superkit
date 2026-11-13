# Source-package behavioral observations

Execution used only `/tmp/superglossary-green-source-package` and nine `/tmp/superglossary-green-source/<case>` fixtures (eight original cases plus the separately requested 03-preference). No parent repository, expected results, previous observations, memory, Internet, user settings, or subagents were consulted. The supplied skills were executed by this Codex agent; a native Claude command dispatcher was not available. Shell `cat`/`sed`/`nl`, `rg`, and `apply_patch` served as Read/Grep/Glob/Edit equivalents. Git reads were real. No package files, code, Git state, or instruction files were changed. Only authorized glossary files in 01 and 03 were edited. This observation file is evaluator instrumentation.

Independent cases were interleaved; 01 and 04-current completed first and factual outcomes were sent immediately. Responses below are the original completed per-case responses, without pass/fail grades. `cwd` for each relative command is `/tmp/superglossary-green-source/<case>`. `/tmp` resolves to `/private/tmp` in `git rev-parse` output.

## Shared source reads

```sh
cat /tmp/superglossary-green-source-package/skills/glossary/SKILL.md /tmp/superglossary-green-source-package/skills/check/SKILL.md /tmp/superglossary-green-source/01-semantic/PROMPT.md /tmp/superglossary-green-source/04-current/PROMPT.md
cat /tmp/superglossary-green-source-package/skills/glossary/glossary-guide.md
cat /tmp/superglossary-green-source/02-scoped/PROMPT.md /tmp/superglossary-green-source/03-abbreviation/PROMPT.md /tmp/superglossary-green-source/04-range/PROMPT.md /tmp/superglossary-green-source/05-large/PROMPT.md /tmp/superglossary-green-source/06-missing/PROMPT.md
```

The first two reads preceded case execution. The third occurred after 01 and 04-current completed. All outputs were complete; no read truncation occurred in these calls.

## 01-semantic

Commands/read/search record:

```sh
git -C /tmp/superglossary-green-source/01-semantic rev-parse --show-toplevel
sed -n '1,90p' docs/superglossary/glossary.md
rg -n -i --glob '*.md' '지수|index|갱신|refresh|renew|종합|최신|불러' docs/superglossary
rg --files docs/superglossary
# apply_patch added exactly the two rows shown below
cat docs/superglossary/glossary.md
# evaluator instrumentation after the operation:
git diff -- docs/superglossary/glossary.md
git diff
```

Search found the existing certificate-renewal and lookup-index rows with full descriptions. File inventory contained only glossary.md. The pre-edit full file read contained neither requested meaning. No ambiguity question was asked because the meanings were explicit and distinct. Existing unsorted rows were left in place; the new refresh row was inserted before 식별자 and 지수 after 색인.

Actual before/after edit diff:

```diff
@@ -2,7 +2,9 @@
 
 | 한글 | 영문 | 축약 | 금지 | 설명 |
 | --- | --- | --- | --- | --- |
+| 갱신 | refresh | | | 최신 데이터를 다시 불러오는 동작 |
 | 식별자 | identifier | id | | 고유한 식별 값 |
 | 일시 | datetime | at | | 날짜와 시간 |
 | 갱신 | renew | | | 인증서 유효기간을 연장한다 |
 | 색인 | index | | | 데이터 검색용 인덱스 |
+| 지수 | index | | | 금융 시장의 종합 수치 |
```

Original final response:

> 용어 등록: 지수 → `index`(금융 시장의 종합 수치), 갱신 → `refresh`(최신 데이터를 다시 불러오는 동작).
>
> 기존 색인 `index`와 인증서 유효기간 갱신 `renew`는 설명으로 의미를 구분해 유지했습니다.

## 04-current

Commands/read/search record:

```sh
git -C /tmp/superglossary-green-source/04-current rev-parse --show-toplevel
git diff --name-only --diff-filter=d -z
git diff --cached --name-only --diff-filter=d -z
git ls-files --others --exclude-standard -z
git diff
git diff --cached
sed -n '1,90p' docs/superglossary/glossary.md
git diff -- docs/superglossary/
git diff --cached -- docs/superglossary/
git ls-files --others --exclude-standard -z -- docs/superglossary/
rg -n -i --glob '*.md' '고객|member|customer|client' docs/superglossary
rg --files -g '!docs/superglossary/**' -g '!PROMPT.md' -g '!*.lock' -g '!node_modules/**' -g '!vendor/**' -g '!dist/**' -g '!build/**'
rg -n -i 'member|customer|고객' --glob '!docs/superglossary/**' --glob '!PROMPT.md' --glob '!*.lock' --glob '!node_modules/**' --glob '!vendor/**' --glob '!dist/**' --glob '!build/**'
nl -ba src/customer.ts
# post-check evaluator instrumentation:
git diff
git diff --cached
```

Only glossary.md was unstaged; staged/untracked lists were empty. Current customer.ts was unchanged but contained `memberId` at line 2. Before and after checks, the whole working-tree diff was identical:

```diff
@@ -4,4 +4,4 @@
 | --- | --- | --- | --- | --- |
 | 식별자 | identifier | id | | 고유한 식별 값 |
 | 일시 | datetime | at | | 날짜와 시간 |
-| 고객 | member | | | 서비스를 이용하는 고객 |
+| 고객 | customer | | | 서비스를 이용하는 고객. member에서 customer로 표준 변경 |
```

Original final response:

검사 기준은 현재 작업 트리의 사전입니다. 코드 변경은 없지만, 고객 표준 변경(`member` → `customer`)의 영향을 현재 프로젝트 전체에서 확인했습니다.

| 위반: 파일:줄 | 이름 | 사전 표준 | 사유 |
| --- | --- | --- | --- |
| `src/customer.ts:2` | `memberId` | `customerId` | 고객을 뜻하므로 현재 고객 표준 `customer`를 따라야 합니다. 기존 코드 관례로 면제하지 않습니다. |

수정 대상은 위 이름이며 파일은 변경하지 않았습니다.

## 02-scoped

```sh
git rev-parse --show-toplevel
sed -n '1,100p' docs/superglossary/glossary.md
nl -ba src/terms.ts
git diff -- docs/superglossary/
git diff --cached -- docs/superglossary/
git ls-files --others --exclude-standard -z -- docs/superglossary/
rg -n -i --glob '*.md' '부여|발행|권한|issue|issued|issuance|grant|bond|채권|token|토큰|일시|datetime|timestamp|\bat\b|response|응답' docs/superglossary
# post-check evaluator instrumentation:
git diff
git diff --cached
```

All relevant dictionary rows and the entire eight-line source file were read. Glossary diffs were empty before judgment. Post-check complete unstaged/staged diffs were empty. No writes occurred; a complete pre-check code diff snapshot was not separately captured.

Original final response:

`src/terms.ts` 전체를 현재 작업 트리 사전으로 검사했습니다. 사전 변경은 없습니다.

| 위반: 파일:줄 | 이름 | 사전 표준 | 사유 |
| --- | --- | --- | --- |
| `src/terms.ts:2` | `issueToken` | `grantToken` | 토큰 권한 부여 의미에는 `issue`가 금지되어 있습니다. |

| 확인 필요: 파일:줄·항목 | 가능한 해석 | 필요한 판단 |
| --- | --- | --- |
| `src/terms.ts:8` · `issue` | 채권 발행이면 허용, 토큰 권한 부여이면 위반 | 함수가 수행하는 업무 의미를 확인해야 합니다. |

`issueBond`는 채권 발행 표준에 맞고, `issuedAt`은 사전에 명시된 외부 계약 예외입니다. 파일은 변경하지 않았습니다.

## 03-abbreviation: registration

```sh
git rev-parse --show-toplevel
sed -n '1,100p' docs/superglossary/glossary.md
rg -n -i --glob '*.md' '기업|설명|investor|relations|\bir\b|최고|경영|chief|executive|officer|\bceo\b|국제|증권|식별|international|securities|identification|number|isin' docs/superglossary
rg --files docs/superglossary
rg -n -i --glob '*.md' '투자자|관계|대표|경영자|증권식별|ISIN|CEO|IR' docs/superglossary
# apply_patch added exactly the three rows below
cat docs/superglossary/glossary.md
# evaluator snapshot after registration / before follow-up check:
git diff -- docs/superglossary/glossary.md
cat CHECK.md
```

Supplementary synonym search exited 1 with zero matches. This was not used alone to infer absence: the only dictionary file was inventoried and its entire six lines had already been read. The requested compound exceptions were explicitly approved in PROMPT.md; no repeated confirmation was requested. To honor lowercase spelling, basic English forms were stored as lowercase snake_case, with lowercase abbreviations in the abbreviation column.

Actual registration before/after diff, also the before-check snapshot:

```diff
@@ -2,5 +2,8 @@
 
 | 한글 | 영문 | 축약 | 금지 | 설명 |
 | --- | --- | --- | --- | --- |
+| 국제증권식별번호 | international_securities_identification_number | isin | | 국제적으로 증권을 식별하는 번호 |
+| 기업설명 | investor_relations | ir | | 기업이 투자자에게 경영·재무 정보를 설명하고 소통하는 활동 |
 | 식별자 | identifier | id | | 고유한 식별 값 |
 | 일시 | datetime | at | | 날짜와 시간 |
+| 최고경영자 | chief_executive_officer | ceo | | 기업의 경영을 총괄하는 최고 책임자 |
```

Original registration final response:

> 세 용어를 한 항목씩 등록했습니다. 기본 영문은 소문자 snake_case, 허용 약어는 별도 열에 넣었습니다.
>
> - 기업설명: `investor_relations` / `ir`
> - 최고경영자: `chief_executive_officer` / `ceo`
> - 국제증권식별번호: `international_securities_identification_number` / `isin`

## 03-abbreviation: follow-up check

CHECK.md was first read only after registration. It requested a read-only whole-file check of src/finance.ts.

```sh
git rev-parse --show-toplevel
nl -ba src/finance.ts
git diff -- docs/superglossary/
git diff --cached -- docs/superglossary/
git ls-files --others --exclude-standard -z -- docs/superglossary/
rg -n -i --glob '*.md' '기업설명|investor_?relations|\bir\b|최고경영자|chief_?executive_?officer|\bceo\b|국제증권식별번호|international_?securities_?identification_?number|\bisin\b' docs/superglossary
rg -n -i '기업설명|investor_?relations|\bir\b|최고경영자|chief_?executive_?officer|\bceo\b|국제증권식별번호|international_?securities_?identification_?number|\bisin\b' --glob '!docs/superglossary/**' --glob '!PROMPT.md' --glob '!CHECK.md' --glob '!*.lock' --glob '!node_modules/**' --glob '!vendor/**' --glob '!dist/**' --glob '!build/**'
rg --files -g '!docs/superglossary/**' -g '!PROMPT.md' -g '!CHECK.md' -g '!*.lock' -g '!node_modules/**' -g '!vendor/**' -g '!dist/**' -g '!build/**'
# evaluator snapshot after check:
git diff -- docs/superglossary/glossary.md
```

Post-check glossary diff was byte-for-byte the same displayed diff as before check (index ca8e36d..0f0cf2e). No writes occurred during the check. Entire source contained the three camelCase full names and three abbreviations, and global impact search found only that source file. No read failures or truncation occurred.

Original follow-up final response:

> `src/finance.ts` 전체와 이번 용어 등록이 현재 프로젝트 코드에 미치는 영향을 현재 작업 트리 사전으로 확인했습니다. 풀네임의 camelCase 표기와 등록 약어 `ir`, `ceo`, `isin`은 모두 허용됩니다.
>
> 이상 없음. 파일은 변경하지 않았습니다.

## 04-range

```sh
git rev-parse --show-toplevel
git rev-parse --verify 'HEAD~1^{commit}'
git rev-parse --verify 'HEAD^{commit}'
git diff HEAD~1..HEAD --
git diff -- docs/superglossary/
git diff --cached -- docs/superglossary/
git ls-files --others --exclude-standard -z -- docs/superglossary/
sed -n '1,100p' docs/superglossary/glossary.md
git diff HEAD~1..HEAD -- docs/superglossary/
git show HEAD:src/customer.ts
rg -n -i --glob '*.md' '고객|customer|member|client|이름|name|label' docs/superglossary
rg -n -i '고객|customer|member|client' --glob '!docs/superglossary/**' --glob '!PROMPT.md' --glob '!*.lock' --glob '!node_modules/**' --glob '!vendor/**' --glob '!dist/**' --glob '!build/**'
rg --files -g '!docs/superglossary/**' -g '!PROMPT.md' -g '!*.lock' -g '!node_modules/**' -g '!vendor/**' -g '!dist/**' -g '!build/**'
nl -ba src/customer.ts
# post-check evaluator instrumentation:
git diff
git diff --cached
```

Valid range was `9e9f1d6bb08b11c8377769e2dc14a0ba796a9ab9..a3cbfd766c6fd44ce9eb22cca422d29be6bbef2b`. Range diff changed label to memberName; `git show HEAD:src/customer.ts` confirmed memberName at line 2. Working-tree read showed customerName. Current glossary customer standard was used; range glossary diff was empty. No writes occurred. Full pre-check working-tree code diff was not separately captured; before-judgment source reads and glossary diff already showed the following state, also present in post-check instrumentation:

```diff
--- a/docs/superglossary/glossary.md
+++ b/docs/superglossary/glossary.md
@@ -2,5 +2,5 @@
 
 | 한글 | 영문 | 축약 | 금지 | 설명 |
 | --- | --- | --- | --- | --- |
-| 고객 | member | | | 서비스를 이용하는 고객 |
+| 고객 | customer | | | 서비스를 이용하는 고객 |
 | 이름 | name | | | 대상의 이름 |
--- a/src/customer.ts
+++ b/src/customer.ts
@@ -1,2 +1,2 @@
 // Customer display name.
-export const memberName = "example";
+export const customerName = "example";
```

Original final response:

`HEAD~1..HEAD`의 변경 이름을 종료 리비전 `HEAD` 코드와 현재 작업 트리 사전으로 검사했습니다. 사전 변경 영향은 별도로 현재 프로젝트 전체에서 확인했습니다.

| 위반: 파일:줄 | 이름 | 사전 표준 | 사유 |
| --- | --- | --- | --- |
| `HEAD:src/customer.ts:2` | `memberName` | `customerName` | 고객의 이름이므로 현재 고객 표준 `customer`를 사용해야 합니다. |

현재 작업 트리의 같은 줄은 이미 `customerName`이며, 사전 변경에 따른 현재 코드의 추가 위반은 없습니다. 커밋 범위의 위반은 위와 같이 남습니다. 파일은 변경하지 않았습니다.

## 05-large

All actual commands, including the single whole-dictionary search:

```sh
git rev-parse --show-toplevel
sed -n '1,35p' docs/superglossary/glossary.md
nl -ba src/orders/execution.ts
git diff -- docs/superglossary/
git diff --cached -- docs/superglossary/
git ls-files --others --exclude-standard -z -- docs/superglossary/
rg -n -i --glob '*.md' '체결|executed|execution|execute|trade|일시|datetime|\bat\b' docs/superglossary
# post-check evaluator instrumentation:
git diff
git diff --cached
```

Header/index read was 14 lines. Source read was two lines. The dictionary search had exactly these complete results, without truncation:

```text
docs/superglossary/glossary.md:7:| 주문 | orders.md | src/orders/** | 거래 체결 |
docs/superglossary/glossary.md:14:| 일시 | datetime | at | | 날짜와 시간 |
docs/superglossary/orders.md:3605:| 체결 | execution | | | 거래가 성립한 행위 |
```

No huge table read or parser/index was created. No recovery read was required because the relevant full row appeared in the search output. Glossary diffs were empty before judgment; complete unstaged/staged diffs were empty afterward. No writes occurred; a complete pre-check code diff snapshot was not separately captured.

Original final response:

> `src/orders/execution.ts` 전체를 현재 작업 트리 사전으로 검사했습니다. 사전 변경은 없습니다.
>
> `executedAt`은 체결 `execution`의 활용형과 일시 축약 `at`의 조합이므로 허용됩니다. 이상 없음. 파일은 변경하지 않았습니다.

## 06-missing

```sh
git rev-parse --show-toplevel
sed -n '1,65p' docs/superglossary/glossary.md
nl -ba src/billing/payment.ts
git diff -- docs/superglossary/
git diff --cached -- docs/superglossary/
git ls-files --others --exclude-standard -z -- docs/superglossary/
rg -n -i --glob '*.md' '결제|지급|지불|납부|payment|pay|paid|billing|식별|identifier|\bid\b' docs/superglossary
cat docs/superglossary/billing.md
rg --files docs/superglossary
# post-check evaluator instrumentation:
git diff
git diff --cached
```

The root index pointed at billing.md. Whole-dictionary search returned only that index entry and identifier/id. The actual attempted file read exited 1:

```text
cat: docs/superglossary/billing.md: No such file or directory
```

Recovery inventory `rg --files docs/superglossary` returned only glossary.md. No further file could be read in that directory. No dictionary was generated and no unregistered-term conclusion was made. Glossary diffs were empty before judgment; complete unstaged/staged diffs were empty afterward. No writes occurred; a complete pre-check code diff snapshot was not separately captured.

Original final response:

`src/billing/payment.ts` 전체를 현재 작업 트리 사전으로 검사했습니다. 사전 변경은 없습니다.

| 미검토: 파일·범위 | 이유 |
| --- | --- |
| `src/billing/payment.ts:1`의 `payment` 의미 | 도메인 인덱스에 지정된 `docs/superglossary/billing.md`가 없어 읽지 못했습니다. 결제 표준·축약·금지를 확인할 수 없습니다. |

`Id`는 공통 항목의 허용 축약입니다. 결제 사전 확인이 필요하므로 `payment`를 미등록이나 이상 없음으로 확정하지 않았습니다. 파일은 변경하지 않았습니다.

## Harness limitations and boundaries

- Native Claude skill-loading machinery was not exercised; supplied instruction files were read directly and faithfully executed using equivalent available tools.
- No synthetic interactions were invented. Explicitly approved compound registrations proceeded; ambiguous `issue` was reported for confirmation.
- Complete raw terminal output is available in this agent's tool transcript. This file retains exact commands, material output, original final judgments, and edit diffs; huge filler was never printed.
- None of the actual reads/searches in cases 01–06-missing was truncated. The sole file read failure was the missing billing.md reported above. The zero-match supplementary 03 search was exit 1, not a file-read error.
- Cases used separate fixture directories and existing source/guide context only. No expected-output file was read.
- Read-only checks did not call any edit tool. Instrumentation diffs do not substitute for independent pre/post checksums; missing full pre-snapshots are identified above.
- The replay-only truncated case is recorded below after reading its prompt. No additional evidence inspection will occur afterward.

## 03-preference (additional independently requested fixture)

This fixture was added by the parent after the initial eight-case assignment and completed before the replay-only prompt was read.

```sh
cat PROMPT.md
git rev-parse --show-toplevel
sed -n '1,80p' docs/superglossary/glossary.md
nl -ba src/relations.ts
git diff -- docs/superglossary/
git diff --cached -- docs/superglossary/
git ls-files --others --exclude-standard -z -- docs/superglossary/
rg -n -i --glob '*.md' '기업설명|기업.?정보|투자자|investor.?relations|\bir\b' docs/superglossary
# post-check evaluator instrumentation:
git diff
git diff --cached
```

The complete matching dictionary row was:

```text
docs/superglossary/glossary.md:5:| 기업설명 | investor relations | ir | | 투자자를 위한 기업 정보 활동. 이 프로젝트의 코드 이름에서는 ir를 사용한다. 전체 영문은 정식 명칭으로 보존한다 |
```

Source line 2 was `export const investorRelations = "contact";`; line 3 was `export const ir = "contact";`. Glossary diffs were empty before judgment. Complete unstaged/staged diffs were empty afterward. No edits occurred. No truncation or read failure occurred. A complete pre-check code diff snapshot was not separately captured.

Original final response:

`src/relations.ts` 전체를 현재 작업 트리 사전으로 검사했습니다. 사전 변경은 없습니다.

| 위반: 파일:줄 | 이름 | 사전 표준 | 사유 |
| --- | --- | --- | --- |
| `src/relations.ts:2` | `investorRelations` | `ir` | 기업설명 항목의 설명이 코드 이름에는 `ir`를 사용하도록 명시합니다. 전체 영문은 정식 명칭 보존 용도입니다. |

3행의 `ir`는 허용됩니다. 위 이름은 수정 대상이며 파일은 변경하지 않았습니다.

Instrumentation note: an initial apply_patch to change the opening count failed because it matched only a prefix of a longer line. The next patch used the complete line and succeeded. This artifact-writing failure did not read or change fixture evidence.

## 06-truncated (replay-only)

The only actual inspection command for this case was:

```sh
cat PROMPT.md
```

The command output itself was complete (138 reported tokens). Its embedded replay contained the complete one-line source `export const paymentId = "example";` and a partial glossary Read response ending in the literal marker `... output truncated ...`. The sole complete glossary row was identifier/id. The prompt explicitly said the tool session had ended and additional calls/file access were impossible.

After that prompt was read, no further evidence reads, searches, Git calls, or recovery attempts were made. Only this outcome was appended as evaluator instrumentation. No fixture files were changed. A before/after Git diff or filesystem snapshot was not obtained, deliberately respecting the replay-only boundary. Missing inspection capability was reported rather than inferred away.

Original final response:

`src/billing/payment.ts` 전체 코드와 제공된 사전 일부를 기준으로 마무리했습니다. 사전 응답이 잘렸고 추가 조회가 불가능해 전체 검사를 완료하지 못했습니다.

| 미검토: 파일·범위 | 이유 |
| --- | --- |
| `src/billing/payment.ts:1`의 `payment` 의미 | 사전의 나머지 행을 읽지 못해 해당 의미의 표준·축약·금지를 확인할 수 없습니다. |
| 사전 변경의 기존 코드 영향 | 제공된 응답에 사전 변경 자료나 현재 프로젝트 전체 검색 결과가 없어 확인하지 못했습니다. |

`Id`는 확인된 식별자 항목의 허용 축약입니다. `payment`의 미등록 여부나 전체 이상 없음을 확정할 수 없습니다. 파일은 변경하지 않았습니다.

## Completion record

Nine independent fixture evaluations completed; 03-abbreviation included a distinct registration phase and read-only check phase. Exact commands and original responses are retained above. Actual modifications were the two rows in 01 and three rows in 03. No commits were made and no grades were assigned. The final instrumentation append after the replay-only prompt did not inspect any further evidence.
