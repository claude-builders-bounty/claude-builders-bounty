#!/usr/bin/env python3
"""
Test suite for n8n Weekly Dev Summary workflow.
Validates workflow structure, node configuration, and acceptance criteria.
"""

import json
import os
import sys
from pathlib import Path

# Path to the workflow JSON file
WORKFLOW_PATH = Path(__file__).parent.parent / "workflows" / "n8n-weekly-dev-summary.json"


def load_workflow():
    """Load and parse the n8n workflow JSON."""
    if not WORKFLOW_PATH.exists():
        raise FileNotFoundError(f"Workflow file not found: {WORKFLOW_PATH}")
    
    with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_workflow_exists():
    """Test that the workflow JSON file exists."""
    assert WORKFLOW_PATH.exists(), f"Workflow file not found: {WORKFLOW_PATH}"


def test_workflow_valid_json():
    """Test that the workflow is valid JSON."""
    workflow = load_workflow()
    assert isinstance(workflow, dict), "Workflow should be a JSON object"
    assert "nodes" in workflow, "Workflow should have 'nodes' field"


def test_workflow_has_name():
    """Test that the workflow has a name."""
    workflow = load_workflow()
    assert "name" in workflow, "Workflow should have a 'name'"
    assert len(workflow["name"]) > 0, "Workflow name should not be empty"


def test_workflow_node_count():
    """Test that the workflow has at least 10 nodes (reasonable complexity)."""
    workflow = load_workflow()
    nodes = workflow.get("nodes", [])
    assert len(nodes) >= 10, f"Workflow should have at least 10 nodes, got {len(nodes)}"


def test_workflow_has_cron_trigger():
    """Test that the workflow has a cron/schedule trigger."""
    workflow = load_workflow()
    nodes = workflow.get("nodes", [])
    
    # Look for schedule trigger node
    trigger_nodes = [n for n in nodes if "schedule" in n.get("type", "").lower() or "trigger" in n.get("type", "").lower()]
    assert len(trigger_nodes) >= 1, "Workflow should have at least one schedule/trigger node"


def test_workflow_has_claude_api_call():
    """Test that the workflow calls Claude API."""
    workflow = load_workflow()
    nodes = workflow.get("nodes", [])
    
    # Look for HTTP request nodes that call Anthropic API
    http_nodes = [n for n in nodes if "http" in n.get("type", "").lower()]
    
    claude_called = False
    for node in http_nodes:
        parameters = node.get("parameters", {})
        url = parameters.get("url", "")
        
        # Check if this is calling Anthropic API
        if "anthropic" in url.lower():
            claude_called = True
            break
    
    assert claude_called, "Workflow should call Claude API (Anthropic endpoint)"


def test_workflow_has_delivery_channels():
    """Test that the workflow has at least 2 delivery channel options."""
    workflow = load_workflow()
    nodes = workflow.get("nodes", [])
    
    # Count nodes that appear to be delivery channels (webhook, email, discord, slack)
    delivery_keywords = ["webhook", "email", "discord", "slack", "smtp"]
    delivery_nodes = []
    
    for node in nodes:
        node_type = node.get("type", "").lower()
        node_name = node.get("name", "").lower()
        
        for keyword in delivery_keywords:
            if keyword in node_type or keyword in node_name:
                delivery_nodes.append(node)
                break
    
    assert len(delivery_nodes) >= 2, f"Workflow should have at least 2 delivery channels, got {len(delivery_nodes)}"


def test_workflow_acceptance_criteria():
    """Test that the workflow meets the acceptance criteria from the issue."""
    workflow = load_workflow()
    nodes = workflow.get("nodes", [])
    
    # Criterion 1: Exportable n8n workflow (.json)
    assert WORKFLOW_PATH.suffix == ".json", "Workflow should be a .json file"
    
    # Criterion 2: Weekly cron trigger
    trigger_nodes = [n for n in nodes if "trigger" in n.get("type", "").lower() or "schedule" in n.get("type", "").lower()]
    assert len(trigger_nodes) >= 1, "Should have a cron/schedule trigger"
    
    # Criterion 3: Fetches commits, closed issues, merged PRs
    http_nodes = [n for n in nodes if "http" in n.get("type", "").lower()]
    github_calls = 0
    
    for node in http_nodes:
        parameters = node.get("parameters", {})
        url = parameters.get("url", "")
        
        if "github.com" in url:
            github_calls += 1
    
    assert github_calls >= 3, f"Should fetch commits, issues, and PRs (got {github_calls} GitHub API calls)"
    
    # Criterion 4: Claude API (claude-sonnet-4-20250514)
    claude_found = False
    for node in nodes:
        parameters = node.get("parameters", {})
        url = parameters.get("url", "")
        body = json.dumps(parameters)
        
        if "anthropic" in url.lower() or "claude-sonnet-4-20250514" in body:
            claude_found = True
            break
    
    assert claude_found, "Should use Claude API with model claude-sonnet-4-20250514"
    
    # Criterion 5: Delivery via Discord/Slack/Email
    # (Already tested in test_workflow_has_delivery_channels)
    
    # Criterion 6: Configurable via environment variables
    code_nodes = [n for n in nodes if "code" in n.get("type", "").lower()]
    env_var_found = False
    
    for node in code_nodes:
        parameters = node.get("parameters", {})
        js_code = parameters.get("jsCode", "")
        
        if "$env" in js_code or "GITHUB_REPO" in js_code or "ANTHROPIC_API_KEY" in js_code:
            env_var_found = True
            break
    
    assert env_var_found, "Workflow should use environment variables for configuration"


def test_workflow_bilingual_support():
    """Test that the workflow supports both English and French."""
    workflow = load_workflow()
    nodes = workflow.get("nodes", [])
    
    # Look for code nodes that handle language selection
    code_nodes = [n for n in nodes if "code" in n.get("type", "").lower()]
    
    lang_found = False
    for node in code_nodes:
        parameters = node.get("parameters", {})
        js_code = parameters.get("jsCode", "")
        
        if "SUMMARY_LANGUAGE" in js_code or "EN" in js_code and "FR" in js_code:
            lang_found = True
            break
    
    assert lang_found, "Workflow should support bilingual output (EN/FR)"


if __name__ == "__main__":
    # Run all test_* functions
    test_functions = [f for f in dir() if f.startswith("test_")]
    
    passed = 0
    failed = 0
    
    for func_name in test_functions:
        try:
            func = locals()[func_name]
            func()
            print(f"✅ {func_name}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {func_name}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {func_name}: Unexpected error: {e}")
            failed += 1
    
    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*40}")
    
    sys.exit(0 if failed == 0 else 1)
