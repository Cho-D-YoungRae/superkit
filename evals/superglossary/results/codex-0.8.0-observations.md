# Codex behavioral observations

Scope: supplied package `/tmp/superglossary-green-codex-package`; independent fixture repositories under `/tmp/superglossary-green-codex/`.
Execution used only the supplied glossary/check skills and their glossary-guide. No parent repository, expected results, prior observations, memory, Internet, user settings, or other user data were read. No subagents were used. No package changes or commits. Only glossary files in 01-semantic and 03-abbreviation were edited. All check requests remained read-only.
This is an execution record, not a pass/fail assessment.

## Shared instructions actually read

Exact commands (default working directory was not used to read repository content):
```sh
cat /tmp/superglossary-green-codex-package/skills/glossary/SKILL.md /tmp/superglossary-green-codex-package/skills/check/SKILL.md
cat /tmp/superglossary-green-codex-package/skills/glossary/glossary-guide.md /tmp/superglossary-green-codex/01-semantic/PROMPT.md
```

These reads were complete; no tool truncation was reported. Subsequent case commands below ran in the named fixture directory. Line-separated commands within a block were issued in the same shell invocation where shown, without output separators. NUL-delimited git list results were preserved by the tool as `\u0000`.

## 01-semantic

Exact read/search commands:
```sh
git rev-parse --show-toplevel
sed -n '1,70p' docs/superglossary/glossary.md
rg -n -i -F -g '*.md' -e '지수' -e 'index' -e '금융' -e '시장' -e '갱신' -e 'refresh' -e 'renew' -e '최신' docs/superglossary/
```
```sh
git diff -- docs/superglossary/glossary.md
```
Before diff was empty. Existing rows were 갱신/renew/certificate validity extension and 색인/index/search index. Both were retained. Applied the two inserted rows below with apply_patch, then ran:
```sh
rg -n -i -F -g '*.md' -e '지수' -e 'index' -e '금융' -e '시장' -e '갱신' -e 'refresh' -e 'renew' -e '최신' docs/superglossary/
git diff -- docs/superglossary/glossary.md
```

Original final response:
> 용어 등록: 지수 → index, 갱신 → refresh. 기존 색인(index)·인증서 갱신(renew)과 의미가 구분되도록 설명을 남겼습니다.

Before/after diff:
```diff
diff --git a/docs/superglossary/glossary.md b/docs/superglossary/glossary.md
index 385c6b4..61a2f45 100644
--- a/docs/superglossary/glossary.md
+++ b/docs/superglossary/glossary.md
@@ -4,5 +4,7 @@
 | --- | --- | --- | --- | --- |
 | 식별자 | identifier | id | | 고유한 식별 값 |
 | 일시 | datetime | at | | 날짜와 시간 |
+| 갱신 | refresh | | | 최신 데이터를 다시 불러오는 동작. 인증서 유효기간 연장과 구분한다 |
 | 갱신 | renew | | | 인증서 유효기간을 연장한다 |
 | 색인 | index | | | 데이터 검색용 인덱스 |
+| 지수 | index | | | 금융 시장의 종합 수치. 데이터 검색용 색인과 구분한다 |
```
No clarification question was asked. No existing row was removed, renamed, or reordered.

## 02-scoped

Exact commands:
```sh
cat PROMPT.md
git rev-parse --show-toplevel
sed -n '1,80p' docs/superglossary/glossary.md
```
```sh
nl -ba src/terms.ts
git diff -- docs/superglossary/
git diff --cached -- docs/superglossary/
git ls-files --others --exclude-standard -z -- docs/superglossary/
rg -n -i -F -g '*.md' -e 'grant' -e 'issue' -e 'issued' -e 'token' -e 'bond' -e '토큰' -e '권한' -e '부여' -e '발행' -e '채권' -e '일시' -e 'datetime' -e 'at' docs/superglossary/
```
Dictionary diff/untracked results were empty. Read all eight source lines. The full grant/issue rows established the token-only ban, separate bond meaning, and explicit external issuedAt exception.

Original final response:

검사 범위는 `src/terms.ts` 전체이며, 현재 작업 트리 사전을 기준으로 확인했습니다. 사전 변경은 없습니다.

| 위반: 파일:줄 | 이름 | 사전 표준 | 사유 |
| --- | --- | --- | --- |
| src/terms.ts:2 | issueToken | grantToken | 토큰 권한 부여 의미에는 grant를 사용하며 issue가 금지되어 있습니다. |

| 확인 필요: 파일:줄 | 이름 | 가능한 해석 | 필요한 판단 |
| --- | --- | --- | --- |
| src/terms.ts:8 | issue | 채권 발행 또는 토큰 권한 부여 | 어떤 동작인지 확인해야 issue 허용 여부를 결정할 수 있습니다. |

