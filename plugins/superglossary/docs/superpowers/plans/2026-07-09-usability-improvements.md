# superglossary v0.3.0 사용성 개선 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [2026-07-09 스펙](../specs/2026-07-09-usability-improvements-design.md)에 따라 검사 정확도(avoid·스톱워드·lookup 상세), 운영 안전장치(gitignore·stale·버전), commands→skills 전환, 폴리시 개선을 구현한다.

**Architecture:** 단일 CLI(`templates/glossary.mjs`, 의존성 0)에 결정론 로직을 집중하고, 스킬(마크다운)은 절차 지시만 담는다. Task 1–7이 CLI·스크립트(TDD), Task 8–10이 컴포넌트(md), Task 11–12가 문서·릴리즈다.

**Tech Stack:** Node.js(내장 모듈만: `node:fs`, `node:path`, `node:child_process`), `node:test`, Claude Code 플러그인(skills/agents), pnpm 스크립트.

## Global Constraints

- **의존성 0**: `templates/glossary.mjs`는 Node 내장 모듈만 import 한다(`node:child_process` 포함 — 내장이므로 허용).
- **모든 사용자 대면 문자열은 한국어**, 코드 식별자·스키마 키는 영문 풀어쓰기(`korean`/`english`/`abbreviation`/`avoid`).
- **생성물 멱등**: 같은 glossary.json으로 build 2회 → 파일 동일(기존 테스트가 회귀 감지).
- **테스트**: `pnpm test`(= `node --test`, tests/ 자동 발견). 기존 24개 테스트는 본 계획이 명시한 2건(addTerm 정규화 deepEqual, lintFiles 반환 형태)의 수정 외에는 계속 통과해야 한다.
- **작업 브랜치**: `feature/usability-improvements`(이미 생성됨, 스펙 커밋 포함). 커밋 메시지는 conventional commits + 한국어(기존 이력 참고: `feat:`, `docs:`, `chore:`, `refactor:`).
- **버전**: Task 12 전까지 `plugin.json`과 CLI `VERSION`은 `0.2.0`으로 유지, Task 12에서 `pnpm bump 0.3.0`으로 동시 상향.
- 커밋 트레일러: `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task 1: `avoid` 필드 — 데이터 계층 충돌 규칙

**Files:**
- Modify: `templates/glossary.mjs` (addTerm/updateTerm/INITIAL_DATA, findConflict 신설)
- Test: `tests/glossary.test.mjs`

**Interfaces:**
- Consumes: 기존 `findTerm(data, korean)`, terms 항목 형태 `{korean, english, abbreviation, description, relatedElements}`
- Produces: terms 항목에 `avoid: string[]` 추가(기본 `[]`), `findConflict(otherTerms, {korean, english, abbreviation, avoid}): string | null` export, `addTerm`이 `avoid` 옵션 수용, `updateTerm(data, korean, fields)`의 fields에 `avoid` 허용. 에러 메시지 패턴: `이미 등록된 한글|영문|축약어`, `이미 등록된 축약어와 충돌`, `이미 등록된 영문과 충돌`, `...은(는) 금지 변형입니다. 표준: ...`, `금지 변형 '...'이(가) 등록 용어 ...과(와) 충돌합니다`, `금지 변형 '...'은(는) 이미 ...의 금지 목록에 있습니다`, `금지 변형 '...'이(가) 자신의 영문|축약어와 같습니다`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/glossary.test.mjs`의 import에 `findConflict`를 추가하고, 파일 끝에 아래 테스트를 추가한다. 또한 기존 테스트 `"addTerm: 새 용어를 정규화해 추가한다"`의 기대 객체에 `avoid: []`를 추가한다:

```js
test("addTerm: 새 용어를 정규화해 추가한다", () => {
  const data = { terms: [] };
  addTerm(data, { korean: "회원", english: "member" });
  assert.deepEqual(data.terms[0], {
    korean: "회원", english: "member", abbreviation: null, description: "", relatedElements: [], avoid: [],
  });
});
```

신규 테스트:

```js
test("addTerm: avoid를 배열로 저장한다", () => {
  const data = { terms: [] };
  addTerm(data, { korean: "회원", english: "member", avoid: ["customer", "user"] });
  assert.deepEqual(data.terms[0].avoid, ["customer", "user"]);
});

test("addTerm: 신규 english가 기존 avoid에 있으면 표준을 안내하며 거부한다", () => {
  const data = { terms: [{ korean: "회원", english: "member", abbreviation: null, avoid: ["customer"] }] };
  assert.throws(
    () => addTerm(data, { korean: "고객", english: "Customer" }),
    /금지 변형입니다. 표준: member/
  );
});

test("addTerm: avoid가 기존 english와 겹치면 거부한다", () => {
  const data = { terms: [{ korean: "회원", english: "member", abbreviation: null }] };
  assert.throws(
    () => addTerm(data, { korean: "고객", english: "client", avoid: ["member"] }),
    /금지 변형 'member'이\(가\) 등록 용어 회원\(member\)과\(와\) 충돌합니다/
  );
});

test("addTerm: avoid가 기존 abbreviation과 겹치면 거부한다", () => {
  const data = { terms: [{ korean: "식별자", english: "identifier", abbreviation: "id" }] };
  assert.throws(
    () => addTerm(data, { korean: "지표", english: "metric", avoid: ["ID"] }),
    /등록 용어 식별자\(identifier\)과\(와\) 충돌합니다/
  );
});

test("addTerm: avoid는 전역 유일 — 다른 용어의 avoid와 겹치면 거부한다", () => {
  const data = { terms: [{ korean: "회원", english: "member", abbreviation: null, avoid: ["customer"] }] };
  assert.throws(
    () => addTerm(data, { korean: "고객", english: "client", avoid: ["customer"] }),
    /이미 회원\(member\)의 금지 목록에 있습니다/
  );
});

test("addTerm: avoid가 자신의 english/abbreviation과 같으면 거부한다", () => {
  assert.throws(
    () => addTerm({ terms: [] }, { korean: "고객", english: "client", avoid: ["client"] }),
    /자신의 영문/
  );
  assert.throws(
    () => addTerm({ terms: [] }, { korean: "고객", english: "client", abbreviation: "cl", avoid: ["cl"] }),
    /자신의 축약어/
  );
});

test("addTerm: english↔abbreviation 교차 충돌을 거부한다", () => {
  const data = { terms: [
    { korean: "식별자", english: "identifier", abbreviation: "id" },
    { korean: "회원", english: "member", abbreviation: null },
  ] };
  assert.throws(() => addTerm(data, { korean: "지표", english: "id" }), /이미 등록된 축약어와 충돌/);
  assert.throws(() => addTerm(data, { korean: "고객", english: "client", abbreviation: "member" }), /이미 등록된 영문과 충돌/);
});

test("updateTerm: avoid 갱신과 충돌 검사", () => {
  const data = { terms: [
    { korean: "회원", english: "member", abbreviation: null, description: "", relatedElements: [], avoid: [] },
    { korean: "주문", english: "order", abbreviation: null, description: "", relatedElements: [], avoid: [] },
  ] };
  updateTerm(data, "회원", { avoid: ["customer", "user"] });
  assert.deepEqual(findTerm(data, "회원").avoid, ["customer", "user"]);
  assert.throws(() => updateTerm(data, "회원", { avoid: ["order"] }), /등록 용어 주문\(order\)과\(와\) 충돌합니다/);
  assert.deepEqual(findTerm(data, "회원").avoid, ["customer", "user"], "실패 시 원본 불변");
});

test("findConflict: 충돌 없으면 null", () => {
  assert.equal(findConflict([], { korean: "회원", english: "member", abbreviation: null, avoid: [] }), null);
});
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `pnpm test`
Expected: FAIL — `findConflict` export 없음(SyntaxError) 또는 신규 테스트들 실패, `addTerm 정규화` 테스트도 `avoid: []` 부재로 실패.

- [ ] **Step 3: 구현**

`templates/glossary.mjs`에서 기존 `addTerm`(22–35행)과 `updateTerm`(41–48행)을 아래로 교체하고, `INITIAL_DATA`의 세 항목에 `avoid: []`를 추가한다:

```js
function avoidOf(term) {
  return term.avoid ?? [];
}

