"""Offline acceptance checks for the n8n workflow bundle.

This intentionally checks structure only. It does not claim that a real n8n
execution or payout has happened; those require the claimant's credentials.
"""

import json
from pathlib import Path


ROOT = Path(__file__).parent
workflow = json.loads((ROOT / "github-weekly-summary.json").read_text())
names = {node["name"] for node in workflow["nodes"]}
text = json.dumps(workflow)

required_names = {
    "Weekly trigger",
    "GitHub commits",
    "GitHub closed issues",
    "GitHub pull requests",
    "Claude weekly narrative",
    "Deliver to Slack or Discord webhook",
}
missing = required_names - names
assert not missing, f"missing nodes: {sorted(missing)}"
assert "everyWeek" in text, "weekly trigger is not configured"
assert "githubApiBaseUrl" in text and "/repos" in text, "GitHub API calls are missing"
assert "commits" in text and "closed" in text and "pulls" in text
assert "claude-sonnet-4-20250514" in text, "required Claude model is missing"
assert "destinationWebhook" in text, "delivery destination is not configurable"
assert "language" in text, "language is not configurable"
assert "toJsonString" in text, "JSON-safe prompt/body encoding is missing"

print(f"PASS: {len(workflow['nodes'])} nodes, {len(workflow['connections'])} connection groups")
print("PASS: offline structure satisfies the documented acceptance criteria")
print("NOTE: real n8n execution screenshot remains claimant-provided evidence")
