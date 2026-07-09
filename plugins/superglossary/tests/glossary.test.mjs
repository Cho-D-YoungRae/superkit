import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, rmSync, readFileSync, writeFileSync as wf, mkdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { loadGlossary, saveGlossary, sortedTerms, addTerm, findTerm, updateTerm, removeTerm, listTerms, lookup, renderCore, renderTerms, build, AUTOGEN, tokenize, lintFiles, scaffold, parseArgs, run, findConflict, escapeCell, CORE_SPLIT_THRESHOLD, STOPWORDS, formatFileList, formatTermDetail, isStale } from "../templates/glossary.mjs";

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
    korean: "회원", english: "member", abbreviation: null, description: "", relatedElements: [], avoid: [],
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

test("tokenize: camelCase/snake_case 분해", () => {
  assert.deepEqual(tokenize("memberId"), ["member", "id"]);
  assert.deepEqual(tokenize("reg_dt"), ["reg", "dt"]);
  assert.deepEqual(tokenize("ship_address"), ["ship", "address"]);
});

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

test("parseArgs: --all은 값 없이 true", () => {
  const { positional, options } = parseArgs(["--all", "a.js", "b.js"]);
  assert.equal(options.all, true);
  assert.deepEqual(positional, ["a.js", "b.js"]);
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

test("run: 알 수 없는 커맨드는 throw", () => {
  assert.throws(() => run(["nope"], "/tmp"), /알 수 없는 커맨드/);
});

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
