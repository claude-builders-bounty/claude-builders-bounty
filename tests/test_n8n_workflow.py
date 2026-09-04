#!/usr/bin/env python3
"""
Automated Test Suite for n8n + Claude Weekly Summary Workflow.
"""

import sys
import os
import json
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
WORKFLOW_FILE = ROOT_DIR / "workflows" / "n8n-weekly-summary" / "github_weekly_summary.workflow.json"


class TestN8nWorkflow(unittest.TestCase):
    """Test n8n workflow JSON structure, nodes, and configurations."""

    def setUp(self):
        self.assertTrue(WORKFLOW_FILE.exists(), f"Workflow file not found at {WORKFLOW_FILE}")
        with open(WORKFLOW_FILE, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def test_valid_n8n_structure(self):
        self.assertIn("name", self.data)
        self.assertIn("nodes", self.data)
        self.assertIn("connections", self.data)
        self.assertIsInstance(self.data["nodes"], list)
        self.assertIsInstance(self.data["connections"], dict)

    def test_cron_trigger_node(self):
        nodes = {n["name"]: n for n in self.data["nodes"]}
        self.assertIn("Every Friday 5pm", nodes)
        cron_node = nodes["Every Friday 5pm"]
        self.assertEqual(cron_node["type"], "n8n-nodes-base.scheduleTrigger")
        cron_expr = cron_node["parameters"]["rule"]["interval"][0]["expression"]
        self.assertEqual(cron_expr, "0 17 * * 5")

    def test_github_fetch_nodes(self):
        nodes = {n["name"]: n for n in self.data["nodes"]}
        self.assertIn("Fetch Commits", nodes)
        self.assertIn("Fetch Closed Issues", nodes)
        self.assertIn("Fetch Merged PRs", nodes)

        # Check endpoints
        self.assertIn("/commits", nodes["Fetch Commits"]["parameters"]["url"])
        self.assertIn("/issues", nodes["Fetch Closed Issues"]["parameters"]["url"])
        self.assertIn("/pulls", nodes["Fetch Merged PRs"]["parameters"]["url"])

    def test_claude_api_node(self):
        nodes = {n["name"]: n for n in self.data["nodes"]}
        self.assertIn("Call Claude API", nodes)
        claude_node = nodes["Call Claude API"]
        self.assertEqual(claude_node["parameters"]["url"], "https://api.anthropic.com/v1/messages")
        self.assertIn("claude-sonnet-4-20250514", claude_node["parameters"]["body"])

    def test_configurable_variables(self):
        nodes = {n["name"]: n for n in self.data["nodes"]}
        self.assertIn("Config Variables", nodes)
        code = nodes["Config Variables"]["parameters"]["jsCode"]
        self.assertIn("GITHUB_OWNER", code)
        self.assertIn("GITHUB_REPO", code)
        self.assertIn("LANGUAGE", code)
        self.assertIn("DISCORD_URL", code)

    def test_delivery_node(self):
        nodes = {n["name"]: n for n in self.data["nodes"]}
        self.assertIn("Send to Discord", nodes)
        self.assertEqual(nodes["Send to Discord"]["parameters"]["method"], "POST")


if __name__ == "__main__":
    unittest.main()
