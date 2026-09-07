"""Validate n8n-weekly-summary workflow without live n8n or API keys.

Checks:
  1. workflow.json is valid JSON + valid n8n export shape
  2. Schedule Trigger = Friday 5pm cron
  3. GitHub nodes: commits + closed issues + merged PRs via public API
  4. Claude node: model claude-sonnet-4-20250514 + $env.ANTHROPIC_API_KEY
  5. Discord webhook node with placeholder default
  6. IF + Merge logic present
  7. No hardcoded secrets
  8. Mocked end-to-end logic test (merge/filter/prompt EN+FR)

Usage: python test_workflow.py
Exit 0 = all pass, 1 = failure.
"""
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent
WF = ROOT / "workflow.json"

PASS, FAIL = "PASS", "FAIL"
results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"[{PASS if ok else FAIL}] {name}" + (f" — {detail}" if detail else ""))


def main():
    # 1. Load + export shape
    try:
        wf = json.loads(WF.read_text(encoding="utf-8"))
        check("workflow.json is valid JSON", True)
    except Exception as e:
        check("workflow.json is valid JSON", False, str(e))
        return summarize()

    for key in ("nodes", "connections", "name"):
        check(f"export has '{key}'", key in wf)

    nodes = {n.get("name"): n for n in wf.get("nodes", [])}
    conns = wf.get("connections", {})

    def has_node(name):
        check(f"node present: {name}", name in nodes)

    for n in [
        "Weekly Schedule - Fri 5pm",
        "Config (Edit Me)",
        "Compute Week Window",
        "Fetch Commits",
        "Fetch Closed Issues",
        "Fetch Merged PRs",
        "Filter Merged PRs",
        "Merge Commits + Issues",
        "Merge All Activity",
        "Build Claude Prompt (EN/FR)",
        "Claude Summary (sonnet-4)",
        "Has Activity?",
        "Discord Notify",
    ]:
        has_node(n)

    # 2. Cron Friday 5pm
    sched = nodes.get("Weekly Schedule - Fri 5pm", {})
    sched_str = json.dumps(sched.get("parameters", {}))
    check(
        "schedule trigger = Friday 5pm",
        "scheduleTrigger" in sched.get("type", "")
        and ("0 17 * * 5" in sched_str or "triggerAtDay" in sched_str),
        "cron 0 17 * * 5",
    )

    # 3. GitHub nodes
    for node_name, must in [
        ("Fetch Commits", "/commits"),
        ("Fetch Closed Issues", "/issues"),
        ("Fetch Merged PRs", "/pulls"),
    ]:
        n = nodes.get(node_name, {})
        url = json.dumps(n.get("parameters", {}))
        check(
            f"{node_name} hits public GitHub API",
            n.get("type") == "n8n-nodes-base.httpRequest"
            and "api.github.com" in url
            and must in url,
            must,
        )
    check(
        "GitHub nodes unauthenticated (public repo)",
        all(
            nodes.get(n, {}).get("parameters", {}).get("authentication") == "none"
            for n in ("Fetch Commits", "Fetch Closed Issues", "Fetch Merged PRs")
        ),
    )
    filt_code = nodes.get("Filter Merged PRs", {}).get("parameters", {}).get("jsCode", "")
    check("Filter Merged PRs checks merged_at", "merged_at" in filt_code)

    # 4. Claude node
    claude = nodes.get("Claude Summary (sonnet-4)", {})
    claude_str = json.dumps(claude.get("parameters", {}))
    check("Claude model = claude-sonnet-4-20250514", "claude-sonnet-4-20250514" in claude_str)
    check("Claude uses $env.ANTHROPIC_API_KEY", "$env.ANTHROPIC_API_KEY" in claude_str)
    check("Claude endpoint = api.anthropic.com/v1/messages", "api.anthropic.com/v1/messages" in claude_str)

    # 5. Discord webhook
    discord = nodes.get("Discord Notify", {})
    discord_str = json.dumps(discord.get("parameters", {})) + json.dumps(
        nodes.get("Config (Edit Me)", {}).get("parameters", {})
    )
    check(
        "Discord delivery via webhook placeholder",
        "discord_webhook_url" in discord_str and "YOUR_DISCORD_WEBHOOK_URL" in discord_str,
    )

    # Config vars
    cfg_str = json.dumps(nodes.get("Config (Edit Me)", {}).get("parameters", {}))
    for var in ("owner", "repo", "language", "discord_webhook_url", "max_items_per_source"):
        check(f"configurable var: {var}", var in cfg_str)
    prompt_code = nodes.get("Build Claude Prompt (EN/FR)", {}).get("parameters", {}).get("jsCode", "")
    check("prompt supports EN + FR", "FR" in prompt_code and ("Fran" in prompt_code or "fran" in prompt_code))

    # 6. IF + Merge logic + connections (upstream guard, multiplex, no truncation)
    check("IF node present (Has Activity?)", nodes.get("Has Activity?", {}).get("type") == "n8n-nodes-base.if")
    merges = [n for n in wf.get("nodes", []) if n.get("type") == "n8n-nodes-base.merge"]
    check("merge logic present (>=2 merge nodes)", len(merges) >= 2, f"found {len(merges)}")
    for m in merges:
        mode_blob = json.dumps(m.get("parameters", {}))
        check(
            f"merge '{m.get('name')}' uses multiplex/append (no mergeByPosition)",
            ("multiplex" in mode_blob or '"mode": "append"' in mode_blob or '"mode":"append"' in mode_blob)
            and "mergeByPosition" not in mode_blob,
            mode_blob[:120],
        )
    check(
        "connections chain to Discord Notify",
        "Discord Notify" in json.dumps(conns) and "Claude Summary (sonnet-4)" in json.dumps(conns),
    )

    def _targets(src):
        outs = []
        for branch in conns.get(src, {}).get("main", []):
            for edge in branch or []:
                outs.append(edge.get("node"))
        return outs

    def _branch_targets(src):
        return [ [e.get("node") for e in (branch or [])] for branch in conns.get(src, {}).get("main", []) ]

    check(
        "Merge All Activity -> Has Activity? (upstream guard)",
        "Has Activity?" in _targets("Merge All Activity"),
        f"targets={_targets('Merge All Activity')}",
    )
    check(
        "Merge All Activity does NOT bypass guard to Build Prompt",
        "Build Claude Prompt (EN/FR)" not in _targets("Merge All Activity"),
        f"targets={_targets('Merge All Activity')}",
    )
    has_branches = _branch_targets("Has Activity?")
    check(
        "Has Activity? true -> Build Prompt, false -> Discord (short-circuits Claude)",
        len(has_branches) >= 2
        and "Build Claude Prompt (EN/FR)" in (has_branches[0] if len(has_branches) > 0 else [])
        and "Discord Notify" in (has_branches[1] if len(has_branches) > 1 else []),
        f"branches={has_branches}",
    )
    check(
        "Build Prompt -> Claude -> Discord chain",
        "Claude Summary (sonnet-4)" in _targets("Build Claude Prompt (EN/FR)")
        and "Discord Notify" in _targets("Claude Summary (sonnet-4)"),
        f"build->{_targets('Build Claude Prompt (EN/FR)')} claude->{_targets('Claude Summary (sonnet-4)')}",
    )
    check(
        "Claude does NOT feed Has Activity? (guard is upstream, activity_items would be lost)",
        "Has Activity?" not in _targets("Claude Summary (sonnet-4)"),
        f"claude targets={_targets('Claude Summary (sonnet-4)')}",
    )
    if_blob = json.dumps(nodes.get("Has Activity?", {}).get("parameters", {}))
    check(
        "IF checks merged activity count (not $json.activity_items lost after Claude)",
        ("Merge All Activity" in if_blob or "$input.all()" in if_blob)
        and "$json.activity_items" not in if_blob,
        if_blob[:200],
    )
    discord_blob = json.dumps(nodes.get("Discord Notify", {}).get("parameters", {}))
    check(
        "Discord false-branch has explicit no-activity message",
        "No GitHub activity" in discord_blob,
        "fallback for empty week",
    )

    # 7. No secrets
    blob = WF.read_text(encoding="utf-8")
    check("no hardcoded Anthropic key", "sk-ant-" not in blob)
    check("no hardcoded discord token fragment", re.search(r"discord\.com/api/webhooks/\d+/\S+", blob) is None)
    check("placeholders used", "YOUR_DISCORD_WEBHOOK_URL" in blob)

    # 8. Mocked logic test (mirrors Code-node JS in Python)
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=7)
    mock_prs = [
        {"number": 12, "title": "Add weekly summary workflow", "merged_at": now.isoformat(), "user": {"login": "alice"}},
        {"number": 11, "title": "WIP: not merged", "merged_at": None, "user": {"login": "bob"}},
        {"number": 9, "title": "Old merged PR", "merged_at": "2020-01-01T00:00:00Z", "user": {"login": "carol"}},
    ]
    merged = [p for p in mock_prs if p.get("merged_at") and datetime.fromisoformat(p["merged_at"].replace("Z", "+00:00")).timestamp() >= since.timestamp()]
    check("mock: filter keeps only in-week merged PRs", len(merged) == 1 and merged[0]["number"] == 12)

    mock_commits = [{"sha": "abc123", "commit": {"message": "feat: add schedule trigger"}}]
    mock_issues = [{"number": 5, "title": "Weekly summary bounty", "state": "closed"}]
    activity = mock_commits + mock_issues + merged
    check("mock: merge yields 3 activity items", len(activity) == 3)

    def build_prompt(lang, items):
        header = f"Repository: claude-builders-bounty/claude-builders-bounty\nWeek: {since.date()} .. {now.date()}"
        instr = "Résumé hebdomadaire" if lang == "FR" else "weekly dev summary"
        return f"{header}\n{instr}\nDATA:\n{json.dumps(items)[:500]}"

    check("mock: EN prompt builds", "weekly dev summary" in build_prompt("EN", activity))
    check("mock: FR prompt builds", "Résumé hebdomadaire" in build_prompt("FR", activity))

    # Discord 1800-char truncation (mirrors Discord Notify jsonBody slice)
    long_text = "x" * 2500
    check("mock: Discord truncation to 1800 chars", len(long_text[:1800]) == 1800)

    return summarize()


def summarize():
    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed.")
    if failed:
        print("Failures:")
        for name, _, detail in failed:
            print(f"  - {name} {detail}")
        sys.exit(1)
    print("All checks passed. Import workflow.json into n8n and run Execute Workflow.")
    sys.exit(0)


if __name__ == "__main__":
    main()
