#!/usr/bin/env python3
"""Validate the n8n weekly dev summary workflow export."""

from __future__ import annotations

import json
from pathlib import Path


WORKFLOW_PATH = Path(__file__).with_name("workflow.json")
REQUIRED_NODES = {
    "Weekly Friday Schedule",
    "Fetch GitHub Commits",
    "Fetch Closed Issues",
    "Fetch Merged PRs",
    "Build Weekly Activity",
    "Summarize with Claude",
    "Extract Claude Text",
    "Post to Slack",
}


def main() -> int:
    workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    node_names = {node.get("name") for node in workflow.get("nodes", [])}
    missing = sorted(REQUIRED_NODES - node_names)
    if missing:
        raise SystemExit(f"Missing required nodes: {', '.join(missing)}")

    connections = workflow.get("connections", {})
    for source, targets in connections.items():
        if source not in node_names:
            raise SystemExit(f"Connection source has no matching node: {source}")
        for target_group in targets.get("main", []):
            for target in target_group:
                target_name = target.get("node")
                if target_name not in node_names:
                    raise SystemExit(f"Connection target has no matching node: {target_name}")

    raw = json.dumps(workflow)
    if "ANTHROPIC_API_KEY" not in raw:
        raise SystemExit("Workflow must reference ANTHROPIC_API_KEY")
    if "SLACK_WEBHOOK_URL" not in raw:
        raise SystemExit("Workflow must reference SLACK_WEBHOOK_URL")
    if "claude-sonnet-4-20250514" not in raw:
        raise SystemExit("Workflow must use claude-sonnet-4-20250514")
    for variable in ("GITHUB_OWNER", "GITHUB_REPO", "DIGEST_LANGUAGE", "SLACK_CHANNEL"):
        if variable not in raw:
            raise SystemExit(f"Workflow must reference {variable}")

    print(f"workflow.json OK: {len(node_names)} nodes, {len(connections)} connections")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
