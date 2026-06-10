#!/usr/bin/env python3
"""Validator for n8n-weekly-dev-summary.workflow.json (claude-builders-bounty #5).

Stdlib-only, CI-runnable proof artifact. Checks structure, schedule, graph
integrity, credential hygiene, and the absence of hardcoded secrets.

Usage:  python3 validate_workflow.py [path/to/workflow.json]
Exit:   0 = all checks pass · 1 = any check fails
"""
import json
import pathlib
import re
import sys

WF = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else
                  pathlib.Path(__file__).parent / "n8n-weekly-dev-summary.workflow.json")

EXPECTED_NODES = {
    "Weekly Trigger (Fri 5pm)": "n8n-nodes-base.scheduleTrigger",
    "Config": "n8n-nodes-base.set",
    "Compute Window": "n8n-nodes-base.code",
    "GitHub: Commits": "n8n-nodes-base.httpRequest",
    "GitHub: Merged PRs": "n8n-nodes-base.httpRequest",
    "GitHub: Closed Issues": "n8n-nodes-base.httpRequest",
    "Build Prompt": "n8n-nodes-base.code",
    "Claude (Messages API)": "n8n-nodes-base.httpRequest",
    "Format Summary": "n8n-nodes-base.code",
    "Deliver (Discord/Slack)": "n8n-nodes-base.httpRequest",
}
CRED_NODES = {"GitHub: Commits", "GitHub: Merged PRs", "GitHub: Closed Issues",
              "Claude (Messages API)"}
SECRET_PATTERNS = [
    (r"sk-ant-[A-Za-z0-9_\-]{8,}", "hardcoded Anthropic key"),
    (r"ghp_[A-Za-z0-9]{20,}", "hardcoded GitHub classic PAT"),
    (r"github_pat_[A-Za-z0-9_]{20,}", "hardcoded GitHub fine-grained PAT"),
    (r"discord\.com/api/webhooks/\d+/[A-Za-z0-9_\-]+", "hardcoded Discord webhook"),
    (r"hooks\.slack\.com/services/T[A-Za-z0-9/]+", "hardcoded Slack webhook"),
]

failures = []
checks = 0


def check(name, ok, detail=""):
    global checks
    checks += 1
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(name)


raw = WF.read_text()
w = json.loads(raw)
check("JSON parses", True, f"{WF.name}, {len(raw)} bytes")

nodes = {n["name"]: n for n in w.get("nodes", [])}
check("exactly 10 nodes", len(nodes) == 10, f"found {len(nodes)}")
check("no duplicate node names", len(nodes) == len(w.get("nodes", [])))

for name, ntype in EXPECTED_NODES.items():
    n = nodes.get(name)
    check(f"node present: {name}", n is not None and n.get("type") == ntype,
          n.get("type") if n else "MISSING")

# Schedule: Friday 5pm cron
rule = nodes["Weekly Trigger (Fri 5pm)"]["parameters"]["rule"]["interval"][0]
check("weekly cron is Friday 5pm", rule.get("expression") == "0 17 * * 5",
      rule.get("expression"))

# Graph integrity: walk main connections from trigger; must reach Deliver, cover all 10
conns = w.get("connections", {})
reached, stack = set(), ["Weekly Trigger (Fri 5pm)"]
while stack:
    cur = stack.pop()
    if cur in reached:
        continue
    reached.add(cur)
    for branch in conns.get(cur, {}).get("main", []):
        for hop in branch:
            stack.append(hop["node"])
check("graph reaches Deliver from trigger", "Deliver (Discord/Slack)" in reached)
check("all 10 nodes reachable (no orphans)", reached == set(nodes),
      f"unreached: {sorted(set(nodes) - reached)}" if reached != set(nodes) else "")
check("Deliver is terminal (no outgoing)", "Deliver (Discord/Slack)" not in conns)

# Credential hygiene: auth via named n8n credentials, never inline
for name in sorted(CRED_NODES):
    n = nodes[name]
    ok = (n["parameters"].get("authentication") == "genericCredentialType"
          and "httpHeaderAuth" in n.get("credentials", {}))
    check(f"credentialed via Header Auth: {name}", ok)

# Claude API specifics
claude = nodes["Claude (Messages API)"]["parameters"]
check("Claude endpoint correct", claude.get("url") == "https://api.anthropic.com/v1/messages")
check("anthropic-version header set", any(
    h.get("name") == "anthropic-version"
    for h in claude.get("headerParameters", {}).get("parameters", [])))
check("model pinned in prompt builder", "claude-sonnet-4-20250514" in raw)

# Secret scan on the whole file
for pat, label in SECRET_PATTERNS:
    check(f"no {label}", re.search(pat, raw) is None)

print(f"\n{checks - len(failures)}/{checks} checks passed.")
if failures:
    print("FAILED:", ", ".join(failures))
    sys.exit(1)
print("Workflow validated: import-ready, linear, credential-clean.")
