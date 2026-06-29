#!/usr/bin/env python3
"""Validate n8n weekly summary workflow JSON against bounty #5 acceptance criteria."""

from __future__ import annotations

import json
import sys
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parent / "n8n-weekly-dev-summary.workflow.json"
REQUIRED_ENV = ("GITHUB_REPO", "ANTHROPIC_API_KEY", "DELIVERY_WEBHOOK_URL", "SUMMARY_LANGUAGE")
REQUIRED_NODES = (
    "Weekly Friday 5pm",
    "Fetch Commits",
    "Fetch Closed Issues",
    "Fetch Merged PRs",
    "Claude Weekly Summary",
    "Deliver to Slack/Discord",
)


def main() -> int:
    data = json.loads(WORKFLOW.read_text(encoding="utf-8"))
    nodes = {n["name"]: n for n in data.get("nodes", [])}
    errors: list[str] = []
    checks: list[str] = []

    cron = nodes.get("Weekly Friday 5pm", {}).get("parameters", {})
    cron_expr = ""
    for interval in cron.get("rule", {}).get("interval", []):
        if interval.get("field") == "cronExpression":
            cron_expr = interval.get("expression", "")
    if cron_expr == "0 17 * * 5":
        checks.append("OK cron Friday 17:00 (0 17 * * 5)")
    else:
        errors.append(f"cron mismatch: {cron_expr}")

    for name in REQUIRED_NODES:
        if name in nodes:
            checks.append(f"OK node: {name}")
        else:
            errors.append(f"missing node: {name}")

    claude_body = json.dumps(nodes.get("Claude Weekly Summary", {}).get("parameters", {}))
    if "claude-sonnet-4-20250514" in claude_body:
        checks.append("OK Claude model claude-sonnet-4-20250514")
    else:
        errors.append("Claude model not claude-sonnet-4-20250514")

    for env in REQUIRED_ENV:
        if env in json.dumps(data):
            checks.append(f"OK references env {env}")
        else:
            errors.append(f"workflow JSON does not reference {env}")

    gh_urls = [
        nodes.get("Fetch Commits", {}).get("parameters", {}).get("url", ""),
        nodes.get("Fetch Closed Issues", {}).get("parameters", {}).get("url", ""),
        nodes.get("Fetch Merged PRs", {}).get("parameters", {}).get("url", ""),
    ]
    if all("api.github.com" in u for u in gh_urls):
        checks.append("OK GitHub API URLs for commits/issues/PRs")
    else:
        errors.append("GitHub API URLs incomplete")

    webhook = nodes.get("Deliver to Slack/Discord", {}).get("parameters", {}).get("url", "")
    if "DELIVERY_WEBHOOK_URL" in webhook:
        checks.append("OK webhook delivery via DELIVERY_WEBHOOK_URL")

    report = Path(__file__).resolve().parent / "samples" / "workflow-validation-report.txt"
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# n8n workflow validation (automated)", "", "## Checks", *checks, "", "## Errors"]
    lines.extend(errors or ["none"])
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(report.read_text(encoding="utf-8"))

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
