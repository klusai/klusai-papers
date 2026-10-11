"""Exercise the actual auto-merge shell with a fake GitHub CLI; no network or writes to GitHub."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def workflow(name):
    # BaseLoader preserves the GitHub Actions `on` key (YAML 1.1 treats it as a boolean).
    return yaml.load((ROOT / ".github/workflows" / name).read_text(), Loader=yaml.BaseLoader)


class AutoMergeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.scratch = Path(self.directory.name)
        self.pr = {
            "state": "open",
            "draft": False,
            "base": {"ref": "main", "repo": {"full_name": "klusai/klusai-papers"}},
            "head": {"ref": "research-pr-ci", "sha": "abc123", "repo": {"full_name": "klusai/klusai-papers"}},
            "user": {"login": "researcher"},
            "labels": [],
            "auto_merge": {"merge_method": "squash"},
        }
        self.protection = {
            "protected": True,
            "protection": {"required_status_checks": {"enforcement_level": "non_admins", "contexts": ["test"]}},
        }
        self.env = {
            **os.environ,
            "PATH": f"{self.scratch}{os.pathsep}{os.environ['PATH']}",
            "GH_TOKEN": "unused-test-token",
            "GH_REPO": "klusai/klusai-papers",
            "PR_NUMBER": "42",
            "UPDATE_TYPE": "",
            "STUB_DIR": str(self.scratch),
            "STUB_PROTECTION_FAIL": "0",
            "STUB_PR_FAIL": "0",
        }
        stub = self.scratch / "gh"
        stub.write_text(
            f"#!{sys.executable}\n"
            + """import json
import os
import sys
from pathlib import Path

root = Path(os.environ["STUB_DIR"])
args = sys.argv[1:]
if args == ["api", "repos/klusai/klusai-papers/pulls/42"]:
    if os.environ["STUB_PR_FAIL"] == "1":
        sys.exit(1)
    print((root / "pr.json").read_text())
elif args == ["api", "repos/klusai/klusai-papers/branches/main"]:
    if os.environ["STUB_PROTECTION_FAIL"] == "1":
        sys.exit(1)
    print((root / "protection.json").read_text())
elif args[:2] == ["pr", "merge"]:
    with (root / "calls.jsonl").open("a") as output:
        output.write(json.dumps(args) + "\\n")
else:
    sys.exit("Unexpected GitHub command: " + repr(args))
