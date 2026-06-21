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
