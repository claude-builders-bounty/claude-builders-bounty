#!/usr/bin/env python3
"""Validate the bundled n8n weekly dev summary workflow."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "workflows" / "n8n-weekly-dev-summary.json"

REQUIRED_NODE_TYPES = {
    "n8n-nodes-base.scheduleTrigger",
    "n8n-nodes-base.set",
    "n8n-nodes-base.httpRequest",
    "n8n-nodes-base.code",
}

REQUIRED_ENV_VARS = {
    "GITHUB_REPO",
    "GITHUB_TOKEN",
    "ANTHROPIC_API_KEY",
    "DESTINATION_WEBHOOK_URL",
    "SUMMARY_LANGUAGE",
}


def main() -> int:
    data = json.loads(WORKFLOW.read_text(encoding="utf-8"))
    nodes = data.get("nodes", [])
    node_types = {node.get("type") for node in nodes}
    missing_types = REQUIRED_NODE_TYPES - node_types
    if missing_types:
        raise SystemExit(f"missing node types: {sorted(missing_types)}")

    raw = json.dumps(data)
    missing_env = {name for name in REQUIRED_ENV_VARS if name not in raw}
    if missing_env:
        raise SystemExit(f"missing env vars: {sorted(missing_env)}")

    if "claude-sonnet-4-20250514" not in raw:
        raise SystemExit("missing required Claude model")

    if "Friday" not in raw and "triggerAtDay" not in raw:
        raise SystemExit("missing weekly schedule configuration")

    print("workflow validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