"""
        )
        stub.chmod(0o755)
        steps = workflow("auto-merge.yml")["jobs"]["auto-merge"]["steps"]
        self.script = next(step["run"] for step in steps if step.get("name") == "Apply auto-merge policy")

    def run_policy(self, expected, returncode=0):
        (self.scratch / "pr.json").write_text(json.dumps(self.pr))
        (self.scratch / "protection.json").write_text(json.dumps(self.protection))
        calls_file = self.scratch / "calls.jsonl"
        calls_file.unlink(missing_ok=True)
        result = subprocess.run(["bash", "-c", self.script], env=self.env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, returncode, result.stdout + result.stderr)
        calls = [json.loads(line) for line in calls_file.read_text().splitlines()] if calls_file.exists() else []
        prefix = ["pr", "merge", "42", "--repo", "klusai/klusai-papers"]
        expected_calls = {
            "enable": [prefix + ["--auto", "--squash", "--match-head-commit", "abc123"]],
            "disable": [prefix + ["--disable-auto"]],
            "none": [],
        }
        self.assertEqual(calls, expected_calls[expected])

    def test_protected_pr_arms_squash_for_current_head(self):
        self.run_policy("enable")

    def test_app_bound_required_check_is_accepted(self):
        checks = self.protection["protection"]["required_status_checks"]
        checks.update(contexts=[], checks=[{"context": "test", "app_id": 15368}], enforcement_level="everyone")
        self.run_policy("enable")

    def test_missing_or_inactive_protection_never_merges(self):
        for protection in [
            {},
            {"protected": False, "protection": self.protection["protection"]},
            {"protected": True},
            {"protected": True, "protection": {"required_status_checks": None}},
            {
                "protected": True,
                "protection": {"required_status_checks": {"enforcement_level": "off", "contexts": ["test"]}},
            },
            {
                "protected": True,
                "protection": {"required_status_checks": {"enforcement_level": "non_admins", "contexts": ["contest"]}},
            },
        ]:
            with self.subTest(protection=protection):
                self.protection = protection
                self.run_policy("none")

    def test_protection_api_failure_never_merges(self):
        self.env["STUB_PROTECTION_FAIL"] = "1"
        self.run_policy("none")

    def test_pr_api_failure_never_merges(self):
        self.env["STUB_PR_FAIL"] = "1"
        self.run_policy("none", returncode=1)

    def test_hard_hold_labels_override_manual_opt_in(self):
        for label in ["needs-review", "hold"]:
            with self.subTest(label=label):
                self.pr["labels"] = [{"name": "automerge"}, {"name": label}]
                self.run_policy("disable")

    def test_draft_transition_disables_queued_merge(self):
        self.pr.update(draft=True, labels=[{"name": "automerge"}])
        self.run_policy("disable")

    def test_hold_without_queued_merge_is_noop(self):
        self.pr.update(draft=True, auto_merge=None)
        self.run_policy("none")

    def test_fork_needs_opt_in(self):
        self.pr["head"]["repo"]["full_name"] = "outside/fork"
        self.run_policy("disable")
        self.pr["labels"] = [{"name": "automerge"}]
        self.run_policy("enable")

    def test_branch_holds_allow_opt_in(self):
        for branch in ["hold/topic", "review/topic"]:
            with self.subTest(branch=branch):
                self.pr["head"]["ref"] = branch
                self.pr["labels"] = []
                self.run_policy("disable")
                self.pr["labels"] = [{"name": "automerge"}]
                self.run_policy("enable")

    def test_dependabot_unknown_and_major_updates_need_opt_in(self):
        self.pr["user"]["login"] = "dependabot[bot]"
        for update in ["", "version-update:semver-major"]:
            with self.subTest(update=update):
                self.env["UPDATE_TYPE"] = update
                self.pr["labels"] = []
                self.run_policy("disable")
                self.pr["labels"] = [{"name": "automerge"}]
                self.run_policy("enable")

    def test_dependabot_minor_and_patch_updates_are_eligible(self):
        self.pr["user"]["login"] = "dependabot[bot]"
        for update in ["version-update:semver-minor", "version-update:semver-patch"]:
            with self.subTest(update=update):
                self.env["UPDATE_TYPE"] = update
                self.run_policy("enable")

    def test_other_base_or_closed_pr_is_ignored(self):
        self.pr["base"]["ref"] = "release"
        self.run_policy("none")
        self.pr["base"]["ref"] = "main"
        self.pr["state"] = "closed"
        self.run_policy("none")

    def test_label_names_are_exact_and_branch_text_is_not_executed(self):
        self.pr["labels"] = [{"name": "hold,automerge"}]
        self.pr["head"]["ref"] = "topic/$(exit 7)"
        self.run_policy("enable")


class WorkflowContractTests(unittest.TestCase):
    def test_ci_runs_checks_on_prs_and_main(self):
        ci = workflow("ci.yml")
        self.assertIn("pull_request", ci["on"])
        self.assertEqual(ci["on"]["push"]["branches"], ["main"])
        self.assertEqual(ci["permissions"], {"contents": "read"})
        job = ci["jobs"]["test"]
        self.assertLessEqual(int(job["timeout-minutes"]), 10)
        self.assertEqual([step["run"] for step in job["steps"] if "run" in step], ["make install", "make check"])
        setup = next(step for step in job["steps"] if step.get("uses", "").startswith("actions/setup-python@"))
        self.assertEqual(setup["with"]["python-version"], "3.13")

    def test_privileged_workflow_has_no_checkout_and_handles_holds(self):
        auto_merge = workflow("auto-merge.yml")
        events = auto_merge["on"]["pull_request_target"]["types"]
        for event in ["converted_to_draft", "ready_for_review", "labeled", "unlabeled", "synchronize", "edited"]:
            self.assertIn(event, events)
        job = auto_merge["jobs"]["auto-merge"]
        self.assertNotIn("if", job)  # Draft events must run to disable a previously queued merge.
        for step in job["steps"]:
            self.assertFalse(step.get("uses", "").startswith("actions/checkout@"))
            self.assertNotIn("${{", step.get("run", ""))
