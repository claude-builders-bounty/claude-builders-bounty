#!/usr/bin/env python3
"""Peer-review acceptance cases for bounty #4 claude-review agent."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
CI_SCRIPT = AGENT_DIR / "tests" / "run-ci-checks.sh"


def resolve_branch_diff_base_ref() -> str:
    """Pick a merge-base ref that exists locally (CI shallow clones omit main)."""
    candidates: list[str] = []
    github_base = os.environ.get("GITHUB_BASE_REF", "").strip()
    if github_base:
        candidates.extend((github_base, f"origin/{github_base}"))
    candidates.extend(("main", "origin/main", "master", "origin/master"))
    for ref in candidates:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", ref],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            return ref
    raise RuntimeError(
        "no git base ref found for branch diff scope check; "
        "fetch the default branch (e.g. git fetch origin main:main) before running tests"
    )


def list_branch_changed_files(base_ref: str) -> list[str]:
    """List paths changed on HEAD since base_ref (needs full git history for ... syntax)."""
    triple_dot = subprocess.run(
        ["git", "diff", f"{base_ref}...HEAD", "--name-only"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if triple_dot.returncode == 0:
        return [line.strip() for line in triple_dot.stdout.splitlines() if line.strip()]

    raise RuntimeError(
        f"git diff {base_ref}...HEAD failed ({triple_dot.stderr.strip()}); "
        "use fetch-depth: 0 in CI checkout so merge-base exists"
    )


class PeerReviewAcceptanceTests(unittest.TestCase):
    """Maps bounty #4 acceptance criteria to repo artifacts and CLI behavior."""

    REQUIRED_SECTIONS = (
        "### Summary of Changes",
        "### Identified Risks",
        "### Improvement Suggestions",
        "### Confidence Score:",
    )

    SAMPLE_FILES = (
        "review-brand-pr8.md",
        "review-bounty-pr2504.md",
        "review-bounty-pr2505.md",
    )

    PROOF_CRITERIA = (
        "CLI: `claude-review --pr <url>`",
        "GitHub Action workflow YAML",
        "Summary (2–3 sentences)",
        "Identified risks (list)",
        "Improvement suggestions (list)",
        "Confidence score (Low/Medium/High)",
        "Tested on ≥2 real GitHub PRs",
        "README with setup and usage",
    )

    def test_unit_tests_cover_edge_cases_and_error_handling(self):
        unit_test = AGENT_DIR / "tests" / "test_claude_review.py"
        text = unit_test.read_text(encoding="utf-8")
        required_cases = (
            "test_empty_diff_parses_no_files",
            "test_main_exits_when_no_token",
            "test_main_exits_on_invalid_token",
            "test_main_exits_on_invalid_pr_url",
            "test_main_exits_on_missing_diff_file",
            "test_fetch_pr_diff_returns_none_on_http_error",
            "test_gh_api_exits_on_auth_failure",
            "test_api_repo_path_url_encodes_special_characters",
            "test_truncates_changed_files_when_max_files_set",
        )
        for case in required_cases:
            self.assertIn(case, text, f"missing edge-case test {case}")

    def test_peer_review_hardening_helpers_present(self):
        text = (AGENT_DIR / "claude_review.py").read_text(encoding="utf-8")
        self.assertIn("def apply_max_files_cap(", text)
        self.assertIn("def _api_repo_path(", text)
        self.assertIn("urllib.parse.quote", text)
        self.assertIn("apply_max_files_cap(metadata, args.max_files)", text)

    def test_repo_root_cli_exists(self):
        cli = REPO_ROOT / "claude-review"
        self.assertTrue(cli.is_file())
        self.assertTrue(cli.stat().st_mode & 0o111)

    def test_cli_help_documents_pr_flag(self):
        result = subprocess.run(
            [str(REPO_ROOT / "claude-review"), "--help"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            check=True,
        )
        self.assertIn("--pr", result.stdout)
        self.assertIn("--post-comment", result.stdout)

    def test_github_action_workflow_exists(self):
        workflow = AGENT_DIR / ".github/workflows/claude-review.yml"
        self.assertTrue(workflow.is_file())
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("pull_request:", text)
        self.assertIn("--post", text)

    def test_ci_workflow_uses_pull_request_trigger(self):
        workflow = REPO_ROOT / ".github/workflows/test-claude-review.yml"
        self.assertTrue(workflow.is_file())
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("pull_request:", text)
        self.assertNotIn("pull_request_target", text, "CI must not use pull_request_target")

    def test_ci_workflow_runs_local_checks_script(self):
        workflow = REPO_ROOT / ".github/workflows/test-claude-review.yml"
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("run-ci-checks.sh", text)

    def test_ci_workflow_fetches_full_git_history(self):
        """Branch attribution scan needs merge-base; shallow checkout breaks peer review."""
        workflow = REPO_ROOT / ".github/workflows/test-claude-review.yml"
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("fetch-depth: 0", text)

    def test_branch_diff_scoped_to_claude_review_only(self):
        """PR must not include unrelated repo paths (e.g. hooks/ or internal/)."""
        base_ref = resolve_branch_diff_base_ref()
        changed = list_branch_changed_files(base_ref)

        allowed_prefixes = (
            "agents/claude-review/",
            "claude-review",
            ".github/workflows/test-claude-review.yml",
            "Makefile",
            "package.json",
            "package-lock.json",
            ".gitignore",
        )
        for path in changed:
            self.assertFalse(
                path.startswith("internal/"),
                f"unrelated path in PR diff: {path!r}",
            )
            self.assertFalse(
                path.startswith("hooks/"),
                f"unrelated path in PR diff: {path!r}",
            )
            self.assertTrue(
                any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in allowed_prefixes),
                f"branch diff includes out-of-scope path: {path}",
            )

    def test_run_ci_checks_script_exists_and_is_executable(self):
        self.assertTrue(CI_SCRIPT.is_file())
        self.assertTrue(CI_SCRIPT.stat().st_mode & 0o111)

    def test_run_ci_checks_guards_attribution_and_peer_review(self):
        script = CI_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("peer review acceptance tests passed", script)
        self.assertIn("git log -1 --format='%B'", script)
        self.assertIn("Ran ${peer_review_tests} tests — OK", script)
        self.assertIn("Forbidden agent attribution trailer found in HEAD commit message", script)

    def test_ci_workflow_triggers_on_test_entry_points(self):
        workflow = (REPO_ROOT / ".github/workflows/test-claude-review.yml").read_text(encoding="utf-8")
        for path in ("Makefile", "package.json", "package-lock.json", ".gitignore"):
            self.assertIn(path, workflow, f"CI must trigger on {path}")

    def test_repo_root_test_entry_points_delegate_to_ci_runner(self):
        package_json = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))
        makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
        gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("run-ci-checks.sh", package_json["scripts"]["test"])
        self.assertIn("run-ci-checks.sh", package_json["scripts"]["test:ci"])
        self.assertIn("run-ci-checks.sh", makefile)
        self.assertIn("ci-validate:", makefile)
        self.assertTrue((REPO_ROOT / "package-lock.json").is_file())
        self.assertIn("node_modules/", gitignore)
        self.assertIn("internal/", gitignore)

    def test_ci_runner_includes_delivery_verification_suite(self):
        ci_script = (AGENT_DIR / "tests" / "run-ci-checks.sh").read_text(encoding="utf-8")
        self.assertIn("test_delivery_verification.py", ci_script)
        self.assertIn("delivery verification tests", ci_script)
        self.assertIn("peer review acceptance tests passed", ci_script)

    def test_sub_agent_definition_has_required_sections(self):
        agent_md = AGENT_DIR / ".claude/agents/claude-review.md"
        self.assertTrue(agent_md.is_file())
        text = agent_md.read_text(encoding="utf-8")
        for section in self.REQUIRED_SECTIONS:
            self.assertIn(section, text, f"agent definition missing {section}")
        self.assertIn("claude-review --pr", text)

    def test_sample_outputs_cover_three_real_prs(self):
        samples_dir = AGENT_DIR / "samples"
        for name in self.SAMPLE_FILES:
            self.assertTrue((samples_dir / name).is_file(), f"missing sample {name}")

    def test_sample_outputs_have_required_sections(self):
        samples_dir = AGENT_DIR / "samples"
        for name in self.SAMPLE_FILES:
            text = (samples_dir / name).read_text(encoding="utf-8")
            for section in self.REQUIRED_SECTIONS:
                self.assertIn(section, text, f"{name} missing {section}")
            self.assertRegex(text, r"\*\*\[(HIGH|MEDIUM|LOW)\]\*\*")

    def test_readme_documents_cli_and_action(self):
        readme = (AGENT_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("claude-review --pr", readme)
        self.assertIn("GitHub Action", readme)
        self.assertIn("run-ci-checks.sh", readme)
        self.assertIn("Attribution guards", readme)

    def test_readme_documents_fork_pr_post_limitation(self):
        readme = (AGENT_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("fork-originated pull requests", readme)
        self.assertIn("HTTP 403", readme)

    def test_proof_maps_acceptance_criteria(self):
        proof = (AGENT_DIR / "PROOF.md").read_text(encoding="utf-8")
        for criterion in self.PROOF_CRITERIA:
            self.assertIn(criterion, proof, f"PROOF.md missing {criterion}")

    def test_repo_root_cli_reviews_local_diff(self):
        diff = textwrap.dedent(
            """\
            diff --git a/src/app.py b/src/app.py
            index 1234567..abcdefg 100644
            --- a/src/app.py
            +++ b/src/app.py
            @@ -1,3 +1,4 @@
             def hello():
            +    return "world"
                 pass
            """
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".diff", delete=False) as handle:
            handle.write(diff)
            diff_path = handle.name

        try:
            result = subprocess.run(
                [
                    str(REPO_ROOT / "claude-review"),
                    "--diff-file",
                    diff_path,
                    "--title",
                    "Add hello return value",
                ],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                check=True,
            )
        finally:
            Path(diff_path).unlink(missing_ok=True)

        output = result.stdout
        for section in self.REQUIRED_SECTIONS:
            self.assertIn(section, output, f"CLI output missing {section}")
        self.assertRegex(output, r"\*\*\[(HIGH|MEDIUM|LOW)\]\*\*")
        self.assertRegex(output, r"### Confidence Score: \*\*(Low|Medium|High)\*\*")
        self.assertIn("_Review generated by claude-review agent_", output)

    def test_cli_flags_high_severity_for_eval(self):
        diff = textwrap.dedent(
            """\
            diff --git a/run.py b/run.py
            index 1234567..abcdefg 100644
            --- a/run.py
            +++ b/run.py
            @@ -1 +1,2 @@
            +eval(user_input)
            """
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".diff", delete=False) as handle:
            handle.write(diff)
            diff_path = handle.name

        try:
            result = subprocess.run(
                [
                    str(REPO_ROOT / "claude-review"),
                    "--diff-file",
                    diff_path,
                    "--title",
                    "Dynamic execution helper",
                ],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                check=True,
            )
        finally:
            Path(diff_path).unlink(missing_ok=True)

        output = result.stdout
        self.assertIn("**[HIGH]**", output)
        self.assertRegex(output, r"(?i)eval|exec")


if __name__ == "__main__":
    unittest.main()
