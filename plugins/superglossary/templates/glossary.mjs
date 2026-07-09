#!/usr/bin/env node
// .claude/superglossary/glossary.mjs — 프로젝트 용어사전 CLI (의존성 0)
import { readFileSync, writeFileSync, existsSync, statSync, mkdirSync } from "node:fs";
import { join, dirname, basename } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

export const VERSION = "0.3.0";

export const AUTOGEN =
  "<!-- 이 파일은 glossary.json에서 자동 생성됩니다. 직접 편집하지 마세요. (glossary.mjs build) -->";

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

export function saveGlossary(dir, data) {
  writeFileSync(join(dir, "glossary.json"), JSON.stringify(data, null, 2) + "\n");
}

export function sortedTerms(data) {
  return [...data.terms].sort((a, b) => a.korean.localeCompare(b.korean, "ko"));
}

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

export function findTerm(data, korean) {
  return data.terms.find((t) => t.korean === korean);
}

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

export function formatTermDetail(t) {
  const abbr = t.abbreviation ? ` (축약: ${t.abbreviation})` : "";
  const lines = [`${t.korean} → ${t.english}${abbr}`];
  if (t.description) lines.push(`  설명: ${t.description}`);
  if ((t.relatedElements ?? []).length) lines.push(`  관련: ${t.relatedElements.join(", ")}`);
  if (avoidOf(t).length) lines.push(`  금지: ${avoidOf(t).join(", ")}`);
  return lines.join("\n");
}

const RULE_COMMENT =
  "<!-- 규칙: 단일어만 등록·조합해 사용한다. 축약어는 이 표에 등록된 것만 허용한다. -->";

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

export function tokenize(identifier) {
  return identifier
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .split(/[_\s]+/)
    .map((s) => s.toLowerCase())
    .filter(Boolean);
}

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

export const INITIAL_DATA = {
  terms: [
    { korean: "식별자", english: "identifier", abbreviation: "id", description: "데이터를 고유 식별하는 값. {엔티티}_id 형식", relatedElements: [], avoid: [] },
    { korean: "일시", english: "datetime", abbreviation: "at", description: "날짜와 시각. created_at 처럼 _at 접미사로 사용", relatedElements: [], avoid: [] },
    { korean: "이름", english: "name", abbreviation: null, description: "대상을 지칭하는 명칭", relatedElements: [], avoid: [] },
  ],
};

export const CLAUDE_BLOCK = `## 용어 사전
@superglossary/core.md

- 클래스/변수/함수/컬럼/테이블 등 모든 네이밍은 위 표의 영문명만 사용한다. 축약어는 표에 등록된 것만 쓰고, 금지 변형은 표준으로 대체한다.
- 표에 없는 단일어가 필요하면 임의로 짓지 말고 superglossary의 add 스킬로 등록한다(복합어는 단일어로 분해). 플러그인이 없으면 \`node .claude/superglossary/glossary.mjs add <korean> <english> [abbreviation]\`을 직접 실행한다. 변경은 같은 diff에 포함한다.
- 용어의 의미가 모호하면 \`node .claude/superglossary/glossary.mjs lookup <질의>\` 또는 \`.claude/superglossary/terms.md\`에서 상세를 확인한다.
- 수정·삭제는 \`glossary.mjs update/remove\`를 쓴다(자동 재빌드). core.md·terms.md는 생성물이므로 직접 편집하지 않는다.
- 기존 모듈 수정 시 그 모듈의 기존 컨벤션을 우선하고, 신규 코드에는 사전을 우선한다. 임의 리네이밍은 하지 않는다.
- 워크플로: 작업 시작 전 핵심 개념 정렬 → 작업 중 사전에 없는 용어만 추가 → 완료 후 check 스킬로 검토.
`;

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

function relatedFromOptions(options) {
  return options.related ? options.related.split(",").map((s) => s.trim()).filter(Boolean) : undefined;
}

function avoidFromOptions(options) {
  return options.avoid ? options.avoid.split(",").map((s) => s.trim()).filter(Boolean) : undefined;
}

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

export function run(argv, dataDir) {
  const [cmd, ...rest] = argv;
  const { positional, options } = parseArgs(rest);
  switch (cmd) {
    case "init": {
      const warnings = scaffold(dataDir);
      return [`초기화 완료: ${dataDir}`, ...warnings].join("\n");
    }
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
    case "lint": {
      const data = loadGlossary(dataDir);
      warnIfStale(dataDir, data);
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
    case "version":
      return `superglossary CLI v${VERSION}`;
    case "help":
      return USAGE;
    default:
      throw new Error(`알 수 없는 커맨드: ${cmd}\n${USAGE}`);
  }
}

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
