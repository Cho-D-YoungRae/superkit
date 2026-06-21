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

export function addTerm(data, { korean, english, abbreviation = null, description = "", relatedElements = [] }) {
  if (!korean || !english) throw new Error("korean과 english는 필수입니다.");
  // 한글은 대소문자 개념이 없어 완전 일치로 검사
  const dupKorean = data.terms.find((t) => t.korean === korean);
  if (dupKorean) throw new Error(`이미 등록된 한글: ${korean} → ${dupKorean.english}`);
  const dupEnglish = data.terms.find((t) => t.english.toLowerCase() === english.toLowerCase());
  if (dupEnglish) throw new Error(`이미 등록된 영문: ${english} (${dupEnglish.korean})`);
  if (abbreviation) {
    const e = data.terms.find((t) => t.abbreviation && t.abbreviation.toLowerCase() === abbreviation.toLowerCase());
    if (e) throw new Error(`이미 등록된 축약어: ${abbreviation} (${e.korean})`);
  }
  data.terms.push({ korean, english, abbreviation, description, relatedElements });
  return data;
}
