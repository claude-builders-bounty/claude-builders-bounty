#!/usr/bin/env python3
"""
dry_run.py — Simulates the n8n weekly-dev-summary workflow in Python.

This is a faithful re-implementation of the n8n workflow so the deliverable
can be tested without a live n8n / Docker / real webhooks. It:

  1. Pulls commits / closed issues / merged PRs from the GitHub REST API
     (or falls back to a deterministic offline fixture when no network /
     no token is available).
  2. Normalises & merges the three streams exactly as the n8n "Code" node
     does (Merge & Format Data node).
  3. Calls the Anthropic Messages API with claude-sonnet-4-20250514, using
     the same system + user prompt template baked into the n8n workflow.
     When ANTHROPIC_API_KEY is missing the call is short-circuited and a
     mock narrative is generated so the dry-run still succeeds.
  4. Formats the response into a Discord-friendly markdown message exactly
     like the "Format Discord Message" n8n node and prints it.

Run it:

    python3 dry_run.py                              # uses defaults
    python3 dry_run.py --owner vercel --repo next.js
    GITHUB_TOKEN=ghp_...  ANTHROPIC_API_KEY=sk-ant-...  python3 dry_run.py

Exit code 0 == success.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any


# ----------------------------------------------------------------------------- #
# Config (mirrors the "Config (Set Variables)" Set node in the n8n workflow)   #
# ----------------------------------------------------------------------------- #

DEFAULT_OWNER = "claude-builders-bounty"
DEFAULT_REPO = "claude-builders-bounty"
DEFAULT_LANGUAGE = "EN"
DEFAULT_LOOKBACK_DAYS = 7
DEFAULT_MAX_ITEMS = 100
DEFAULT_WEBHOOK_URL = "https://discord.com/api/webhooks/REPLACE_ME"
CLAUDE_MODEL = "claude-sonnet-4-20250514"


# ----------------------------------------------------------------------------- #
# Step 1+2: GitHub fetch (mirrors the three parallel HTTP Request nodes)       #
# ----------------------------------------------------------------------------- #

def _github_get(path: str, token: str | None, timeout: int = 15) -> Any:
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "weekly-dev-summary-dryrun/1.0")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
        return json.loads(r.read().decode("utf-8"))


def _fixture() -> dict[str, list[dict]]:
    """Deterministic offline data so the dry-run works without credentials."""
    now = datetime.now(timezone.utc)
    return {
        "commits": [
            {
                "sha": "a1b2c3d4e5f60718293a4b5c6d7e8f9001020304",
                "html_url": "https://github.com/o/r/commit/a1b2c3d",
                "commit": {
                    "author": {"name": "Alice", "date": now.isoformat()},
                    "message": "feat: add weekly summary workflow\n",
                },
            },
            {
                "sha": "b2c3d4e5f60718293a4b5c6d7e8f9001020304a1",
                "html_url": "https://github.com/o/r/commit/b2c3d4e",
                "commit": {
                    "author": {"name": "Bob", "date": (now - timedelta(days=1)).isoformat()},
                    "message": "fix: correct date math in dry-run\n",
                },
            },
            {
                "sha": "c3d4e5f60718293a4b5c6d7e8f9001020304a1b2",
                "html_url": "https://github.com/o/r/commit/c3d4e5f",
                "commit": {
                    "author": {"name": "Alice", "date": (now - timedelta(days=2)).isoformat()},
                    "message": "docs: add README setup section\n",
                },
            },
        ],
        "issues": [
            {
                "number": 5,
                "title": "[BOUNTY $200] WORKFLOW: n8n + Claude Code — automated weekly dev summary",
                "user": {"login": "maintainer"},
                "html_url": "https://github.com/o/r/issues/5",
                "closed_at": now.isoformat(),
                "pull_request": None,
            },
            {
                "number": 12,
                "title": "bug: cron fires twice on DST boundary",
                "user": {"login": "carol"},
                "html_url": "https://github.com/o/r/issues/12",
                "closed_at": (now - timedelta(days=1)).isoformat(),
                "pull_request": None,
            },
        ],
        "pulls": [
            {
                "number": 42,
                "title": "feat: Claude API integration",
                "user": {"login": "Alice"},
                "html_url": "https://github.com/o/r/pull/42",
                "merged_at": now.isoformat(),
                "additions": 240,
                "deletions": 18,
            },
            {
                "number": 43,
                "title": "chore: bump deps",
                "user": {"login": "Bob"},
                "html_url": "https://github.com/o/r/pull/43",
                "merged_at": (now - timedelta(days=2)).isoformat(),
                "additions": 12,
                "deletions": 12,
            },
        ],
    }


def fetch_github(owner: str, repo: str, lookback_days: int, max_items: int,
                 token: str | None) -> tuple[dict, str]:
    """Return (data, source) where source is 'live' or 'fixture'."""
    since = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).isoformat()
    qs = urllib.parse.urlencode({
        "since": since,
        "per_page": max_items,
    })
    try:
        commits = _github_get(f"/repos/{owner}/{repo}/commits?{qs}", token)
        issues = _github_get(f"/repos/{owner}/{repo}/issues?{qs}&state=closed", token)
        prs = _github_get(
            f"/repos/{owner}/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page={max_items}",
            token,
        )
        return {"commits": commits, "issues": issues, "pulls": prs}, "live"
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError) as exc:
        print(f"[dry-run] GitHub fetch failed ({exc.__class__.__name__}: {exc}); using fixture.",
              file=sys.stderr)
        return _fixture(), "fixture"


# ----------------------------------------------------------------------------- #
# Step 3: Merge & format (mirrors the n8n "Merge & Format Data" Code node)    #
# ----------------------------------------------------------------------------- #

def merge_and_format(raw: dict, config: dict) -> dict:
    cutoff = (datetime.now(timezone.utc)
              - timedelta(days=config["lookback_days"])).isoformat()
    commits_raw = raw.get("commits") or []
    issues_raw = raw.get("issues") or []
    prs_raw = raw.get("pulls") or []
    closed_issues = [i for i in issues_raw if not i.get("pull_request")]
    merged_prs = [p for p in prs_raw if p.get("merged_at") and p["merged_at"] >= cutoff]

    def _commit(c):
        return {
            "hash": (c.get("sha") or "")[:7],
            "message": (c.get("commit", {}).get("message") or "").split("\n")[0][:200],
            "author": (c.get("commit", {}).get("author", {}).get("name")
                       or c.get("author", {}).get("login") or "unknown"),
            "url": c.get("html_url", ""),
            "date": c.get("commit", {}).get("author", {}).get("date", ""),
        }

    def _issue(i):
        return {
            "number": i.get("number"),
            "title": i.get("title", ""),
            "author": (i.get("user") or {}).get("login", "unknown"),
            "url": i.get("html_url", ""),
            "closedAt": i.get("closed_at", ""),
        }

    def _pr(p):
        return {
            "number": p.get("number"),
            "title": p.get("title", ""),
            "author": (p.get("user") or {}).get("login", "unknown"),
            "url": p.get("html_url", ""),
            "mergedAt": p.get("merged_at", ""),
            "additions": p.get("additions", 0),
            "deletions": p.get("deletions", 0),
        }

    return {
        "owner": config["owner"],
        "repo": config["repo"],
        "language": config.get("language", "EN"),
        "webhookUrl": config.get("webhookUrl", DEFAULT_WEBHOOK_URL),
        "lookbackDays": config["lookback_days"],
        "weekEnding": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "windowStart": cutoff,
        "commits": [_commit(c) for c in commits_raw],
        "closedIssues": [_issue(i) for i in closed_issues],
        "mergedPRs": [_pr(p) for p in merged_prs],
        "stats": {
            "totalCommits": len(commits_raw),
            "totalIssuesClosed": len(closed_issues),
            "totalPRsMerged": len(merged_prs),
        },
    }


# ----------------------------------------------------------------------------- #
# Step 4: Claude call (mirrors the n8n "Claude API — Generate Summary" node)   #
# ----------------------------------------------------------------------------- #

def _claude_prompt(data: dict) -> dict:
    """Body of POST https://api.anthropic.com/v1/messages — mirrors the workflow."""
    system = (
        "You are an engineering lead writing a concise weekly narrative summary "
        "for a GitHub repository. Highlight: top contributors, areas of focus, "
        "themes, and any notable trends. Use a narrative tone, not a bullet list. "
        f"Keep it under 350 words. Write in {data.get('language') or 'EN'}."
    )
    def _section(title: str, items: list[str], empty: str = "(none)") -> list[str]:
        return [title, *(items if items else [empty]), ""]

    user_lines = [
        f"Generate a weekly development summary for the repository "
        f"**{data['owner']}/{data['repo']}** for the week ending {data['weekEnding']}.",
        "",
        "## Stats",
        f"- Commits this week: {data['stats']['totalCommits']}",
        f"- Issues closed: {data['stats']['totalIssuesClosed']}",
        f"- PRs merged: {data['stats']['totalPRsMerged']}",
        "",
    ]
    user_lines += _section(
        "## Commits",
        [f"- `{c['hash']}` {c['message']} — {c['author']}" for c in data["commits"]],
    )
    user_lines += _section(
        "## Issues closed",
        [f"- #{i['number']} {i['title']} (opened by {i['author']})" for i in data["closedIssues"]],
    )
    user_lines += _section(
        "## PRs merged",
        [f"- #{p['number']} {p['title']} (by {p['author']}, +{p['additions']}/-{p['deletions']})"
         for p in data["mergedPRs"]],
    )
    user_lines += [
        "Write a narrative weekly summary highlighting key themes, top contributors, "
        "and any trends you observe. If there is no activity, say so explicitly. "
        "Do not invent any data.",
    ]
    return {
        "model": CLAUDE_MODEL,
        "max_tokens": 2048,
        "system": system,
        "messages": [{"role": "user", "content": "\n".join(user_lines)}],
    }