export function findConflict(otherTerms, { korean, english, abbreviation = null, avoid = [] }) {
  const e = english ? english.toLowerCase() : null;
  const a = abbreviation ? abbreviation.toLowerCase() : null;
  const av = avoid.map((s) => s.toLowerCase());
  if (e && av.includes(e)) return `금지 변형 '${english}'이(가) 자신의 영문과 같습니다`;
  if (a && av.includes(a)) return `금지 변형 '${abbreviation}'이(가) 자신의 축약어와 같습니다`;
  for (const t of otherTerms) {
    const te = t.english.toLowerCase();
    const ta = t.abbreviation ? t.abbreviation.toLowerCase() : null;
    const tav = avoidOf(t).map((s) => s.toLowerCase());
    if (t.korean === korean) return `이미 등록된 한글: ${korean} → ${t.english}`;
    if (e === te) return `이미 등록된 영문: ${english} (${t.korean})`;
    if (e && e === ta) return `이미 등록된 축약어와 충돌: ${english} (${t.korean})`;
    if (e && tav.includes(e)) return `'${english}'은(는) 금지 변형입니다. 표준: ${t.english}(${t.korean})`;
    if (a && a === ta) return `이미 등록된 축약어: ${abbreviation} (${t.korean})`;
    if (a && a === te) return `이미 등록된 영문과 충돌: ${abbreviation} (${t.korean})`;
    if (a && tav.includes(a)) return `'${abbreviation}'은(는) 금지 변형입니다. 표준: ${t.english}(${t.korean})`;
    for (const v of av) {
      if (v === te || v === ta) return `금지 변형 '${v}'이(가) 등록 용어 ${t.korean}(${t.english})과(와) 충돌합니다`;
      if (tav.includes(v)) return `금지 변형 '${v}'은(는) 이미 ${t.korean}(${t.english})의 금지 목록에 있습니다`;
    }
  }
  return null;
}

export function addTerm(data, { korean, english, abbreviation = null, description = "", relatedElements = [], avoid = [] }) {
  if (!korean || !english) throw new Error("korean과 english는 필수입니다.");
  const conflict = findConflict(data.terms, { korean, english, abbreviation, avoid });
  if (conflict) throw new Error(conflict);
  data.terms.push({ korean, english, abbreviation, description, relatedElements, avoid });
  return data;
}
```

```js
export function updateTerm(data, korean, fields) {
  const term = findTerm(data, korean);
  if (!term) throw new Error(`등록되지 않은 용어: ${korean}`);
  const next = { ...term };
  for (const key of ["english", "abbreviation", "description", "relatedElements", "avoid"]) {
    if (fields[key] !== undefined) next[key] = fields[key];
  }
  const conflict = findConflict(data.terms.filter((t) => t.korean !== korean), next);
  if (conflict) throw new Error(conflict);
  Object.assign(term, next);
  return data;
}
```

`INITIAL_DATA` 교체:

```js
export const INITIAL_DATA = {
  terms: [
    { korean: "식별자", english: "identifier", abbreviation: "id", description: "데이터를 고유 식별하는 값. {엔티티}_id 형식", relatedElements: [], avoid: [] },
    { korean: "일시", english: "datetime", abbreviation: "at", description: "날짜와 시각. created_at 처럼 _at 접미사로 사용", relatedElements: [], avoid: [] },
    { korean: "이름", english: "name", abbreviation: null, description: "대상을 지칭하는 명칭", relatedElements: [], avoid: [] },
  ],
};
```

기존 addTerm 안의 중복 검사(한글/영문/축약어)는 findConflict로 대체되어 삭제된다.

- [ ] **Step 4: 테스트 통과 확인**

Run: `pnpm test`
Expected: PASS (전건 — 기존 충돌 테스트 3건은 findConflict의 동일 메시지로 계속 통과)

- [ ] **Step 5: 커밋**

```bash
git add templates/glossary.mjs tests/glossary.test.mjs
git commit -m "feat: avoid(금지 변형) 필드와 충돌 규칙 추가

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: 렌더 보강 — 셀 이스케이프·금지 요약·금지 컬럼·분할 안내

**Files:**
- Modify: `templates/glossary.mjs` (renderCore/renderTerms/build)
- Test: `tests/glossary.test.mjs`

**Interfaces:**
- Consumes: Task 1의 `avoidOf(term)`, terms 항목의 `avoid`
- Produces: `escapeCell(value): string` export, `renderCore`가 avoid 요약 블록(`금지 변형(대신 표준 사용):`) 포함, `renderTerms`가 6번째 컬럼 `금지` 포함, `build(dir): string | null` (180줄 초과 시 안내 문자열 반환, 아니면 null), `CORE_SPLIT_THRESHOLD = 180` export

- [ ] **Step 1: 실패하는 테스트 작성**

import에 `escapeCell, CORE_SPLIT_THRESHOLD` 추가 후:

```js
test("escapeCell: 파이프와 개행을 이스케이프한다", () => {
  assert.equal(escapeCell("현재가|주문시점가"), "현재가\\|주문시점가");
  assert.equal(escapeCell("첫줄\n둘째줄"), "첫줄<br>둘째줄");
  assert.equal(escapeCell(null), "");
});

test("renderTerms: 설명의 파이프가 표를 깨지 않는다", () => {
  const data = { terms: [{ korean: "가격", english: "price", abbreviation: null, description: "현재가|주문시점가 구분", relatedElements: [], avoid: [] }] };
  assert.ok(renderTerms(data).includes("현재가\\|주문시점가 구분"));
});

test("renderCore: avoid 요약 블록 — 있는 용어만, 없으면 블록 생략", () => {
  const withAvoid = { terms: [
    { korean: "회원", english: "member", abbreviation: null, avoid: ["customer", "user"] },
    { korean: "주문", english: "order", abbreviation: null, avoid: [] },
  ] };
  const out = renderCore(withAvoid);
  assert.ok(out.includes("금지 변형(대신 표준 사용):"));
  assert.ok(out.includes("- customer, user → member(회원)"));
  assert.ok(!out.includes("order(주문)"), "avoid 없는 용어는 요약에 없음");
  const without = renderCore({ terms: [{ korean: "주문", english: "order", abbreviation: null }] });
  assert.ok(!without.includes("금지 변형"));
});

test("renderTerms: 금지 컬럼을 포함한다", () => {
  const data = { terms: [{ korean: "회원", english: "member", abbreviation: null, description: "", relatedElements: [], avoid: ["customer"] }] };
  const out = renderTerms(data);
  assert.ok(out.includes("| 한글 | 영문 | 축약 | 설명 | 관련 요소 | 금지 |"));
  assert.ok(out.includes("| customer |"));
});

test("build: core.md가 임계선을 넘으면 분할 안내를 반환한다", () => {
  const dir = tmp();
  try {
    const many = Array.from({ length: CORE_SPLIT_THRESHOLD }, (_, i) => ({
      korean: `용어${String(i).padStart(3, "0")}`, english: `term${i}`, abbreviation: null, description: "", relatedElements: [], avoid: [],
    }));
    saveGlossary(dir, { terms: many });
    assert.match(build(dir), /core\.md가 \d+줄입니다/);
    saveGlossary(dir, { terms: many.slice(0, 3) });
    assert.equal(build(dir), null);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `pnpm test`
Expected: FAIL — `escapeCell` export 없음 등

- [ ] **Step 3: 구현**

`templates/glossary.mjs`에서 `renderCore`/`renderTerms`/`build`를 아래로 교체한다(`RULE_COMMENT`·`AUTOGEN`은 유지):

```js
export function escapeCell(value) {
  return String(value ?? "").replace(/\|/g, "\\|").replace(/\r?\n/g, "<br>");
}

export function renderCore(data) {
  const terms = sortedTerms(data);
  const rows = terms
    .map((t) => `| ${escapeCell(t.korean)} | ${escapeCell(t.english)} | ${escapeCell(t.abbreviation ?? "")} |`)
    .join("\n");
  const avoided = terms.filter((t) => avoidOf(t).length > 0);
  const avoidBlock = avoided.length
    ? `\n금지 변형(대신 표준 사용):\n${avoided.map((t) => `- ${avoidOf(t).join(", ")} → ${t.english}(${t.korean})`).join("\n")}\n`
    : "";
  return `${AUTOGEN}
${RULE_COMMENT}

| 한글 | 영문 | 축약 |
| --- | --- | --- |
${rows}
${avoidBlock}`;
}

export function renderTerms(data) {
  const rows = sortedTerms(data)
    .map(
      (t) =>
        `| ${escapeCell(t.korean)} | ${escapeCell(t.english)} | ${escapeCell(t.abbreviation ?? "")} | ${escapeCell(t.description ?? "")} | ${escapeCell((t.relatedElements ?? []).join(", "))} | ${escapeCell(avoidOf(t).join(", "))} |`
    )
    .join("\n");
  return `${AUTOGEN}

| 한글 | 영문 | 축약 | 설명 | 관련 요소 | 금지 |
| --- | --- | --- | --- | --- | --- |
${rows}
`;
}

export const CORE_SPLIT_THRESHOLD = 180;

export function build(dir) {
  const data = loadGlossary(dir);
  const core = renderCore(data);
  writeFileSync(join(dir, "core.md"), core);
  writeFileSync(join(dir, "terms.md"), renderTerms(data));
  const lines = core.split("\n").length;
  return lines > CORE_SPLIT_THRESHOLD
    ? `안내: core.md가 ${lines}줄입니다. 분류(category) 도입이나 파일 분할을 검토하세요.`
    : null;
}
```

주의: `renderCore`는 avoid가 없을 때 v0.2.0과 바이트 동일한 출력을 유지해야 한다(멱등성·기존 테스트 보존). 템플릿 리터럴 마지막이 `${rows}\n${avoidBlock}`이고 avoidBlock이 빈 문자열이면 기존과 동일하다.

- [ ] **Step 4: 테스트 통과 확인**

Run: `pnpm test`
Expected: PASS (기존 renderCore/renderTerms/build 멱등 테스트 포함 전건)

- [ ] **Step 5: 커밋**

```bash
git add templates/glossary.mjs tests/glossary.test.mjs
git commit -m "feat: 렌더 보강 — 셀 이스케이프·금지 요약·금지 컬럼·분할 안내

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: CLI 인자 — 불리언 플래그·`--avoid`·빌드 안내 출력

