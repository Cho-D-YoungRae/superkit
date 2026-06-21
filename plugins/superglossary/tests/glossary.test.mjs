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
