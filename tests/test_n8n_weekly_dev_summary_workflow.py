import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / "workflows" / "n8n-weekly-dev-summary" / "weekly-dev-summary.workflow.json"
README_PATH = ROOT / "workflows" / "n8n-weekly-dev-summary" / "README.md"
EVIDENCE_DIR = ROOT / "workflows" / "n8n-weekly-dev-summary" / "evidence"


class N8nWeeklyDevSummaryWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
        cls.workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
        cls.readme = README_PATH.read_text(encoding="utf-8")

    def test_workflow_is_importable_shape(self):
        self.assertIn("nodes", self.workflow)
        self.assertIn("connections", self.workflow)
        self.assertIn("settings", self.workflow)
        self.assertGreaterEqual(len(self.workflow["nodes"]), 8)

    def test_required_nodes_are_present(self):
        names = {node["name"]: node["type"] for node in self.workflow["nodes"]}

        self.assertEqual(names["Weekly Friday 5pm Trigger"], "n8n-nodes-base.scheduleTrigger")
        self.assertEqual(names["CLI Verification Trigger"], "n8n-nodes-base.executeWorkflowTrigger")
        self.assertEqual(names["Fetch Weekly Activity from GitHub API"], "n8n-nodes-base.code")
        self.assertEqual(names["Call Claude Sonnet 4 API"], "n8n-nodes-base.httpRequest")
        self.assertEqual(names["Deliver Summary to Discord Webhook"], "n8n-nodes-base.httpRequest")

    def test_workflow_satisfies_bounty_requirements(self):
        required_fragments = [
            "0 17 * * 5",
            "https://api.github.com/repos",
            "/commits",
            "/issues",
            "/pulls",
            "merged_at",
            "pull_request",
            "https://api.anthropic.com/v1/messages",
            "claude-sonnet-4-20250514",
            "SUMMARY_WEBHOOK_URL",
            "SUMMARY_LANGUAGE",
            "ANTHROPIC_BASE_URL",
        ]

        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.workflow_text)

    def test_connected_execution_path_is_present(self):
        connections = self.workflow["connections"]
        main_path = [
            ("Weekly Friday 5pm Trigger", "Build Config and Weekly Window"),
            ("Build Config and Weekly Window", "Fetch Weekly Activity from GitHub API"),
            ("Fetch Weekly Activity from GitHub API", "Build Claude Summary Request"),
            ("Build Claude Summary Request", "Call Claude Sonnet 4 API"),
            ("Call Claude Sonnet 4 API", "Build Discord Webhook Payload"),
            ("Build Discord Webhook Payload", "Deliver Summary to Discord Webhook"),
        ]

        for source, target in main_path:
            with self.subTest(source=source, target=target):
                outputs = connections[source]["main"][0]
                self.assertTrue(any(connection["node"] == target for connection in outputs))

    def test_secrets_are_not_hardcoded(self):
        forbidden_fragments = ["sk-ant-", "ghp_", "discord.com/api/webhooks/"]

        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, self.workflow_text)

    def test_readme_setup_is_five_steps_or_fewer(self):
        setup_section = self.readme.split("## Setup in 5 Steps", 1)[1].split("## Configuration", 1)[0]
        numbered_steps = [
            line for line in setup_section.splitlines()
            if line.strip().startswith(("1.", "2.", "3.", "4.", "5.", "6."))
        ]

        self.assertLessEqual(len(numbered_steps), 5)
        self.assertIn("ANTHROPIC_API_KEY", self.readme)
        self.assertIn("SUMMARY_WEBHOOK_URL", self.readme)

    def test_execution_evidence_files_are_committed(self):
        summary = EVIDENCE_DIR / "n8n-cli-execution-summary.txt"
        screenshot = EVIDENCE_DIR / "n8n-success-screenshot.png"

        self.assertTrue(summary.exists())
        self.assertIn("Execution success: true", summary.read_text(encoding="utf-8"))
        self.assertGreater(screenshot.stat().st_size, 10_000)


if __name__ == "__main__":
    unittest.main()
