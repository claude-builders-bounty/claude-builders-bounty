#!/usr/bin/env python3
"""
Unit and Integration Tests for n8n Workflow Schema & Structure.
"""
import unittest
import json
import os

class TestN8nWorkflowSchema(unittest.TestCase):
    def setUp(self):
        self.workflow_path = "/root/bounty_submissions/n8n_claude_weekly_summary_200usd/workflows/weekly_dev_summary_n8n.json"
        self.assertTrue(os.path.exists(self.workflow_path), "Workflow file does not exist")
        with open(self.workflow_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def test_top_level_keys(self):
        self.assertIn("name", self.data)
        self.assertIn("nodes", self.data)
        self.assertIn("connections", self.data)
        self.assertIsInstance(self.data["nodes"], list)
        self.assertIsInstance(self.data["connections"], dict)

    def test_required_nodes_exist(self):
        node_names = [n["name"] for n in self.data["nodes"]]
        expected_nodes = [
            "Schedule Trigger (Friday 5 PM)",
            "Config & Environment",
            "Calculate Date Window",
            "Fetch Weekly Commits",
            "Fetch Closed PRs",
            "Fetch Closed Issues",
            "Synthesize & Prepare Claude Prompt",
            "Claude API (Generate Narrative)",
            "Format Multi-Channel Payloads",
            "Route: Discord?",
            "Send Discord Notification",
            "Send Slack Notification"
        ]
        for name in expected_nodes:
            self.assertIn(name, node_names, f"Missing required node: {name}")

    def test_schedule_trigger_configuration(self):
        trigger_node = next(n for n in self.data["nodes"] if n["name"] == "Schedule Trigger (Friday 5 PM)")
        cron = trigger_node["parameters"]["rule"]["interval"][0]["expression"]
        self.assertEqual(cron, "0 17 * * 5", "Cron must trigger at 5 PM on Fridays")

    def test_claude_node_configuration(self):
        claude_node = next(n for n in self.data["nodes"] if n["name"] == "Claude API (Generate Narrative)")
        self.assertEqual(claude_node["parameters"]["url"], "https://api.anthropic.com/v1/messages")
        self.assertEqual(claude_node["parameters"]["method"], "POST")
        headers = claude_node["parameters"]["headerParameters"]["parameters"]
        header_names = [h["name"] for h in headers]
        self.assertIn("x-api-key", header_names)
        self.assertIn("anthropic-version", header_names)

    def test_all_connections_reference_existing_nodes(self):
        node_names = {n["name"] for n in self.data["nodes"]}
        for source_node, conn_types in self.data["connections"].items():
            self.assertIn(source_node, node_names, f"Connection source node not found: {source_node}")
            for main_conns in conn_types.get("main", []):
                for conn in main_conns:
                    self.assertIn(conn["node"], node_names, f"Target node not found: {conn['node']}")

if __name__ == "__main__":
    unittest.main()
