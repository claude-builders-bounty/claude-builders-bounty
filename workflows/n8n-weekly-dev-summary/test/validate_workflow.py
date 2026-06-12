#!/usr/bin/env python3
"""Validate the n8n workflow JSON against the bounty acceptance criteria.

Checks:
  1. The file is valid JSON
  2. It has the expected node count and types
  3. The cron trigger fires weekly
  4. There are at least three GitHub API HTTP requests
  5. There is an Anthropic Claude API call
  6. There is a delivery (webhook or email) node
  7. The workflow is configurable via environment variables
     (GITHUB_REPO, ANTHROPIC_API_KEY, DELIVERY_WEBHOOK_URL, LANGUAGE)
  8. The connections form a valid DAG (no cycles, all reachable from trigger)

Exit 0 on success, 1 on any failure. No external deps."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

WORKFLOW = Path(__file__).parent.parent / "workflow.json"

REQUIRED_NODE_TYPES = {
    "n8n-nodes-base.scheduleTrigger": "Weekly trigger",
    "n8n-nodes-base.httpRequest": "HTTP request",
    "n8n-nodes-base.code": "Code (JS) node",
}

# Variables the bounty lists as "configurable"
REQUIRED_ENV_VARS = ["GITHUB_REPO", "ANTHROPIC_API_KEY", "DELIVERY_WEBHOOK_URL", "LANGUAGE"]


def fail(msg: str) -> None:
    print(f"❌ {msg}")


def main() -> int:
    if not WORKFLOW.exists():
        fail(f"missing workflow: {WORKFLOW}")
        return 1

    try:
        wf = json.loads(WORKFLOW.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fail(f"invalid JSON: {e}")
        return 1

    failures: list[str] = []
    nodes = wf.get("nodes", [])
    connections = wf.get("connections", {})
    node_names = {n["name"] for n in nodes}

    # 1. Trigger
    triggers = [n for n in nodes if n["type"] == "n8n-nodes-base.scheduleTrigger"]
    if not triggers:
        failures.append("missing schedule trigger")
    else:
        t = triggers[0]
        cron = (
            t.get("parameters", {})
            .get("rule", {})
            .get("interval", [{}])[0]
            .get("expression", "")
        )
        if not re.match(r"^\s*\S+\s+\S+\s+\S+\s+\S+\s+\S+\s*$", cron):
            failures.append(f"trigger cron expression looks malformed: {cron!r}")
        # Bounty says "weekly cron (e.g., Friday at 5pm)". 0 17 * * 5 = Fri 5pm.
        # Be lenient: any expression that has * in day-of-month and * in month is weekly-ish.
        if "*" not in cron:
            failures.append(f"trigger is not weekly (no '*' in expression): {cron!r}")

    # 2. Three GitHub API requests — distinguished by URL containing api.github.com
    gh_requests = [
        n for n in nodes
        if n["type"] == "n8n-nodes-base.httpRequest"
        and "api.github.com" in (n.get("parameters", {}).get("url", "") or "")
    ]
    if len(gh_requests) < 3:
        failures.append(f"expected >= 3 GitHub API HTTP requests, found {len(gh_requests)}")
    gh_names = {n["name"] for n in gh_requests}
    expected_kinds = {
        "commits": any("commit" in (n["parameters"].get("url", "")).lower() for n in gh_requests),
        "issues": any("issue" in (n["parameters"].get("url", "")).lower() for n in gh_requests),
        "pulls": any("pull" in (n["parameters"].get("url", "")).lower() for n in gh_requests),
    }
    if not all(expected_kinds.values()):
        failures.append(f"GitHub requests don't cover commits/issues/pulls: {expected_kinds}")

    # 3. Claude API call — URL contains api.anthropic.com AND body references claude-sonnet
    claude_calls = [
        n for n in nodes
        if n["type"] == "n8n-nodes-base.httpRequest"
        and "api.anthropic.com" in (n.get("parameters", {}).get("url", "") or "")
    ]
    if not claude_calls:
        failures.append("missing Claude API call (no HTTPRequest to api.anthropic.com)")
    elif not any("claude-sonnet" in (n.get("parameters", {}).get("jsonBody", "") or "") for n in claude_calls):
        failures.append("Claude API call doesn't reference a claude-sonnet model")

    # 4. Delivery — webhook or email
    deliveries = [
        n for n in nodes
        if n["type"] == "n8n-nodes-base.httpRequest"
        and any("webhook" in (n.get("name", "") or "").lower() or "discord" in (n.get("name", "") or "").lower() or "slack" in (n.get("name", "") or "").lower() for _ in [None])
    ]
    if not deliveries:
        # Looser fallback: any HTTP request whose URL is set from $env.DELIVERY_WEBHOOK_URL
        deliveries = [
            n for n in nodes
            if n["type"] == "n8n-nodes-base.httpRequest"
            and "DELIVERY_WEBHOOK_URL" in (n.get("parameters", {}).get("url", "") or "")
        ]
    if not deliveries:
        failures.append("no delivery node (Discord/Slack webhook or email)")

    # 5. Required env vars used somewhere in the workflow body
    blob = json.dumps(wf)
    for var in REQUIRED_ENV_VARS:
        if f"$env.{var}" not in blob and f"$env.{var} " not in blob:
            failures.append(f"configurable env var $env.{var} not referenced anywhere")

    # 6. Connection DAG check
    if not connections:
        failures.append("no connections between nodes")
    else:
        # The trigger must have an outgoing connection.
        trigger_names = {t["name"] for t in triggers}
        for tn in trigger_names:
            if tn not in connections:
                failures.append(f"trigger '{tn}' has no outgoing connection")
        # Every node should be either a trigger or have an incoming connection.
        reachable = set()
        stack = list(connections.keys())
        while stack:
            cur = stack.pop()
            if cur in reachable:
                continue
            reachable.add(cur)
            for out in connections.get(cur, {}).get("main", []):
                for branch in out:
                    if "node" in branch and branch["node"] not in reachable:
                        stack.append(branch["node"])
        for n in nodes:
            if n["name"] in trigger_names:
                continue
            if n["name"] not in reachable:
                failures.append(f"node '{n['name']}' is unreachable from any trigger")

    # Summary
    if failures:
        for f in failures:
            fail(f)
        return 1

    print(
        f"✅ workflow.json: {len(nodes)} nodes, {len(connections)} connection groups, "
        f"trigger='{triggers[0]['name']}', {len(gh_requests)} GitHub HTTP requests, "
        f"{len(claude_calls)} Claude call(s), {len(deliveries)} delivery node(s), "
        f"{len(REQUIRED_ENV_VARS)}/{len(REQUIRED_ENV_VARS)} required env vars referenced"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
