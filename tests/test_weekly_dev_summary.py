# SPDX-License-Identifier: MIT
"""
Tests for n8n Weekly Dev Summary Workflow & Documentation.
"""

import json
import os
import re
import pytest

WORKFLOW_PATH = os.path.join(
    os.path.dirname(__file__), "..", "workflows", "weekly-summary", "workflow.json"
)
README_PATH = os.path.join(
    os.path.dirname(__file__), "..", "workflows", "weekly-summary", "README.md"
)


def test_workflow_json_structure():
    """Verify that workflow.json is valid JSON with required n8n root fields."""
    assert os.path.exists(WORKFLOW_PATH), f"File not found: {WORKFLOW_PATH}"
    with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "nodes" in data
    assert "connections" in data
    assert len(data["nodes"]) >= 6


def test_workflow_acceptance_criteria_nodes():
    """Verify nodes meet all issue #5 acceptance criteria."""
    with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = {node["name"]: node for node in data["nodes"]}

    # 1. Trigger node (cron)
    assert "Weekly Trigger (Fri 5PM)" in nodes
    trigger = nodes["Weekly Trigger (Fri 5PM)"]
    assert trigger["type"] == "n8n-nodes-base.scheduleTrigger"

    # 2. Configurable variables
    assert "Set Workflow Config" in nodes
    config_node = nodes["Set Workflow Config"]
    var_names = [
        v["name"] for v in config_node["parameters"]["values"]["string"]
    ]
    assert "GITHUB_OWNER" in var_names
    assert "GITHUB_REPO" in var_names
    assert "DELIVERY_WEBHOOK_URL" in var_names
    assert "SUMMARY_LANGUAGE" in var_names

    # 3. GitHub API fetches: commits, closed issues, merged PRs
    assert "Fetch Weekly Commits" in nodes
    assert "Fetch Merged PRs" in nodes
    assert "Fetch Closed Issues" in nodes

    # 4. Calls Claude API
    assert "Call Claude API" in nodes
    claude_node = nodes["Call Claude API"]
    assert "api.anthropic.com" in claude_node["parameters"]["url"]

    # 5. Delivers via Webhook
    assert "Deliver via Webhook (Slack/Discord)" in nodes


def test_readme_setup_steps_count():
    """Verify README setup instructions have 5 steps or fewer."""
    assert os.path.exists(README_PATH), f"File not found: {README_PATH}"
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Match numbered steps e.g. "1. ", "2. "
    step_matches = re.findall(r"^\d+\.\s+", content, flags=re.MULTILINE)
    assert 1 <= len(step_matches) <= 5, f"Expected <= 5 setup steps, found {len(step_matches)}"