def _mock_narrative(data: dict) -> str:
    """Deterministic mock used when ANTHROPIC_API_KEY is missing."""
    top_authors = sorted(
        {c["author"] for c in data["commits"]}
        | {i["author"] for i in data["closedIssues"]}
        | {p["author"] for p in data["mergedPRs"]}
    )
    s = data["stats"]
    lang = data.get("language") or "EN"
    if s["totalCommits"] == 0 and s["totalIssuesClosed"] == 0 and s["totalPRsMerged"] == 0:
        return ("It was a quiet week on the repository — no commits, closed issues, "
                "or merged PRs were recorded in the lookback window.")
    return (
        f"This week **{data['owner']}/{data['repo']}** saw {s['totalCommits']} commits, "
        f"{s['totalIssuesClosed']} issues closed and {s['totalPRsMerged']} PRs merged. "
        f"Active contributors included {', '.join(top_authors) if top_authors else 'no one'}. "
        f"Themes this week centred on the merged work captured in PRs, with bug-fix and "
        f"documentation commits rounding out the picture. (Mock narrative — set "
        f"ANTHROPIC_API_KEY to call the real {CLAUDE_MODEL} model. Output language: {lang}.)"
    )


def call_claude(data: dict, api_key: str | None) -> tuple[str, str]:
    """Return (narrative_text, source) where source is 'api' or 'mock'."""
    body = _claude_prompt(data)
    if not api_key:
        return _mock_narrative(data), "mock"

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
    )
    req.add_header("x-api-key", api_key)
    req.add_header("anthropic-version", "2023-06-01")
    req.add_header("content-type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310
            payload = json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError) as exc:
        print(f"[dry-run] Claude call failed ({exc.__class__.__name__}: {exc}); using mock.",
              file=sys.stderr)
        return _mock_narrative(data), "mock"

    parts = []
    for block in payload.get("content") or []:
        if block.get("type") == "text" and block.get("text"):
            parts.append(block["text"])
    return ("\n".join(parts) if parts else _mock_narrative(data),
            "api" if parts else "mock")


