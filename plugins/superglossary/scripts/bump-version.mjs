#!/usr/bin/env node
// 플러그인 버전 관리 스크립트.
//
// 버전의 단일 출처(single source of truth)는
// `.claude-plugin/plugin.json` 의 "version" 필드입니다.
//
// 사용법:
//   node scripts/bump-version.mjs <version>   새 SemVer 버전으로 갱신
//   node scripts/bump-version.mjs --check      현재 버전이 유효한 SemVer인지 검증
//
// pnpm 스크립트로도 호출할 수 있습니다:
//   pnpm bump <version>
//   pnpm version:check

import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const PLUGIN_MANIFEST = join(ROOT, ".claude-plugin", "plugin.json");

// SemVer 2.0.0 (선택적 pre-release / build metadata 포함). https://semver.org
const SEMVER =
  /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-(?:[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$/;

function fail(message) {
  console.error(`✗ ${message}`);
  process.exit(1);
}

async function readManifest() {
  return JSON.parse(await readFile(PLUGIN_MANIFEST, "utf8"));
}

async function check() {
  const { version } = await readManifest();
  if (!version || !SEMVER.test(version)) {
    fail(`plugin.json version이 유효한 SemVer가 아닙니다: ${JSON.stringify(version)}`);
  }
  console.log(`✓ 현재 버전: ${version}`);
}

async function bump(version) {
  if (!SEMVER.test(version)) {
    fail(`유효한 SemVer가 아닙니다: "${version}" (예: 1.2.3, 0.1.0, 1.0.0-rc.1)`);
  }
  const manifest = await readManifest();
  const previous = manifest.version;
  manifest.version = version;
  await writeFile(PLUGIN_MANIFEST, JSON.stringify(manifest, null, 2) + "\n");

  console.log(`✓ 버전 갱신: ${previous} → ${version}`);
  console.log("");
  console.log("다음 단계를 잊지 마세요:");
  console.log(`  1. CHANGELOG.md의 [Unreleased] → [${version}] - <YYYY-MM-DD> 정리`);
  console.log(`  2. develop → main PR 병합`);
  console.log(`  3. git tag v${version} && git push --tags`);
  console.log(`  4. gh release create v${version}`);
}

const arg = process.argv[2];

if (!arg) {
  fail("버전을 지정하거나 --check 를 사용하세요. 예: node scripts/bump-version.mjs 0.2.0");
} else if (arg === "--check") {
  await check();
} else {
  await bump(arg);
}
