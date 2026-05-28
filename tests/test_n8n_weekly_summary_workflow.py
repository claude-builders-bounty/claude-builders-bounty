import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "workflows" / "n8n-weekly-dev-summary.json"


class N8nWeeklySummaryWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = json.loads(WORKFLOW.read_text(encoding="utf-8"))
        self.nodes = {node["name"]: node for node in self.workflow["nodes"]}
        self.workflow_text = WORKFLOW.read_text(encoding="utf-8")

    def test_required_nodes_are_present(self) -> None:
        for name in (
            "Weekly Friday 5pm",
            "Fetch commits",
            "Fetch closed issues",
            "Fetch merged PRs",
            "Generate summary with Claude",
            "Send Slack or Discord webhook",
            "Send email",
        ):
            self.assertIn(name, self.nodes)

    def test_weekly_trigger_is_friday_at_5pm(self) -> None:
        interval = self.nodes["Weekly Friday 5pm"]["parameters"]["rule"]["interval"][0]
        self.assertEqual(interval["field"], "weeks")
        self.assertEqual(interval["triggerAtDay"], [5])
        self.assertEqual(interval["triggerAtHour"], 17)

    def test_configurable_variables_and_model_are_present(self) -> None:
        for phrase in (
            "GITHUB_REPO",
            "GITHUB_TOKEN",
            "ANTHROPIC_API_KEY",
            "SUMMARY_LANGUAGE",
            "DELIVERY_MODE",
            "DESTINATION_WEBHOOK_URL",
            "DESTINATION_EMAIL",
            "claude-sonnet-4-20250514",
        ):
            self.assertIn(phrase, self.workflow_text)

    def test_connections_reach_delivery_nodes(self) -> None:
        connections = self.workflow["connections"]
        self.assertIn("Deliver by webhook?", connections)
        delivery_targets = [
            output["node"]
            for branch in connections["Deliver by webhook?"]["main"]
            for output in branch
        ]
        self.assertIn("Send Slack or Discord webhook", delivery_targets)
        self.assertIn("Send email", delivery_targets)


if __name__ == "__main__":
    unittest.main()
