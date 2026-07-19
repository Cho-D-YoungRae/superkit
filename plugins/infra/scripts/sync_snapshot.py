#!/usr/bin/env python3
"""인벤토리 문서 vs 실제 상태 대조 — read-only 수집만 수행 (stdlib 전용)."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_lib  # noqa: E402

CHART_VER_RE = re.compile(r"^(?P<name>.+)-(?P<ver>\d[\w.]*)$")


def parse_installed_by(value):
    value = str(value)
    if value.startswith("helm://"):
        body = value[len("helm://"):]
        ref, _, ver = body.partition("@")
        return ("helm", ref, ver or None)
    method = value.split("://")[0].split()[0] if value else ""
    return (method, "", None)


def build_expected(root):
    ents = harness_lib.iter_entities(root)
    exp = {"servers": {}, "clusters": {}, "components": {}, "providers": {}}
    for e in ents:
        if "_error" in e:
            continue
        t = e.get("type")
        if t == "provider":
            exp["providers"][e["id"]] = e
        elif t == "server":
            exp["servers"][e["id"]] = e
        elif t == "k8s-cluster":
            exp["clusters"][e["id"]] = e
        elif t == "component":
            exp["components"][e["id"]] = e
    return exp


def build_collect_commands(root):
    exp = build_expected(root)
    cmds = []
    for cid, c in exp["clusters"].items():
        ctx = c.get("context")
        cmds.append({"target": cid, "kind": "nodes",
                     "cmd": ["kubectl", "--context", ctx, "get", "nodes", "-o", "name"]})
        cmds.append({"target": cid, "kind": "helm-releases",
                     "cmd": ["helm", "--kube-context", ctx, "list", "-A", "-o", "json"]})
    for pid, p in exp["providers"].items():
        if p.get("kind") == "aws" and p.get("cli_profile"):
            cmds.append({"target": pid, "kind": "instances", "cmd": [
                "aws", "ec2", "describe-instances", "--profile", str(p["cli_profile"]),
                "--query", "Reservations[].Instances[].[Tags[?Key=='Name'].Value | [0]]",
                "--output", "text"]})
        elif p.get("kind") == "gcp" and p.get("cli_profile"):
            cmds.append({"target": pid, "kind": "instances", "cmd": [
                "gcloud", "compute", "instances", "list",
                "--configuration", str(p["cli_profile"]), "--format", "value(name)"]})
    return cmds


def collect(root):
    actual = {"clusters": {}, "providers": {}}
    for item in build_collect_commands(root):
        try:
            r = subprocess.run(item["cmd"], capture_output=True, text=True, timeout=60)
            ok = r.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            ok, r = False, None
        if item["kind"] == "nodes":
            actual["clusters"].setdefault(item["target"], {"reachable": False, "helm_releases": []})
            actual["clusters"][item["target"]]["reachable"] = ok
        elif item["kind"] == "helm-releases":
            entry = actual["clusters"].setdefault(item["target"], {"reachable": False, "helm_releases": []})
            if ok:
                try:
                    rels = json.loads(r.stdout or "[]")
                    entry["helm_releases"] = [
                        {"name": x.get("name"), "namespace": x.get("namespace"), "chart": x.get("chart")}
                        for x in rels]
                except json.JSONDecodeError:
                    pass
        elif item["kind"] == "instances":
            names = [l.strip() for l in (r.stdout.splitlines() if ok else []) if l.strip() and l.strip() != "None"]
            actual["providers"][item["target"]] = {"reachable": ok, "instances": names}
    return actual


def _version_matches(expected_ver, actual_ver):
    if expected_ver is None:
        return True
    if "x" in expected_ver or "*" in expected_ver:
        prefix = expected_ver.replace("*", "x").split("x")[0]
        return actual_ver.startswith(prefix)
    return expected_ver == actual_ver


def diff_state(expected, actual):
    report = {"missing_in_docs": [], "ghost_in_docs": [], "version_mismatch": [], "unverifiable": []}
    # 클러스터·컴포넌트(helm) 대조
    for cid in expected["clusters"]:
        cluster_actual = actual.get("clusters", {}).get(cid)
        if not cluster_actual or not cluster_actual.get("reachable"):
            report["unverifiable"].append(f"{cid}: 클러스터 수집 실패 — 확인 불가")
            continue
        releases = {r["name"]: r for r in cluster_actual.get("helm_releases", [])}
        doc_components = {c_id: c for c_id, c in expected["components"].items() if c.get("runs_on") == cid}
        for rname, rel in releases.items():
            if rname not in doc_components:
                report["missing_in_docs"].append(f"{cid}: helm 릴리스 {rname} ({rel.get('chart')}) — 문서에 없음")
        for c_id, comp in doc_components.items():
            method, ref, ver = parse_installed_by(comp.get("installed_by", ""))
            if method != "helm":
                continue
            if c_id not in releases:
                report["ghost_in_docs"].append(f"{cid}: 컴포넌트 {c_id} — 실측에 없음")
                continue
            m = CHART_VER_RE.match(releases[c_id].get("chart") or "")
            if m and not _version_matches(ver, m.group("ver")):
                report["version_mismatch"].append(
                    f"{c_id}: 문서 {comp.get('installed_by')} vs 실측 {releases[c_id]['chart']}")
    # provider 인스턴스 대조 (Name 태그 = 문서 서버 id 가정)
    for pid, prov in expected["providers"].items():
        if prov.get("kind") not in ("aws", "gcp"):
            continue
        prov_actual = actual.get("providers", {}).get(pid)
        if not prov_actual or not prov_actual.get("reachable"):
            report["unverifiable"].append(f"{pid}: provider 수집 실패 — 확인 불가")
            continue
        instances = set(prov_actual.get("instances", []))
        doc_servers = {s_id for s_id, s in expected["servers"].items() if s.get("provider") == pid}
        for name in sorted(instances - doc_servers):
            report["missing_in_docs"].append(f"{pid}: 인스턴스 {name} — 문서에 없음")
        for s_id in sorted(doc_servers - instances):
            report["ghost_in_docs"].append(f"{pid}: 서버 {s_id} — 실측에 없음")
    return report


def main():
    ap = argparse.ArgumentParser(description="인벤토리 vs 실제 상태 drift 대조")
    ap.add_argument("--root")
    ap.add_argument("--collect", action="store_true", help="수집 명령을 실제 실행 (read-only)")
    ap.add_argument("--mock-actual", help="수집 대신 JSON 파일 주입 (테스트용)")
    args = ap.parse_args()
    root = Path(args.root) if args.root else harness_lib.find_harness_root()
    if root is None:
        print("하네스를 찾지 못했습니다 — 하네스 디렉터리에서 실행하거나 --root를 지정하세요.")
        return 1
    expected = build_expected(root)
    if args.mock_actual:
        actual = json.loads(Path(args.mock_actual).read_text(encoding="utf-8"))
    elif args.collect:
        actual = collect(root)
    else:  # dry: 수집 명령만 보여준다
        print("# 수집 명령 (read-only)")
        for item in build_collect_commands(root):
            print(f"[{item['target']}/{item['kind']}] {' '.join(item['cmd'])}")
        return 0
    report = diff_state(expected, actual)
    print(f"# sync 결과 — {root}")
    for key, title in (("missing_in_docs", "실제에만 있음(문서 누락)"), ("ghost_in_docs", "문서에만 있음(유령)"),
                       ("version_mismatch", "버전 불일치"), ("unverifiable", "확인 불가")):
        print(f"## {title}: {len(report[key])}건")
        for line in report[key]:
            print(f"- {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
