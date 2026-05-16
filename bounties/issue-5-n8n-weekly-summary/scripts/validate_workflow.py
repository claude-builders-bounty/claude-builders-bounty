#!/usr/bin/env python3
"""Validate the bounty #5 n8n workflow export without needing n8n installed."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "weekly-github-dev-summary.workflow.json"
README = ROOT / "README.md"


def flatten(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield str(k)
            yield from flatten(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from flatten(item)
    else:
        yield str(obj)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    data = json.loads(WORKFLOW.read_text())
    nodes = data.get("nodes", [])
    node_names = {n.get("name") for n in nodes}
    node_types = {n.get("type") for n in nodes}
    all_text = "\n".join(flatten(data))
    readme = README.read_text()

    require(data.get("name"), "workflow name is missing")
    require("n8n-nodes-base.scheduleTrigger" in node_types, "weekly schedule trigger is missing")
    require("n8n-nodes-base.manualTrigger" in node_types, "manual test trigger is missing")
    require("Fetch GitHub Activity" in node_names, "GitHub fetch node is missing")
    require("Normalize Week Data" in node_names, "data normalization node is missing")
    require("Claude API — Narrative Summary" in node_names, "Claude API node is missing")
    require("Format Slack/Discord Payload" in node_names, "delivery formatter node is missing")
    require("Dry Run Result" in node_names, "dry-run validation result node is missing")

    for needle in [
        "https://api.github.com/graphql",
        "commits",
        "closed_issues",
        "merged_prs",
        "https://api.anthropic.com/v1/messages",
        "claude-sonnet-4-20250514",
        "GITHUB_REPO",
        "DESTINATION_CHANNEL",
        "LANGUAGE",
        "SLACK_WEBHOOK_URL",
        "DISCORD_WEBHOOK_URL",
        "DRY_RUN",
    ]:
        require(needle in all_text, f"required workflow feature missing: {needle}")

    require("## Setup in 5 steps" in readme, "README must include 5-step setup")
    require(readme.count("1. **Import**") == 1, "README setup steps should be concise and explicit")

    connections = data.get("connections", {})
    require("Weekly Schedule — Friday 5pm" in connections, "schedule trigger is not connected")
    require("Manual Trigger" in connections, "manual trigger is not connected")

    print("PASS workflow JSON is valid and covers the bounty acceptance criteria")
    print(f"nodes={len(nodes)} file={WORKFLOW.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
