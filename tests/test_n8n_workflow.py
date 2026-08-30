#!/usr/bin/env python3
import json
import unittest
from pathlib import Path

class TestN8nWorkflow(unittest.TestCase):
    def setUp(self):
        self.workflow_path = Path(__file__).resolve().parent.parent / "workflows" / "n8n-claude-weekly-dev-summary" / "workflow.json"
        self.assertTrue(self.workflow_path.exists(), "workflow.json must exist")
        with open(self.workflow_path, "r") as f:
            self.data = json.load(f)

    def test_json_validity_and_nodes(self):
        nodes = self.data.get("nodes", [])
        self.assertGreater(len(nodes), 4, "Must contain essential n8n processing nodes")

        node_names = [n["name"] for n in nodes]
        self.assertIn("Weekly Schedule (Friday 5PM)", node_names)
        self.assertIn("Config & Environment Variables", node_names)
        self.assertIn("Fetch Recent Commits", node_names)
        self.assertIn("Fetch Merged PRs", node_names)
        self.assertIn("Fetch Closed Issues", node_names)
        self.assertIn("Generate Narrative with Claude API", node_names)
        self.assertIn("Deliver via Webhook (Discord/Slack)", node_names)

    def test_claude_model_pinned(self):
        claude_node = next(n for n in self.data["nodes"] if n["name"] == "Generate Narrative with Claude API")
        json_body = claude_node["parameters"]["jsonBody"]
        self.assertIn("claude-sonnet-4-20250514", json_body)

if __name__ == "__main__":
    unittest.main()
