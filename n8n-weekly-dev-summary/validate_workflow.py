#!/usr/bin/env python3
"""Static validation for the n8n weekly summary workflow template."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED_NODE_NAMES = {
    "Weekly Trigger",
    "Set Run Config",
    "Get Weekly Commits",
    "Get Closed Issues",
    "Get Closed PRs",
    "Build Claude Prompt",
    "Generate Claude Summary",
    "Send Summary To Webhook",
}

REQUIRED_CONFIG_KEYS = {
    "repo_owner",
    "repo_name",
    "webhook_url",
    "destination_channel",
    "language",
    "claude_api_key",
    "claude_model",
    "github_token",
}


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    sys.exit(1)


workflow_path = Path(__file__).with_name("workflow.json")
if not workflow_path.exists():
    fail(f"Missing file: {workflow_path}")

with workflow_path.open("r", encoding="utf-8") as handle:
    workflow = json.load(handle)

nodes = workflow.get("nodes", [])
if not isinstance(nodes, list) or not nodes:
    fail("Workflow contains no nodes")

node_names = {node.get("name") for node in nodes}
missing_nodes = sorted(REQUIRED_NODE_NAMES - node_names)
if missing_nodes:
    fail(f"Missing required nodes: {', '.join(missing_nodes)}")

config_node = next(node for node in nodes if node.get("name") == "Set Run Config")
strings = (
    config_node.get("parameters", {})
    .get("values", {})
    .get("string", [])
)
config_keys = {entry.get("name") for entry in strings}
missing_keys = sorted(REQUIRED_CONFIG_KEYS - config_keys)
if missing_keys:
    fail(f"Missing required config keys: {', '.join(missing_keys)}")

workflow_text = workflow_path.read_text(encoding="utf-8")
if "0 17 * * 5" not in workflow_text:
    fail("Weekly cron expression not found")

if "SUMMARY_LANGUAGE" not in workflow_text:
    fail("Language variable binding not found")

if "api.anthropic.com/v1/messages" not in workflow_text:
    fail("Claude API endpoint missing")

if "repos/{{$json.repo_owner}}/{{$json.repo_name}}/commits" not in workflow_text:
    fail("GitHub commits endpoint missing")

print("Workflow validation passed")
