#!/usr/bin/env python3
"""플러그인 버전 관리 스크립트.

버전의 단일 출처(single source of truth)는 `.claude-plugin/plugin.json` 의 "version" 필드입니다.

사용법:
  python3 scripts/bump_version.py <version>   새 SemVer 버전으로 갱신
  python3 scripts/bump_version.py --check     plugin.json과 CLI VERSION의 일치·유효성 검증
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_MANIFEST = os.path.join(ROOT, ".claude-plugin", "plugin.json")
CLI_TEMPLATE = os.path.join(ROOT, "templates", "glossary.py")
VERSION_CONST = re.compile(r'^VERSION = "([^"]+)"$', re.MULTILINE)

# SemVer 2.0.0 (선택적 pre-release / build metadata 포함). https://semver.org
SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-(?:[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


def fail(message):
    print(f"✗ {message}", file=sys.stderr)
    sys.exit(1)


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def read_manifest():
    return json.loads(read_text(PLUGIN_MANIFEST))


def read_cli_version():
    source = read_text(CLI_TEMPLATE)
    matched = VERSION_CONST.search(source)
    return source, (matched.group(1) if matched else None)


def check():
    version = read_manifest().get("version")
    if not version or not SEMVER.match(version):
        fail(f"plugin.json version이 유효한 SemVer가 아닙니다: {json.dumps(version, ensure_ascii=False)}")
    _, cli_version = read_cli_version()
    if cli_version is None:
        fail("templates/glossary.py에서 VERSION 상수를 찾지 못했습니다.")
    if cli_version != version:
        fail(f"버전 불일치: plugin.json={version}, glossary.py={cli_version} — bump_version.py로 동기화하세요.")
    print(f"✓ 현재 버전: {version} (plugin.json = glossary.py)")


def bump(version):
    if not SEMVER.match(version):
        fail(f'유효한 SemVer가 아닙니다: "{version}" (예: 1.2.3, 0.1.0, 1.0.0-rc.1)')
    manifest = read_manifest()
    previous = manifest.get("version")
    manifest["version"] = version
    with open(PLUGIN_MANIFEST, "w", encoding="utf-8") as f:
        f.write(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    source, cli_version = read_cli_version()
    if cli_version is None:
        fail("templates/glossary.py에서 VERSION 상수를 찾지 못했습니다.")
    with open(CLI_TEMPLATE, "w", encoding="utf-8") as f:
        f.write(VERSION_CONST.sub(f'VERSION = "{version}"', source, count=1))

    print(f"✓ 버전 갱신: {previous} → {version} (plugin.json + glossary.py)")
    print()
    print("다음 단계를 잊지 마세요:")
    print(f"  1. CHANGELOG.md의 [Unreleased] → [{version}] - <YYYY-MM-DD> 정리")
    print("  2. develop → main PR 병합")
    print(f"  3. git tag v{version} && git push --tags")
    print(f"  4. gh release create v{version}")


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    if not arg:
        fail("버전을 지정하거나 --check 를 사용하세요. 예: python3 scripts/bump_version.py 0.4.0")
    elif arg == "--check":
        check()
    else:
        bump(arg)


if __name__ == "__main__":
    main()
