import json
import subprocess
import sys
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = PLUGIN_ROOT / "hooks" / "scripts" / "change_reminder.py"
OK = PLUGIN_ROOT / "tests" / "fixtures" / "harness-ok"
OFF = PLUGIN_ROOT / "tests" / "fixtures" / "harness-off"


def run_hook(cwd, command, raw=None):
    payload = raw if raw is not None else json.dumps(
        {"hook_event_name": "PostToolUse", "cwd": str(cwd), "tool_name": "Bash",
         "tool_input": {"command": command}})
    return subprocess.run([sys.executable, str(SCRIPT)], input=payload,
                          capture_output=True, text=True)


class TestChangeReminder(unittest.TestCase):
    def assert_reminded(self, r):
        self.assertEqual(r.returncode, 0)
        out = json.loads(r.stdout)
        self.assertIn("change", out["hookSpecificOutput"]["additionalContext"])

    def assert_silent(self, r):
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "")

    def test_kubectl_apply_reminds(self):
        self.assert_reminded(run_hook(OK, "kubectl --context prod-k8s apply -f d.yaml"))

    def test_helm_upgrade_reminds(self):
        self.assert_reminded(run_hook(OK, "helm --kube-context prod-k8s upgrade vm vm/victoria-metrics-single"))

    def test_rollout_restart_reminds(self):
        self.assert_reminded(run_hook(OK, "kubectl --context prod-k8s rollout restart deploy/api"))

    def test_terraform_apply_reminds(self):
        self.assert_reminded(run_hook(OK, "terraform apply -auto-approve"))

    def test_argocd_sync_reminds(self):
        self.assert_reminded(run_hook(OK, "argocd app sync my-app"))

    def test_readonly_silent(self):
        self.assert_silent(run_hook(OK, "kubectl --context prod-k8s get pods -A"))

    def test_rollout_status_silent(self):
        self.assert_silent(run_hook(OK, "kubectl --context prod-k8s rollout status deploy/api"))

    def test_dry_run_silent(self):
        self.assert_silent(run_hook(OK, "kubectl --context prod-k8s apply --dry-run=client -f d.yaml"))

    def test_reminder_off_silent(self):
        self.assert_silent(run_hook(OFF, "kubectl --context prod-k8s apply -f d.yaml"))

    def test_outside_harness_silent(self):
        self.assert_silent(run_hook("/", "kubectl apply -f d.yaml"))

    def test_broken_stdin_exit0(self):
        self.assert_silent(run_hook(OK, "", raw="not-json"))

    def test_helm_delete_with_flags_reminds(self):
        self.assert_reminded(run_hook(OK, "helm --kube-context prod-k8s delete my-release"))

    def test_argocd_sync_with_server_flag_reminds(self):
        self.assert_reminded(run_hook(OK, "argocd --server argocd.prod.internal app sync my-app"))

    def test_hyphenated_label_value_silent(self):
        self.assert_silent(run_hook(OK, "kubectl --context prod-k8s get pods -l tier=auto-scale-group"))

    def test_hyphenated_resource_name_silent(self):
        self.assert_silent(run_hook(OK, "kubectl --context prod-k8s logs my-edit-service-7f8"))


if __name__ == "__main__":
    unittest.main()
