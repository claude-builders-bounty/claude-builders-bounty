#!/usr/bin/env python3
"""Static validation for the n8n weekly GitHub summary workflow."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "workflows" / "n8n-weekly-dev-summary.json"


def node(workflow: dict, name: str) -> dict:
    for item in workflow["nodes"]:
        if item.get("name") == name:
            return item
    raise AssertionError(f"missing node: {name}")


def main() -> None:
    workflow = json.loads(WORKFLOW.read_text(encoding="utf-8"))
    nodes = workflow.get("nodes")
    assert isinstance(nodes, list) and len(nodes) >= 10, "workflow must contain a complete node graph"
    names = {item.get("name") for item in nodes}
    required = {
        "Weekly Friday 17:00",
        "Build Config",
        "GitHub Commits",
        "GitHub Closed Issues",
        "GitHub Merged PRs",
        "Prepare Claude Prompt",
        "Claude Narrative Summary",
        "Format Delivery",
        "Delivery Mode Email?",
        "Send Discord Webhook",
        "Send Email",
    }
    missing = required - names
    assert not missing, f"missing required nodes: {sorted(missing)}"

    schedule = node(workflow, "Weekly Friday 17:00")
    interval = schedule["parameters"]["rule"]["interval"][0]
    assert interval["field"] == "weeks", "trigger must be weekly"
    assert interval["triggerAtDay"] == [5], "trigger must run on Friday"
    assert interval["triggerAtHour"] == 17, "trigger must run at 17:00"

    commits = node(workflow, "GitHub Commits")
    issues = node(workflow, "GitHub Closed Issues")
    prs = node(workflow, "GitHub Merged PRs")
    assert "/commits?" in commits["parameters"]["url"]
    assert "/issues?state=closed" in issues["parameters"]["url"]
    assert "search/issues" in prs["parameters"]["url"] and "is:merged" in prs["parameters"]["url"]
    for api_node in (commits, issues, prs, node(workflow, "Claude Narrative Summary"), node(workflow, "Send Discord Webhook")):
        assert api_node.get("continueOnFail") is False, f"{api_node['name']} must fail loudly"

    config_code = node(workflow, "Build Config")["parameters"]["jsCode"]
    assert "GITHUB_REPO" in config_code
    assert "SUMMARY_LANGUAGE" in config_code
    assert "DELIVERY_MODE" in config_code

    prompt_code = node(workflow, "Prepare Claude Prompt")["parameters"]["jsCode"]
    assert "flattenJson" in prompt_code
    assert "Array.isArray(i.json)" in prompt_code
    assert "Array.isArray(commits)" in prompt_code
    assert "Array.isArray(closedRaw)" in prompt_code
    assert "Array.isArray(mergedPRs)" in prompt_code
    assert "mergedSearch.items" in prompt_code
    assert "mergedRaw.filter" in prompt_code
    assert "inWindow(item.closed_at)" in prompt_code
    assert "pull_request?.merged_at" in prompt_code
    assert "searchResultWithoutMergedAt" in prompt_code
    assert "item.state === 'closed'" in prompt_code
    assert "Overview, Highlights, Risks/Follow-ups, Next Week" in prompt_code

    claude = node(workflow, "Claude Narrative Summary")
    body = claude["parameters"]["jsonBody"]
    assert "claude-sonnet-4-20250514" in body
    assert "ANTHROPIC_API_KEY" in json.dumps(claude)

    delivery_if = node(workflow, "Delivery Mode Email?")
    assert delivery_if["parameters"]["conditions"]["string"][0]["value2"] == "email"
    assert "discordWebhookUrl" in json.dumps(node(workflow, "Send Discord Webhook"))
    assert "DISCORD_WEBHOOK_URL" in json.dumps(node(workflow, "Build Config"))
    assert "EMAIL_TO" in json.dumps(node(workflow, "Build Config"))

    connections = workflow.get("connections", {})
    assert "Weekly Friday 17:00" in connections
    assert "Build Config" in connections
    assert "Delivery Mode Email?" in connections

    print("n8n workflow validation passed")


if __name__ == "__main__":
    main()
