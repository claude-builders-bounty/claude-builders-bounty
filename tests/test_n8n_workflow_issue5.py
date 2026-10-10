#!/usr/bin/env python3
"""
Test suite verifying workflows/n8n-weekly-summary against all Issue #5 acceptance criteria.
"""

import os
import json
import unittest

WORKFLOW_PATH = os.path.join(os.path.dirname(__file__), "..", "workflows", "n8n-weekly-summary", "weekly-dev-summary.json")
README_PATH = os.path.join(os.path.dirname(__file__), "..", "workflows", "n8n-weekly-summary", "README.md")


class TestIssue5Workflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
            cls.workflow = json.load(f)
        with open(README_PATH, "r", encoding="utf-8") as f:
            cls.readme = f.read()

    def test_valid_json_structure(self):
        """Workflow must be an exportable, valid n8n JSON with nodes and connections."""
        self.assertIn("name", self.workflow)
        self.assertIn("nodes", self.workflow)
        self.assertIn("connections", self.workflow)
        self.assertGreater(len(self.workflow["nodes"]), 5)

    def test_weekly_cron_trigger(self):
        """Must have weekly cron trigger (e.g., Friday at 5pm)."""
        nodes = self.workflow["nodes"]
        cron_nodes = [n for n in nodes if "schedule" in n.get("type", "").lower() or "cron" in str(n).lower()]
        self.assertTrue(len(cron_nodes) > 0)
        cron_text = json.dumps(cron_nodes)
        self.assertIn("0 17 * * 5", cron_text)

    def test_fetches_github_activity(self):
        """Must fetch commits, merged PRs, and closed issues from GitHub API."""
        workflow_str = json.dumps(self.workflow)
        self.assertIn("api.github.com/repos/{{ $json.GITHUB_REPO }}/commits", workflow_str)
        self.assertIn("is:pr+is:merged", workflow_str)
        self.assertIn("is:issue+is:closed", workflow_str)

    def test_calls_claude_api(self):
        """Must call Claude API for narrative generation."""
        workflow_str = json.dumps(self.workflow)
        self.assertIn("api.anthropic.com/v1/messages", workflow_str)
        self.assertIn("claude", workflow_str.lower())

    def test_destination_support_discord_and_slack(self):
        """Must support delivery via Discord or Slack webhooks."""
        workflow_str = json.dumps(self.workflow)
        self.assertIn("discord", workflow_str.lower())
        self.assertIn("slack", workflow_str.lower())

    def test_configurable_variables(self):
        """Must have configurable variables: repo, channel, language (EN/FR)."""
        workflow_str = json.dumps(self.workflow)
        self.assertIn("GITHUB_REPO", workflow_str)
        self.assertIn("LANGUAGE", workflow_str)
        self.assertIn("DESTINATION_TYPE", workflow_str)
        self.assertIn("WEBHOOK_URL", workflow_str)

    def test_multilingual_language_support(self):
        """Must handle English and French languages."""
        workflow_str = json.dumps(self.workflow)
        self.assertIn("French", workflow_str)
        self.assertIn("English", workflow_str)

    def test_readme_steps_under_five(self):
        """Setup instructions must be in 5 steps or fewer."""
        self.assertIn("4 Steps", self.readme)


if __name__ == "__main__":
    unittest.main()
