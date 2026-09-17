#!/usr/bin/env python3
"""
Validation test for n8n Weekly Dev Summary Workflow
Tests JSON syntax, required node types, graph connectivity, and configuration parameters.
"""

import json
import unittest
from pathlib import Path

WORKFLOW_FILE = Path(__file__).parent / "workflow.json"

class TestN8nWorkflow(unittest.TestCase):
    def setUp(self):
        with open(WORKFLOW_FILE, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def test_valid_json_structure(self):
        self.assertIn("nodes", self.data)
        self.assertIn("connections", self.data)
        self.assertGreater(len(self.data["nodes"]), 5)

    def test_required_nodes_exist(self):
        node_names = [n["name"] for n in self.data["nodes"]]
        expected_nodes = [
            "Weekly Trigger (Friday 5PM)",
            "Config Variables",
            "Compute Date Range",
            "Fetch Commits",
            "Fetch Closed Issues",
            "Fetch Merged PRs",
            "Aggregate & Format Prompt",
            "Call Claude API",
            "Deliver via Webhook"
        ]
        for expected in expected_nodes:
            self.assertIn(expected, node_names)

    def test_cron_trigger_schedule(self):
        trigger_node = next(n for n in self.data["nodes"] if n["name"] == "Weekly Trigger (Friday 5PM)")
        interval = trigger_node["parameters"]["rule"]["interval"][0]
        self.assertEqual(interval["expression"], "0 17 * * 5")

    def test_claude_api_node_configuration(self):
        claude_node = next(n for n in self.data["nodes"] if n["name"] == "Call Claude API")
        self.assertEqual(claude_node["parameters"]["url"], "https://api.anthropic.com/v1/messages")
        self.assertIn("claude-sonnet-4-20250514", claude_node["parameters"]["jsonBody"])

    def test_connections_reachability(self):
        connections = self.data["connections"]
        self.assertIn("Weekly Trigger (Friday 5PM)", connections)
        self.assertIn("Call Claude API", connections)

if __name__ == "__main__":
    unittest.main()
