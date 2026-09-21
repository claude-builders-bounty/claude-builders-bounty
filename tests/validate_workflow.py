#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
workflow = json.loads((root / "skills/n8n-weekly-summary/n8n-workflow.json").read_text())
nodes = {n["name"]: n for n in workflow["nodes"]}
required = {
    "Friday 5 PM", "Manual Test Trigger", "Set Configuration", "Fetch Closed Issues",
    "Fetch Closed Pull Requests", "Fetch Weekly Commits", "Normalize Issues",
    "Normalize Merged PRs", "Normalize Commits", "Merge All Activity",
    "Generate with Claude", "Verify Claude Response", "Destination Configured?",
    "Deliver to Discord", "Fail Missing Destination",
}
assert not (required - nodes.keys()), required - nodes.keys()
assert nodes["Friday 5 PM"]["parameters"]["rule"]["interval"][0]["expression"] == "0 17 * * 5"
raw = json.dumps(workflow)
for token in ("GITHUB_OWNER", "GITHUB_REPO", "DESTINATION_WEBHOOK_URL", "LANGUAGE", "claude-sonnet-4-20250514"):
    assert token in raw
assert "merged_at >= cfg.WEEK_START" in nodes["Normalize Merged PRs"]["parameters"]["jsCode"]
issue_code = nodes["Normalize Issues"]["parameters"]["jsCode"]
assert "!x.pull_request" in issue_code
assert "x.closed_at <= cfg.WEEK_END" in issue_code
commit_code = nodes["Normalize Commits"]["parameters"]["jsCode"]
assert "typeof x.sha === 'string'" in commit_code
assert "x.sha.length > 0" in commit_code
assert "x.commit && typeof x.commit.message === 'string'" in commit_code
assert "commits: rows.map" in commit_code
for fetch in ("Fetch Closed Issues", "Fetch Closed Pull Requests", "Fetch Weekly Commits"):
    assert nodes[fetch].get("alwaysOutputData") is True, f"{fetch} can false-succeed on an empty week"
assert "refusing false success" in nodes["Verify Claude Response"]["parameters"]["jsCode"]
connections = workflow["connections"]
assert connections["Destination Configured?"]["main"][0][0]["node"] == "Deliver to Discord"
assert connections["Destination Configured?"]["main"][1][0]["node"] == "Fail Missing Destination"
# No credential-shaped literal values in the export.
for forbidden in ("sk-ant-api", "github_pat_", "ghp_"):
    assert forbidden not in raw
print("workflow contract and adversarial structure validation: PASS")
