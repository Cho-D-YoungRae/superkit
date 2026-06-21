# superglossary v0.2.0 용어사전 기능 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 프로젝트 도메인 용어를 `.claude/superglossary/`에 관리하고 Claude가 일관된 영문 네이밍을 쓰도록 돕는 커맨드·스킬·서브에이전트·CLI를 superglossary 플러그인에 추가한다.

**Architecture:** 모든 결정론 로직은 의존성 0의 단일 Node CLI(`templates/glossary.mjs`)에 모은다(`init/build/add/update/remove/list/lint`). 커맨드(init·add)·스킬(glossary-check)·서브에이전트(check-analyzer·glossary-scanner, model: sonnet)는 이 CLI를 호출하는 얇은 마크다운 래퍼다. 사용자 프로젝트에는 `glossary.mjs`만 복사되고, 초기 데이터는 CLI에 내장된 상수에서 생성한다.

**Tech Stack:** Node 24 (ESM `.mjs`), `node:fs`/`node:path`/`node:url`/`node:os` 내장 모듈만, 테스트는 `node:test` 내장 러너. 플러그인 매니페스트/마켓플레이스(JSON), pnpm(개발용 스크립트 한정).

## Global Constraints

- **외부 의존성 0**: `glossary.mjs`와 테스트는 Node 내장 모듈만 사용한다(`npm install` 불필요). 개발용 `scripts/bump-version.mjs`(pnpm)는 건드리지 않는다.
- **스키마 필드명은 풀어쓴다**: `korean` / `english` / `abbreviation` / `description` / `relatedElements`. 약어 키 금지.
- **`relatedElements`는 문자열 배열**. `abbreviation`은 없으면 `null`.
- **분류(category)는 v1에 없다** (스키마·생성물·CLI 어디에도 추가하지 않는다).
- **데이터 위치는 `.claude/superglossary/`**, 상시 로드 import는 `.claude/CLAUDE.md`의 `@superglossary/core.md`.
- **생성물 정렬은 `korean` 가나다순** (`localeCompare(a, b, "ko")`), 빌드는 멱등.
- **생성물 상단 경고 주석**: `<!-- 이 파일은 glossary.json에서 자동 생성됩니다. 직접 편집하지 마세요. (glossary.mjs build) -->`
- **서브에이전트는 `model: sonnet`**.
- **모든 사용자 대면 텍스트·생성 문서는 한국어**.
- **커밋은 Conventional Commits**, 메시지 끝에 `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- **작업 흐름 차단 금지**: 자동 수정·차단형 훅을 만들지 않는다.

---

## File Structure

```
superglossary/
├── templates/
│   └── glossary.mjs            # [신규] CLI + export 함수 + 초기 데이터 상수 (사용자에게 복사됨)
├── tests/
│   └── glossary.test.mjs       # [신규] node:test 유닛/통합 테스트 (플러그인 레포 전용)
├── commands/
│   ├── init.md                 # [신규] /superglossary:init
│   └── add.md                  # [신규] /superglossary:add
├── skills/
│   └── glossary-check/
│       └── SKILL.md            # [신규]
├── agents/
│   ├── check-analyzer.md       # [신규] model: sonnet
│   └── glossary-scanner.md     # [신규] model: sonnet
├── package.json                # [수정] "test": "node --test" 추가
├── .claude-plugin/plugin.json  # [수정] version 0.2.0
├── README.md                   # [수정] 워크플로우·설치·강의 출처
├── CHANGELOG.md                # [수정] [Unreleased] 갱신
└── CLAUDE.md                   # [수정] 컴포넌트 위치 반영
```

`glossary.mjs`는 함수를 `export`하고, 직접 실행 시에만 CLI `main`을 돈다(`process.argv[1] === fileURLToPath(import.meta.url)`). 테스트는 `templates/glossary.mjs`에서 함수를 import한다.

---

## Task 1: 프로젝트 셋업 + 데이터 I/O

**Files:**
- Modify: `package.json` (scripts에 `"test"` 추가)
- Create: `templates/glossary.mjs`
- Test: `tests/glossary.test.mjs`

**Interfaces:**
- Produces:
  - `loadGlossary(dir: string): {terms: Term[]}` — `dir/glossary.json`을 읽어 파싱. `Term = {korean, english, abbreviation, description, relatedElements}`.
  - `saveGlossary(dir: string, data): void` — `dir/glossary.json`에 2-space + 끝 개행으로 저장.
  - `sortedTerms(data): Term[]` — `korean` 가나다순 복사 정렬.
  - 상수 `AUTOGEN: string` — 경고 주석 한 줄.

- [ ] **Step 1: package.json에 test 스크립트 추가**

`package.json`의 `scripts`를 다음으로 만든다(기존 bump/version:check 유지):

```json
  "scripts": {
    "bump": "node scripts/bump-version.mjs",
    "version:check": "node scripts/bump-version.mjs --check",
    "test": "node --test"
  },
```

- [ ] **Step 2: 실패하는 테스트 작성**

`tests/glossary.test.mjs`:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { loadGlossary, saveGlossary, sortedTerms } from "../templates/glossary.mjs";

function tmp() {
  return mkdtempSync(join(tmpdir(), "glossary-"));
}

test("saveGlossary/loadGlossary 라운드트립", () => {
  const dir = tmp();
  try {
    const data = { terms: [{ korean: "회원", english: "member", abbreviation: null, description: "", relatedElements: [] }] };
    saveGlossary(dir, data);
    const loaded = loadGlossary(dir);
    assert.deepEqual(loaded, data);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("sortedTerms는 korean 가나다순으로 정렬한다", () => {
  const data = { terms: [
    { korean: "주문", english: "order" },
    { korean: "가격", english: "price" },
    { korean: "회원", english: "member" },
  ] };
  assert.deepEqual(sortedTerms(data).map(t => t.korean), ["가격", "주문", "회원"]);
});
```

- [ ] **Step 3: 테스트 실패 확인**

Run: `pnpm test`
Expected: FAIL — `Cannot find module '../templates/glossary.mjs'` 또는 export 미정의.

- [ ] **Step 4: 최소 구현**

`templates/glossary.mjs`:

