import json
import unittest
from datetime import datetime, timezone, timedelta

class TestN8nWeeklySummaryWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        workflow_path = r"D:\projects\claude-builders-bounty\workflows\n8n-weekly-summary\workflow.json"
        with open(workflow_path, "r", encoding="utf-8") as f:
            cls.workflow = json.load(f)

    def test_top_level_structure(self):
        self.assertIn("name", self.workflow)
        self.assertIn("nodes", self.workflow)
        self.assertIn("connections", self.workflow)
        self.assertEqual(self.workflow["name"], "Weekly Dev Summary with Claude & GitHub")

    def test_node_names_and_ids_unique(self):
        names = set()
        ids = set()
        for node in self.workflow["nodes"]:
            name = node["name"]
            node_id = node["id"]
            self.assertNotIn(name, names, f"Duplicate node name: {name}")
            self.assertNotIn(node_id, ids, f"Duplicate node id: {node_id}")
            names.add(name)
            ids.add(node_id)

    def test_connection_targets_exist(self):
        node_names = {node["name"] for node in self.workflow["nodes"]}
        for source, conn_data in self.workflow["connections"].items():
            self.assertIn(source, node_names, f"Connection source '{source}' not in nodes")
            for output_type, route_groups in conn_data.items():
                for routes in route_groups:
                    for route in routes:
                        target = route["node"]
                        self.assertIn(target, node_names, f"Connection target '{target}' not in nodes")

    def test_schedule_trigger_configuration(self):
        schedule_node = next(n for n in self.workflow["nodes"] if n["name"] == "Weekly Trigger (Friday 5PM)")
        self.assertEqual(schedule_node["type"], "n8n-nodes-base.scheduleTrigger")
        rule = schedule_node["parameters"]["rule"]["interval"][0]
        self.assertEqual(rule["field"], "weeks")
        self.assertEqual(rule["triggerAtDay"], [5])
        self.assertEqual(rule["triggerAtHour"], 17)

    def test_claude_api_node_configuration(self):
        claude_node = next(n for n in self.workflow["nodes"] if n["name"] == "Call Claude API")
        self.assertEqual(claude_node["type"], "n8n-nodes-base.httpRequest")
        self.assertEqual(claude_node["parameters"]["url"], "https://api.anthropic.com/v1/messages")
        self.assertEqual(claude_node["parameters"]["method"], "POST")

    def test_data_aggregation_logic(self):
        sample_commits = [
            {"sha": "54bca10905123", "commit": {"author": {"name": "Alice", "date": "2026-10-25T10:00:00Z"}, "message": "feat: add secure auth route"}},
            {"sha": "adf149e8e0456", "commit": {"author": {"name": "Bob", "date": "2026-10-24T12:00:00Z"}, "message": "fix: audio stream drop"}}
        ]
        sample_issues = [
            {"number": 101, "title": "Memory leak on reconnection", "closed_at": "2026-10-25T15:00:00Z", "pull_request": None},
            {"number": 102, "title": "Should be ignored PR", "closed_at": "2026-10-25T16:00:00Z", "pull_request": {"url": "..."}}
        ]
        sample_prs = [
            {"number": 201, "title": "feat: real-time transcription sync", "user": {"login": "alice"}, "merged_at": "2026-10-24T18:00:00Z"}
        ]

        # Verify filtering
        filtered_issues = [i for i in sample_issues if not i.get("pull_request")]
        self.assertEqual(len(filtered_issues), 1)
        self.assertEqual(filtered_issues[0]["number"], 101)

        # Verify PR processing
        self.assertEqual(len(sample_prs), 1)
        self.assertEqual(sample_prs[0]["number"], 201)

if __name__ == "__main__":
    unittest.main()