`issueBond`는 채권 발행 의미라 허용하고, `TokenResponse.issuedAt`은 외부 계약 필드 예외에 해당합니다. `issueToken`은 수정 대상입니다.

Before/after diff caused by this check: none; no file writes.

## 03-abbreviation — registration, before CHECK

Exact commands:
```sh
cat PROMPT.md
git rev-parse --show-toplevel
sed -n '1,80p' docs/superglossary/glossary.md
```
```sh
rg -n -i -F -g '*.md' -e '기업' -e '설명' -e 'investor' -e 'relations' -e 'ir' -e '최고' -e '경영' -e 'chief' -e 'executive' -e 'officer' -e 'ceo' -e '국제' -e '증권' -e '식별' -e 'international' -e 'securities' -e 'identification' -e 'number' -e 'isin' docs/superglossary/
git diff -- docs/superglossary/glossary.md
```
Original glossary had only identifier/id and datetime/at. Before diff was empty. The initial read included the entire short glossary, so absent matches were not the sole evidence. Applied the three rows below with apply_patch.
```sh
rg -n -i -F -g '*.md' -e '기업설명' -e 'investor' -e 'ir' -e '최고경영자' -e 'chief' -e 'ceo' -e '국제증권식별번호' -e 'international' -e 'isin' docs/superglossary/
git diff -- docs/superglossary/glossary.md
cat CHECK.md
```

Original registration final response, before CHECK:

용어 등록: 기업설명 → investor_relations / ir, 최고경영자 → chief_executive_officer / ceo, 국제증권식별번호 → international_securities_identification_number / isin.

승인한 합성어 예외를 적용했고, 기본 영문과 허용 축약을 각 열에 소문자로 기록했습니다.

Diff already present before CHECK:
```diff
diff --git a/docs/superglossary/glossary.md b/docs/superglossary/glossary.md
index ca8e36d..a0b076f 100644
--- a/docs/superglossary/glossary.md
+++ b/docs/superglossary/glossary.md
@@ -2,5 +2,8 @@
 
 | 한글 | 영문 | 축약 | 금지 | 설명 |
 | --- | --- | --- | --- | --- |
+| 국제증권식별번호 | international_securities_identification_number | isin | | 증권을 국제적으로 식별하는 표준 번호 |
+| 기업설명 | investor_relations | ir | | 기업이 투자자에게 경영 현황과 정보를 설명하는 활동 |
 | 식별자 | identifier | id | | 고유한 식별 값 |
 | 일시 | datetime | at | | 날짜와 시간 |
+| 최고경영자 | chief_executive_officer | ceo | | 기업 경영을 총괄하는 최고 책임자 |
```

## 03-abbreviation — CHECK, after registration

Exact commands:
```sh
nl -ba src/finance.ts
git diff -- docs/superglossary/
git diff --cached -- docs/superglossary/
git ls-files --others --exclude-standard -z -- docs/superglossary/
rg --files -g '!.git/**' -g '!docs/superglossary/**'
rg -n -i -F -e 'investor' -e 'relations' -e 'ir' -e 'chief' -e 'executive' -e 'officer' -e 'ceo' -e 'international' -e 'securities' -e 'identification' -e 'number' -e 'isin' --glob '!docs/superglossary/**' --glob '!.git/**' --glob '!PROMPT.md' --glob '!CHECK.md' .
```
Source lines 2–4 contained each camelCase full form and its abbreviation. File inventory contained only src/finance.ts plus the two prompt files outside the dictionary. Current project impact search found the same source names. The unstaged glossary diff was exactly the registration diff above; cached/untracked dictionary results were empty.

Original CHECK final response:

검사 범위는 `src/finance.ts` 전체이며, 현재 작업 트리 사전을 기준으로 신규 등록 용어가 현재 프로젝트 코드에 미치는 영향도 확인했습니다. 기본 영문의 camelCase 표기와 등록 축약 `ir`, `ceo`, `isin`은 모두 허용됩니다.

이상 없음.

Before-CHECK → after-CHECK diff: none. CHECK made no edits; registration diff remained unchanged.

## 03-preference

Exact commands:
```sh
cat PROMPT.md
git rev-parse --show-toplevel
sed -n '1,80p' docs/superglossary/glossary.md
nl -ba src/company.ts
git diff -- docs/superglossary/
git diff --cached -- docs/superglossary/
git ls-files --others --exclude-standard -z -- docs/superglossary/
```
Failed read: `nl: src/company.ts: No such file or directory`. This was an incorrectly anticipated path in the same command that read the prompt. The prompt actually requested src/relations.ts. It was recovered with:
```sh
nl -ba src/relations.ts
rg -n -i -F -g '*.md' -e '기업' -e '설명' -e 'investor' -e 'relations' -e 'ir' -e '관계' docs/superglossary/
```
Dictionary diff/untracked results were empty. Read all three source lines and the complete dictionary row specifying ir for code names.

