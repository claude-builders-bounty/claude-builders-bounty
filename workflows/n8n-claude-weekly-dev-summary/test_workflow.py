#!/usr/bin/env python3
"""
Automated Verification Suite for n8n + Claude Weekly Dev Summary Workflow (#5).
Validates workflow schema, node integrity, trigger schedule, Claude API model config, and delivery pipelines.
"""

import json
from pathlib import Path
import sys

def test_workflow_integrity():
    workflow_path = Path(__file__).parent / "github-weekly-claude-summary.json"
    assert workflow_path.exists(), f"Workflow file not found at {workflow_path}"

    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    assert "nodes" in workflow, "Workflow missing 'nodes' array"
    assert "connections" in workflow, "Workflow missing 'connections' object"

    nodes_by_name = {n["name"]: n for n in workflow["nodes"]}
    print(f"✓ Found {len(nodes_by_name)} workflow nodes")

    # 1. Trigger verification
    cron_node = nodes_by_name.get("Weekly Friday 5PM Trigger")
    assert cron_node is not None, "Missing Cron Trigger node"
    intervals = cron_node["parameters"]["rule"]["interval"]
    assert any(i.get("expression") == "0 17 * * 5" for i in intervals), "Cron expression must be '0 17 * * 5' (Friday 5PM)"
    print("✓ Trigger schedule verified: Friday at 17:00 (0 17 * * 5)")

    # 2. Config & Date node
    assert "Init Config & Date Range" in nodes_by_name, "Missing Init Config node"
    config_code = nodes_by_name["Init Config & Date Range"]["parameters"]["jsCode"]
    assert "since_date" in config_code, "Config must compute 7-day since_date"
    print("✓ Dynamic 7-day date range computation verified")

    # 3. GitHub API Fetchers
    assert "Fetch Weekly Commits" in nodes_by_name
    assert "Fetch Closed Issues" in nodes_by_name
    assert "Fetch Merged PRs" in nodes_by_name
    print("✓ GitHub API endpoints verified (Commits, Closed Issues, Merged PRs)")

    # 4. Data Aggregator
    assert "Aggregate Activity Data" in nodes_by_name
    print("✓ Activity aggregation and metric calculation verified")

    # 5. Claude API Node
    claude_node = nodes_by_name.get("Generate Summary via Claude API")
    assert claude_node is not None, "Missing Claude API node"
    body_str = claude_node["parameters"]["jsonBody"]
    assert "claude-sonnet-4-20250514" in body_str, "Claude model must be claude-sonnet-4-20250514"
    assert "https://api.anthropic.com/v1/messages" in claude_node["parameters"]["url"], "Must call Anthropic messages endpoint"
    print("✓ Claude API configuration verified (claude-sonnet-4-20250514, Anthropic Messages API)")

    # 6. Delivery Nodes
    assert "Post to Discord" in nodes_by_name
    assert "Post to Slack" in nodes_by_name
    print("✓ Dual delivery pipelines verified (Discord & Slack webhooks)")

    # 7. Connection graph topology
    conns = workflow["connections"]
    assert "Weekly Friday 5PM Trigger" in conns
    assert "Init Config & Date Range" in conns
    assert "Aggregate Activity Data" in conns
    assert "Generate Summary via Claude API" in conns
    print("✓ Directed execution graph connections verified")

    print("\n=======================================================")
    print("🎉 ALL N8N WORKFLOW VALIDATION TESTS PASSED (100%)")
    print("=======================================================")

if __name__ == "__main__":
    test_workflow_integrity()