```js
#!/usr/bin/env node
// .claude/superglossary/glossary.mjs — 프로젝트 용어사전 CLI (의존성 0)
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

export const AUTOGEN =
  "<!-- 이 파일은 glossary.json에서 자동 생성됩니다. 직접 편집하지 마세요. (glossary.mjs build) -->";

export function loadGlossary(dir) {
  return JSON.parse(readFileSync(join(dir, "glossary.json"), "utf8"));
}

export function saveGlossary(dir, data) {
  writeFileSync(join(dir, "glossary.json"), JSON.stringify(data, null, 2) + "\n");
}

export function sortedTerms(data) {
  return [...data.terms].sort((a, b) => a.korean.localeCompare(b.korean, "ko"));
}
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `pnpm test`
Expected: PASS (2 tests)

- [ ] **Step 6: 커밋**

```bash
git add package.json templates/glossary.mjs tests/glossary.test.mjs
git commit -m "feat: glossary.mjs 데이터 I/O와 테스트 기반 추가

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: addTerm (중복·충돌 검사)

**Files:**
- Modify: `templates/glossary.mjs`
- Test: `tests/glossary.test.mjs`

**Interfaces:**
- Consumes: `sortedTerms` (불필요), `loadGlossary`/`saveGlossary`.
- Produces: `addTerm(data, term): data` — `term = {korean, english, abbreviation?, description?, relatedElements?}`. 같은 `korean`·`english`·`abbreviation`(대소문자 무시) 중복 시 `Error` throw. 통과 시 `data.terms`에 정규화된 레코드(`abbreviation` 기본 `null`, `description` 기본 `""`, `relatedElements` 기본 `[]`)를 push하고 `data` 반환.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/glossary.test.mjs`에 추가:

```js
import { addTerm } from "../templates/glossary.mjs";

test("addTerm: 새 용어를 정규화해 추가한다", () => {
  const data = { terms: [] };
  addTerm(data, { korean: "회원", english: "member" });
  assert.deepEqual(data.terms[0], {
    korean: "회원", english: "member", abbreviation: null, description: "", relatedElements: [],
  });
});

test("addTerm: 같은 한글은 거부한다", () => {
  const data = { terms: [{ korean: "회원", english: "member", abbreviation: null }] };
  assert.throws(() => addTerm(data, { korean: "회원", english: "customer" }), /이미 등록된 한글/);
});

test("addTerm: 같은 영문은 거부한다", () => {
  const data = { terms: [{ korean: "회원", english: "member", abbreviation: null }] };
  assert.throws(() => addTerm(data, { korean: "고객", english: "Member" }), /이미 등록된 영문/);
});

test("addTerm: 같은 축약어는 거부한다", () => {
  const data = { terms: [{ korean: "식별자", english: "identifier", abbreviation: "id" }] };
  assert.throws(() => addTerm(data, { korean: "지수", english: "index", abbreviation: "ID" }), /이미 등록된 축약어/);
});
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `pnpm test`
Expected: FAIL — `addTerm is not a function`.

- [ ] **Step 3: 구현**

`glossary.mjs`에 추가:

```js
export function addTerm(data, { korean, english, abbreviation = null, description = "", relatedElements = [] }) {
  if (!korean || !english) throw new Error("korean과 english는 필수입니다.");
  if (data.terms.find((t) => t.korean === korean)) {
    const e = data.terms.find((t) => t.korean === korean);
    throw new Error(`이미 등록된 한글: ${korean} → ${e.english}`);
  }
  if (data.terms.find((t) => t.english.toLowerCase() === english.toLowerCase())) {
    const e = data.terms.find((t) => t.english.toLowerCase() === english.toLowerCase());
    throw new Error(`이미 등록된 영문: ${english} (${e.korean})`);
  }
  if (abbreviation) {
    const e = data.terms.find((t) => t.abbreviation && t.abbreviation.toLowerCase() === abbreviation.toLowerCase());
    if (e) throw new Error(`이미 등록된 축약어: ${abbreviation} (${e.korean})`);
  }
  data.terms.push({ korean, english, abbreviation, description, relatedElements });
  return data;
}
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `pnpm test`
Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add templates/glossary.mjs tests/glossary.test.mjs
git commit -m "feat: glossary addTerm 중복·충돌 검사

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: updateTerm / removeTerm / findTerm

**Files:**
- Modify: `templates/glossary.mjs`
- Test: `tests/glossary.test.mjs`

**Interfaces:**
- Produces:
  - `findTerm(data, korean): Term | undefined`
  - `updateTerm(data, korean, fields): data` — `korean`으로 찾아 `english`/`abbreviation`/`description`/`relatedElements` 중 전달된 것만 갱신. 없으면 throw.
  - `removeTerm(data, korean): data` — 찾아서 삭제. 없으면 throw.

- [ ] **Step 1: 실패하는 테스트 작성**

```js
import { updateTerm, removeTerm, findTerm } from "../templates/glossary.mjs";

test("updateTerm: 지정 필드만 갱신한다", () => {
  const data = { terms: [{ korean: "청구", english: "claim", abbreviation: null, description: "", relatedElements: [] }] };
  updateTerm(data, "청구", { english: "billing", description: "요금 청구" });
  assert.equal(findTerm(data, "청구").english, "billing");
  assert.equal(findTerm(data, "청구").description, "요금 청구");
});

test("updateTerm: 없는 용어는 throw", () => {
  assert.throws(() => updateTerm({ terms: [] }, "없음", { english: "x" }), /등록되지 않은 용어/);
});

test("removeTerm: 용어를 삭제한다", () => {
  const data = { terms: [{ korean: "청구", english: "claim" }] };
  removeTerm(data, "청구");
  assert.equal(data.terms.length, 0);
});

test("removeTerm: 없는 용어는 throw", () => {
  assert.throws(() => removeTerm({ terms: [] }, "없음"), /등록되지 않은 용어/);
});
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `pnpm test`
Expected: FAIL — 함수 미정의.

- [ ] **Step 3: 구현**

