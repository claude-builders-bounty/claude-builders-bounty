import json
import os
import unittest

WORKFLOW_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "workflows",
    "github-weekly-summary",
    "workflow.json"
)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class TestN8nWorkflow(unittest.TestCase):
    def setUp(self):
        self.assertTrue(os.path.exists(WORKFLOW_PATH), f"Workflow file not found: {WORKFLOW_PATH}")
        with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
            self.wf = json.load(f)

    def test_workflow_json_schema(self):
        """Validate workflow top-level schema and basic structure."""
        self.assertIn("name", self.wf)
        self.assertIn("nodes", self.wf)
        self.assertIn("connections", self.wf)
        self.assertIsInstance(self.wf["nodes"], list)
        self.assertGreaterEqual(len(self.wf["nodes"]), 10)

    def test_cron_schedule_configuration(self):
        """Verify trigger is a weekly cron for Friday at 5:00 PM (17:00)."""
        schedule_nodes = [
            n for n in self.wf["nodes"] 
            if n.get("type") == "n8n-nodes-base.scheduleTrigger"
        ]
        self.assertGreaterEqual(len(schedule_nodes), 1, "Schedule trigger node missing")
        sched = schedule_nodes[0]
        params = sched.get("parameters", {})
        rule = params.get("rule", {})
        interval = rule.get("interval", [])
        self.assertGreaterEqual(len(interval), 1)
        int_conf = interval[0]
        self.assertEqual(int_conf.get("field"), "weeks")
        self.assertEqual(int_conf.get("triggerAtDay"), 5, "Should trigger on Friday (day 5)")
        self.assertEqual(int_conf.get("triggerAtHour"), 17, "Should trigger at 17:00 (5:00 PM)")
        self.assertEqual(int_conf.get("triggerAtMinute"), 0)

    def test_configurable_variables(self):
        """Verify configurable variables: github_repo, language (EN/FR), delivery_channel, claude_model."""
        config_nodes = [
            n for n in self.wf["nodes"]
            if n.get("name") == "Workflow Configuration"
        ]
        self.assertEqual(len(config_nodes), 1)
        cfg = config_nodes[0]
        assignments = cfg.get("parameters", {}).get("assignments", {}).get("assignments", [])
        names = {a.get("name") for a in assignments}
        
        required_keys = {"github_repo", "language", "delivery_channel", "claude_model", "anthropic_api_key"}
        for k in required_keys:
            self.assertIn(k, names, f"Missing required configuration key: {k}")

    def test_github_api_endpoints(self):
        """Verify GitHub API fetching: commits, closed issues, merged PRs."""
        http_nodes = {
            n.get("name"): n
            for n in self.wf["nodes"]
            if "httpRequest" in n.get("type", "")
        }
        
        # 1. Commits
        self.assertIn("Fetch GitHub Commits", http_nodes)
        commits_url = http_nodes["Fetch GitHub Commits"]["parameters"]["url"]
        self.assertIn("/commits?since=", commits_url)

        # 2. Merged PRs
        self.assertIn("Fetch Merged Pull Requests", http_nodes)
        prs_url = http_nodes["Fetch Merged Pull Requests"]["parameters"]["url"]
        self.assertIn("/pulls?state=closed", prs_url)

        # 3. Closed Issues
        self.assertIn("Fetch Closed Issues", http_nodes)
        issues_url = http_nodes["Fetch Closed Issues"]["parameters"]["url"]
        self.assertIn("/issues?state=closed", issues_url)

    def test_claude_model_configuration(self):
        """Verify calls Claude API with claude-sonnet-4-20250514."""
        claude_nodes = [
            n for n in self.wf["nodes"]
            if n.get("name") == "Claude Code Summary Generator"
        ]
        self.assertEqual(len(claude_nodes), 1)
        node = claude_nodes[0]
        self.assertEqual(node["parameters"]["method"], "POST")
        self.assertEqual(node["parameters"]["url"], "https://api.anthropic.com/v1/messages")
        
        # Verify in prompt builder that claude-sonnet-4-20250514 is targeted
        builder_nodes = [
            n for n in self.wf["nodes"]
            if n.get("name") == "Aggregate Activity & Build Prompt"
        ]
        self.assertEqual(len(builder_nodes), 1)
        code = builder_nodes[0]["parameters"]["jsCode"]
        self.assertIn("claude-sonnet-4-20250514", code)

    def test_multichannel_switch_rules(self):
        """Verify delivery via Slack, Discord, or Email."""
        switch_nodes = [
            n for n in self.wf["nodes"]
            if n.get("name") == "Route Delivery Channel"
        ]
        self.assertEqual(len(switch_nodes), 1)
        
        # Verify destination nodes exist in connections
        node_names = {n.get("name") for n in self.wf["nodes"]}
        self.assertIn("Send to Slack Webhook", node_names)
        self.assertIn("Send to Discord Webhook", node_names)
        self.assertIn("Send Email Digest", node_names)

    def test_artifacts_and_documentation_exist(self):
        """Verify execution screenshot, README, and samples exist."""
        readme = os.path.join(BASE_DIR, "workflows", "github-weekly-summary", "README.md")
        screenshot = os.path.join(BASE_DIR, "workflows", "github-weekly-summary", "screenshots", "n8n_workflow_execution.png")
        sample_en = os.path.join(BASE_DIR, "workflows", "github-weekly-summary", "sample_output", "sample_summary_en.md")
        sample_fr = os.path.join(BASE_DIR, "workflows", "github-weekly-summary", "sample_output", "sample_summary_fr.md")

        self.assertTrue(os.path.exists(readme), "README.md missing")
        self.assertTrue(os.path.exists(screenshot), "Screenshot missing")
        self.assertGreater(os.path.getsize(screenshot), 10000, "Screenshot file is too small")
        self.assertTrue(os.path.exists(sample_en), "English sample summary missing")
        self.assertTrue(os.path.exists(sample_fr), "French sample summary missing")

if __name__ == '__main__':
    unittest.main()
