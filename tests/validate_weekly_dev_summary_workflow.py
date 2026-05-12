#!/usr/bin/env python3
"""Static validator for the n8n weekly GitHub dev summary workflow.

This keeps the bounty deliverable reviewable without requiring live n8n,
GitHub, Anthropic, or Slack credentials.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "workflows" / "weekly-dev-summary-n8n.json"


def load_workflow() -> dict:
    with WORKFLOW.open(encoding="utf-8") as fh:
        return json.load(fh)


def node_by_name(workflow: dict, name: str) -> dict:
    for node in workflow.get("nodes", []):
        if node.get("name") == name:
            return node
    raise AssertionError(f"Missing node: {name}")


def assert_contains(value: object, expected: str, context: str) -> None:
    text = json.dumps(value, sort_keys=True)
    assert expected in text, f"{context} must contain {expected!r}"


def main() -> int:
    workflow = load_workflow()

    assert workflow.get("name"), "Workflow must have a name"
    assert isinstance(workflow.get("nodes"), list) and workflow["nodes"], "Workflow must define nodes"
    assert workflow.get("connections"), "Workflow must define node connections"

    manual = node_by_name(workflow, "Manual Trigger")
    assert manual["type"] == "n8n-nodes-base.manualTrigger"

    schedule = node_by_name(workflow, "Weekly Friday 5pm Trigger")
    assert schedule["type"] == "n8n-nodes-base.scheduleTrigger"
    assert_contains(schedule, "0 17 * * 5", "Weekly trigger")

    config = node_by_name(workflow, "Config")
    for field in (
        "githubRepo",
        "githubToken",
        "anthropicApiKey",
        "slackWebhookUrl",
        "language",
    ):
        assert_contains(config, field, "Config node")

    fetch = node_by_name(workflow, "Fetch GitHub Activity")
    assert fetch["type"] == "n8n-nodes-base.code"
    for required in (
        "/commits?since=",
        "/issues?state=closed",
        "/pulls?state=closed",
        "merged_at",
        "closedIssues",
        "mergedPulls",
    ):
        assert_contains(fetch, required, "GitHub activity fetch node")

    claude = node_by_name(workflow, "Generate Claude Summary")
    assert claude["type"] == "n8n-nodes-base.httpRequest"
    assert_contains(claude, "https://api.anthropic.com/v1/messages", "Claude API node")
    assert_contains(claude, "claude-sonnet-4-20250514", "Claude API node")
    assert_contains(claude, "anthropic-version", "Claude API node")
    assert_contains(claude, "x-api-key", "Claude API node")

    extract = node_by_name(workflow, "Extract Summary Text")
    assert extract["type"] == "n8n-nodes-base.code"

    slack = node_by_name(workflow, "Send Slack Webhook")
    assert slack["type"] == "n8n-nodes-base.httpRequest"
    assert_contains(slack, "slackWebhookUrl", "Slack delivery node")

    print(
        "OK: weekly dev summary workflow has schedule, config, GitHub activity fetch, "
        "Claude generation, Slack delivery, and importable JSON structure."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
