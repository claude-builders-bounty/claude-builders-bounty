#!/usr/bin/env python3
"""
Validator script for n8n workflow JSON schema and node connectivity.
"""
import json
import sys
from pathlib import Path

def validate_workflow(json_path: Path):
    if not json_path.exists():
        print(f"[-] Error: {json_path} does not exist", file=sys.stderr)
        return False

    with open(json_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"[-] Invalid JSON syntax: {e}", file=sys.stderr)
            return False

    # Check required n8n workflow fields
    required_keys = ["nodes", "connections"]
    for k in required_keys:
        if k not in data:
            print(f"[-] Missing top-level key: '{k}'", file=sys.stderr)
            return False

    nodes = data.get("nodes", [])
    connections = data.get("connections", {})

    print(f"[+] Loaded workflow: '{data.get('name')}' with {len(nodes)} nodes")

    node_names = set()
    for node in nodes:
        name = node.get("name")
        node_type = node.get("type")
        if not name or not node_type:
            print(f"[-] Node missing 'name' or 'type': {node}", file=sys.stderr)
            return False
        node_names.add(name)

    # Check required core nodes exist
    expected_nodes = [
        "Weekly Schedule (Friday 5PM)",
        "Workflow Configuration",
        "Compute Date Window",
        "GitHub - Fetch Commits",
        "GitHub - Fetch Pull Requests",
        "GitHub - Fetch Issues",
        "Aggregate GitHub Metrics",
        "Claude API - Generate Summary",
        "Format Webhook Payload",
        "Dispatch Summary to Webhook"
    ]

    for expected in expected_nodes:
        if expected not in node_names:
            print(f"[-] Expected node '{expected}' not found in workflow.", file=sys.stderr)
            return False
        print(f"  [✓] Node found: {expected}")

    # Check connections refer to valid nodes
    for source_node, conn_data in connections.items():
        if source_node not in node_names:
            print(f"[-] Connection source '{source_node}' does not match any node name.", file=sys.stderr)
            return False
        main_outputs = conn_data.get("main", [])
        for output_group in main_outputs:
            for target in output_group:
                target_node = target.get("node")
                if target_node not in node_names:
                    print(f"[-] Connection target '{target_node}' does not exist.", file=sys.stderr)
                    return False

    print("[+] All connections and node targets verified successfully.")
    return True

if __name__ == "__main__":
    target_file = Path(__file__).parent / "workflow.json"
    if not target_file.exists():
        target_file = Path(__file__).parent / "n8n_github_weekly_summary.json"
    valid = validate_workflow(target_file)
    if valid:
        print("\n✅ Workflow validation PASSED.")
        sys.exit(0)
    else:
        print("\n❌ Workflow validation FAILED.")
        sys.exit(1)
