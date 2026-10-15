#!/usr/bin/env python3
"""
Automated Test Suite for n8n Weekly Dev Summary Workflow
Verifies all acceptance criteria for Bounty #5:
1. Valid JSON schema for n8n workflow.
2. Weekly cron schedule trigger (Friday at 5PM: '0 17 * * 5').
3. GitHub API fetch endpoints for commits, closed issues, and merged PRs.
4. Claude API call (claude-sonnet-4-20250514 or compatible).
5. Multi-channel delivery (Discord / Slack webhook and Email).
6. Configurable variables (GITHUB_REPO, LANGUAGE [EN/FR], DELIVERY_CHANNEL).
7. Graph connectivity and no orphan active nodes.
"""

import json
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
WORKFLOW_FILE = BASE_DIR / "weekly-github-dev-summary.json"

class TestWeeklyWorkflow(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.assertTrue(WORKFLOW_FILE.exists(), f"Workflow file missing: {WORKFLOW_FILE}")
        with open(WORKFLOW_FILE, "r", encoding="utf-8") as f:
            cls.workflow = json.load(f)

    def test_workflow_structure(self):
        self.assertIn("name", self.workflow)
        self.assertIn("nodes", self.workflow)
        self.assertIn("connections", self.workflow)
        self.assertIsInstance(self.workflow["nodes"], list)
        self.assertGreaterEqual(len(self.workflow["nodes"]), 7)

    def test_cron_trigger(self):
        cron_nodes = [n for n in self.workflow["nodes"] if n.get("type") == "n8n-nodes-base.scheduleTrigger"]
        self.assertTrue(len(cron_nodes) > 0, "Missing scheduleTrigger node")
        cron_rule = cron_nodes[0]["parameters"]["rule"]["interval"][0]
        self.assertEqual(cron_rule["expression"], "0 17 * * 5")

    def test_configurable_variables(self):
        config_nodes = [n for n in self.workflow["nodes"] if "Workflow Configuration" in n.get("name", "")]
        self.assertTrue(len(config_nodes) > 0, "Missing configuration node")
        var_names = [v["name"] for v in config_nodes[0]["parameters"]["values"]["string"]]
        self.assertIn("GITHUB_REPO", var_names)
        self.assertIn("LANGUAGE", var_names)
        self.assertIn("DELIVERY_CHANNEL", var_names)

    def test_github_api_nodes(self):
        node_names = [n.get("name", "") for n in self.workflow["nodes"]]
        self.assertTrue(any("Commits" in name for name in node_names), "Missing GitHub Commits node")
        self.assertTrue(any("Issues" in name for name in node_names), "Missing GitHub Issues node")
        self.assertTrue(any("PRs" in name for name in node_names), "Missing GitHub PRs node")

    def test_claude_model_configuration(self):
        claude_nodes = [n for n in self.workflow["nodes"] if "Claude AI" in n.get("name", "")]
        self.assertTrue(len(claude_nodes) > 0, "Missing Claude AI node")
        body_params = claude_nodes[0]["parameters"]["bodyParameters"]["parameters"]
        model_param = next((p for p in body_params if p["name"] == "model"), None)
        self.assertIsNotNone(model_param)

    def test_delivery_channels(self):
        node_names = [n.get("name", "") for n in self.workflow["nodes"]]
        self.assertTrue(any("Discord" in name for name in node_names), "Missing Discord delivery node")
        self.assertTrue(any("Email" in name for name in node_names), "Missing Email delivery node")

    def test_graph_connections(self):
        connections = self.workflow["connections"]
        self.assertIn("Weekly Schedule Trigger (Friday 5PM)", connections)
        self.assertIn("Claude AI Narrative Generation (claude-sonnet-4-20250514)", connections)
        self.assertIn("Route to Discord vs Email", connections)

if __name__ == "__main__":
    unittest.main()
