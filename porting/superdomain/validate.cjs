// Repository-side checks only; not part of the installed plugin.
// Usage: node validate.cjs <plugin-root> <official-plugin-schema.json>
// Dependencies: ajv (v8), js-yaml.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const Ajv = require('ajv/dist/2020');
const yaml = require('js-yaml');

const [rootArg, schemaArg] = process.argv.slice(2);
assert(rootArg && schemaArg, 'Pass a plugin directory and the downloaded official schema');
const root = fs.realpathSync(rootArg);
const schema = JSON.parse(fs.readFileSync(schemaArg, 'utf8'));
assert.equal(schema.$id, 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json');
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'plugin.json'), 'utf8'));
const validate = new Ajv({allErrors: true}).compile(schema);
assert(validate(manifest), JSON.stringify(validate.errors));

const files = [];
function walk(dir) {
  for (const entry of fs.readdirSync(dir, {withFileTypes: true})) {
    const full = path.join(dir, entry.name);
    assert(!entry.isSymbolicLink(), `Package must not depend on symlinks: ${full}`);
    if (entry.isDirectory()) walk(full);
    else {
      assert(entry.isFile(), `Unsupported file: ${full}`);
      files.push(full);
    }
  }
}
walk(root);
let links = 0;
const skillNames = [];
for (const file of files) {
  const content = fs.readFileSync(file, 'utf8');
  assert(!file.endsWith('/CLAUDE.md') && !file.endsWith('/CLAUDE.local.md'), file);
  if (file.endsWith('.json')) JSON.parse(content);
  if (/\.ya?ml$/.test(file)) yaml.load(content);
  if (path.basename(file) === 'SKILL.md') {
    const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
    assert(match, `Missing frontmatter: ${file}`);
    const meta = yaml.load(match[1]);
    assert.equal(meta.name, path.basename(path.dirname(file)));
    assert(typeof meta.description === 'string' && meta.description.length > 0);
    assert.deepEqual(Object.keys(meta).sort(), ['description', 'name']);
    skillNames.push(meta.name);
  }
  if (!file.endsWith('.md')) continue;
  assert(!/\$\{CLAUDE_(?:PLUGIN_ROOT|SKILL_DIR)\}|\$ARGUMENTS/.test(content), file);
  const prose = content.replace(/^```[^\n]*\n[\s\S]*?^```[^\n]*$/gm, '').replace(/`[^`\n]*`/g, '');
  for (const match of prose.matchAll(/\[[^\]\n]*\]\(([^)\n]+)\)/g)) {
    const target = match[1];
    // Template examples represent future user documents, not package resources.
    if (/^(?:https?:|mailto:|#)/.test(target) || /[<>]/.test(target)) continue;
    const resolved = path.resolve(path.dirname(file), target.split('#')[0]);
    assert(resolved.startsWith(root + path.sep), `Link escapes package: ${file}: ${target}`);
    assert(fs.existsSync(resolved), `Broken package resource: ${file}: ${target}`);
    links++;
  }
}
assert.deepEqual(skillNames.sort(), ['adr', 'conventions', 'domain', 'review']);
assert(fs.existsSync(path.join(root, 'LICENSE')));
console.log(JSON.stringify({manifest: 'valid', skills: skillNames, files: files.length, resolvedLinks: links}));