**Files:**
- Modify: `templates/glossary.mjs` (parseArgs, run의 add/update/remove/build/init 케이스)
- Test: `tests/glossary.test.mjs`

**Interfaces:**
- Consumes: Task 1 `addTerm`/`updateTerm`의 avoid, Task 2 `build(): string|null`
- Produces: `parseArgs`가 `--all`을 값 소비 없이 `true`로 파싱, run `add`/`update`가 `--avoid "a,b"` 수용, build를 호출하는 모든 run 케이스(build/add/update/remove)가 분할 안내를 출력에 덧붙임. (init 케이스의 안내 연결은 Task 6에서 scaffold 반환과 함께 정리)

- [ ] **Step 1: 실패하는 테스트 작성**

```js
test("parseArgs: --all은 값 없이 true", () => {
  const { positional, options } = parseArgs(["--all", "a.js", "b.js"]);
  assert.equal(options.all, true);
  assert.deepEqual(positional, ["a.js", "b.js"]);
});

test("run add --avoid → 저장·재빌드에 반영된다", () => {
  const dir = tmp();
  try {
    saveGlossary(dir, { terms: [] });
    run(["add", "회원", "member", "--avoid", "customer,user"], dir);
    assert.deepEqual(loadGlossary(dir).terms[0].avoid, ["customer", "user"]);
    assert.ok(loadFile(join(dir, "core.md")).includes("- customer, user → member(회원)"));
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("run update --avoid → 갱신된다", () => {
  const dir = tmp();
  try {
    saveGlossary(dir, { terms: [{ korean: "회원", english: "member", abbreviation: null, description: "", relatedElements: [], avoid: [] }] });
    run(["update", "회원", "--avoid", "customer"], dir);
    assert.deepEqual(loadGlossary(dir).terms[0].avoid, ["customer"]);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `pnpm test`
Expected: FAIL — `--all`이 `"a.js"`를 값으로 삼킴, add가 avoid를 무시

- [ ] **Step 3: 구현**

`parseArgs`를 아래로 교체:

```js
const BOOLEAN_OPTIONS = new Set(["all"]);

export function parseArgs(rest) {
  const positional = [];
  const options = {};
  for (let i = 0; i < rest.length; i++) {
    const a = rest[i];
    if (a.startsWith("--")) {
      const eq = a.indexOf("=");
      if (eq !== -1) options[a.slice(2, eq)] = a.slice(eq + 1);
      else if (BOOLEAN_OPTIONS.has(a.slice(2))) options[a.slice(2)] = true;
      else options[a.slice(2)] = rest[++i];
    } else {
      positional.push(a);
    }
  }
  return { positional, options };
}
```

`relatedFromOptions` 아래에 추가:

```js
function avoidFromOptions(options) {
  return options.avoid ? options.avoid.split(",").map((s) => s.trim()).filter(Boolean) : undefined;
}
```

run의 케이스를 교체(add에 avoid, 각 케이스에 build 안내 연결):

```js
    case "build": {
      const notice = build(dataDir);
      return ["빌드 완료: core.md, terms.md", notice].filter(Boolean).join("\n");
    }
    case "add": {
      const [korean, english, abbreviation] = positional;
      const data = loadGlossary(dataDir);
      addTerm(data, {
        korean, english, abbreviation: abbreviation ?? null,
        description: options.desc ?? "",
        relatedElements: relatedFromOptions(options) ?? [],
        avoid: avoidFromOptions(options) ?? [],
      });
      saveGlossary(dataDir, data);
      const notice = build(dataDir);
      return [`추가: ${korean} → ${english}`, notice].filter(Boolean).join("\n");
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
      const avoid = avoidFromOptions(options);
      if (avoid !== undefined) fields.avoid = avoid;
      updateTerm(data, korean, fields);
      saveGlossary(dataDir, data);
      const notice = build(dataDir);
      return [`수정: ${korean}`, notice].filter(Boolean).join("\n");
    }
    case "remove": {
      const [korean] = positional;
      const data = loadGlossary(dataDir);
      removeTerm(data, korean);
      saveGlossary(dataDir, data);
      const notice = build(dataDir);
      return [`삭제: ${korean}`, notice].filter(Boolean).join("\n");
    }
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `pnpm test`
Expected: PASS (기존 `run add → list`·`run remove` 테스트 포함)

- [ ] **Step 5: 커밋**

