#!/usr/bin/env node
// .claude/superglossary/glossary.mjs — 프로젝트 용어사전 CLI (의존성 0)
import { readFileSync, writeFileSync, existsSync, statSync, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

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
- 워크플로: 작업 시작 전 핵심 개념 정렬 → 작업 중 검색 없이 작성하고 빈 용어만 추가 → 완료 후 \`glossary-check\`로 검토.
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
      throw new Error(`알 수 없는 커맨드: ${cmd}\n사용법: glossary.mjs <init|build|add|update|remove|list|lookup|lint> ...`);
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
