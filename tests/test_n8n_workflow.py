import json
import unittest
from pathlib import Path


WORKFLOW_PATH = Path(__file__).resolve().parents[1] / "workflows" / "n8n-weekly-dev-summary.json"


class N8nWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))

    def test_workflow_has_required_nodes(self):
        node_names = {node["name"] for node in self.workflow["nodes"]}

        self.assertIn("Weekly Friday Trigger", node_names)
        self.assertIn("Fetch GitHub Activity", node_names)
        self.assertIn("Claude Summary", node_names)
        self.assertIn("Send Slack Summary", node_names)

    def test_workflow_uses_required_configuration(self):
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")

        for name in [
            "GITHUB_OWNER",
            "GITHUB_REPO",
            "GITHUB_TOKEN",
            "ANTHROPIC_API_KEY",
            "SLACK_WEBHOOK_URL",
            "SUMMARY_LANGUAGE",
        ]:
            self.assertIn(name, workflow_text)

    def test_workflow_fetches_required_github_activity(self):
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("/commits?since=", workflow_text)
        self.assertIn("/issues?state=closed", workflow_text)
        self.assertIn("/pulls?state=closed", workflow_text)

    def test_workflow_calls_claude_and_slack(self):
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("https://api.anthropic.com/v1/messages", workflow_text)
        self.assertIn("destinationWebhookUrl", workflow_text)

    def test_workflow_targets_required_claude_model(self):
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("claude-sonnet-4-20250514", workflow_text)

    def test_workflow_is_connected_to_delivery(self):
        connections = self.workflow["connections"]

        self.assertIn("Format Slack Payload", connections)
        delivery_targets = connections["Format Slack Payload"]["main"][0]
        self.assertEqual(delivery_targets[0]["node"], "Send Slack Summary")
