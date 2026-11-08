import json
import unittest
from pathlib import Path

WORKFLOW_PATH = Path(__file__).resolve().parent.parent / "weekly_dev_summary.json"


class TestN8nWorkflow(unittest.TestCase):
    def setUp(self):
        self.assertTrue(WORKFLOW_PATH.exists(), f"Workflow file missing: {WORKFLOW_PATH}")
        self.raw_content = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.data = json.loads(self.raw_content)

    def test_json_validity_and_root_structure(self):
        self.assertIn("name", self.data)
        self.assertIn("nodes", self.data)
        self.assertIn("connections", self.data)
        self.assertTrue(len(self.data["nodes"]) >= 7)

    def test_schedule_trigger_cron(self):
        schedule_nodes = [n for n in self.data["nodes"] if n.get("type") == "n8n-nodes-base.scheduleTrigger"]
        self.assertTrue(len(schedule_nodes) >= 1)
        cron_expr = schedule_nodes[0]["parameters"]["rule"]["interval"][0]["expression"]
        self.assertEqual(cron_expr, "0 17 * * 5", "Expected Friday 5pm cron trigger")

    def test_claude_api_node_parameters(self):
        claude_nodes = [n for n in self.data["nodes"] if "Claude" in n.get("name", "")]
        self.assertTrue(len(claude_nodes) >= 1)
        node = claude_nodes[0]
        self.assertEqual(node["parameters"]["method"], "POST")
        self.assertIn("api.anthropic.com", node["parameters"]["url"])
        self.assertIn("claude-sonnet-4-20250514", node["parameters"]["jsonBody"])

    def test_webhook_delivery_node(self):
        delivery_nodes = [n for n in self.data["nodes"] if "Webhook" in n.get("name", "")]
        self.assertTrue(len(delivery_nodes) >= 1)
        node = delivery_nodes[0]
        self.assertEqual(node["parameters"]["method"], "POST")

    def test_connections_graph_integrity(self):
        node_names = {n["name"] for n in self.data["nodes"]}
        connections = self.data["connections"]

        for source_node, conn_types in connections.items():
            self.assertIn(source_node, node_names, f"Connection source '{source_node}' not found in nodes list")
            for conn_type, outputs in conn_types.items():
                for output_group in outputs:
                    for target in output_group:
                        target_name = target.get("node")
                        self.assertIn(target_name, node_names, f"Connection target '{target_name}' not found in nodes list")


if __name__ == "__main__":
    unittest.main()
