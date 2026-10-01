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


class TestServerSideMutating(unittest.TestCase):
    """서버 계열 mutating도 리마인드 대상이다 (검토 P2-6).

    hook을 서브프로세스로 실행해 stdout 유무로 판정한다 — 리마인드가 나가면
    hookSpecificOutput JSON이 찍히고, 아니면 아무것도 찍히지 않는다.
    """

    MUTATING = [
        "systemctl restart nginx",
        "sudo systemctl daemon-reload",
        "ssh prod-web-01 'systemctl restart nginx'",
        "apt-get install -y postgresql",
        "ssh prod-db-01 'apt install -y redis'",
        "yum remove httpd",
        "docker run -d nginx",
        "docker rm -f old-container",
        "docker compose up -d",
        "psql -h db -c 'DROP TABLE stale'",
        "mysql -e 'CREATE USER app@localhost'",
        "aws ec2 terminate-instances --instance-ids i-0abc --profile main --region ap-northeast-2",
        "aws rds modify-db-instance --db-instance-identifier prod --profile main",
    ]
    READ_ONLY = [
        "systemctl status nginx",
        "apt list --installed",
        "docker ps",
        "docker logs app",
        "psql -h db -c 'SELECT count(*) FROM users'",
        "aws ec2 describe-instances --profile main --region ap-northeast-2",
        "aws s3 list-buckets --profile main",
        "ssh prod-web-01 'df -h'",
    ]

    def _reminded(self, command):
        r = run_hook(OK, command)
        self.assertEqual(r.returncode, 0, f"hook은 항상 exit 0이어야 한다: {r.stderr}")
        return r.stdout.strip() != ""

    def test_server_side_mutating_matches(self):
        for cmd in self.MUTATING:
            with self.subTest(cmd=cmd):
                self.assertTrue(self._reminded(cmd), cmd)

    def test_read_only_does_not_match(self):
        for cmd in self.READ_ONLY:
            with self.subTest(cmd=cmd):
                self.assertFalse(self._reminded(cmd), cmd)

    def test_dry_run_still_excluded(self):
        self.assertFalse(self._reminded("kubectl apply -f x.yaml --dry-run=client"))
        self.assertFalse(self._reminded("docker compose up -d --dry-run"))

    def test_existing_four_families_still_match(self):
        for cmd in ("terraform apply", "kubectl apply -f x.yaml",
                    "helm upgrade vm vm/vm", "argocd app sync myapp"):
            with self.subTest(cmd=cmd):
                self.assertTrue(self._reminded(cmd), cmd)


if __name__ == "__main__":
    unittest.main()
