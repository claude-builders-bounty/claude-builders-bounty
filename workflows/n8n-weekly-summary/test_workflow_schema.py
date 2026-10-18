#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation script for n8n weekly summary workflow JSON
======================================================
"""

import json
import unittest
from pathlib import Path

class TestN8nWorkflow(unittest.TestCase):
    def test_workflow_structure(self):
        wf_path = Path(__file__).resolve().parent / "github_weekly_summary.json"
        self.assertTrue(wf_path.exists(), "Workflow JSON file must exist.")
        
        with open(wf_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("nodes", data)
        self.assertIn("connections", data)
        self.assertGreaterEqual(len(data["nodes"]), 7)

        node_names = [n["name"] for n in data["nodes"]]
        self.assertIn("Weekly Schedule (Friday 5PM)", node_names)
        self.assertIn("Set Configuration", node_names)
        self.assertIn("Fetch Weekly Commits", node_names)
        self.assertIn("Fetch Closed Issues", node_names)
        self.assertIn("Fetch Merged PRs", node_names)
        self.assertIn("Generate Narrative via Claude API", node_names)
        self.assertIn("Dispatch to Discord/Slack Webhook", node_names)

        # Check unique node IDs
        ids = [n["id"] for n in data["nodes"]]
        self.assertEqual(len(ids), len(set(ids)), "Node IDs must be unique.")

if __name__ == "__main__":
    unittest.main()