```js
export function findTerm(data, korean) {
  return data.terms.find((t) => t.korean === korean);
}

export function updateTerm(data, korean, fields) {
  const term = findTerm(data, korean);
  if (!term) throw new Error(`등록되지 않은 용어: ${korean}`);
  for (const key of ["english", "abbreviation", "description", "relatedElements"]) {
    if (fields[key] !== undefined) term[key] = fields[key];
  }
  return data;
}

export function removeTerm(data, korean) {
  const idx = data.terms.findIndex((t) => t.korean === korean);
  if (idx === -1) throw new Error(`등록되지 않은 용어: ${korean}`);
  data.terms.splice(idx, 1);
  return data;
}
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `pnpm test`
Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add templates/glossary.mjs tests/glossary.test.mjs
git commit -m "feat: glossary update/remove/find

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: listTerms / lookup

**Files:**
- Modify: `templates/glossary.mjs`
- Test: `tests/glossary.test.mjs`

**Interfaces:**
- Produces:
  - `listTerms(data): Term[]` — `sortedTerms`와 동일(가나다순 전체).
  - `lookup(data, query): Term[]` — `korean`/`english`/`abbreviation`에 `query`(대소문자 무시)가 포함된 용어들.

- [ ] **Step 1: 실패하는 테스트 작성**

```js
import { listTerms, lookup } from "../templates/glossary.mjs";

test("lookup: 한글·영문·축약어 부분일치", () => {
  const data = { terms: [
    { korean: "회원", english: "member", abbreviation: null },
    { korean: "식별자", english: "identifier", abbreviation: "id" },
  ] };
  assert.deepEqual(lookup(data, "mem").map(t => t.korean), ["회원"]);
  assert.deepEqual(lookup(data, "ID").map(t => t.korean), ["식별자"]);
});

test("listTerms: 가나다순 전체", () => {
  const data = { terms: [{ korean: "회원", english: "member" }, { korean: "가격", english: "price" }] };
  assert.deepEqual(listTerms(data).map(t => t.korean), ["가격", "회원"]);
});
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `pnpm test`
Expected: FAIL — 함수 미정의.

- [ ] **Step 3: 구현**

```js
export function listTerms(data) {
  return sortedTerms(data);
}

export function lookup(data, query) {
  const q = query.toLowerCase();
  return sortedTerms(data).filter(
    (t) =>
      t.korean.toLowerCase().includes(q) ||
      t.english.toLowerCase().includes(q) ||
      (t.abbreviation && t.abbreviation.toLowerCase().includes(q))
  );
}
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `pnpm test`
Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add templates/glossary.mjs tests/glossary.test.mjs
git commit -m "feat: glossary list/lookup 조회

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: renderCore / renderTerms / build (멱등)

**Files:**
- Modify: `templates/glossary.mjs`
- Test: `tests/glossary.test.mjs`

**Interfaces:**
- Produces:
  - `renderCore(data): string` — `AUTOGEN` + 규칙 주석 + `한글 | 영문 | 축약` 표(가나다순, `abbreviation` null은 빈칸). `description` 제외.
  - `renderTerms(data): string` — `AUTOGEN` + `한글 | 영문 | 축약 | 설명 | 관련 요소` 표(`relatedElements`는 `, ` join).
  - `build(dir): void` — `loadGlossary` → `core.md`·`terms.md` 기록.

- [ ] **Step 1: 실패하는 테스트 작성**

```js
import { renderCore, renderTerms, build, AUTOGEN } from "../templates/glossary.mjs";

test("renderCore: 가나다순 + 축약 빈칸 + 경고주석", () => {
  const data = { terms: [
    { korean: "회원", english: "member", abbreviation: null },
    { korean: "식별자", english: "identifier", abbreviation: "id" },
  ] };
  const out = renderCore(data);
  assert.ok(out.startsWith(AUTOGEN));
  const body = out.indexOf("식별자");
  const member = out.indexOf("회원");
  assert.ok(body < member, "가나다순(식별자<회원)");
  assert.ok(out.includes("| 회원 | member |  |"), "null 축약은 빈칸");
});

test("renderTerms: relatedElements를 콤마로 잇는다", () => {
  const data = { terms: [
    { korean: "식별자", english: "identifier", abbreviation: "id", description: "고유 식별", relatedElements: ["member_id", "product_id"] },
  ] };
  assert.ok(renderTerms(data).includes("| member_id, product_id |"));
});

