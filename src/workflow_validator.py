#!/usr/bin/env python3
import sys
import os
import json

REQUIRED_NODES = [
    "Weekly Schedule Trigger (Fridays 5pm)",
    "Set Workflow Variables",
    "Fetch Recent GitHub Commits",
    "Fetch Closed GitHub PRs",
    "Claude API Dev Summary Synthesizer",
    "Deliver via Webhook (Discord / Slack)"
]

def validate_n8n_workflow(filepath: str) -> dict:
    """Validates n8n export workflow JSON file structure, connections, and node elements."""
    if not os.path.exists(filepath):
        return {"success": False, "error": f"File not found: {filepath}"}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        nodes = data.get("nodes", [])
        node_names = [n.get("name") for n in nodes]
        connections = data.get("connections", {})

        missing_nodes = [name for name in REQUIRED_NODES if name not in node_names]

        # Check Claude API node configuration
        claude_node = next((n for n in nodes if n.get("name") == "Claude API Dev Summary Synthesizer"), None)
        has_claude_model = False
        if claude_node:
            body = str(claude_node.get("parameters", {}).get("bodyParameters", {}))
            has_claude_model = "claude-3-7-sonnet-20250219" in body or "claude" in body

        is_valid = len(missing_nodes) == 0 and len(nodes) >= 5 and len(connections) >= 3 and has_claude_model

        return {
            "success": is_valid,
            "node_count": len(nodes),
            "connection_count": len(connections),
            "missing_nodes": missing_nodes,
            "has_claude_model": has_claude_model
        }

    except Exception as e:
        return {"success": False, "error": f"JSON parse error: {e}"}

def main():
    filepath = sys.argv[1] if len(sys.argv) > 1 else "src/n8n_weekly_dev_summary.json"
    print(f"🔍 Validating n8n workflow file [{filepath}]...")
    res = validate_n8n_workflow(filepath)
    if res["success"]:
        print(f"✅ Workflow Validation PASSED! ({res['node_count']} nodes, {res['connection_count']} connection sets)")
    else:
        print(f"❌ Workflow Validation FAILED! Details: {res}")
        sys.exit(1)

if __name__ == "__main__":
    main()
