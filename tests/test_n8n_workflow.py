import json
import os
import unittest

WORKFLOW_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "workflows", "n8n-weekly-dev-summary", "workflow.json")
)


class TestN8nWeeklySummaryWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
            cls.workflow = json.load(f)

    def test_valid_n8n_export_structure(self):
        self.assertIn("name", self.workflow)
        self.assertIn("nodes", self.workflow)
        self.assertIn("connections", self.workflow)
        self.assertEqual(len(self.workflow["nodes"]), 8)

    def test_weekly_cron_trigger(self):
        trigger = self.workflow["nodes"][0]
        self.assertEqual(trigger["type"], "n8n-nodes-base.scheduleTrigger")
        cron_expr = trigger["parameters"]["rule"]["interval"][0]["expression"]
        self.assertEqual(cron_expr, "0 17 * * 5")

    def test_configurable_variables_present(self):
        cfg_node = self.workflow["nodes"][1]
        names = {a["name"] for a in cfg_node["parameters"]["assignments"]["assignments"]}
        self.assertIn("github_repo", names)
        self.assertIn("destination_channel", names)
        self.assertIn("language", names)
        self.assertIn("webhook_url", names)

    def test_github_api_endpoints_and_claude_model(self):
        urls = [n["parameters"].get("url", "") for n in self.workflow["nodes"]]
        self.assertTrue(any("/commits" in u for u in urls))
        self.assertTrue(any("/issues" in u for u in urls))
        self.assertTrue(any("/pulls" in u for u in urls))

        claude_node = next(
            n for n in self.workflow["nodes"] if "anthropic.com/v1/messages" in n["parameters"].get("url", "")
        )
        self.assertIn("claude-sonnet-4-20250514", claude_node["parameters"]["jsonBody"])


if __name__ == "__main__":
    unittest.main()
