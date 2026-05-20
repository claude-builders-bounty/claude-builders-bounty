#!/usr/bin/env python3
"""Static checks for the weekly dev summary n8n workflow."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "weekly-dev-summary.json"


def main() -> None:
    workflow = json.loads(WORKFLOW.read_text())
    nodes = {node["name"]: node for node in workflow["nodes"]}

    required_nodes = [
        "Weekly Friday 5pm Trigger",
        "Manual Test Trigger",
        "Build config",
        "Fetch commits",
        "Fetch closed issues",
        "Fetch merged pull requests",
        "Compose Claude request",
        "Generate narrative with Claude",
        "Format Slack webhook message",
        "Send Slack webhook",
    ]
    missing = [name for name in required_nodes if name not in nodes]
    assert not missing, f"missing nodes: {missing}"

    schedule = nodes["Weekly Friday 5pm Trigger"]["parameters"]["rule"]["interval"][0]
    assert schedule["field"] == "weeks"
    assert schedule["triggerAtDay"] == [5]
    assert schedule["triggerAtHour"] == 17

    claude_node = nodes["Generate narrative with Claude"]
    assert claude_node["parameters"]["method"] == "POST"
    assert claude_node["parameters"]["url"] == "https://api.anthropic.com/v1/messages"
    assert "claude-sonnet-4-20250514" in nodes["Compose Claude request"]["parameters"]["jsCode"]

    build_code = nodes["Build config"]["parameters"]["jsCode"]
    for variable in [
        "github_owner",
        "github_repo",
        "summary_language",
        "anthropic_api_key",
        "destination_webhook_url",
    ]:
        assert variable in build_code

    send_node = nodes["Send Slack webhook"]
    assert send_node["parameters"]["method"] == "POST"
    assert send_node["parameters"]["url"] == "={{ $json.webhookUrl }}"

    connections = workflow["connections"]
    assert connections["Build config"]["main"][0][0]["node"] == "Fetch commits"
    assert connections["Format Slack webhook message"]["main"][0][0]["node"] == "Send Slack webhook"

    print("weekly-dev-summary workflow checks passed")


if __name__ == "__main__":
    main()
