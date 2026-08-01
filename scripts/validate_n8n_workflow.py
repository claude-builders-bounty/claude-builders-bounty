#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "workflows" / "n8n-weekly-dev-summary.json"

REQUIRED_NODES = {
    "Weekly Friday 5pm",
    "Set Config",
    "Fetch Commits",
    "Fetch Closed Issues",
    "Fetch Closed PRs",
    "Combine Activity",
    "Claude Summary",
    "Send Email",
}


def load_workflow():
    return json.loads(WORKFLOW.read_text())


def node_by_name(workflow, name):
    for node in workflow["nodes"]:
        if node.get("name") == name:
            return node
    raise AssertionError(f"missing node: {name}")


def validate_shape(workflow):
    node_names = {node["name"] for node in workflow["nodes"]}
    missing = REQUIRED_NODES - node_names
    if missing:
        raise AssertionError(f"missing required nodes: {', '.join(sorted(missing))}")

    schedule = node_by_name(workflow, "Weekly Friday 5pm")
    interval = schedule["parameters"]["rule"]["interval"][0]
    if interval.get("field") != "weeks" or interval.get("triggerAtDay") != [5]:
        raise AssertionError("schedule trigger must run weekly on Friday")
    if interval.get("triggerAtHour") != 17:
        raise AssertionError("schedule trigger must run at 17:00")

    raw = WORKFLOW.read_text()
    required_tokens = [
        "GITHUB_REPO",
        "GITHUB_TOKEN",
        "ANTHROPIC_API_KEY",
        "SUMMARY_EMAIL_TO",
        "SUMMARY_LANGUAGE",
        "claude-sonnet-4-20250514",
    ]
    missing_tokens = [token for token in required_tokens if token not in raw]
    if missing_tokens:
        raise AssertionError(f"missing configuration tokens: {', '.join(missing_tokens)}")


def check_code_node_syntax(workflow):
    for node in workflow["nodes"]:
        js_code = node.get("parameters", {}).get("jsCode")
        if not js_code:
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as handle:
            handle.write(js_code)
            filename = handle.name
        try:
            subprocess.run(["node", "--check", filename], check=True, capture_output=True, text=True)
        finally:
            Path(filename).unlink(missing_ok=True)


def github_get(path, token):
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"https://api.github.com{path}", headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def dry_run_github(repo):
    token = os.environ.get("GITHUB_TOKEN", "")
    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(timespec="seconds")
    encoded_since = urllib.parse.quote(since)
    encoded_repo = urllib.parse.quote(repo, safe="/")

    commits = github_get(f"/repos/{encoded_repo}/commits?since={encoded_since}&per_page=100", token)
    issues = github_get(f"/repos/{encoded_repo}/issues?state=closed&since={encoded_since}&per_page=100", token)
    pulls = github_get(
        f"/repos/{encoded_repo}/pulls?state=closed&sort=updated&direction=desc&per_page=100",
        token,
    )

    closed_issues = [issue for issue in issues if "pull_request" not in issue]
    merged_pulls = [
        pull
        for pull in pulls
        if pull.get("merged_at") and pull["merged_at"] >= since.replace("+00:00", "Z")
    ]
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1200,
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Write a concise weekly development summary in EN for {repo}. "
                    "Include highlights, merged PRs, closed issues, and notable risks."
                ),
            }
        ],
    }
    return {
        "repo": repo,
        "since": since,
        "commits": len(commits),
        "closed_issues": len(closed_issues),
        "merged_pull_requests": len(merged_pulls),
        "claude_request_model": payload["model"],
    }


def main():
    parser = argparse.ArgumentParser(description="Validate the n8n weekly dev summary workflow.")
    parser.add_argument("--live-repo", help="Optional public GitHub repo for a live API dry run.")
    args = parser.parse_args()

    workflow = load_workflow()
    validate_shape(workflow)
    check_code_node_syntax(workflow)
    print(f"workflow OK: {len(workflow['nodes'])} nodes; Code node syntax OK")

    if args.live_repo:
        summary = dry_run_github(args.live_repo)
        print("github dry run OK:")
        print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        sys.exit(1)