Original final response:

검사 범위는 `src/relations.ts` 전체이며, 현재 작업 트리 사전을 기준으로 확인했습니다. 사전 변경은 없습니다.

| 위반: 파일:줄 | 이름 | 사전 표준 | 사유 |
| --- | --- | --- | --- |
| src/relations.ts:2 | investorRelations | ir | 기업설명 항목의 설명이 이 프로젝트의 코드 이름에는 ir를 사용하도록 명시합니다. |

`src/relations.ts:3`의 `ir`는 허용됩니다. `investorRelations`는 수정 대상입니다.

Before/after diff caused by this check: none; no file writes.

## 04-current

Exact commands:
```sh
cat PROMPT.md
git rev-parse --show-toplevel
sed -n '1,80p' docs/superglossary/glossary.md
```
```sh
git diff --name-only --diff-filter=d -z
git diff --cached --name-only --diff-filter=d -z
git ls-files --others --exclude-standard -z
git diff --
git diff --cached --
git ls-files --others --exclude-standard -z -- docs/superglossary/
rg --files -g '!.git/**' -g '!docs/superglossary/**'
```
Only docs/superglossary/glossary.md appeared in changed-file results; source inventory contained src/customer.ts. Current glossary changed 고객 from member to customer (no forbidden-column entry).
```sh
git diff -- docs/superglossary/
git diff --cached -- docs/superglossary/
rg -n -i -F -e '고객' -e 'member' -e 'customer' --glob '!docs/superglossary/**' --glob '!.git/**' --glob '!PROMPT.md' .
nl -ba src/customer.ts
rg -n -i -F -g '*.md' -e '고객' -e 'member' -e 'customer' -e '식별자' -e 'identifier' -e 'id' docs/superglossary/
```
Read source comment “Existing customer identity.” and `export const memberId = 7;`.

Original final response:

코드 변경 대상은 없으며, 현재 작업 트리 사전의 고객 표준 변경(member → customer)이 현재 프로젝트 코드에 미치는 영향을 검사했습니다.

| 위반: 파일:줄 | 이름 | 사전 표준 | 사유 |
| --- | --- | --- | --- |
| src/customer.ts:2 | memberId | customerId | 고객 식별자 의미이며 현재 고객 표준은 customer입니다. |

memberId는 현재 표준에 맞춰 수정할 대상입니다.

Before/after diff caused by this check: none; existing glossary change was preserved:
```diff
-| 고객 | member | | | 서비스를 이용하는 고객 |
+| 고객 | customer | | | 서비스를 이용하는 고객. member에서 customer로 표준 변경 |
```

## 04-range

Exact commands:
```sh
cat PROMPT.md
git rev-parse --show-toplevel
sed -n '1,80p' docs/superglossary/glossary.md
```
```sh
git rev-parse --verify 'HEAD~1^{commit}'
git rev-parse --verify 'HEAD^{commit}'
git diff 'HEAD~1..HEAD' --
git diff -- docs/superglossary/
git diff --cached -- docs/superglossary/
git diff 'HEAD~1..HEAD' -- docs/superglossary/
git ls-files --others --exclude-standard -z -- docs/superglossary/
```
Resolved start `aa835787fe7188fd27a28af416619ce10cd1ef7a`, end `f1d95b1333f43c7f26151aea17475332db406ab6`. Range changed label to memberName in source. Unstaged dictionary changed member to customer; cached and range dictionary diffs were empty.
```sh
git show 'HEAD:src/customer.ts'
rg -n -i -F -e '고객' -e 'member' -e 'customer' --glob '!docs/superglossary/**' --glob '!.git/**' --glob '!PROMPT.md' .
nl -ba src/customer.ts
rg -n -i -F -g '*.md' -e '고객' -e 'member' -e 'customer' -e '이름' -e 'name' docs/superglossary/
```
HEAD source line 2 was memberName; current source line 2 was customerName, both under “Customer display name.” comment. These were evaluated separately.

Original final response:

`HEAD~1..HEAD`의 종료 리비전 코드를 현재 작업 트리 사전으로 검사했습니다. 사전의 고객 표준 변경이 현재 프로젝트 코드에 미치는 영향도 별도로 확인했습니다.

| 위반: 파일:줄 | 이름 | 사전 표준 | 사유 |
| --- | --- | --- | --- |
| HEAD의 src/customer.ts:2 | memberName | customerName | 고객 이름을 뜻하며 현재 사전의 고객 표준은 customer입니다. |

현재 작업 트리의 `src/customer.ts:2`는 이미 `customerName`을 사용하므로 사전 변경 영향 검사에서는 위반이 없습니다.

