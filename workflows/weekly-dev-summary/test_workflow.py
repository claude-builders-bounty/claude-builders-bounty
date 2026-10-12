#!/usr/bin/env python3
"""
Test suite validating the n8n weekly dev summary workflow JSON schema and structure.
"""

import json
import unittest
from pathlib import Path

WORKFLOW_FILE = Path(__file__).parent / "weekly_dev_summary_n8n.json"

class TestN8nWorkflow(unittest.TestCase):
    def setUp(self):
        self.assertTrue(WORKFLOW_FILE.exists(), "weekly_dev_summary_n8n.json must exist")
        self.data = json.loads(WORKFLOW_FILE.read_text(encoding="utf-8"))

    def test_top_level_structure(self):
        self.assertIn("name", self.data)
        self.assertIn("nodes", self.data)
        self.assertIn("connections", self.data)
        self.assertIsInstance(self.data["nodes"], list)
        self.assertIsInstance(self.data["connections"], dict)

    def test_node_types_and_ids(self):
        node_names = [n["name"] for n in self.data["nodes"]]
        expected_nodes = [
            "Schedule Trigger (Friday 5PM)",
            "Workflow Configuration",
            "Fetch Commits",
            "Fetch Closed Issues",
            "Aggregate Activity & Build Prompt",
            "Generate Summary with Claude",
            "Deliver via Webhook (Discord/Slack)"
        ]
        for exp in expected_nodes:
            self.assertIn(exp, node_names)

    def test_schedule_cron_settings(self):
        trigger = next(n for n in self.data["nodes"] if "Schedule Trigger" in n["name"])
        rule = trigger["parameters"]["rule"]["interval"][0]
        self.assertEqual(rule["field"], "weeks")
        self.assertEqual(rule["triggerAtDay"], [5])  # Friday
        self.assertEqual(rule["triggerAtHour"], 17)  # 5 PM

    def test_claude_api_node(self):
        claude_node = next(n for n in self.data["nodes"] if "Generate Summary with Claude" in n["name"])
        self.assertEqual(claude_node["parameters"]["method"], "POST")
        self.assertEqual(claude_node["parameters"]["url"], "https://api.anthropic.com/v1/messages")

if __name__ == "__main__":
    unittest.main()