test("build: 멱등 — 두 번 빌드해도 동일", () => {
  const dir = tmp();
  try {
    saveGlossary(dir, { terms: [{ korean: "회원", english: "member", abbreviation: null, description: "", relatedElements: [] }] });
    build(dir);
    const core1 = loadFile(join(dir, "core.md")), terms1 = loadFile(join(dir, "terms.md"));
    build(dir);
    assert.equal(loadFile(join(dir, "core.md")), core1);
    assert.equal(loadFile(join(dir, "terms.md")), terms1);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
```

테스트 상단 import에 `readFileSync`를 활용한 헬퍼를 추가한다:

```js
import { readFileSync } from "node:fs";
function loadFile(p) { return readFileSync(p, "utf8"); }
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `pnpm test`
Expected: FAIL — render/build 미정의.

- [ ] **Step 3: 구현**

```js
const RULE_COMMENT =
  "<!-- 규칙: 단일어만 등록·조합해 사용한다. 축약어는 이 표에 등록된 것만 허용한다. -->";

export function renderCore(data) {
  const rows = sortedTerms(data)
    .map((t) => `| ${t.korean} | ${t.english} | ${t.abbreviation ?? ""} |`)
    .join("\n");
  return `${AUTOGEN}
${RULE_COMMENT}

| 한글 | 영문 | 축약 |
| --- | --- | --- |
${rows}
`;
}

export function renderTerms(data) {
  const rows = sortedTerms(data)
    .map(
      (t) =>
        `| ${t.korean} | ${t.english} | ${t.abbreviation ?? ""} | ${t.description ?? ""} | ${(t.relatedElements ?? []).join(", ")} |`
    )
    .join("\n");
  return `${AUTOGEN}

| 한글 | 영문 | 축약 | 설명 | 관련 요소 |
| --- | --- | --- | --- | --- |
${rows}
`;
}

export function build(dir) {
  const data = loadGlossary(dir);
  writeFileSync(join(dir, "core.md"), renderCore(data));
  writeFileSync(join(dir, "terms.md"), renderTerms(data));
}
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `pnpm test`
Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add templates/glossary.mjs tests/glossary.test.mjs
git commit -m "feat: glossary build (core.md/terms.md 멱등 생성)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: tokenize / lintFiles

**Files:**
- Modify: `templates/glossary.mjs`
- Test: `tests/glossary.test.mjs`

**Interfaces:**
- Produces:
  - `tokenize(identifier): string[]` — camelCase/snake_case를 소문자 토큰으로 분해. 빈 토큰 제거.
  - `lintFiles(data, files): {token: string, count: number}[]` — 각 파일에서 식별자(`/[A-Za-z_][A-Za-z0-9_]*/g`)를 추출·토큰화해 사전(`english`+`abbreviation` 소문자)과 대조, 미매칭 토큰(길이 ≥ 2)을 빈도와 함께 내림차순 반환. 존재하지 않거나 디렉토리인 경로는 건너뛴다. 의미 확정은 하지 않는다.

- [ ] **Step 1: 실패하는 테스트 작성**

```js
import { tokenize, lintFiles } from "../templates/glossary.mjs";
import { writeFileSync as wf } from "node:fs";

test("tokenize: camelCase/snake_case 분해", () => {
  assert.deepEqual(tokenize("memberId"), ["member", "id"]);
  assert.deepEqual(tokenize("reg_dt"), ["reg", "dt"]);
  assert.deepEqual(tokenize("ship_address"), ["ship", "address"]);
});

test("lintFiles: 미등록 토큰을 빈도와 함께 반환", () => {
  const dir = tmp();
  try {
    const f = join(dir, "sample.js");
    wf(f, "const customer = 1; const customerName = 2; const memberId = 3;");
    const data = { terms: [
      { korean: "회원", english: "member", abbreviation: null },
      { korean: "식별자", english: "identifier", abbreviation: "id" },
      { korean: "이름", english: "name", abbreviation: null },
    ] };
    const result = lintFiles(data, [f]);
    const customer = result.find((r) => r.token === "customer");
    assert.ok(customer && customer.count === 2, "customer 2회 미등록");
    assert.ok(!result.find((r) => r.token === "member"), "member는 등록되어 제외");
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `pnpm test`
Expected: FAIL — 함수 미정의.

- [ ] **Step 3: 구현**

`glossary.mjs` import에 `existsSync`, `statSync`를 추가하고 함수를 작성한다:

```js
// 상단 import 수정:
// import { readFileSync, writeFileSync, existsSync, statSync } from "node:fs";

export function tokenize(identifier) {
  return identifier
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .split(/[_\s]+/)
    .map((s) => s.toLowerCase())
    .filter(Boolean);
}

export function lintFiles(data, files) {
  const known = new Set();
  for (const t of data.terms) {
    known.add(t.english.toLowerCase());
    if (t.abbreviation) known.add(t.abbreviation.toLowerCase());
  }
  const counts = new Map();
  for (const file of files) {
    if (!existsSync(file) || statSync(file).isDirectory()) continue;
    const ids = readFileSync(file, "utf8").match(/[A-Za-z_][A-Za-z0-9_]*/g) || [];
    for (const id of ids) {
      for (const tok of tokenize(id)) {
        if (tok.length < 2 || known.has(tok)) continue;
        counts.set(tok, (counts.get(tok) || 0) + 1);
      }
    }
  }
  return [...counts.entries()]
    .map(([token, count]) => ({ token, count }))
    .sort((a, b) => b.count - a.count);
}
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `pnpm test`
Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add templates/glossary.mjs tests/glossary.test.mjs
git commit -m "feat: glossary lint (토큰 추출·사전 대조 후보)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: scaffold (초기 데이터 + CLAUDE.md 블록)

**Files:**
- Modify: `templates/glossary.mjs`
- Test: `tests/glossary.test.mjs`

**Interfaces:**
- Consumes: `saveGlossary`, `build`.
- Produces:
  - 상수 `INITIAL_DATA` — 식별자/일시(at)/이름 3개 용어.
  - 상수 `CLAUDE_BLOCK` — `## 용어 사전` 섹션 텍스트(import + 규칙).
  - `scaffold(dataDir): void` — `dataDir`(=`.claude/superglossary`) 생성, `glossary.json` 없으면 `INITIAL_DATA` 저장, `build`, `dataDir/../CLAUDE.md`(=`.claude/CLAUDE.md`)에 `## 용어 사전` 섹션이 없으면 `CLAUDE_BLOCK` append.

- [ ] **Step 1: 실패하는 테스트 작성**

```js
import { scaffold } from "../templates/glossary.mjs";
import { mkdirSync } from "node:fs";

test("scaffold: 초기 데이터·생성물·CLAUDE.md 블록", () => {
  const root = tmp();
  try {
    const dataDir = join(root, ".claude", "superglossary");
    scaffold(dataDir);
    const data = loadGlossary(dataDir);
    assert.ok(data.terms.find((t) => t.korean === "일시" && t.abbreviation === "at"), "일시=at");
    assert.ok(!data.terms.find((t) => t.korean === "주소"), "주소 없음");
    assert.ok(loadFile(join(dataDir, "core.md")).includes("identifier"));
    const claude = loadFile(join(root, ".claude", "CLAUDE.md"));
    assert.ok(claude.includes("## 용어 사전"));
    assert.ok(claude.includes("@superglossary/core.md"));
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("scaffold: 기존 CLAUDE.md에 중복 추가하지 않는다", () => {
  const root = tmp();
  try {
    const dataDir = join(root, ".claude", "superglossary");
    mkdirSync(join(root, ".claude"), { recursive: true });
    wf(join(root, ".claude", "CLAUDE.md"), "# 기존\n\n## 용어 사전\n기존 내용\n");
    scaffold(dataDir);
    const claude = loadFile(join(root, ".claude", "CLAUDE.md"));
    assert.equal(claude.match(/## 용어 사전/g).length, 1, "섹션 1개 유지");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `pnpm test`
Expected: FAIL — `scaffold is not a function`.

- [ ] **Step 3: 구현**

`glossary.mjs` import에 `mkdirSync`를 추가하고 작성한다:

```js
// import { readFileSync, writeFileSync, existsSync, statSync, mkdirSync } from "node:fs";
// import { join } from "node:path";  (dirname 불필요 — ../로 접근)

export const INITIAL_DATA = {
  terms: [
    { korean: "식별자", english: "identifier", abbreviation: "id", description: "데이터를 고유 식별하는 값. {엔티티}_id 형식", relatedElements: [] },
    { korean: "일시", english: "datetime", abbreviation: "at", description: "날짜와 시각. created_at 처럼 _at 접미사로 사용", relatedElements: [] },
    { korean: "이름", english: "name", abbreviation: null, description: "대상을 지칭하는 명칭", relatedElements: [] },
  ],
};

export const CLAUDE_BLOCK = `## 용어 사전
@superglossary/core.md

- 클래스/변수/함수/컬럼/테이블 등 모든 네이밍은 위 표의 영문명만 사용한다. 축약어는 표에 등록된 것만 허용한다.
- 표에 없는 단일어가 필요하면 임의로 짓지 말고, Claude가 직접 \`node .claude/superglossary/glossary.mjs add <korean> <english> [abbreviation]\`로 추가한다(사용자는 \`/superglossary:add\`도 사용 가능). 복합어는 단일어로 분해해 등록하고, 변경은 같은 diff에 포함한다.
- 용어 수정·삭제가 필요하면 \`node .claude/superglossary/glossary.mjs update <korean> ...\` 또는 \`remove <korean>\`을 사용한다(둘 다 자동 재빌드).
- 기존 모듈 수정 시 그 모듈의 기존 컨벤션을 우선하고, 신규 코드에는 사전을 우선한다. 임의 리네이밍은 하지 않는다.
- 비즈니스 의미·주의사항이 필요하면 \`.claude/superglossary/terms.md\`를 찾는다. core.md·terms.md는 생성물이므로 직접 편집하지 않는다.
- 워크플로: 작업 시작 전 핵심 개념 정렬 → 작업 중 검색 없이 작성하고 사전에 없는 용어만 추가 → 완료 후 \`glossary-check\`로 검토.
`;

export function scaffold(dataDir) {
  mkdirSync(dataDir, { recursive: true });
  if (!existsSync(join(dataDir, "glossary.json"))) saveGlossary(dataDir, INITIAL_DATA);
  build(dataDir);
  const claudeMd = join(dataDir, "..", "CLAUDE.md");
  const existing = existsSync(claudeMd) ? readFileSync(claudeMd, "utf8") : "";
  if (!existing.includes("## 용어 사전")) {
    const next = existing.trimEnd();
    writeFileSync(claudeMd, (next ? next + "\n\n" : "") + CLAUDE_BLOCK);
  }
}
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `pnpm test`
Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add templates/glossary.mjs tests/glossary.test.mjs
git commit -m "feat: glossary scaffold (초기 데이터·CLAUDE.md 연결)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 8: CLI 진입점 (argv 파싱·디스패치)

**Files:**
- Modify: `templates/glossary.mjs`
- Test: `tests/glossary.test.mjs`

**Interfaces:**
- Consumes: 모든 이전 함수.
- Produces:
  - `parseArgs(rest): {positional: string[], options: {[k]: string}}` — `--key value`와 `--key=value`를 옵션으로, 나머지는 positional로.
  - `run(argv, dataDir): string` — 서브커맨드 디스패치(`init`/`build`/`add`/`update`/`remove`/`list`/`lookup`/`lint`), 사람이 읽을 결과 문자열 반환. 오류는 throw.
  - 직접 실행 시 `run(process.argv.slice(2), <SELF_DIR>)`를 호출하고, throw 시 stderr 출력 + `exitCode=1`. `init`은 `process.cwd()/.claude/superglossary`를 대상으로 한다(나머지는 SELF_DIR).

- [ ] **Step 1: 실패하는 테스트 작성**

```js
import { parseArgs, run } from "../templates/glossary.mjs";

test("parseArgs: positional과 옵션 분리", () => {
  const { positional, options } = parseArgs(["청구", "claim", "--desc", "요금", "--related=a,b"]);
  assert.deepEqual(positional, ["청구", "claim"]);
  assert.equal(options.desc, "요금");
  assert.equal(options.related, "a,b");
});

test("run add → list가 등록을 반영하고 생성물을 빌드한다", () => {
  const dir = tmp();
  try {
    saveGlossary(dir, { terms: [] });
    run(["add", "회원", "member"], dir);
    run(["add", "식별자", "identifier", "id", "--desc", "고유값"], dir);
    const listed = run(["list"], dir);
    assert.ok(listed.includes("회원") && listed.includes("member"));
    assert.ok(loadFile(join(dir, "core.md")).includes("identifier"), "add가 재빌드한다");
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("run remove가 용어를 제거한다", () => {
  const dir = tmp();
  try {
    saveGlossary(dir, { terms: [{ korean: "회원", english: "member", abbreviation: null, description: "", relatedElements: [] }] });
    run(["remove", "회원"], dir);
    assert.equal(loadGlossary(dir).terms.length, 0);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `pnpm test`
Expected: FAIL — `parseArgs`/`run` 미정의.

- [ ] **Step 3: 구현**

`glossary.mjs` 상단 import에 `fileURLToPath`를 추가하고(`import { fileURLToPath } from "node:url";`), `dirname`도 추가한다(`import { join, dirname } from "node:path";`). 파일 끝에 작성한다:

```js
export function parseArgs(rest) {
  const positional = [];
  const options = {};
  for (let i = 0; i < rest.length; i++) {
    const a = rest[i];
    if (a.startsWith("--")) {
      const eq = a.indexOf("=");
      if (eq !== -1) options[a.slice(2, eq)] = a.slice(eq + 1);
      else options[a.slice(2)] = rest[++i];
    } else {
      positional.push(a);
    }
  }
  return { positional, options };
}

function relatedFromOptions(options) {
  return options.related ? options.related.split(",").map((s) => s.trim()).filter(Boolean) : undefined;
}

export function run(argv, dataDir) {
  const [cmd, ...rest] = argv;
  const { positional, options } = parseArgs(rest);
  switch (cmd) {
    case "init":
      scaffold(dataDir);
      return `초기화 완료: ${dataDir}`;
    case "build":
      build(dataDir);
      return "빌드 완료: core.md, terms.md";
    case "add": {
      const [korean, english, abbreviation] = positional;
      const data = loadGlossary(dataDir);
      addTerm(data, {
        korean, english, abbreviation: abbreviation ?? null,
        description: options.desc ?? "", relatedElements: relatedFromOptions(options) ?? [],
      });
      saveGlossary(dataDir, data);
      build(dataDir);
      return `추가: ${korean} → ${english}`;
    }
    case "update": {
      const [korean] = positional;
      const data = loadGlossary(dataDir);
      const fields = {};
      if (options.english !== undefined) fields.english = options.english;
      if (options.abbreviation !== undefined) fields.abbreviation = options.abbreviation || null;
      if (options.desc !== undefined) fields.description = options.desc;
      const related = relatedFromOptions(options);
      if (related !== undefined) fields.relatedElements = related;
      updateTerm(data, korean, fields);
      saveGlossary(dataDir, data);
      build(dataDir);
      return `수정: ${korean}`;
    }
    case "remove": {
      const [korean] = positional;
      const data = loadGlossary(dataDir);
      removeTerm(data, korean);
      saveGlossary(dataDir, data);
      build(dataDir);
      return `삭제: ${korean}`;
    }
    case "list": {
      const data = loadGlossary(dataDir);
      return listTerms(data).map((t) => `${t.korean}\t${t.english}\t${t.abbreviation ?? ""}`).join("\n");
    }
    case "lookup": {
      const data = loadGlossary(dataDir);
      return lookup(data, positional[0] ?? "").map((t) => `${t.korean}\t${t.english}\t${t.abbreviation ?? ""}`).join("\n");
    }
    case "lint": {
      const data = loadGlossary(dataDir);
      return lintFiles(data, positional).map((r) => `${r.token}\t${r.count}`).join("\n");
    }
    default:
      return "사용법: glossary.mjs <init|build|add|update|remove|list|lookup|lint> ...";
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const SELF_DIR = dirname(fileURLToPath(import.meta.url));
  const argv = process.argv.slice(2);
  const dataDir = argv[0] === "init" ? join(process.cwd(), ".claude", "superglossary") : SELF_DIR;
  try {
    const out = run(argv, dataDir);
    if (out) console.log(out);
  } catch (err) {
    console.error(`✗ ${err.message}`);
    process.exitCode = 1;
  }
}
```

> 주: `init`은 `process.cwd()/.claude/superglossary`를 대상으로 한다. init 커맨드가 이 위치에 `glossary.mjs`를 미리 복사한 뒤 거기서 실행하므로 `SELF_DIR`와 동일 경로가 된다.

- [ ] **Step 4: 테스트 통과 확인**

Run: `pnpm test`
Expected: PASS (전체)

- [ ] **Step 5: 수동 스모크 테스트**

Run:
```bash
mkdir -p /tmp/sg-smoke && cp templates/glossary.mjs /tmp/sg-smoke/ && cd /tmp/sg-smoke
node glossary.mjs init && node glossary.mjs add 청구 claim && node glossary.mjs list
node glossary.mjs build && node glossary.mjs build && git -C /tmp/sg-smoke init -q && git -C /tmp/sg-smoke add -A
cd - && rm -rf /tmp/sg-smoke
```
Expected: init/add/list 정상 출력, 두 번째 build 후에도 core.md/terms.md 동일.

- [ ] **Step 6: 커밋**

```bash
git add templates/glossary.mjs tests/glossary.test.mjs
git commit -m "feat: glossary CLI 진입점(서브커맨드 디스패치)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 9: commands/init.md

**Files:**
- Create: `commands/init.md`

- [ ] **Step 1: 파일 작성**

```markdown
---
description: 프로젝트 용어사전을 초기화하고 .claude/CLAUDE.md에 연결합니다
argument-hint: ""
allowed-tools: Bash, Read, Write, Edit, Task, AskUserQuestion
---

# 용어사전 초기화

다음을 순서대로 수행한다.

1. `.claude/superglossary/` 디렉토리를 만들고 `${CLAUDE_PLUGIN_ROOT}/templates/glossary.mjs`를 `.claude/superglossary/glossary.mjs`로 복사한다.
2. `node .claude/superglossary/glossary.mjs init`을 실행한다 → 초기 `glossary.json`(없을 때) · `core.md` · `terms.md` 생성 + `.claude/CLAUDE.md`에 `## 용어 사전` 블록 삽입(이미 있으면 건너뜀).
3. 생성·연결 결과를 사용자에게 보고한다.

## 기존 코드베이스(brownfield)라면

코드가 이미 존재하면, **용어 후보·혼용 스캔 여부를 먼저 사용자에게 묻는다**(AskUserQuestion).

- 동의하면 `glossary-scanner` 서브에이전트를 Task로 dispatch한다.
- scanner가 반환한 **(a) 단일어 후보**와 **(b) 혼용 리포트(영문 변형·빈도)**를 사용자에게 제시한다.
- 사용자가 후보를 선별하고, 혼용 건은 **표준 1개**를 고르면, 각 항목을 `node .claude/superglossary/glossary.mjs add <korean> <english> [abbreviation] [--desc "..."]`로 등록한다.
- **자동 리네이밍은 하지 않는다.** 비표준 사용처는 이후 `glossary-check`가 보고한다.

분류(category)는 v1에서 다루지 않는다.
```

- [ ] **Step 2: 커밋**

```bash
git add commands/init.md
git commit -m "feat: /superglossary:init 커맨드

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 10: commands/add.md

**Files:**
- Create: `commands/add.md`

- [ ] **Step 1: 파일 작성**

```markdown
---
description: 용어사전에 단일어를 등록합니다 (복합어는 분해 안내)
argument-hint: <한글> <영문> [축약어] [-- 설명]
allowed-tools: Bash, Read
---

# 용어 등록

입력: `$ARGUMENTS`

1. **복합어 검사**: 입력 한글이 복합어(예: "회원번호")면 단일어로 분해를 안내한다. 등록된 단일어 조합으로 표현 가능하면(예: 회원=member + 식별자=id → `member_id`) 그 방법을 제시하고, 미등록 단일어만 등록 대상으로 삼는다.
2. **등록**: 단일어마다 `node .claude/superglossary/glossary.mjs add <korean> <english> [abbreviation] [--desc "설명"] [--related "a,b"]`를 실행한다. 스크립트가 중복·충돌(한글/영문/축약어)을 검사하고 통과 시 추가 + 재빌드한다.
3. 스크립트가 충돌로 비정상 종료(기존 항목 출력)하면, 그 내용을 사용자에게 설명하고 해당 항목 등록을 중단한다.

> 분류(category)는 v1에서 다루지 않는다. 수정·삭제는 `glossary.mjs update`/`remove`를 쓴다.
```

- [ ] **Step 2: 커밋**

```bash
git add commands/add.md
git commit -m "feat: /superglossary:add 커맨드

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 11: skills/glossary-check/SKILL.md

**Files:**
- Create: `skills/glossary-check/SKILL.md`

- [ ] **Step 1: 파일 작성**

```markdown
---
name: glossary-check
description: 작업 완료 후나 커밋 전에 코드 네이밍을 프로젝트 용어사전과 대조해 위반·누락 용어를 검토할 때 사용한다. "용어 검사", "사전이랑 맞는지 확인", "네이밍 점검" 같은 요청에 트리거.
---

# 용어사전 검토

`.claude/superglossary/`가 있는 프로젝트에서 코드 네이밍을 사전과 대조한다.

1. **대상 결정**: 인자가 없으면 `git diff`(staged + unstaged)의 변경 파일, 경로가 주어지면 그 범위.
2. **후보 추출(결정론)**: `node .claude/superglossary/glossary.mjs lint <files...>`로 미매칭 토큰·미등록 축약어 후보를 빈도와 함께 얻는다.
3. **의미 확정(서브에이전트)**: 위 후보와 `node .claude/superglossary/glossary.mjs list` 결과를 `check-analyzer` 서브에이전트에 넘겨(Task) 의미 기반 확정을 받는다.
4. **보고**: 위반(코드→사전 다른 영문/미등록 축약어)과 추가 후보(사전→코드 미등록 용어)를 표로 보고한다. **자동 수정은 하지 않는다** — 적용은 사용자 판단.

작업 완료 후 커밋 전에 실행하기를 권장한다.
```

- [ ] **Step 2: 커밋**

```bash
git add skills/glossary-check/SKILL.md
git commit -m "feat: glossary-check 스킬

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 12: agents/check-analyzer.md

**Files:**
- Create: `agents/check-analyzer.md`

- [ ] **Step 1: 파일 작성**

```markdown
---
name: check-analyzer
description: 코드 식별자를 용어사전과 대조해 위반과 추가 후보를 의미 기반으로 확정하는 분석 에이전트
model: sonnet
tools: Read, Grep, Glob, Bash
---

당신은 프로젝트 용어사전 준수를 검토하는 분석가다. 입력으로 lint 후보(미매칭 토큰+빈도)와 사전(`list` 결과)을 받는다. 필요하면 `node .claude/superglossary/glossary.mjs lookup <q>`로 사전을 추가 조회한다.

## 판단

- **코드→사전 위반**
  - 사전에 등록된 개념을 다른 영문으로 사용(예: 사전 `member` ↔ 코드 `customer`).
  - 사전에 없는 축약어 사용(예: `reg_dt`의 `reg`).
- **사전→코드 추가 후보**
  - 코드에 반복 등장하지만 미등록인 단일어.

## 원칙

- **의미로 판단한다.** 동의어(member/customer/user)는 같은 개념일 수 있다 — 빈도와 문맥을 함께 본다.
- **노이즈 제외.** 일반 영어 단어·언어 키워드·라이브러리 식별자는 위반에서 뺀다.
- **기존 컨벤션 존중.** 기존 모듈의 네이밍을 우선한다. 자동 수정·임의 리네이밍을 제안하지 않는다.

## 출력

1. **위반 목록**: `파일:라인 | 코드 표현 | 사전 표준(영문) | 사유`
2. **추가 후보**: `한글(추정) | 영문 | 사유` — 사용자가 `/superglossary:add`로 등록할 대상.

확정 가능한 것만 보고하고, 애매하면 후보로 분류한다.
```

- [ ] **Step 2: 커밋**

```bash
git add agents/check-analyzer.md
git commit -m "feat: check-analyzer 서브에이전트(sonnet)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 13: agents/glossary-scanner.md

**Files:**
- Create: `agents/glossary-scanner.md`

- [ ] **Step 1: 파일 작성**

```markdown
---
name: glossary-scanner
description: 기존 코드베이스를 스캔해 단일어 용어 후보와 용어 혼용(영문 변형·빈도)을 추출하는 에이전트
model: sonnet
tools: Read, Grep, Glob
---

당신은 기존 코드베이스에서 용어를 추출하는 분석가다. init이 brownfield에서 호출한다.

## 작업

1. **단일어 후보 추출**: 엔티티/테이블/도메인 클래스·컬럼·주요 변수명을 스캔해 핵심 개념을 추출한다. **복합어는 단일어로 분해한다**(`member_id` → `member`, `id`). 단일어 중심 원칙을 지킨다.
2. **혼용 탐지**: 같은 개념에 쓰인 영문 변형과 사용 빈도를 집계한다(예: 사용자 → `user`×120 / `member`×45 / `customer`×12).

## 출력

1. **단일어 후보**: `한글 | 영문 | 축약(선택) | 근거(등장 위치)`
2. **혼용 리포트**: `개념(한글) | 변형들과 빈도 | 최다 빈도(참고)`

**표준 선정은 사용자 몫이다.** 강요하지 말고 빈도만 제시한다. 분류(category)는 다루지 않는다.
```

- [ ] **Step 2: 커밋**

```bash
git add agents/glossary-scanner.md
git commit -m "feat: glossary-scanner 서브에이전트(sonnet)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 14: 매니페스트 버전 + plugin validate

**Files:**
- Modify: `.claude-plugin/plugin.json` (version)

- [ ] **Step 1: 버전 상향**

Run: `pnpm bump 0.2.0`
Expected: `plugin.json` version이 `0.2.0`으로 갱신.

- [ ] **Step 2: 플러그인 검증**

Run: `claude plugin validate .`
Expected: 통과(컴포넌트 commands/skills/agents 인식). 오류가 나면 해당 파일 frontmatter를 수정하고 재실행.

- [ ] **Step 3: 커밋**

```bash
git add .claude-plugin/plugin.json
git commit -m "chore: v0.2.0 버전 상향

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 15: README / CHANGELOG / CLAUDE.md 갱신

**Files:**
- Modify: `README.md`, `CHANGELOG.md`, `CLAUDE.md`

- [ ] **Step 1: README.md 갱신**

기존 "추후 제공" 문구를 걷어내고 다음을 포함한다(한국어):
- **권장 워크플로우**(상단 가까이): 시작 전 정렬 → 작업 중 검색 없이 작성하고 사전에 없는 용어만 추가 → 완료 후 `glossary-check` → (선택) 커밋/PR 검사.
- **구성 요소**: 커맨드 `/superglossary:init`·`/superglossary:add`, 스킬 `glossary-check`, 서브에이전트 `check-analyzer`·`glossary-scanner`, CLI `glossary.mjs`(의존성 0).
- **데이터·로딩**: `.claude/superglossary/`(glossary.json·core.md·terms.md·glossary.mjs), 상시 로드는 `.claude/CLAUDE.md`의 `@superglossary/core.md`.
- **설치·테스트**: 로컬은 `claude --plugin-dir .`, 배포는 `/plugin marketplace add Cho-D-YoungRae/superglossary` → `/plugin install superglossary@superglossary`.
- **(선택) 자동 트리거**: pre-commit/CI에서 `glossary-check` 또는 `node .claude/superglossary/glossary.mjs lint`를 **경고 전용**으로 거는 예시. 기본 미포함임을 명시. "빌드 후 git diff가 비어야 한다"는 생성물 stale 검사 예시.
- **출처 명시**: 강의 「김영한의 실전 데이터베이스 - 설계 1편, 현대적 데이터 모델링 완전 정복」의 '용어 사전' 부분을 참고했음을 적고 링크(https://www.inflearn.com/course/김영한-실전-데이터베이스-설계1편/dashboard?cid=338886).

- [ ] **Step 2: CHANGELOG.md 갱신**

`[Unreleased]` 아래에 `### Added`로 커맨드·스킬·서브에이전트·CLI 추가를 기록한다(릴리즈 시 `[0.2.0] - <YYYY-MM-DD>`로 정리).

- [ ] **Step 3: CLAUDE.md 갱신**

"매니페스트-only 상태" 서술을 갱신하고 컴포넌트 위치를 반영한다: `commands/`, `skills/`, `agents/`는 저장소 루트, 사용자 배포 CLI 원본은 `templates/glossary.mjs`, 테스트는 `tests/`(node:test). "용어사전 데이터는 사용자 프로젝트의 `.claude/superglossary/`에 생성됨"을 적는다.

- [ ] **Step 4: 커밋**

```bash
git add README.md CHANGELOG.md CLAUDE.md
git commit -m "docs: v0.2.0 용어사전 기능 문서화(README/CHANGELOG/CLAUDE.md)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 16: E2E 시나리오 검증

**Files:** (없음 — 검증 전용)

- [ ] **Step 1: 임시 프로젝트에서 전체 흐름 확인**

Run:
```bash
SG=$(pwd)
mkdir -p /tmp/sg-e2e && cd /tmp/sg-e2e && git init -q
mkdir -p .claude/superglossary && cp "$SG/templates/glossary.mjs" .claude/superglossary/
node .claude/superglossary/glossary.mjs init
node .claude/superglossary/glossary.mjs add 청구 claim
node .claude/superglossary/glossary.mjs add 재고관리단위 "Stock Keeping Unit" SKU
node .claude/superglossary/glossary.mjs update 청구 --english billing
node .claude/superglossary/glossary.mjs list
printf 'const customer = 1;\nconst regDt = 2;\n' > sample.js
node .claude/superglossary/glossary.mjs lint sample.js
node .claude/superglossary/glossary.mjs build && git add -A && git status --porcelain
cd "$SG" && rm -rf /tmp/sg-e2e
```
Expected:
- init: `.claude/superglossary/{glossary.json,core.md,terms.md}` 생성, `.claude/CLAUDE.md`에 `@superglossary/core.md` 포함, 초기 데이터에 일시(`at`)·주소 없음.
- add/update/list: 청구→billing 반영, SKU 단일 표 등록.
- lint sample.js: `customer`, `dt`(regDt 분해) 등 미등록 후보 출력.
- 두 번째 build 후 `git status --porcelain`에 core.md/terms.md 변화 없음(멱등).

- [ ] **Step 2: 전체 테스트 + 검증 재확인**

Run: `pnpm test && claude plugin validate .`
Expected: 모든 테스트 PASS, validate 통과.

- [ ] **Step 3: 결과 보고**

E2E 결과(각 시나리오 성공/실패)를 사용자에게 보고한다. 실패 항목이 있으면 해당 Task로 돌아가 수정한다.

---

## Self-Review (작성자 체크리스트 — 완료)

**1. Spec coverage:** 스펙 §4~§13의 컴포넌트(커맨드 2·스킬 1·에이전트 2·CLI 7서브커맨드)·데이터 모델(풀어쓰기 스키마, 분류 제외, relatedElements 배열)·CLAUDE.md 통합·brownfield 혼용·멱등·강의 출처가 각각 Task 1~16에 매핑됨. CRUD(add/update/remove)·lint·list 모두 태스크 보유.

**2. Placeholder scan:** 모든 코드 스텝에 실제 코드, 모든 마크다운 컴포넌트에 전체 내용 포함. "TBD/적절히" 없음.

**3. Type consistency:** 함수 시그니처 일관 — `loadGlossary`/`saveGlossary`(dir), `addTerm`/`updateTerm`/`removeTerm`/`findTerm`/`listTerms`/`lookup`(data), `renderCore`/`renderTerms`/`build`, `tokenize`/`lintFiles`, `scaffold`(dataDir), `parseArgs`/`run`(argv, dataDir). `Term` 필드(`korean`/`english`/`abbreviation`/`description`/`relatedElements`)가 전 태스크에서 동일.
