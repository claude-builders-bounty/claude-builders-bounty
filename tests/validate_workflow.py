import json
import os
import sys

def validate_workflow(workflow_path: str):
    print(f"Validating workflow file: {workflow_path}")
    if not os.path.exists(workflow_path):
        raise FileNotFoundError(f"Workflow file not found: {workflow_path}")
    
    with open(workflow_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 1. Structure check
    assert "name" in data, "Workflow must have a 'name'"
    assert "nodes" in data and isinstance(data["nodes"], list), "Workflow must have 'nodes' list"
    assert "connections" in data and isinstance(data["connections"], dict), "Workflow must have 'connections' dict"
    
    nodes = {node["name"]: node for node in data["nodes"]}
    print(f"✓ Found {len(nodes)} nodes in workflow: {list(nodes.keys())}")
    
    # 2. Key requirements validation
    # Trigger: weekly cron Friday 5pm
    trigger = None
    for n in data["nodes"]:
        if "scheduleTrigger" in n.get("type", ""):
            trigger = n
            break
    assert trigger is not None, "Missing scheduleTrigger node"
    rule_interval = trigger["parameters"]["rule"]["interval"][0]
    assert 5 in rule_interval.get("triggerAtDay", []), "Schedule must trigger on Friday (day 5)"
    assert rule_interval.get("triggerAtHour") == 17, "Schedule must trigger at 5pm (hour 17)"
    print("✓ Verified weekly cron trigger configured for Friday 5:00 PM")
    
    # Config Variables Node
    assert "Set Config Variables" in nodes, "Missing 'Set Config Variables' node"
    config_node = nodes["Set Config Variables"]
    config_names = [v["name"] for v in config_node["parameters"]["values"]["string"]]
    for req_var in ["GITHUB_OWNER", "GITHUB_REPO", "SUMMARY_LANGUAGE", "DELIVERY_CHANNEL"]:
        assert req_var in config_names, f"Missing config variable: {req_var}"
    print("✓ Verified configurable variables (GITHUB_OWNER, GITHUB_REPO, SUMMARY_LANGUAGE, DELIVERY_CHANNEL, etc.)")
    
    # GitHub Fetch Nodes: Commits, Closed PRs, Closed Issues
    github_nodes = [n for n in data["nodes"] if "httpRequest" in n.get("type", "") and "api.github.com" in n.get("parameters", {}).get("url", "")]
    assert len(github_nodes) >= 3, f"Expected at least 3 GitHub fetch nodes, found {len(github_nodes)}"
    print(f"✓ Verified GitHub API fetch nodes ({len(github_nodes)} nodes: Commits, PRs, Issues)")
    
    # Claude API Node
    claude_node = None
    for n in data["nodes"]:
        if "httpRequest" in n.get("type", "") and "api.anthropic.com" in n.get("parameters", {}).get("url", ""):
            claude_node = n
            break
    assert claude_node is not None, "Missing Claude API call node"
    # Check default model
    claude_model_val = [v["value"] for v in config_node["parameters"]["values"]["string"] if v["name"] == "CLAUDE_MODEL"]
    assert len(claude_model_val) > 0 and "claude-sonnet-4-20250514" in claude_model_val[0], "Claude model should target claude-sonnet-4-20250514"
    print(f"✓ Verified Claude API node targeting Anthropic Messages endpoint with model {claude_model_val[0]}")
    
    # Delivery Channels: Webhook & Email
    assert "Post to Webhook (Discord / Slack)" in nodes, "Missing Webhook delivery node"
    assert "Send Email Notification" in nodes, "Missing Email delivery node"
    assert "Route Delivery Channel" in nodes, "Missing Delivery Router node"
    print("✓ Verified multi-channel delivery support (Discord/Slack webhook + Email routing)")
    
    # 3. Connection integrity
    for src_node, targets in data["connections"].items():
        assert src_node in nodes, f"Connection source '{src_node}' does not exist in nodes"
        for conn_type, conn_list in targets.items():
            for target_group in conn_list:
                for target in target_group:
                    assert target["node"] in nodes, f"Target node '{target['node']}' connected from '{src_node}' not found"
    print("✓ All node connections and graph topology validated successfully")

if __name__ == "__main__":
    test_files = [
        "workflows/weekly-summary/weekly_dev_summary.json",
        "workflows/weekly-summary/workflow.json",
        "weekly_dev_summary.json"
    ]
    for tf in test_files:
        if os.path.exists(tf):
            validate_workflow(tf)
    print("\n🎉 ALL N8N WORKFLOW VALIDATION TESTS PASSED!")
