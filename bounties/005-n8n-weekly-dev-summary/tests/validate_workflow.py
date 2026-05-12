#!/usr/bin/env python3
"""Structural smoke-test for the weekly-dev-summary n8n workflow JSON."""

import json
import sys
from pathlib import Path

workflow_path = Path(__file__).resolve().parents[1] / "workflows" / "weekly-dev-summary.json"

try:
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"FAIL: Cannot parse workflow JSON — {e}")
    sys.exit(1)

nodes = workflow.get("nodes", [])
node_names = {n["name"] for n in nodes}
connections = workflow.get("connections", {})

REQUIRED_NODES = {
    "Every Friday at 5pm",
    "Compute Date Window",
    "Fetch Commits",
    "Fetch Closed Issues",
    "Fetch Merged PRs",
    "Merge GitHub Activity",
    "Build Claude Prompt",
    "Call Claude API",
    "Extract Summary Text",
    "Post to Webhook",
}

missing = REQUIRED_NODES - node_names
assert not missing, f"Missing nodes: {sorted(missing)}"
print(f"  nodes: all {len(REQUIRED_NODES)} required nodes present")

# Verify schedule node uses cron expression 0 17 * * 5
sched = next(n for n in nodes if n["name"] == "Every Friday at 5pm")
cron = sched["parameters"]["rule"]["interval"][0]["expression"]
assert cron == "0 17 * * 5", f"Expected cron '0 17 * * 5', got '{cron}'"
print(f"  schedule: cron = {cron!r} ✓")

# Verify Claude model
workflow_text = workflow_path.read_text(encoding="utf-8")
assert "claude-sonnet-4-20250514" in workflow_text, "Claude model not found"
print("  model: claude-sonnet-4-20250514 ✓")

# Verify all required env vars are referenced
for var in ("GITHUB_REPO", "GITHUB_TOKEN", "CLAUDE_API_KEY", "DESTINATION_WEBHOOK_URL", "SUMMARY_LANGUAGE"):
    assert var in workflow_text, f"Env var {var} not referenced in workflow"
print("  env vars: GITHUB_REPO, GITHUB_TOKEN, CLAUDE_API_KEY, DESTINATION_WEBHOOK_URL, SUMMARY_LANGUAGE ✓")

# Verify GitHub API and Anthropic API URLs
assert "https://api.github.com" in workflow_text, "GitHub API URL not found"
assert "https://api.anthropic.com/v1/messages" in workflow_text, "Anthropic API URL not found"
print("  api endpoints: GitHub + Anthropic ✓")

# Verify connection chain: trigger → compute → parallel fetches → merge → build → call → extract → post
assert "Every Friday at 5pm" in connections, "Trigger has no outgoing connections"
trigger_targets = {c["node"] for c in connections["Every Friday at 5pm"]["main"][0]}
assert "Compute Date Window" in trigger_targets
print("  connections: trigger → compute ✓")

compute_targets = {c["node"] for c in connections["Compute Date Window"]["main"][0]}
assert compute_targets == {"Fetch Commits", "Fetch Closed Issues", "Fetch Merged PRs"}, \
    f"Expected parallel fetch, got {compute_targets}"
print("  connections: compute → 3 parallel fetches ✓")

# Verify both EN and FR are supported
assert "SUMMARY_LANGUAGE" in workflow_text
assert "FR" in workflow_text
assert "EN" in workflow_text
print("  language: EN + FR support ✓")

print("\nAll checks passed.")
