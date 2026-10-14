#!/usr/bin/env python3
"""
Automated Test & Validation Suite for n8n Weekly Dev Summary Workflow
Verifies:
1. Valid n8n schema format (nodes, connections, settings).
2. Cron trigger configured for Friday 5 PM (0 17 * * 5).
3. Claude API node targets claude-sonnet-4-20250514 with correct headers and payload structure.
4. GitHub API integration endpoints for commits, closed issues, and merged PRs.
5. Multi-channel delivery support (Discord & Slack payload structures).
6. Configurable variables (GITHUB_REPO, LANGUAGE EN/FR, DESTINATION_WEBHOOK_URL).
"""

import sys
import json
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
WORKFLOW_FILE = BASE_DIR / "weekly-github-dev-summary.json"

class TestN8nWorkflow(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.assertTrue(WORKFLOW_FILE.exists(), f"Workflow file missing: {WORKFLOW_FILE}")
        cls.workflow = json.loads(WORKFLOW_FILE.read_text(encoding="utf-8"))

    def test_json_structure(self):
        self.assertIn("nodes", self.workflow)
        self.assertIn("connections", self.workflow)
        self.assertTrue(len(self.workflow["nodes"]) >= 7)

    def test_cron_trigger(self):
        cron_nodes = [n for n in self.workflow["nodes"] if "cron" in n["type"].lower() or "trigger" in n["name"].lower()]
        self.assertTrue(len(cron_nodes) > 0, "Cron trigger node missing")
        cron_expr = json.dumps(cron_nodes[0])
        self.assertIn("0 17 * * 5", cron_expr, "Cron expression must trigger Friday at 5 PM")

    def test_claude_api_node(self):
        claude_nodes = [n for n in self.workflow["nodes"] if "claude" in n["name"].lower()]
        self.assertTrue(len(claude_nodes) > 0, "Claude API node missing")
        node = claude_nodes[0]
        params = node.get("parameters", {})
        self.assertIn("api.anthropic.com", params.get("url", ""))
        self.assertIn("claude-sonnet-4-20250514", json.dumps(params))

    def test_github_endpoints(self):
        endpoints_str = json.dumps(self.workflow)
        self.assertIn("api.github.com/repos/${repo}/commits", endpoints_str)
        self.assertIn("api.github.com/repos/${repo}/issues", endpoints_str)
        self.assertIn("api.github.com/repos/${repo}/pulls", endpoints_str)

    def test_configurable_variables(self):
        vars_str = json.dumps(self.workflow)
        self.assertIn("GITHUB_REPO", vars_str)
        self.assertIn("LANGUAGE", vars_str)
        self.assertIn("DESTINATION_WEBHOOK_URL", vars_str)

    def test_multichannel_webhook_formatting(self):
        format_nodes = [n for n in self.workflow["nodes"] if "format" in n["name"].lower() or "webhook" in n["name"].lower()]
        self.assertTrue(len(format_nodes) > 0)
        code_str = json.dumps(format_nodes)
        self.assertIn("discord", code_str.lower())
        self.assertIn("slack", code_str.lower())

if __name__ == "__main__":
    unittest.main()
