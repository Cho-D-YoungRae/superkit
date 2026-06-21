import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, rmSync, readFileSync, writeFileSync as wf, mkdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { loadGlossary, saveGlossary, sortedTerms, addTerm, findTerm, updateTerm, removeTerm, listTerms, lookup, renderCore, renderTerms, build, AUTOGEN, tokenize, lintFiles, scaffold, parseArgs, run } from "../templates/glossary.mjs";

function tmp() {
  return mkdtempSync(join(tmpdir(), "glossary-"));
}

function loadFile(p) { return readFileSync(p, "utf8"); }

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

test("addTerm: 새 용어를 정규화해 추가한다", () => {
  const data = { terms: [] };
  addTerm(data, { korean: "회원", english: "member" });
  assert.deepEqual(data.terms[0], {
    korean: "회원", english: "member", abbreviation: null, description: "", relatedElements: [],
  });
});

test("addTerm: data를 반환한다", () => {
  const data = { terms: [] };
  assert.strictEqual(addTerm(data, { korean: "주문", english: "order" }), data);
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
    assert.ok(claude.includes("# 기존"), "기존 내용 보존");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

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

test("run: 알 수 없는 커맨드는 throw", () => {
  assert.throws(() => run(["nope"], "/tmp"), /알 수 없는 커맨드/);
});
