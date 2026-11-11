import json
import unittest
import os

class TestN8nWorkflow(unittest.TestCase):
    def setUp(self):
        wf_path = os.path.join(os.path.dirname(__file__), "..", "workflows", "weekly-github-summary.json")
        with open(wf_path, "r", encoding="utf-8") as f:
            self.wf = json.load(f)

    def test_workflow_structure(self):
        self.assertIn("nodes", self.wf)
        self.assertIn("connections", self.wf)
        node_names = [n["name"] for n in self.wf["nodes"]]
        self.assertIn("Weekly Friday 5PM Trigger", node_names)
        self.assertIn("Set Config Variables", node_names)
        self.assertIn("Fetch Weekly Commits", node_names)
        self.assertIn("Fetch Closed Issues", node_names)
        self.assertIn("Call Claude Sonnet 4 API", node_names)
        self.assertIn("Deliver via Webhook", node_names)

    def test_claude_model_pinned(self):
        claude_node = next(n for n in self.wf["nodes"] if n["name"] == "Call Claude Sonnet 4 API")
        self.assertIn("claude-sonnet-4-20250514", claude_node["parameters"]["jsonBody"])

if __name__ == "__main__":
    unittest.main()
