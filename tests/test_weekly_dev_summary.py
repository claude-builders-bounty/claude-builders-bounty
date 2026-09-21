import json
import unittest
import os

class TestWeeklyDevSummaryWorkflow(unittest.TestCase):
    def setUp(self):
        self.workflow_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "workflows",
            "weekly_dev_summary.json"
        )
        with open(self.workflow_path, "r") as f:
            self.data = json.load(f)

    def test_workflow_structure(self):
        self.assertIn("nodes", self.data)
        self.assertIn("connections", self.data)
        self.assertTrue(len(self.data["nodes"]) > 0)

    def test_schedule_trigger(self):
        schedule_nodes = [
            n for n in self.data["nodes"]
            if n.get("type") == "n8n-nodes-base.scheduleTrigger"
        ]
        self.assertEqual(len(schedule_nodes), 1)
        interval = schedule_nodes[0]["parameters"]["rule"]["interval"][0]
        self.assertEqual(interval["field"], "weeks")
        self.assertEqual(interval["triggerAtDay"], [5])
        self.assertEqual(interval["triggerAtHour"], 17)
        self.assertEqual(interval["triggerAtMinute"], 0)

    def test_claude_model_configuration(self):
        prompt_node = next(
            n for n in self.data["nodes"]
            if n.get("name") == "Format Data & Build Claude Prompt"
        )
        code = prompt_node["parameters"]["jsCode"]
        self.assertIn("claude-sonnet-4-20250514", code)
        self.assertIn("lang === \"FR\"", code)

    def test_configurable_variables(self):
        config_node = next(
            n for n in self.data["nodes"]
            if n.get("name") == "Set Configuration"
        )
        code = config_node["parameters"]["jsCode"]
        for var in ["GITHUB_OWNER", "GITHUB_REPO", "WEBHOOK_URL", "LANGUAGE", "ANTHROPIC_API_KEY"]:
            self.assertIn(var, code)

if __name__ == "__main__":
    unittest.main()
