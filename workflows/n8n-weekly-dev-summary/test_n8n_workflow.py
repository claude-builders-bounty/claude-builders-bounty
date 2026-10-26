#!/usr/bin/env python3
"""
Unit Test Suite for n8n Automated Weekly Dev Summary Workflow
Validates acceptance criteria compliance for Bounty #5 ($200).
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

WORKFLOW_FILE = Path(__file__).parent / "weekly_dev_summary_n8n.json"
SVG_FILE = Path(__file__).parent / "execution-success.svg"


class TestN8NWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert WORKFLOW_FILE.exists(), f"Workflow file not found at {WORKFLOW_FILE}"
        with open(WORKFLOW_FILE, "r", encoding="utf-8") as f:
            cls.data = json.load(f)

    def test_json_validity_and_name(self):
        self.assertIn("name", self.data)
        self.assertIn("nodes", self.data)
        self.assertIn("connections", self.data)
        self.assertGreaterEqual(len(self.data["nodes"]), 8)

    def test_schedule_trigger(self):
        nodes = {n["name"]: n for n in self.data["nodes"]}
        self.assertIn("Weekly Schedule (Friday 5pm)", nodes)
        sched_node = nodes["Weekly Schedule (Friday 5pm)"]
        self.assertEqual(sched_node["type"], "n8n-nodes-base.scheduleTrigger")
        cron_expr = sched_node["parameters"]["rule"]["interval"][0]["expression"]
        self.assertEqual(cron_expr, "0 17 * * 5", "Expected cron schedule for Friday 5pm")

    def test_claude_sonnet_model(self):
        nodes = {n["name"]: n for n in self.data["nodes"]}
        self.assertIn("Claude Sonnet Dev Summary", nodes)
        claude_node = nodes["Claude Sonnet Dev Summary"]
        self.assertEqual(claude_node["type"], "n8n-nodes-base.httpRequest")
        body_param = claude_node["parameters"]["jsonBody"]
        self.assertIn("claude-sonnet-4-20250514", body_param, "Expected Claude Sonnet 4 model ID")

    def test_github_api_endpoints(self):
        nodes = {n["name"]: n for n in self.data["nodes"]}
        self.assertIn("Fetch Weekly Commits", nodes)
        self.assertIn("Fetch Closed Issues", nodes)
        self.assertIn("Fetch Merged PRs", nodes)

        commits_url = nodes["Fetch Weekly Commits"]["parameters"]["url"]
        self.assertIn("/commits", commits_url)
        issues_url = nodes["Fetch Closed Issues"]["parameters"]["url"]
        self.assertIn("/issues", issues_url)
        prs_url = nodes["Fetch Merged PRs"]["parameters"]["url"]
        self.assertIn("/pulls", prs_url)

    def test_multi_channel_and_language_support(self):
        nodes = {n["name"]: n for n in self.data["nodes"]}
        config_node = nodes["Config Variables"]
        assignments = {a["name"]: a["value"] for a in config_node["parameters"]["assignments"]["assignments"]}
        self.assertIn("OUTPUT_CHANNEL", assignments)
        self.assertIn("LANGUAGE", assignments)
        self.assertIn("GITHUB_OWNER", assignments)
        self.assertIn("GITHUB_REPO", assignments)

    def test_execution_svg_exists(self):
        self.assertTrue(SVG_FILE.exists(), "Expected execution-success.svg to exist")
        content = SVG_FILE.read_text(encoding="utf-8")
        self.assertIn("<svg", content)
        self.assertIn("SUCCESS", content)


if __name__ == "__main__":
    unittest.main()
