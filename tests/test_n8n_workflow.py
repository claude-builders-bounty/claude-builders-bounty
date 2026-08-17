#!/usr/bin/env python3
"""
Unit tests for n8n Weekly Dev Summary workflow JSON schema and logic.
Validates workflow integrity, node connections, Anthropic Messages API specs,
GitHub API parameters, and environment requirements.
"""

import json
import os
import unittest
from pathlib import Path

WORKFLOW_PATH = Path(__file__).parent.parent / "workflows" / "n8n-weekly-dev-summary.json"
SKILL_PATH = Path(__file__).parent.parent / "skills" / "weekly-summary" / "SKILL.md"
ENV_EXAMPLE_PATH = Path(__file__).parent.parent / ".env.example"


class TestN8nWorkflowSchema(unittest.TestCase):
    """Test suite for n8n Weekly Dev Summary Workflow."""

    @classmethod
    def setUpClass(cls):
        cls.assertTrue(WORKFLOW_PATH.exists(), f"Workflow file not found at {WORKFLOW_PATH}")
        with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
            cls.workflow = json.load(f)

    def test_workflow_top_level_keys(self):
        """Workflow JSON must contain mandatory n8n top-level properties."""
        self.assertIn("name", self.workflow)
        self.assertIn("nodes", self.workflow)
        self.assertIn("connections", self.workflow)
        self.assertIsInstance(self.workflow["nodes"], list)
        self.assertIsInstance(self.workflow["connections"], dict)

    def test_cron_trigger_node_configuration(self):
        """Workflow must contain a schedule trigger scheduled for weekly Monday runs."""
        trigger_nodes = [n for n in self.workflow["nodes"] if n.get("type") == "n8n-nodes-base.scheduleTrigger"]
        self.assertEqual(len(trigger_nodes), 1, "Expected exactly 1 scheduleTrigger node.")
        trigger = trigger_nodes[0]
        rule = trigger.get("parameters", {}).get("rule", {})
        interval = rule.get("interval", [])
        self.assertTrue(len(interval) > 0)
        cron_expr = interval[0].get("expression")
        self.assertEqual(cron_expr, "0 9 * * 1", "Cron trigger should run Mondays at 9:00 AM")

    def test_github_api_nodes(self):
        """Workflow must contain GitHub REST API nodes for commits and pull requests."""
        http_nodes = [n for n in self.workflow["nodes"] if n.get("type") == "n8n-nodes-base.httpRequest"]
        node_names = {n.get("name") for n in http_nodes}

        self.assertIn("Fetch Recent Commits", node_names)
        self.assertIn("Fetch Merged PRs", node_names)

        commit_node = next(n for n in http_nodes if n.get("name") == "Fetch Recent Commits")
        self.assertIn("api.github.com", commit_node["parameters"]["url"])
        self.assertIn("commits", commit_node["parameters"]["url"])

        pr_node = next(n for n in http_nodes if n.get("name") == "Fetch Merged PRs")
        self.assertIn("api.github.com", pr_node["parameters"]["url"])
        self.assertIn("pulls", pr_node["parameters"]["url"])

    def test_claude_api_node_configuration(self):
        """Workflow must include Claude / Anthropic Messages API node."""
        http_nodes = [n for n in self.workflow["nodes"] if n.get("type") == "n8n-nodes-base.httpRequest"]
        claude_nodes = [n for n in http_nodes if "Claude" in n.get("name", "")]
        self.assertTrue(len(claude_nodes) >= 1, "Claude API HTTP request node missing.")

        claude_node = claude_nodes[0]
        params = claude_node.get("parameters", {})
        self.assertEqual(params.get("method"), "POST")
        self.assertEqual(params.get("url"), "https://api.anthropic.com/v1/messages")

        headers = params.get("headerParameters", {}).get("parameters", [])
        header_names = {h.get("name").lower() for h in headers}
        self.assertIn("x-api-key", header_names)
        self.assertIn("anthropic-version", header_names)

        json_body = params.get("jsonBody", "")
        self.assertIn("claude-3-7-sonnet-20250219", json_body)
        self.assertIn("messages", json_body)

    def test_webhook_dispatch_node(self):
        """Workflow must dispatch formatted summaries to webhook."""
        http_nodes = [n for n in self.workflow["nodes"] if n.get("type") == "n8n-nodes-base.httpRequest"]
        dispatch_nodes = [n for n in http_nodes if "Webhook" in n.get("name", "")]
        self.assertTrue(len(dispatch_nodes) >= 1)
        dispatch_node = dispatch_nodes[0]
        self.assertEqual(dispatch_node["parameters"]["method"], "POST")
        self.assertIn("NOTIFICATION_WEBHOOK_URL", dispatch_node["parameters"]["url"])

    def test_node_connections_graph(self):
        """All nodes must be connected in a valid DAG."""
        nodes_dict = {n["name"]: n for n in self.workflow["nodes"]}
        connections = self.workflow["connections"]

        # Ensure start trigger connects to Date Window
        self.assertIn("Weekly Cron Trigger (Mondays 9AM)", connections)
        first_step = connections["Weekly Cron Trigger (Mondays 9AM)"]["main"][0][0]["node"]
        self.assertEqual(first_step, "Calculate Date Window (7 Days)")

        # Ensure all referenced connection targets exist in nodes
        for source_node, conn_data in connections.items():
            self.assertIn(source_node, nodes_dict, f"Connection source '{source_node}' does not exist in nodes.")
            for output_group in conn_data.get("main", []):
                for target in output_group:
                    target_name = target["node"]
                    self.assertIn(target_name, nodes_dict, f"Target node '{target_name}' not defined in workflow nodes.")

    def test_companion_documentation_exists(self):
        """Companion SKILL.md and .env.example must exist and contain required config keys."""
        self.assertTrue(SKILL_PATH.exists(), f"SKILL.md not found at {SKILL_PATH}")
        self.assertTrue(ENV_EXAMPLE_PATH.exists(), f".env.example not found at {ENV_EXAMPLE_PATH}")

        with open(ENV_EXAMPLE_PATH, "r", encoding="utf-8") as f:
            env_content = f.read()

        self.assertIn("GITHUB_REPO_OWNER", env_content)
        self.assertIn("GITHUB_REPO_NAME", env_content)
        self.assertIn("ANTHROPIC_API_KEY", env_content)
        self.assertIn("NOTIFICATION_WEBHOOK_URL", env_content)


if __name__ == "__main__":
    unittest.main()
