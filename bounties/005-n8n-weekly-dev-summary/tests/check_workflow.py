#!/usr/bin/env python3
"""Smoke-check the n8n workflow export."""

from __future__ import annotations

import json
from pathlib import Path


workflow_path = Path(__file__).resolve().parents[1] / "workflows" / "weekly-dev-summary.json"
workflow = json.loads(workflow_path.read_text(encoding="utf-8"))

node_names = {node["name"] for node in workflow["nodes"]}
required_nodes = {
    "Weekly Friday 5pm",
    "Fetch GitHub Activity",
    "Build Claude Request",
    "Claude Summary",
    "Post to Discord",
}
missing = required_nodes - node_names
assert not missing, f"Missing nodes: {sorted(missing)}"

workflow_text = workflow_path.read_text(encoding="utf-8")
assert "claude-sonnet-4-20250514" in workflow_text
assert "GITHUB_REPO" in workflow_text
assert "DESTINATION_WEBHOOK_URL" in workflow_text
assert "SUMMARY_LANGUAGE" in workflow_text
assert "GITHUB_TOKEN" in workflow_text
assert "CLAUDE_API_KEY" in workflow_text
assert "https://api.github.com" in workflow_text
assert "https://api.anthropic.com/v1/messages" in workflow_text

print("n8n weekly dev summary workflow check passed")
