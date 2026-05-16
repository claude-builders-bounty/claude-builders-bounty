"""Tests for n8n weekly dev summary workflow"""
import json, pytest

with open("weekly-dev-summary.json") as f:
    workflow = json.load(f)

class TestN8nWorkflow:
    def test_has_cron_trigger(self):
        nodes = {n["name"]: n for n in workflow["nodes"]}
        assert "Weekly Cron (Friday 5pm)" in nodes
        trigger = nodes["Weekly Cron (Friday 5pm)"]
        assert trigger["type"] == "n8n-nodes-base.scheduleTrigger"

    def test_has_github_api_nodes(self):
        names = [n["name"] for n in workflow["nodes"]]
        assert "Fetch Weekly Commits" in names
        assert "Fetch Closed Issues" in names
        assert "Fetch Merged PRs" in names

    def test_has_claude_api_node(self):
        names = [n["name"] for n in workflow["nodes"]]
        assert "Call Claude API" in names

    def test_has_output_node(self):
        names = [n["name"] for n in workflow["nodes"]]
        assert "Save Markdown File" in names

    def test_connections_valid(self):
        connections = workflow.get("connections", {})
        assert len(connections) >= 5