# ----------------------------------------------------------------------------- #
# Step 5: Format Discord message (mirrors the n8n "Format Discord Message")    #
# ----------------------------------------------------------------------------- #

def format_discord(data: dict, narrative: str) -> str:
    s = data["stats"]
    repo = f"{data['owner']}/{data['repo']}"
    summary = (
        f"📬 **Weekly Dev Summary — {repo}**\n"
        f"_Week ending {data['weekEnding']}_\n\n"
        f"**Stats** — {s['totalCommits']} commits · "
        f"{s['totalIssuesClosed']} issues closed · "
        f"{s['totalPRsMerged']} PRs merged\n\n"
        + narrative[:1900]
    )
    return summary


# ----------------------------------------------------------------------------- #
# CLI                                                                            #
# ----------------------------------------------------------------------------- #

def main() -> int:
    p = argparse.ArgumentParser(description="Simulate the n8n weekly dev summary workflow.")
    p.add_argument("--owner", default=os.environ.get("GH_OWNER", DEFAULT_OWNER))
    p.add_argument("--repo", default=os.environ.get("GH_REPO", DEFAULT_REPO))
    p.add_argument("--language", default=os.environ.get("LANGUAGE", DEFAULT_LANGUAGE),
                   choices=["EN", "FR"])
    p.add_argument("--lookback-days", type=int,
                   default=int(os.environ.get("LOOKBACK_DAYS", DEFAULT_LOOKBACK_DAYS)))
    p.add_argument("--max-items", type=int,
                   default=int(os.environ.get("MAX_ITEMS", DEFAULT_MAX_ITEMS)))
    p.add_argument("--webhook-url", default=os.environ.get("DISCORD_WEBHOOK_URL", DEFAULT_WEBHOOK_URL))
    p.add_argument("--json", action="store_true",
                   help="Emit the final Discord payload as JSON instead of pretty text.")
    args = p.parse_args()

    config = {
        "owner": args.owner,
        "repo": args.repo,
        "language": args.language,
        "lookback_days": args.lookback_days,
        "max_items": args.max_items,
        "webhookUrl": args.webhook_url,
    }

    print(f"[1/4] Fetching GitHub activity for {config['owner']}/{config['repo']} "
          f"(last {config['lookback_days']} days)…")
    raw, gh_source = fetch_github(config["owner"], config["repo"],
                                  config["lookback_days"], config["max_items"],
                                  os.environ.get("GITHUB_TOKEN"))
    print(f"      source: {gh_source}")

    print("[2/4] Merging & normalising…")
    data = merge_and_format(raw, config)
    print(f"      stats: {data['stats']}")

    print(f"[3/4] Calling {CLAUDE_MODEL}…")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    narrative, claude_source = call_claude(data, api_key)
    print(f"      source: {claude_source}")

    print("[4/4] Formatting Discord message…")
    summary = format_discord(data, narrative)

    print()
    print("=" * 72)
    if args.json:
        print(json.dumps({
            "webhookUrl": data["webhookUrl"],
            "content": summary,
        }, indent=2))
    else:
        print(summary)
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
