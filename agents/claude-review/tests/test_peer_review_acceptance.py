#!/usr/bin/env python3
"""Peer-review acceptance cases for bounty #4 claude-review agent."""

from __future__ import annotations

import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]


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
