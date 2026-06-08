#!/usr/bin/env python3
"""Peer-review acceptance cases for bounty #1 generate-changelog skill."""

from __future__ import annotations

import re
import subprocess
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]


class PeerReviewAcceptanceTests(unittest.TestCase):
    """Maps bounty #1 acceptance criteria to repo artifacts and CLI behavior."""

    PROOF_CRITERIA = (
        "/generate-changelog",
        "bash changelog.sh",
        "Fetches commits since last git tag",
        "Added",
        "Fixed",
        "Changed",
        "Removed",
        "samples/CHANGELOG.sample.md",
        "Quick start",
    )

    CHANGELOG_SECTIONS = ("Added", "Fixed", "Changed", "Removed")

    def test_skill_definition_enables_generate_changelog_command(self):
        skill_md = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: generate-changelog", skill_md)
        self.assertIn("bash changelog.sh", skill_md)

    def test_repo_root_changelog_sh_exists(self):
        cli = REPO_ROOT / "changelog.sh"
        self.assertTrue(cli.is_file())
        text = cli.read_text(encoding="utf-8")
        self.assertIn("skills/generate-changelog/changelog.sh", text)

    def test_changelog_help_documents_since_and_preview(self):
        result = subprocess.run(
            ["bash", str(SKILL_DIR / "changelog.sh"), "--help"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            check=True,
        )
        self.assertIn("--since", result.stdout)
        self.assertIn("--preview", result.stdout)
        self.assertIn("--append", result.stdout)

    def test_sample_output_has_required_sections(self):
        sample = (SKILL_DIR / "samples" / "CHANGELOG.sample.md").read_text(encoding="utf-8")
        self.assertIn("# Changelog", sample)
        self.assertIn("## [", sample)
        self.assertRegex(sample, r"- \d{4}-\d{2}-\d{2}")
        found = [section for section in self.CHANGELOG_SECTIONS if f"### {section}" in sample]
        self.assertGreaterEqual(len(found), 2, "sample should include at least two category sections")

    def test_readme_quick_start_is_three_steps_or_fewer(self):
        readme = (SKILL_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("Quick start", readme)
        steps = re.findall(r"^\d+\.\s", readme, re.M)
        self.assertGreaterEqual(len(steps), 3)
        self.assertLessEqual(len(steps), 3)

    def test_proof_maps_acceptance_criteria(self):
        proof = (SKILL_DIR / "PROOF.md").read_text(encoding="utf-8")
        for criterion in self.PROOF_CRITERIA:
            self.assertIn(criterion, proof, f"PROOF.md missing {criterion}")

    def test_changelog_fetches_commits_since_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
            (repo / "README").write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "add", "README"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "Initial commit"], cwd=repo, check=True)
            subprocess.run(["git", "tag", "v1.0.0"], cwd=repo, check=True)
            (repo / "feature.txt").write_text("feature\n", encoding="utf-8")
            subprocess.run(["git", "add", "feature.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "feat: tagged feature"], cwd=repo, check=True)
            (repo / "fix.txt").write_text("fix\n", encoding="utf-8")
            subprocess.run(["git", "add", "fix.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "fix: tagged bug"], cwd=repo, check=True)

            output = Path(tmp) / "CHANGELOG.md"
            subprocess.run(
                [
                    "bash",
                    str(SKILL_DIR / "changelog.sh"),
                    str(repo),
                    "--output",
                    str(output),
                ],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
            )
            text = output.read_text(encoding="utf-8")
            self.assertIn("### Added", text)
            self.assertIn("### Fixed", text)
            self.assertIn("tagged feature", text)
            self.assertIn("tagged bug", text)
            self.assertNotIn("Initial commit", text)

    def test_repo_root_wrapper_delegates_to_skill_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
            (repo / "README").write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "add", "README"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "Initial commit"], cwd=repo, check=True)
            subprocess.run(["git", "tag", "v1.0.0"], cwd=repo, check=True)
            (repo / "feature.txt").write_text("feature\n", encoding="utf-8")
            subprocess.run(["git", "add", "feature.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "feat: wrapper check"], cwd=repo, check=True)

            output = Path(tmp) / "CHANGELOG.md"
            subprocess.run(
                ["bash", str(REPO_ROOT / "changelog.sh"), str(repo), "--output", str(output)],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
            )
            text = output.read_text(encoding="utf-8")
            self.assertIn("wrapper check", text)


if __name__ == "__main__":
    unittest.main()