Before/after diff caused by this check: none; existing working-tree code/dictionary changes were preserved. The inspected relevant states were:
```diff
# Commit range:
-export const label = "example";
+export const memberName = "example";
# Current dictionary versus HEAD:
-| 고객 | member | | | 서비스를 이용하는 고객 |
+| 고객 | customer | | | 서비스를 이용하는 고객 |
# HEAD versus current source, established by show/read:
-export const memberName = "example";
+export const customerName = "example";
```

## 05-large

Exact commands:
```sh
cat PROMPT.md
git rev-parse --show-toplevel
sed -n '1,45p' docs/superglossary/glossary.md
```
```sh
nl -ba src/orders/execution.ts
git diff -- docs/superglossary/
git diff --cached -- docs/superglossary/
git ls-files --others --exclude-standard -z -- docs/superglossary/
rg -n -i -F -g '*.md' -e '체결' -e 'execution' -e 'execute' -e 'executed' -e 'exec' -e '일시' -e 'datetime' -e 'at' docs/superglossary/
```
Read root dictionary header/domain index only. No bulk read of orders.md. Whole-dictionary search returned the complete row at orders.md:3605: `| 체결 | execution | | | 거래가 성립한 행위 |`, plus datetime/at at glossary.md:14. Source line 2 was executedAt, with trade-finalization timestamp context. Dictionary diffs/untracked results were empty. Output was not truncated.

Original final response:

검사 범위는 `src/orders/execution.ts` 전체이며, 현재 작업 트리 사전을 기준으로 확인했습니다. `executedAt`은 체결 `execution`의 활용형과 일시 축약 `at`의 조합으로 허용됩니다. 사전 변경은 없습니다.

이상 없음.

Before/after diff caused by this check: none; no file writes.

## 06-missing

Exact commands:
```sh
cat PROMPT.md
git rev-parse --show-toplevel
sed -n '1,80p' docs/superglossary/glossary.md
```
```sh
nl -ba src/billing/payment.ts
git diff -- docs/superglossary/
git diff --cached -- docs/superglossary/
git ls-files --others --exclude-standard -z -- docs/superglossary/
rg -n -i -F -g '*.md' -e '결제' -e '청구' -e '지불' -e 'payment' -e 'pay' -e 'billing' -e 'bill' -e 'amount' -e '금액' -e '식별자' -e 'id' docs/superglossary/
sed -n '1,80p' docs/superglossary/billing.md
```
Failed read, exit 1: `sed: docs/superglossary/billing.md: No such file or directory`. The glossary index links this file for src/billing/**. Source was one paymentId declaration. Dictionary diff/untracked results were empty.
Recovery/expansion:
```sh
rg --files docs/superglossary/
rg -n -i -F -g '*.md' -e '납부' -e '정산' -e 'settlement' -e 'paid' -e 'charge' docs/superglossary/
```
File inventory returned only glossary.md. Alternate meaning search returned no matches (exit 1). No file was created.

Original final response:

검사 범위는 `src/billing/payment.ts` 전체이며, 현재 작업 트리 사전을 기준으로 확인했습니다. 사전 변경은 없습니다.

| 미검토: 파일·범위 | 이유 |
| --- | --- |
| src/billing/payment.ts:1의 paymentId | 결제 도메인 인덱스가 가리키는 docs/superglossary/billing.md가 없어 payment의 표준·축약·금지·예외를 확인하지 못했습니다. |

`id`는 공통 사전의 허용 축약이지만, `paymentId` 전체를 이상 없음이나 추가 후보로 확정할 수 없습니다.

Before/after diff caused by this check: none; no file writes.

## 06-truncated

Only command:
```sh
cat PROMPT.md
```
The prompt replay supplied the complete one-line paymentId source and a glossary response ending in `... output truncated ...` after identifier/id. Per the fixture request, this replay was the sole available inspection evidence. No subsequent fixture/package read, search, git inspection, or recovery call was made. Actual truncation was present in the replay; the tool reading PROMPT.md itself did not truncate.

Original final response:

검사 대상은 `src/billing/payment.ts` 전체입니다. 현재 사전 응답이 잘려 검사 완료 여부를 확정할 수 없습니다.

| 미검토: 파일·범위 | 이유 |
| --- | --- |
| src/billing/payment.ts:1의 paymentId | 확보한 사전에는 identifier/id만 보이며, 잘린 나머지에서 payment의 표준·축약·금지·예외를 확인하지 못했습니다. |
| 사전 변경의 기존 코드 영향 | 변경 내역과 영향 검색 결과가 제공되지 않았고, 추가 도구 호출도 불가능합니다. |

`payment`를 미등록으로 판단하거나 “이상 없음”으로 보고할 근거가 부족합니다.

Before/after diff caused by this check: none; no file writes. This outcome was settled before recording this report. Report creation is evaluator instrumentation, not additional fixture inspection.