```bash
git add templates/glossary.mjs tests/glossary.test.mjs
git commit -m "feat: add/update --avoid 플래그와 불리언 옵션 파싱

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: lint 개편 — 스톱워드·위반/후보 분리·파일 위치·다단어 english

**Files:**
- Modify: `templates/glossary.mjs` (STOPWORDS 신설, lintFiles 교체, run lint 케이스)
- Test: `tests/glossary.test.mjs` (기존 lintFiles 테스트 1건 수정 + 신규)

**Interfaces:**
- Consumes: Task 1 `avoidOf`, 기존 `tokenize`
- Produces: `STOPWORDS: Set<string>` export, `lintFiles(data, files, {all=false}): {violations: Array<{token, count, files: string[], standard, korean}>, candidates: Array<{token, count, files: string[]}>}`, `formatFileList(files): string` export(최대 3개 + `외 N`), run lint 출력 형식:

```
[위반]
customer	member(회원)	8	src/A.java, src/B.java 외 1
[후보]
delivery	6	src/A.java
```

빈 결과는 `이상 없음` 한 줄. **검사 순서: 등록어 → avoid → 스톱워드 → 후보** (스펙 결정 #10).

- [ ] **Step 1: 실패하는 테스트 작성**

import에 `STOPWORDS, formatFileList` 추가. 기존 테스트 `"lintFiles: 미등록 토큰을 빈도와 함께 반환"`을 새 반환 형태로 수정:

```js
test("lintFiles: 미등록 토큰을 빈도와 함께 candidates로 반환", () => {
  const dir = tmp();
  try {
    const f = join(dir, "sample.js");
    wf(f, "const customer = 1; const customerName = 2; const memberId = 3;");
    const data = { terms: [
      { korean: "회원", english: "member", abbreviation: null },
      { korean: "식별자", english: "identifier", abbreviation: "id" },
      { korean: "이름", english: "name", abbreviation: null },
    ] };
    const { candidates } = lintFiles(data, [f]);
    const customer = candidates.find((r) => r.token === "customer");
    assert.ok(customer && customer.count === 2, "customer 2회 미등록");
    assert.deepEqual(customer.files, [f]);
    assert.ok(!candidates.find((r) => r.token === "member"), "member는 등록되어 제외");
    assert.ok(!candidates.find((r) => r.token === "const"), "const는 스톱워드로 제외");
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
```

신규 테스트:

```js
test("STOPWORDS: 언어·기술 어휘는 포함, 도메인 개연성 일반명사는 제외", () => {
  for (const w of ["const", "public", "import", "string", "repository", "service"]) {
    assert.ok(STOPWORDS.has(w), `${w}는 스톱워드여야 함`);
  }
  for (const w of ["user", "order", "member", "customer", "item", "price", "product", "address", "status", "state"]) {
    assert.ok(!STOPWORDS.has(w), `${w}는 스톱워드가 아니어야 함`);
  }
});

test("lintFiles: avoid 매치는 violations로 분리되고 스톱워드보다 우선한다", () => {
  const dir = tmp();
  try {
    const f = join(dir, "sample.js");
    // 'repository'는 스톱워드지만 avoid로 등록되면 위반으로 잡혀야 한다(결정 #10)
    wf(f, "class MemberStore {} class MemberRepository {} const customerId = 1;");
    const data = { terms: [
      { korean: "저장소", english: "store", abbreviation: null, avoid: ["repository"] },
      { korean: "회원", english: "member", abbreviation: null, avoid: ["customer"] },
      { korean: "식별자", english: "identifier", abbreviation: "id" },
    ] };
    const { violations, candidates } = lintFiles(data, [f]);
    const repo = violations.find((v) => v.token === "repository");
    assert.ok(repo && repo.standard === "store" && repo.korean === "저장소");
    const cust = violations.find((v) => v.token === "customer");
    assert.ok(cust && cust.standard === "member");
    assert.ok(!candidates.find((c) => c.token === "customer"), "위반은 후보에 중복되지 않음");
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("lintFiles: --all은 스톱워드 필터를 해제한다", () => {
  const dir = tmp();
  try {
    const f = join(dir, "sample.js");
    wf(f, "const value = 1;");
    const data = { terms: [] };
    assert.ok(!lintFiles(data, [f]).candidates.find((c) => c.token === "const"));
    assert.ok(lintFiles(data, [f], { all: true }).candidates.find((c) => c.token === "const"));
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("lintFiles: 다단어 english는 구성 단어로 매칭된다", () => {
  const dir = tmp();
  try {
    const f = join(dir, "sample.js");
    wf(f, "const stockKeepingUnit = 1;");
    const data = { terms: [{ korean: "재고관리단위", english: "Stock Keeping Unit", abbreviation: "SKU" }] };
    assert.equal(lintFiles(data, [f]).candidates.length, 0);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("formatFileList: 3개 초과는 '외 N'으로 줄인다", () => {
  assert.equal(formatFileList(["a", "b"]), "a, b");
  assert.equal(formatFileList(["a", "b", "c", "d", "e"]), "a, b, c 외 2");
});

test("run lint: 위반/후보 섹션과 '이상 없음'", () => {
  const dir = tmp();
  try {
    // 식별자(id)를 등록해 두어 clean.js의 memberId가 전부 등록어로 매칭되게 한다
    saveGlossary(dir, { terms: [
      { korean: "회원", english: "member", abbreviation: null, description: "", relatedElements: [], avoid: ["customer"] },
      { korean: "식별자", english: "identifier", abbreviation: "id", description: "", relatedElements: [], avoid: [] },
    ] });
    build(dir);
    const f = join(dir, "sample.js");
    wf(f, "const customerId = 1; const deliveryFee = 2;");
    const out = run(["lint", f], dir);
    assert.ok(out.includes("[위반]"));
    assert.ok(out.includes("customer\tmember(회원)"));
    assert.ok(out.includes("[후보]"));
    assert.ok(out.includes("delivery"));
    const clean = join(dir, "clean.js");
    wf(clean, "const memberId = 1;");
    assert.equal(run(["lint", clean], dir), "이상 없음");
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
```

참고: `sample.js`의 토큰 중 `const`는 스톱워드, `customer`는 위반, `id`는 등록어라 `[후보]`에는 `delivery`·`fee`만 남는다.

- [ ] **Step 2: 테스트 실패 확인**

Run: `pnpm test`
Expected: FAIL — `STOPWORDS` export 없음, lintFiles 반환 형태 불일치

- [ ] **Step 3: 구현**

`tokenize` 아래에 STOPWORDS를 추가하고 `lintFiles`를 교체한다:

```js
// 결정 #11: 언어 키워드·표준 타입·기술 계층 어휘만 포함한다.
// 도메인 개연성이 있는 일반명사(user, order, item, price, status, state 등)는 넣지 않는다.
export const STOPWORDS = new Set([
  // 언어 키워드 (JS/TS/Java/Kotlin/Python/Go/SQL)
  "abstract", "and", "as", "assert", "async", "await", "boolean", "break", "byte", "case", "cascade",
  "catch", "chan", "char", "class", "const", "constraint", "continue", "def", "default", "defer",
  "delete", "do", "double", "elif", "else", "enum", "except", "exists", "export", "extends", "false",
  "final", "finally", "float", "for", "foreign", "from", "fun", "func", "function", "global", "go",
  "having", "if", "implements", "import", "in", "init", "inner", "insert", "instanceof", "int",
  "interface", "internal", "is", "join", "key", "lambda", "left", "let", "like", "limit", "long",
  "module", "namespace", "new", "nil", "none", "nonlocal", "not", "null", "object", "of", "offset",
  "open", "or", "outer", "override", "package", "pass", "primary", "private", "protected", "public",
  "raise", "range", "readonly", "references", "require", "return", "right", "sealed", "select",
  "self", "short", "static", "struct", "super", "switch", "table", "this", "throw", "throws", "true",
  "try", "type", "typeof", "union", "unique", "val", "var", "void", "when", "where", "while", "with", "yield",
  // 표준 타입·라이브러리 어휘
  "array", "bigdecimal", "bigint", "biginteger", "buffer", "bytes", "calendar", "collection",
  "collections", "column", "com", "console", "date", "datetime", "dict", "duration", "error",
  "errors", "example", "exception", "file", "files", "fs", "http", "https", "index", "instant",
  "integer", "io", "iterator", "java", "javax", "json", "kotlin", "list", "local", "locale", "map",
  "math", "net", "node", "number", "optional", "os", "path", "process", "promise", "regex",
  "runtime", "set", "sql", "stream", "string", "sys", "time", "timestamp", "tuple", "uri", "url",
  "util", "utils", "uuid", "xml", "zone", "zoned",
  // 범용 프로그래밍 어휘
  "add", "app", "application", "apply", "arg", "args", "bar", "baz", "bin", "build", "builder",
  "by", "call", "check", "config", "configuration", "context", "convert", "count", "create",
  "current", "data", "dist", "doc", "docs", "empty", "execute", "fetch", "find", "first", "foo",
  "format", "get", "handle", "handler", "impl", "info", "invoke", "last", "length", "lib", "load",
  "main", "make", "max", "meta", "min", "mock", "next", "now", "old", "on", "opts", "options",
  "param", "params", "parse", "prev", "read", "remove", "request", "response", "result", "results",
  "run", "save", "size", "spec", "src", "start", "stop", "stub", "sum", "temp", "test", "tests",
  "tmp", "to", "token", "update", "validate", "value", "values", "verify", "view", "write",
  // 기술 계층 어휘 (결정 #11)
  "adapter", "api", "cli", "controller", "dao", "db", "dto", "entity", "facade", "factory", "grpc",
  "manager", "model", "orm", "provider", "proxy", "repository", "rest", "sdk", "service",
  "singleton", "ui", "vo",
]);

export function lintFiles(data, files, { all = false } = {}) {
  const known = new Set();
  const avoidMap = new Map();
  for (const t of data.terms) {
    const e = t.english.toLowerCase();
    known.add(e);
    if (e.includes(" ")) for (const w of e.split(/\s+/)) known.add(w);
    if (t.abbreviation) known.add(t.abbreviation.toLowerCase());
    for (const v of avoidOf(t)) avoidMap.set(v.toLowerCase(), t);
  }
  const hits = new Map();
  for (const file of files) {
    if (!existsSync(file) || statSync(file).isDirectory()) continue;
    const ids = readFileSync(file, "utf8").match(/[A-Za-z_][A-Za-z0-9_]*/g) || [];
    for (const id of ids) {
      for (const tok of tokenize(id)) {
        if (tok.length < 2 || known.has(tok)) continue;
        if (!avoidMap.has(tok) && !all && STOPWORDS.has(tok)) continue;
        const hit = hits.get(tok) ?? { count: 0, files: new Set() };
        hit.count += 1;
        hit.files.add(file);
        hits.set(tok, hit);
      }
    }
  }
  const entries = [...hits.entries()]
    .map(([token, hit]) => ({ token, count: hit.count, files: [...hit.files] }))
    .sort((a, b) => b.count - a.count);
  return {
    violations: entries
      .filter((entry) => avoidMap.has(entry.token))
      .map((entry) => {
        const standard = avoidMap.get(entry.token);
        return { ...entry, standard: standard.english, korean: standard.korean };
      }),
    candidates: entries.filter((entry) => !avoidMap.has(entry.token)),
  };
}

export function formatFileList(files) {
  const shown = files.slice(0, 3).join(", ");
  return files.length > 3 ? `${shown} 외 ${files.length - 3}` : shown;
}
```

run의 lint 케이스 교체:

```js
    case "lint": {
      const data = loadGlossary(dataDir);
      const { violations, candidates } = lintFiles(data, positional, { all: options.all === true });
      const lines = [];
      if (violations.length) {
        lines.push("[위반]");
        for (const v of violations) lines.push(`${v.token}\t${v.standard}(${v.korean})\t${v.count}\t${formatFileList(v.files)}`);
      }
      if (candidates.length) {
        lines.push("[후보]");
        for (const c of candidates) lines.push(`${c.token}\t${c.count}\t${formatFileList(c.files)}`);
      }
      return lines.length ? lines.join("\n") : "이상 없음";
    }
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `pnpm test`
Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add templates/glossary.mjs tests/glossary.test.mjs
git commit -m "feat: lint 개편 — 스톱워드·위반/후보 분리·파일 위치

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: lookup 상세·stale 경고·친절한 에러

**Files:**
- Modify: `templates/glossary.mjs` (loadGlossary, formatTermDetail/isStale/warnIfStale 신설, run의 list/lookup/lint 케이스)
- Test: `tests/glossary.test.mjs`

**Interfaces:**
- Consumes: Task 2 `renderCore`/`renderTerms`
- Produces: `formatTermDetail(term): string`, `isStale(dir, data): boolean` export. run의 `list`/`lookup`/`lint`가 stale 시 stderr 경고 1줄(stdout 불변). `loadGlossary`는 ENOENT 시 `용어사전이 없습니다...` 에러. `lookup` 무일치 시 `일치하는 용어 없음`.

- [ ] **Step 1: 실패하는 테스트 작성**

import에 `formatTermDetail, isStale` 추가:

```js
test("formatTermDetail: 전 필드 출력, 빈 필드 줄 생략", () => {
  const full = formatTermDetail({ korean: "회원", english: "member", abbreviation: "mbr", description: "가입 사용자", relatedElements: ["member_id"], avoid: ["customer"] });
  assert.equal(full, "회원 → member (축약: mbr)\n  설명: 가입 사용자\n  관련: member_id\n  금지: customer");
  const minimal = formatTermDetail({ korean: "주문", english: "order", abbreviation: null, description: "", relatedElements: [], avoid: [] });
  assert.equal(minimal, "주문 → order");
});

test("run lookup: 상세를 출력하고 무일치 시 안내한다", () => {
  const dir = tmp();
  try {
    saveGlossary(dir, { terms: [{ korean: "청구", english: "claim", abbreviation: null, description: "요금 청구", relatedElements: [], avoid: [] }] });
    build(dir);
    const out = run(["lookup", "청구"], dir);
    assert.ok(out.includes("청구 → claim"));
    assert.ok(out.includes("설명: 요금 청구"));
    assert.equal(run(["lookup", "없는말"], dir), "일치하는 용어 없음");
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("isStale: 빌드 직후 false, json 변경 후 true, 생성물 없으면 true", () => {
  const dir = tmp();
  try {
    saveGlossary(dir, { terms: [{ korean: "회원", english: "member", abbreviation: null, description: "", relatedElements: [], avoid: [] }] });
    assert.equal(isStale(dir, loadGlossary(dir)), true, "생성물 없음 = stale");
    build(dir);
    assert.equal(isStale(dir, loadGlossary(dir)), false);
    const data = loadGlossary(dir);
    data.terms.push({ korean: "주문", english: "order", abbreviation: null, description: "", relatedElements: [], avoid: [] });
    saveGlossary(dir, data);
    assert.equal(isStale(dir, loadGlossary(dir)), true);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("loadGlossary: glossary.json이 없으면 안내 에러", () => {
  const dir = tmp();
  try {
    assert.throws(() => loadGlossary(dir), /용어사전이 없습니다/);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `pnpm test`
Expected: FAIL — export 없음, ENOENT raw 에러

- [ ] **Step 3: 구현**

`loadGlossary` 교체:

```js
export function loadGlossary(dir) {
  try {
    return JSON.parse(readFileSync(join(dir, "glossary.json"), "utf8"));
  } catch (err) {
    if (err.code === "ENOENT") {
      throw new Error("용어사전이 없습니다. /superglossary:init(또는 glossary.mjs init)을 먼저 실행하세요.");
    }
    throw err;
  }
}
```

`lookup` 함수 아래에 추가:

```js
export function formatTermDetail(t) {
  const abbr = t.abbreviation ? ` (축약: ${t.abbreviation})` : "";
  const lines = [`${t.korean} → ${t.english}${abbr}`];
  if (t.description) lines.push(`  설명: ${t.description}`);
  if ((t.relatedElements ?? []).length) lines.push(`  관련: ${t.relatedElements.join(", ")}`);
  if (avoidOf(t).length) lines.push(`  금지: ${avoidOf(t).join(", ")}`);
  return lines.join("\n");
}
```

`build` 아래에 추가:

```js
export function isStale(dir, data) {
  const targets = [["core.md", renderCore], ["terms.md", renderTerms]];
  for (const [name, render] of targets) {
    const p = join(dir, name);
    if (!existsSync(p) || readFileSync(p, "utf8") !== render(data)) return true;
  }
  return false;
}

function warnIfStale(dir, data) {
  if (isStale(dir, data)) {
    console.error("⚠ core.md/terms.md가 glossary.json과 다릅니다. 'glossary.mjs build'를 실행하세요.");
  }
}
```

run의 `list`/`lookup` 케이스 교체 + `lint` 케이스의 `const data = loadGlossary(dataDir);` 다음 줄에 `warnIfStale(dataDir, data);` 삽입:

```js
    case "list": {
      const data = loadGlossary(dataDir);
      warnIfStale(dataDir, data);
      return listTerms(data).map((t) => `${t.korean}\t${t.english}\t${t.abbreviation ?? ""}`).join("\n");
    }
    case "lookup": {
      const data = loadGlossary(dataDir);
      warnIfStale(dataDir, data);
      const found = lookup(data, positional[0] ?? "");
      return found.length ? found.map(formatTermDetail).join("\n\n") : "일치하는 용어 없음";
    }
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `pnpm test`
Expected: PASS (stale 상태 테스트에서 stderr 경고가 출력될 수 있으나 실패 아님)

- [ ] **Step 5: 커밋**

```bash
git add templates/glossary.mjs tests/glossary.test.mjs
git commit -m "feat: lookup 상세 출력과 stale 경고·친절한 에러

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: version/help·init 위치 가드·gitignore 경고·CLAUDE_BLOCK 갱신

**Files:**
- Modify: `templates/glossary.mjs` (VERSION/USAGE 신설, scaffold/CLAUDE_BLOCK/메인 블록 교체, run의 init/version/help/default 케이스)
- Test: `tests/glossary.test.mjs`

**Interfaces:**
- Consumes: Task 2 `build`, Task 1 데이터 계층
- Produces: `VERSION = "0.2.0"` export(Task 7·12가 사용), `USAGE: string` export, `assertDataDirPlacement(dataDir): void`(부적합 시 throw), `gitIgnoreWarnings(dataDir): string[]`, `scaffold(dataDir): string[]`(경고 배열 반환), run `version`/`help` 케이스, 메인 블록 dataDir가 항상 SELF_DIR

- [ ] **Step 1: 실패하는 테스트 작성**

테스트 파일 상단에 `import { execFileSync } from "node:child_process";` 추가, import에 `VERSION, assertDataDirPlacement` 추가:

```js
test("VERSION: plugin.json version과 일치한다", () => {
  const manifest = JSON.parse(readFileSync(new URL("../.claude-plugin/plugin.json", import.meta.url), "utf8"));
  assert.equal(VERSION, manifest.version);
});

test("run version/help", () => {
  assert.match(run(["version"], "/tmp"), /^superglossary CLI v\d+\.\d+\.\d+/);
  assert.ok(run(["help"], "/tmp").includes("사용법"));
  assert.throws(() => run(["nope"], "/tmp"), /알 수 없는 커맨드[\s\S]*사용법/);
});

test("assertDataDirPlacement: .claude/superglossary만 허용", () => {
  assert.throws(() => assertDataDirPlacement("/tmp/plugin/templates"), /복사한 뒤 실행하세요/);
  assert.doesNotThrow(() => assertDataDirPlacement(join("/tmp/proj", ".claude", "superglossary")));
});

test("scaffold: git 레포가 아니면 gitignore 경고 없음", () => {
  const root = tmp();
  try {
    const warnings = scaffold(join(root, ".claude", "superglossary"));
    assert.deepEqual(warnings, []);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("scaffold: .gitignore가 .claude/를 무시하면 경고를 반환한다", () => {
  try {
    execFileSync("git", ["--version"], { stdio: "ignore" });
  } catch {
    return; // git 없는 환경은 건너뜀
  }
  const root = tmp();
  try {
    execFileSync("git", ["init", "-q"], { cwd: root });
    wf(join(root, ".gitignore"), ".claude/\n");
    const warnings = scaffold(join(root, ".claude", "superglossary"));
    assert.ok(warnings.some((w) => w.includes("무시되어")), "무시 경고 포함");
    assert.ok(warnings.some((w) => w.includes("!.claude/superglossary/")), "해법 안내 포함");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("scaffold: 새 CLAUDE_BLOCK은 add 스킬·lookup 안내를 포함한다", () => {
  const root = tmp();
  try {
    scaffold(join(root, ".claude", "superglossary"));
    const claude = loadFile(join(root, ".claude", "CLAUDE.md"));
    assert.ok(claude.includes("add 스킬"));
    assert.ok(claude.includes("lookup"));
    assert.ok(claude.includes("@superglossary/core.md"));
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
```

기존 `run: 알 수 없는 커맨드는 throw` 테스트는 위 `run version/help` 테스트가 포함하므로 **삭제**한다(중복).

- [ ] **Step 2: 테스트 실패 확인**

Run: `pnpm test`
Expected: FAIL — `VERSION` 등 export 없음

- [ ] **Step 3: 구현**

파일 상단 import 교체(basename·execFileSync 추가):

```js
import { readFileSync, writeFileSync, existsSync, statSync, mkdirSync } from "node:fs";
import { join, dirname, basename } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

export const VERSION = "0.2.0";
```

`CLAUDE_BLOCK`을 스펙 §5.6 전문으로 교체:

```js
export const CLAUDE_BLOCK = `## 용어 사전
@superglossary/core.md

- 클래스/변수/함수/컬럼/테이블 등 모든 네이밍은 위 표의 영문명만 사용한다. 축약어는 표에 등록된 것만 쓰고, 금지 변형은 표준으로 대체한다.
- 표에 없는 단일어가 필요하면 임의로 짓지 말고 superglossary의 add 스킬로 등록한다(복합어는 단일어로 분해). 플러그인이 없으면 \`node .claude/superglossary/glossary.mjs add <korean> <english> [abbreviation]\`을 직접 실행한다. 변경은 같은 diff에 포함한다.
- 용어의 의미가 모호하면 \`node .claude/superglossary/glossary.mjs lookup <질의>\` 또는 \`.claude/superglossary/terms.md\`에서 상세를 확인한다.
- 수정·삭제는 \`glossary.mjs update/remove\`를 쓴다(자동 재빌드). core.md·terms.md는 생성물이므로 직접 편집하지 않는다.
- 기존 모듈 수정 시 그 모듈의 기존 컨벤션을 우선하고, 신규 코드에는 사전을 우선한다. 임의 리네이밍은 하지 않는다.
- 워크플로: 작업 시작 전 핵심 개념 정렬 → 작업 중 사전에 없는 용어만 추가 → 완료 후 check 스킬로 검토.
`;
```

`scaffold`를 아래로 교체:

```js
export function assertDataDirPlacement(dataDir) {
  if (basename(dataDir) !== "superglossary" || basename(dirname(dataDir)) !== ".claude") {
    throw new Error("glossary.mjs를 <프로젝트>/.claude/superglossary/로 복사한 뒤 실행하세요.");
  }
}

export function gitIgnoreWarnings(dataDir) {
  const root = dirname(dirname(dataDir));
  const warnings = [];
  for (const rel of [join(".claude", "superglossary", "glossary.json"), join(".claude", "CLAUDE.md")]) {
    try {
      execFileSync("git", ["check-ignore", "-q", rel], { cwd: root, stdio: "ignore" });
      warnings.push(`⚠ ${rel} 이(가) .gitignore에 의해 무시되어 팀과 공유되지 않습니다.`);
    } catch {
      // 무시 대상 아님(exit 1) 또는 git 부재·비레포 — 경고 없음
    }
  }
  if (warnings.length) {
    warnings.push("  .gitignore를 다음과 같이 조정하세요:", "    .claude/*", "    !.claude/CLAUDE.md", "    !.claude/superglossary/");
  }
  return warnings;
}

export function scaffold(dataDir) {
  assertDataDirPlacement(dataDir);
  mkdirSync(dataDir, { recursive: true });
  if (!existsSync(join(dataDir, "glossary.json"))) saveGlossary(dataDir, INITIAL_DATA);
  build(dataDir);
  const claudeMd = join(dataDir, "..", "CLAUDE.md");
  const existing = existsSync(claudeMd) ? readFileSync(claudeMd, "utf8") : "";
  if (!existing.includes("## 용어 사전")) {
    const next = existing.trimEnd();
    writeFileSync(claudeMd, (next ? next + "\n\n" : "") + CLAUDE_BLOCK);
  }
  return gitIgnoreWarnings(dataDir);
}
```

`USAGE`를 `run` 위에 추가하고 run의 `init`/`version`/`help`/`default` 케이스를 교체:

```js
export const USAGE = `사용법: node glossary.mjs <subcommand>
  init                                          초기화(.claude/superglossary/에 복사 후 실행)
  build                                         glossary.json → core.md·terms.md 재생성
  add <korean> <english> [abbreviation] [--desc "설명"] [--related "a,b"] [--avoid "a,b"]
  update <korean> [--english E] [--abbreviation A] [--desc D] [--related "a,b"] [--avoid "a,b"]
  remove <korean>
  list                                          전체 용어(간결)
  lookup <질의>                                  용어 상세 검색
  lint [--all] <files...>                       코드 대조([위반]/[후보], --all=스톱워드 해제)
  version | help`;
```

```js
    case "init": {
      const warnings = scaffold(dataDir);
      return [`초기화 완료: ${dataDir}`, ...warnings].join("\n");
    }
```

```js
    case "version":
      return `superglossary CLI v${VERSION}`;
    case "help":
      return USAGE;
    default:
      throw new Error(`알 수 없는 커맨드: ${cmd}\n${USAGE}`);
```

메인 블록을 교체(SELF_DIR 통일 — init의 cwd 특례 제거):

```js
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const SELF_DIR = dirname(fileURLToPath(import.meta.url));
  try {
    const out = run(process.argv.slice(2), SELF_DIR);
    if (out) console.log(out);
  } catch (err) {
    console.error(`✗ ${err.message}`);
    process.exitCode = 1;
  }
}
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `pnpm test`
Expected: PASS — 기존 scaffold 2개 테스트(초기 데이터·중복 방지)는 반환값을 무시하므로 그대로 통과

- [ ] **Step 5: 커밋**

```bash
git add templates/glossary.mjs tests/glossary.test.mjs
git commit -m "feat: version/help·init 위치 가드·gitignore 경고·CLAUDE 블록 갱신

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 7: bump 스크립트가 CLI VERSION을 동기화

**Files:**
- Modify: `scripts/bump-version.mjs`

**Interfaces:**
- Consumes: Task 6의 `export const VERSION = "..."` 상수(정규식 `^export const VERSION = "([^"]+)";$`로 탐지)
- Produces: `pnpm bump <v>`가 plugin.json과 templates/glossary.mjs를 함께 갱신, `pnpm version:check`가 둘의 일치까지 검증

- [ ] **Step 1: 구현** (이 태스크는 스크립트라 자동 테스트 대신 실행 검증 — Task 6의 `VERSION: plugin.json version과 일치한다` 테스트가 상시 회귀 방어)

`scripts/bump-version.mjs`에서 `PLUGIN_MANIFEST` 상수 아래에 추가:

```js
const CLI_TEMPLATE = join(ROOT, "templates", "glossary.mjs");
const VERSION_CONST = /^export const VERSION = "([^"]+)";$/m;

async function readCliVersion() {
  const source = await readFile(CLI_TEMPLATE, "utf8");
  const matched = source.match(VERSION_CONST);
  return { source, version: matched ? matched[1] : null };
}
```

`check()`를 교체:

```js
async function check() {
  const { version } = await readManifest();
  if (!version || !SEMVER.test(version)) {
    fail(`plugin.json version이 유효한 SemVer가 아닙니다: ${JSON.stringify(version)}`);
  }
  const cli = await readCliVersion();
  if (cli.version === null) {
    fail("templates/glossary.mjs에서 VERSION 상수를 찾지 못했습니다.");
  }
  if (cli.version !== version) {
    fail(`버전 불일치: plugin.json=${version}, glossary.mjs=${cli.version} — pnpm bump로 동기화하세요.`);
  }
  console.log(`✓ 현재 버전: ${version} (plugin.json = glossary.mjs)`);
}
```

`bump()`의 `await writeFile(PLUGIN_MANIFEST, ...)` 다음에 추가:

```js
  const cli = await readCliVersion();
  if (cli.version === null) {
    fail("templates/glossary.mjs에서 VERSION 상수를 찾지 못했습니다.");
  }
  await writeFile(CLI_TEMPLATE, cli.source.replace(VERSION_CONST, `export const VERSION = "${version}";`));
```

그리고 bump의 성공 로그 첫 줄을 `console.log(\`✓ 버전 갱신: ${previous} → ${version} (plugin.json + glossary.mjs)\`);`로 바꾼다.

- [ ] **Step 2: 실행 검증**

Run: `pnpm version:check`
Expected: `✓ 현재 버전: 0.2.0 (plugin.json = glossary.mjs)`

Run: `pnpm bump 0.2.0 && pnpm version:check && git diff --stat`
Expected: 갱신 로그 후 check 통과, diff는 비어 있거나 동일 내용(0.2.0 → 0.2.0 멱등)

Run: `pnpm test`
Expected: PASS

- [ ] **Step 3: 커밋**

```bash
git add scripts/bump-version.mjs
git commit -m "feat: bump 스크립트가 CLI VERSION 상수를 동기화

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 8: init 커맨드 → 스킬 전환

**Files:**
- Create: `skills/init/SKILL.md`
- Delete: `commands/init.md`

**Interfaces:**
- Consumes: Task 6 scaffold의 gitignore 경고 출력, Task 3 `--avoid` 플래그
- Produces: `/superglossary:init` 스킬(사용자 전용). 이후 태스크가 참조하는 이름: `glossary-scanner`(기존 에이전트, 변경 없음)

- [ ] **Step 1: `skills/init/SKILL.md` 생성** (아래 전문 그대로)

```markdown
---
name: init
description: 프로젝트 용어사전을 초기화하고 .claude/CLAUDE.md에 연결합니다. 재실행하면 CLI 복사본을 최신으로 갱신합니다(데이터 보존).
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Task, AskUserQuestion
---

# 용어사전 초기화

다음을 순서대로 수행한다.

1. `.claude/superglossary/` 디렉토리를 만들고 `${CLAUDE_PLUGIN_ROOT}/templates/glossary.mjs`를 `.claude/superglossary/glossary.mjs`로 복사한다. **기존 복사본이 있어도 덮어쓴다** — 재실행이 곧 CLI 업그레이드이며, `glossary.json`과 기존 CLAUDE.md 블록은 보존된다.
2. 프로젝트 루트에서 `node .claude/superglossary/glossary.mjs init`을 실행한다 → 초기 `glossary.json`(없을 때) · `core.md` · `terms.md` 생성 + `.claude/CLAUDE.md`에 `## 용어 사전` 블록 삽입(이미 있으면 건너뜀).
3. 출력에 **`.gitignore` 경고**가 있으면 그대로 사용자에게 전달하고, 안내된 패턴으로 `.gitignore`를 수정할지 확인한다(동의 시 수정). 용어사전은 팀과 공유되어야 가치가 있다.
4. 생성·연결 결과(및 CLI 버전: `node .claude/superglossary/glossary.mjs version`)를 사용자에게 보고한다.

## 기존 코드베이스(brownfield)라면

코드가 이미 존재하면, **용어 후보·혼용 스캔 여부를 먼저 사용자에게 묻는다**(AskUserQuestion).

- 동의하면 `glossary-scanner` 서브에이전트를 Task로 dispatch한다.
- scanner가 반환한 **(a) 단일어 후보**와 **(b) 혼용 리포트(영문 변형·빈도)**를 사용자에게 제시한다.
- 사용자가 후보를 선별하고, 혼용 건은 **표준 1개**를 고르면 — 탈락 변형을 금지 목록에 보존하며 등록한다:
  `node .claude/superglossary/glossary.mjs add <korean> <english> [abbreviation] [--desc "..."] --avoid "탈락변형1,탈락변형2"`
- **자동 리네이밍은 하지 않는다.** 비표준 사용처는 이후 check 스킬의 lint가 `[위반]`으로 보고한다.

분류(category)는 다루지 않는다.
```

- [ ] **Step 2: 기존 커맨드 삭제**

```bash
git rm commands/init.md
```

- [ ] **Step 3: 검증**

Run: `claude plugin validate .`
Expected: 검증 통과(에러 없음)

- [ ] **Step 4: 커밋**

```bash
git add skills/init/SKILL.md
git commit -m "refactor: init 커맨드를 스킬로 전환(사용자 전용·업그레이드 경로 명시)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 9: add 커맨드 → 스킬 전환 (모델 자율 호출 허용)

**Files:**
- Create: `skills/add/SKILL.md`
- Delete: `commands/add.md`

**Interfaces:**
- Consumes: Task 3 `--avoid`, Task 1 충돌 메시지(표준 안내 포함)
- Produces: `/superglossary:add` 스킬 — 사용자 호출 + Claude 자율 호출(용어 등록의 단일 진입점, CLAUDE_BLOCK이 "add 스킬"로 지칭)

- [ ] **Step 1: `skills/add/SKILL.md` 생성** (아래 전문 그대로)

```markdown
---
name: add
description: 용어사전에 새 용어를 등록한다. 사용자가 용어 추가를 요청할 때("용어 추가", "사전에 등록")와, 작업 중 사전(core.md)에 없는 개념의 영문 네이밍이 필요해졌을 때 사용한다. 복합어는 단일어로 분해해 등록한다.
argument-hint: <한글> <영문> [축약어] [--desc "설명"]
allowed-tools: Bash, Read
---

# 용어 등록

입력: `$ARGUMENTS` (비어 있으면 대화·작업 맥락에서 등록할 개념을 파악한다)

1. **복합어 검사**: 등록 대상이 복합어(예: "회원번호")면 단일어로 분해한다. 등록된 단일어 조합으로 표현 가능하면(예: 회원=member + 식별자=id → `member_id`) 그 방법을 쓰고, 미등록 단일어만 등록 대상으로 삼는다.
2. **등록**: 단일어마다 실행한다 —
   `node .claude/superglossary/glossary.mjs add <korean> <english> [abbreviation] [--desc "설명"] [--related "a,b"] [--avoid "금지변형,..."]`
   스크립트가 중복·충돌(한글/영문/축약어/금지 변형)을 검사하고 통과 시 추가 + 재빌드한다. 같은 개념에 쓰이면 안 되는 영문 변형을 알고 있다면 `--avoid`로 함께 보존한다.
3. **충돌 시**: 스크립트가 기존 항목·표준을 출력하며 비정상 종료하면, 그 내용을 설명하고 해당 항목 등록을 중단한다(금지 변형 충돌이면 안내된 표준을 사용).
4. **자율 등록이었다면**: 작업을 계속하기 전에 "용어 등록: 회원 → member" 형식 한 줄로 사용자에게 알린다.

> 분류(category)는 다루지 않는다. 수정·삭제는 `glossary.mjs update`/`remove`를 쓴다.
```

- [ ] **Step 2: 기존 커맨드 삭제**

```bash
git rm commands/add.md
```

- [ ] **Step 3: 검증**

Run: `claude plugin validate .`
Expected: 검증 통과. 추가로 `ls commands 2>&1` → 디렉토리 없음(또는 비어 있음) 확인

- [ ] **Step 4: 커밋**

```bash
git add skills/add/SKILL.md
git commit -m "refactor: add 커맨드를 스킬로 전환(자율 등록 단일 진입점)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 10: check 스킬 개명·하이브리드 + check-analyzer 갱신

**Files:**
- Create: `skills/check/SKILL.md` (기존 `skills/glossary-check/SKILL.md` 대체)
- Delete: `skills/glossary-check/SKILL.md`
- Modify: `agents/check-analyzer.md`

**Interfaces:**
- Consumes: Task 4 lint 출력 형식(`[위반]`/`[후보]`, 토큰·빈도·파일), Task 6 `list`
- Produces: `/superglossary:check` 스킬(하이브리드: 후보 ≤10 인라인, >10 dispatch). check-analyzer 입력 계약: `[후보]` 섹션(파일 위치 포함) + `list` 결과

- [ ] **Step 1: 스킬 이동·재작성**

```bash
git mv skills/glossary-check skills/check
```

`skills/check/SKILL.md`를 아래 전문으로 교체:

```markdown
---
name: check
description: 작업 완료 후나 커밋 전에 코드 네이밍을 프로젝트 용어사전과 대조해 위반·누락 용어를 검토할 때 사용한다. "용어 검사", "사전이랑 맞는지 확인", "네이밍 점검" 같은 요청에 트리거.
---

# 용어사전 검토

1. **사전 확인**: `.claude/superglossary/`가 없으면 `/superglossary:init` 실행을 제안하고 종료한다.
2. **대상 결정**: 인자가 없으면 `git diff --name-only`(staged+unstaged 합집합) + `git ls-files --others --exclude-standard`(신규 untracked)의 파일, 경로가 주어지면 그 범위.
3. **후보 추출(결정론)**: `node .claude/superglossary/glossary.mjs lint <files...>` 실행. 출력은 두 섹션 — `[위반]`(금지 변형 사용: `토큰	표준(한글)	빈도	파일`)과 `[후보]`(미등록 토큰: `토큰	빈도	파일`).
4. **위반 처리**: `[위반]`은 사전이 결정론적으로 확정한 결과다. 그대로 보고 표에 올린다.
5. **후보 처리(하이브리드)**:
   - `[후보]`가 **10개 이하**면 이 세션에서 직접 의미 확정한다. 판단 기준: ① 사전 등록 개념을 다른 영문으로 쓴 동의어(빈도·문맥 확인) ② 미등록 축약어 ③ 반복 등장하는 미등록 단일어는 추가 후보 ④ 일반 영어·라이브러리 식별자는 노이즈로 제외 ⑤ 기존 모듈 컨벤션 존중.
   - **10개 초과**면 `[후보]` 목록(파일 위치 포함)과 `node .claude/superglossary/glossary.mjs list` 결과를 `check-analyzer` 서브에이전트에 넘겨(Task) 확정을 받는다.
6. **보고**: 위반(금지 변형 + 의미 위반)과 추가 후보(add 스킬로 등록할 대상)를 표로 보고한다. **자동 수정은 하지 않는다** — 적용은 사용자 판단.

작업 완료 후 커밋 전에 실행하기를 권장한다.
```

- [ ] **Step 2: `agents/check-analyzer.md` 교체** (아래 전문 그대로)

```markdown
---
name: check-analyzer
description: 코드 식별자를 용어사전과 대조해 위반과 추가 후보를 의미 기반으로 확정하는 분석 에이전트
model: sonnet
tools: Read, Grep, Glob, Bash
---

당신은 프로젝트 용어사전 준수를 검토하는 분석가다. 입력으로 lint의 `[후보]` 섹션(미매칭 토큰+빈도+등장 파일)과 사전(`list` 결과)을 받는다. **금지 변형(`[위반]`)은 lint가 이미 확정했으므로 입력에 없다** — 다시 판단하지 않는다. 필요하면 `node .claude/superglossary/glossary.mjs lookup <q>`로 사전 상세를 조회한다.

## 판단

- **코드→사전 위반**
  - 사전에 등록된 개념을 다른 영문으로 사용(예: 사전 `member` ↔ 코드 `client`).
  - 사전에 없는 축약어 사용(예: `reg_dt`의 `reg`).
- **사전→코드 추가 후보**
  - 코드에 반복 등장하지만 미등록인 단일어.

## 원칙

- **의미로 판단한다.** 동의어는 같은 개념일 수 있다 — 빈도와 문맥을 함께 본다.
- **입력의 파일 위치를 활용한다.** 토큰마다 등장 파일이 주어지므로 그 파일을 우선 열어 문맥을 확인한다(전역 재검색 최소화).
- **노이즈 제외.** 일반 영어 단어·라이브러리 식별자는 위반에서 뺀다(언어 키워드는 lint가 이미 걸렀다).
- **기존 컨벤션 존중.** 기존 모듈의 네이밍을 우선한다. 자동 수정·임의 리네이밍을 제안하지 않는다.

## 출력

1. **위반 목록**: `파일:라인 | 코드 표현 | 사전 표준(영문) | 사유`
2. **추가 후보**: `한글(추정) | 영문 | 사유` — 사용자가 add 스킬(`/superglossary:add`)로 등록할 대상.

확정 가능한 것만 보고하고, 애매하면 후보로 분류한다.
```

- [ ] **Step 3: 검증**

Run: `claude plugin validate . && ls skills`
Expected: 검증 통과, `skills/` 아래 `add  check  init`

- [ ] **Step 4: 커밋**

```bash
git add -A skills agents/check-analyzer.md
git commit -m "refactor: glossary-check를 check 스킬로 개명·하이브리드화

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 11: 문서 갱신 — README·CLAUDE.md·CHANGELOG

**Files:**
- Modify: `README.md`, `CLAUDE.md`, `CHANGELOG.md`

**Interfaces:**
- Consumes: Task 1–10의 최종 동작(스킬 3개, lint 2섹션, avoid, version/help)
- Produces: 사용자 문서 일치. CHANGELOG는 `[Unreleased]` 아래에 기록(버전 확정은 Task 12)

- [ ] **Step 1: README.md 수정**

**권장 워크플로우** 블록을 다음으로 교체:

```
1. 최초 1회  — /superglossary:init 으로 초기화 (큰 기능 전엔 다룰 핵심 개념을 사전과 정렬)
2. 작업 중   — 검색 없이 작업하되, 사전에 없는 용어를 만나면 add 스킬로 그것만 추가
3. 완료 후   — check 스킬로 일관성 검사 ([위반]은 사전이 확정, 후보는 의미 검토)
4. (선택)    — 커밋/PR 전 자동 lint (아래 '자동 트리거' 참고)
```

**구성 요소** 표를 다음으로 교체:

```markdown
| 종류 | 이름 | 역할 |
|------|------|------|
| 스킬 | `/superglossary:init` | 프로젝트에 용어사전 초기화·CLI 업그레이드 (사용자 전용) |
| 스킬 | `/superglossary:add` | 새 용어 등록 — 사용자 호출 + Claude가 필요 시 자율 호출 |
| 스킬 | `/superglossary:check` | 용어 일관성 검사 (소규모는 인라인, 대규모는 서브에이전트) |
| 서브에이전트 | `check-analyzer` | 대규모 후보의 의미 기반 확정 (model: sonnet) |
| 서브에이전트 | `glossary-scanner` | 코드·문서에서 용어 후보·혼용 스캔 (model: sonnet) |
| CLI | `templates/glossary.mjs` | 의존성 0의 독립 CLI (`init`/`build`/`add`/`update`/`remove`/`list`/`lookup`/`lint`/`version`/`help`) |
```

**데이터 및 로딩** 섹션의 파일 주석에 avoid를 반영하고, 섹션 끝에 추가:

```markdown
**금지 변형(avoid)**: 표준으로 선정되지 않은 영문 변형을 용어에 보존합니다(예: `member`의 avoid = `customer`, `user`). `lint`가 LLM 판단 없이 `[위반]`으로 확정합니다.
```

**설치** 섹션 뒤에 새 섹션 추가:

```markdown
## 업그레이드

플러그인 업데이트 후 각 프로젝트에서 `/superglossary:init`을 재실행하면 CLI 복사본이 최신으로 갱신됩니다. `glossary.json`과 기존 `.claude/CLAUDE.md` 블록은 보존됩니다.

- 현재 CLI 버전 확인: `node .claude/superglossary/glossary.mjs version`
- CLAUDE.md 블록 문구까지 최신화하려면: `.claude/CLAUDE.md`의 `## 용어 사전` 섹션을 지우고 init을 재실행
```

- [ ] **Step 2: CLAUDE.md(프로젝트) 수정**

저장소 구조의 커맨드·스킬 항목 두 줄을 다음으로 교체:

```markdown
- `skills/` — 스킬 정의 (`init/`, `add/`, `check/` — 각 디렉토리에 `SKILL.md`).
```

(`commands/` 줄은 삭제. "컴포넌트 규칙"의 `commands/, skills/, agents/`는 `skills/, agents/`로 수정.)

- [ ] **Step 3: CHANGELOG.md의 `[Unreleased]`에 추가**

```markdown
## [Unreleased]

### Added

- `avoid`(금지 변형) 필드 — brownfield 표준화 결정을 보존, `lint`가 결정론적으로 위반 확정 (`--avoid` 플래그)
- `lint` 스톱워드 필터(`--all`로 해제)·토큰별 등장 파일 출력·`[위반]`/`[후보]` 섹션 분리
- `lookup` 상세 출력(설명·관련·금지), `version`/`help` 서브커맨드
- stale 감지 경고(list/lookup/lint), `.gitignore` 무시 경고(init), glossary.json 부재 시 친절한 에러
- `pnpm bump`가 CLI `VERSION` 상수를 plugin.json과 동기화, `version:check`가 일치 검증

### Changed

- 커맨드(`commands/`)를 스킬(`skills/init`·`skills/add`)로 전환 — 호출명 `/superglossary:init`·`/superglossary:add`는 동일
- `glossary-check` 스킬을 `check`로 개명(`/superglossary:check`) + 하이브리드 검사(후보 10개 이하 인라인, 초과 시 check-analyzer)
- add 스킬이 Claude 자율 등록의 단일 진입점 — 사용자 프로젝트 CLAUDE.md 블록 갱신(신규 init부터)
- `lint` 출력 형식 변경(섹션·파일 위치), init의 데이터 디렉토리를 스크립트 위치 기준으로 통일

### Fixed

- 생성 표의 `|`·개행 이스케이프, english↔abbreviation 교차 충돌 검사, core.md 분할 안내(스펙 §6) 구현
```

- [ ] **Step 4: 검증·커밋**

Run: `pnpm test && claude plugin validate .`
Expected: 전건 통과

```bash
git add README.md CLAUDE.md CHANGELOG.md
git commit -m "docs: v0.3.0 문서 갱신(README·CLAUDE.md·CHANGELOG)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 12: 버전 상향·최종 검증·스모크

**Files:**
- Modify: `.claude-plugin/plugin.json`, `templates/glossary.mjs`(VERSION — bump가 자동), `CHANGELOG.md`

**Interfaces:**
- Consumes: Task 7 bump 동기화, Task 1–11 전체

- [ ] **Step 1: 버전 상향**

```bash
pnpm bump 0.3.0 && pnpm version:check
```
Expected: `✓ 버전 갱신: 0.2.0 → 0.3.0 (plugin.json + glossary.mjs)` 후 `✓ 현재 버전: 0.3.0 (plugin.json = glossary.mjs)`

- [ ] **Step 2: CHANGELOG 확정**

`## [Unreleased]` 아래 내용을 `## [0.3.0] - 2026-07-09`로 옮기고(빈 `[Unreleased]` 유지), 하단 링크를 갱신:

```markdown
[Unreleased]: https://github.com/Cho-D-YoungRae/superglossary/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/Cho-D-YoungRae/superglossary/compare/v0.2.0...v0.3.0
```

- [ ] **Step 3: 전체 검증**

Run: `pnpm test`
Expected: PASS (약 45개 내외, fail 0)

Run: `claude plugin validate .`
Expected: 통과

- [ ] **Step 4: 스모크 시나리오** (임시 디렉토리에서 CLI 직접 검증)

```bash
REPO=$(pwd)   # superglossary 플러그인 레포 루트에서 시작
SMOKE=$(mktemp -d)/proj && mkdir -p "$SMOKE/.claude/superglossary" && cd "$SMOKE"
cp "$REPO/templates/glossary.mjs" .claude/superglossary/
node .claude/superglossary/glossary.mjs init
node .claude/superglossary/glossary.mjs add 회원 member --avoid "customer,user"
echo 'const customerId = 1; const deliveryFee = 2;' > s.js
node .claude/superglossary/glossary.mjs lint s.js      # [위반] customer → member(회원) + [후보] delivery, fee 확인
node .claude/superglossary/glossary.mjs lookup 회원     # 금지: customer, user 확인
node .claude/superglossary/glossary.mjs version         # v0.3.0 확인
node .claude/superglossary/glossary.mjs help            # 사용법 확인
cat .claude/superglossary/core.md                       # 금지 변형 요약 줄 확인
```

- [ ] **Step 5: 커밋**

```bash
git add .claude-plugin/plugin.json templates/glossary.mjs CHANGELOG.md
git commit -m "chore: v0.3.0 버전 상향

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

이후 릴리즈는 CONTRIBUTING의 Git flow(develop PR → main PR → 태그)를 따른다. 스킬 동작(자연어 트리거·서브에이전트 dispatch)의 실사용 검증은 `claude --plugin-dir .`로 로컬 로드해 수행한다.
