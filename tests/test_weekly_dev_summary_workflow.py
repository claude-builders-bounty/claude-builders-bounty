#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "workflows" / "n8n-weekly-dev-summary" / "weekly-dev-summary.workflow.json"


class WeeklyDevSummaryWorkflowTests(unittest.TestCase):
    def test_workflow_has_required_nodes(self) -> None:
        workflow = json.loads(WORKFLOW.read_text(encoding="utf-8"))
        node_names = {node["name"] for node in workflow["nodes"]}

        self.assertIn("Weekly Schedule", node_names)
        self.assertIn("Fetch Commits", node_names)
        self.assertIn("Fetch Issues", node_names)
        self.assertIn("Fetch Pull Requests", node_names)
        self.assertIn("Claude Summary", node_names)
        self.assertIn("Send Slack Summary", node_names)

    def test_claude_prompt_requires_no_invention(self) -> None:
        workflow = json.loads(WORKFLOW.read_text(encoding="utf-8"))
        claude = next(node for node in workflow["nodes"] if node["name"] == "Claude Summary")
        body = claude["parameters"]["jsonBody"]

        self.assertIn("Do not invent facts", body)
        self.assertIn("Executive Summary", body)
        self.assertIn("Suggested Next Actions", body)


if __name__ == "__main__":
    unittest.main()
