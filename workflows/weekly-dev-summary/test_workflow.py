#!/usr/bin/env python3
"""
Test validation for n8n workflow.json.
Verifies valid JSON structure, node links, cron expression, and API parameter mapping.
"""
import json
import os

def test_n8n_workflow_schema():
    with open("workflow.json", "r", encoding="utf-8") as f:
        workflow = json.load(f)

    # 1. Structure assertions
    assert "nodes" in workflow, "Missing nodes key"
    assert "connections" in workflow, "Missing connections key"

    nodes = {n["name"]: n for n in workflow["nodes"]}
    
    # 2. Required node verification
    required_nodes = [
        "Weekly Trigger (Friday 5PM)",
        "Configuration Variables",
        "Fetch Weekly Commits",
        "Fetch Merged PRs",
        "Aggregate Git Activity",
        "Synthesize with Claude Sonnet",
        "Send Discord / Slack Alert"
    ]
    for r in required_nodes:
        assert r in nodes, f"Missing required node: {r}"

    # 3. Verify Cron Schedule (Friday 5PM)
    cron_rule = nodes["Weekly Trigger (Friday 5PM)"]["parameters"]["rule"]["interval"][0]["expression"]
    assert cron_rule == "0 17 * * 5", f"Incorrect cron expression: {cron_rule} (expected '0 17 * * 5')"

    # 4. Verify Claude model call
    claude_body = nodes["Synthesize with Claude Sonnet"]["parameters"]["jsonBody"]
    assert "claude-sonnet-4-20250514" in claude_body, "Expected claude-sonnet-4-20250514 model specification"

    # 5. Verify Connections integrity
    conns = workflow["connections"]
    for src_node, targets in conns.items():
        assert src_node in nodes, f"Source node in connections does not exist: {src_node}"
        for group in targets.get("main", []):
            for t in group:
                assert t["node"] in nodes, f"Target node in connections does not exist: {t['node']}"

    print("[✓] ALL N8N WORKFLOW ACCEPTANCE CRITERIA VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    test_n8n_workflow_schema()
