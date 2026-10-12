import json
import os
import unittest

class TestN8nWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        workflow_path = os.path.join(os.path.dirname(__file__), "weekly_dev_summary.json")
        with open(workflow_path, "r", encoding="utf-8") as f:
            cls.workflow = json.load(f)
        cls.nodes_by_name = {n["name"]: n for n in cls.workflow["nodes"]}

    def test_json_valid_and_has_nodes(self):
        self.assertIn("nodes", self.workflow)
        self.assertIn("connections", self.workflow)
        self.assertGreater(len(self.workflow["nodes"]), 5)

    def test_weekly_cron_trigger(self):
        trigger = self.nodes_by_name.get("Weekly Schedule (Friday 5PM)")
        self.assertIsNotNone(trigger)
        self.assertEqual(trigger["type"], "n8n-nodes-base.scheduleTrigger")
        cron_expr = trigger["parameters"]["rule"]["interval"][0]["expression"]
        self.assertEqual(cron_expr, "0 17 * * 5")

    def test_configurable_variables(self):
        config_node = self.nodes_by_name.get("Configuration & Environment")
        self.assertIsNotNone(config_node)
        str_vars = {v["name"]: v["value"] for v in config_node["parameters"]["values"]["string"]}
        self.assertIn("github_repo_owner", str_vars)
        self.assertIn("github_repo_name", str_vars)
        self.assertIn("destination_channel", str_vars)
        self.assertIn("language", str_vars)
        self.assertIn("claude_model", str_vars)
        self.assertEqual(str_vars["claude_model"], "claude-sonnet-4-20250514")

    def test_github_api_endpoints(self):
        self.assertIn("Fetch Weekly Commits", self.nodes_by_name)
        self.assertIn("Fetch Closed Issues", self.nodes_by_name)
        self.assertIn("Fetch Closed PRs", self.nodes_by_name)
        
        commit_url = self.nodes_by_name["Fetch Weekly Commits"]["parameters"]["url"]
        self.assertIn("/commits", commit_url)
        issue_url = self.nodes_by_name["Fetch Closed Issues"]["parameters"]["url"]
        self.assertIn("/issues", issue_url)
        pr_url = self.nodes_by_name["Fetch Closed PRs"]["parameters"]["url"]
        self.assertIn("/pulls", pr_url)

    def test_claude_api_node(self):
        claude_node = self.nodes_by_name.get("Call Claude API (Sonnet)")
        self.assertIsNotNone(claude_node)
        self.assertEqual(claude_node["parameters"]["url"], "https://api.anthropic.com/v1/messages")
        body = claude_node["parameters"]["jsonBody"]
        self.assertIn("claude-sonnet-4-20250514", body)

    def test_notification_webhook(self):
        format_node = self.nodes_by_name.get("Format Webhook Payload")
        deliver_node = self.nodes_by_name.get("Deliver Discord/Slack Webhook")
        self.assertIsNotNone(format_node)
        self.assertIsNotNone(deliver_node)
        code = format_node["parameters"]["jsCode"]
        self.assertIn("slack", code)
        self.assertIn("discord", code)

if __name__ == "__main__":
    unittest.main()
