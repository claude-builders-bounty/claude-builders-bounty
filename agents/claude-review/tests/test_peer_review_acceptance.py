#!/usr/bin/env python3
"""Peer-review acceptance cases for bounty #4 claude-review agent."""

import unittest
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]


class PeerReviewAcceptanceTests(unittest.TestCase):
    """Maps bounty #4 acceptance criteria to repo artifacts."""

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

    def test_github_action_workflow_exists(self):
        workflow = AGENT_DIR / ".github/workflows/claude-review.yml"
        self.assertTrue(workflow.is_file())
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("pull_request:", text)
        self.assertIn("--post", text)

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


if __name__ == "__main__":
    unittest.main()
