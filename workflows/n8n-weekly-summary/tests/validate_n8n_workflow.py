#!/usr/bin/env python3
"""
Automated validation test for n8n-weekly-dev-summary.json workflow.
Ensures JSON integrity, correct node configuration, and acceptance criteria compliance.
"""

import os
import json
import unittest

class TestN8nWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.json_path = os.path.join(base_dir, "n8n-weekly-dev-summary.json")
        cls.readme_path = os.path.join(base_dir, "README.md")
        cls.en_summary_path = os.path.join(base_dir, "examples", "sample-summary-en.md")
        cls.fr_summary_path = os.path.join(base_dir, "examples", "sample-summary-fr.md")

        with open(cls.json_path, "r", encoding="utf-8") as f:
            cls.data = json.load(f)

    def test_files_exist(self):
        self.assertTrue(os.path.exists(self.json_path))
        self.assertTrue(os.path.exists(self.readme_path))
        self.assertTrue(os.path.exists(self.en_summary_path))
        self.assertTrue(os.path.exists(self.fr_summary_path))

    def test_workflow_structure(self):
        self.assertIn("nodes", self.data)
        self.assertIn("connections", self.data)
        self.assertGreaterEqual(len(self.data["nodes"]), 6)

    def test_cron_trigger(self):
        trigger = next((n for n in self.data["nodes"] if "scheduleTrigger" in n["type"]), None)
        self.assertIsNotNone(trigger, "Schedule trigger node must be present")
        rule = trigger["parameters"]["rule"]["interval"][0]
        self.assertEqual(rule["expression"], "0 17 * * 5", "Cron must run Friday at 17:00")

    def test_claude_model_and_endpoint(self):
        claude_node = next((n for n in self.data["nodes"] if n["name"] == "Claude Weekly Narrative"), None)
        self.assertIsNotNone(claude_node)
        self.assertIn("api.anthropic.com/v1/messages", claude_node["parameters"]["url"])
        self.assertIn("claude-sonnet-4-20250514", json.dumps(self.data))

    def test_github_endpoints(self):
        node_urls = [n.get("parameters", {}).get("url", "") for n in self.data["nodes"]]
        has_commits = any("/commits" in u for u in node_urls)
        has_prs = any("/pulls" in u for u in node_urls)
        has_issues = any("/issues" in u for u in node_urls)

        self.assertTrue(has_commits, "Workflow must fetch commits")
        self.assertTrue(has_prs, "Workflow must fetch pull requests")
        self.assertTrue(has_issues, "Workflow must fetch closed issues")

if __name__ == "__main__":
    unittest.main()
