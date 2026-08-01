import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "workflows" / "n8n-weekly-dev-summary.json"
VALIDATOR = ROOT / "scripts" / "validate_n8n_workflow.py"


class N8nWorkflowTests(unittest.TestCase):
    def test_workflow_contains_required_nodes(self):
        workflow = json.loads(WORKFLOW.read_text())
        node_names = {node["name"] for node in workflow["nodes"]}

        self.assertIn("Weekly Friday 5pm", node_names)
        self.assertIn("Fetch Commits", node_names)
        self.assertIn("Fetch Closed Issues", node_names)
        self.assertIn("Fetch Closed PRs", node_names)
        self.assertIn("Claude Summary", node_names)
        self.assertIn("Send Email", node_names)

    def test_workflow_exposes_configurable_environment_inputs(self):
        raw = WORKFLOW.read_text()

        self.assertIn("GITHUB_REPO", raw)
        self.assertIn("GITHUB_TOKEN", raw)
        self.assertIn("ANTHROPIC_API_KEY", raw)
        self.assertIn("SUMMARY_EMAIL_TO", raw)
        self.assertIn("SUMMARY_LANGUAGE", raw)
        self.assertIn("claude-sonnet-4-20250514", raw)

    def test_workflow_validator_passes_static_checks(self):
        result = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("workflow OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
