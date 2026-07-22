#!/usr/bin/env python3
"""Python validator for the n8n Weekly Dev Summary workflow.

Runs the exact same logic as the n8n workflow:
  1. Fetch commits, closed issues, merged PRs from GitHub API (last 7 days)
  2. Consolidate into a structured digest
  3. Call Claude API (claude-sonnet-4-20250514) with EN/FR system prompt
  4. Format the narrative summary

Prints the summary to stdout. Use it to validate the workflow logic
without setting up n8n, or to generate sample outputs.

Env vars (same as n8n workflow):
  GITHUB_TOKEN       (required) — GitHub PAT
  ANTHROPIC_API_KEY  (required for real Claude call; falls back to template if unset)
  GITHUB_REPO        (required) — owner/repo
  LANGUAGE           (optional, default EN) — EN or FR
  WEEK_LOOKBACK_DAYS (optional, default 7)

Usage:
  export GITHUB_TOKEN=ghp_xxx
  export ANTHROPIC_API_KEY=sk-ant-xxx  # optional
  export GITHUB_REPO=owner/repo
  export LANGUAGE=EN
  python3 validate-workflow.py > summary.md
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone


def github_get(url: str, token: str) -> list | dict:
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "n8n-weekly-summary-validator")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def fetch_commits(repo: str, token: str, since: str) -> list[dict]:
    url = f"https://api.github.com/repos/{repo}/commits?since={since}&per_page=100"
    return github_get(url, token)


def fetch_closed_issues(repo: str, token: str, since: str) -> list[dict]:
    url = f"https://api.github.com/repos/{repo}/issues?state=closed&since={since}&per_page=100"
    items = github_get(url, token)
    # GitHub returns PRs on /issues endpoint too — filter them out
    return [i for i in items if not i.get("pull_request")]


def fetch_merged_prs(repo: str, token: str, since: str) -> list[dict]:
    url = f"https://api.github.com/repos/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page=100"
    prs = github_get(url, token)
    return [p for p in prs if p.get("merged_at") and p["merged_at"] >= since]


def consolidate(commits: list, issues: list, prs: list, repo: str, language: str, since: str) -> dict:
    return {
        "repo": repo,
        "week_start": since,
        "week_end": datetime.now(timezone.utc).isoformat(),
        "language": language,
        "stats": {
            "commits": len(commits),
            "closed_issues": len(issues),
            "merged_prs": len(prs),
        },
        "commit_authors": sorted({c["commit"]["author"]["name"] for c in commits if c.get("commit", {}).get("author", {}).get("name")}),
        "top_commits": [
            {
                "sha": c.get("sha", "")[:7],
                "author": c.get("commit", {}).get("author", {}).get("name"),
                "message": (c.get("commit", {}).get("message") or "").split("\n")[0][:120],
                "date": c.get("commit", {}).get("author", {}).get("date"),
            }
            for c in commits[:15]
        ],
        "closed_issues": [
            {"number": i.get("number"), "title": i.get("title"), "closed_at": i.get("closed_at")}
            for i in issues[:10]
        ],
        "merged_prs": [
            {
                "number": p.get("number"),
                "title": p.get("title"),
                "author": p.get("user", {}).get("login"),
                "merged_at": p.get("merged_at"),
                "additions": p.get("additions"),
                "deletions": p.get("deletions"),
            }
            for p in prs[:10]
        ],
    }


def call_claude(digest: dict, api_key: str, model: str = "claude-sonnet-4-20250514") -> str:
    """Call Claude API with EN/FR system prompt. Returns the narrative text."""
    language = digest["language"]
    if language == "FR":
        system = "Tu es un ingénieur logiciel senior qui rédige des résumés hebdomadaires de développement. Réponds en français. Sois concis, factuel et structuré."
        user = (
            "Rédige un résumé narratif hebdomadaire pour ce dépôt GitHub.\n\n"
            f"Données JSON:\n{json.dumps(digest, indent=2, ensure_ascii=False)}\n\n"
            "Format de sortie (Markdown):\n"
            "- Titre avec le nom du dépôt et la période\n"
            "- Paragraphe d'aperçu (commits, issues, PRs fusionnées)\n"
            "- Section « Points forts » (3-5 puces)\n"
            "- Section « Détails techniques » (changements notables)\n"
            "- Section « Prochaines étapes » (recommandations)\n\n"
            "Limite: 400 mots."
        )
    else:
        system = "You are a senior software engineer writing weekly development summaries. Be concise, factual, and well-structured."
        user = (
            "Write a narrative weekly summary for this GitHub repo.\n\n"
            f"JSON data:\n{json.dumps(digest, indent=2)}\n\n"
            "Output format (Markdown):\n"
            "- Title with repo name and date range\n"
            "- Overview paragraph (commits, issues, merged PRs)\n"
            "- Highlights section (3-5 bullets)\n"
            "- Technical details section (notable changes)\n"
            "- Next steps section (recommendations)\n\n"
            "Limit: 400 words."
        )

    payload = json.dumps({
        "model": model,
        "max_tokens": 1500,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        method="POST",
    )
    req.add_header("x-api-key", api_key)
    req.add_header("anthropic-version", "2023-06-01")
    req.add_header("content-type", "application/json")
    with urllib.request.urlopen(req, timeout=60) as r:
        resp = json.loads(r.read().decode())
    if isinstance(resp, dict) and isinstance(resp.get("content"), list):
        return "\n".join(b.get("text", "") for b in resp["content"] if b.get("type") == "text")
    return f"⚠️ Unexpected Claude response: {json.dumps(resp)[:500]}"


def template_summary(digest: dict) -> str:
    """Fallback: generate a basic summary WITHOUT Claude API (when no key set)."""
    language = digest["language"]
    stats = digest["stats"]
    if language == "FR":
        return (
            f"## Résumé Hebdomadaire — `{digest['repo']}`\n"
            f"_Semaine du {digest['week_start'][:10]} au {digest['week_end'][:10]}_\n\n"
            f"### Aperçu\n"
            f"Cette semaine, {stats['commits']} commits ont été poussés, "
            f"{stats['closed_issues']} issues ont été fermées, et "
            f"{stats['merged_prs']} PRs ont été fusionnées.\n\n"
            f"### Points forts\n"
            + "\n".join(f"- {c['message'][:80]} ({c['sha']})" for c in digest["top_commits"][:5])
            + f"\n\n### Auteurs de commits\n"
            + ", ".join(digest["commit_authors"][:10])
        )
    return (
        f"## Weekly Summary — `{digest['repo']}`\n"
        f"_Week of {digest['week_start'][:10]} to {digest['week_end'][:10]}_\n\n"
        f"### Overview\n"
        f"This week, {stats['commits']} commits were pushed, "
        f"{stats['closed_issues']} issues were closed, and "
        f"{stats['merged_prs']} PRs were merged.\n\n"
        f"### Highlights\n"
        + "\n".join(f"- {c['message'][:80]} ({c['sha']})" for c in digest["top_commits"][:5])
        + f"\n\n### Commit Authors\n"
        + ", ".join(digest["commit_authors"][:10])
    )


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPO")
    language = (os.environ.get("LANGUAGE") or "EN").upper()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    lookback = int(os.environ.get("WEEK_LOOKBACK_DAYS") or "7")

    if not token:
        print("ERROR: GITHUB_TOKEN env var not set", file=sys.stderr)
        return 2
    if not repo:
        print("ERROR: GITHUB_REPO env var not set", file=sys.stderr)
        return 2

    since = (datetime.now(timezone.utc) - timedelta(days=lookback)).isoformat()

    print(f"Fetching GitHub data for {repo} (since {since[:10]})...", file=sys.stderr)
    commits = fetch_commits(repo, token, since)
    issues = fetch_closed_issues(repo, token, since)
    prs = fetch_merged_prs(repo, token, since)
    print(
        f"  → {len(commits)} commits, {len(issues)} closed issues, {len(prs)} merged PRs",
        file=sys.stderr,
    )

    digest = consolidate(commits, issues, prs, repo, language, since)

    if api_key:
        print(f"Calling Claude API ({language})...", file=sys.stderr)
        try:
            summary = call_claude(digest, api_key)
        except Exception as e:
            print(f"  ⚠️ Claude API failed: {e}", file=sys.stderr)
            print("  → Falling back to template summary", file=sys.stderr)
            summary = template_summary(digest)
    else:
        print("No ANTHROPIC_API_KEY set → using template summary (set the key for real Claude output)", file=sys.stderr)
        summary = template_summary(digest)

    # Print final summary to stdout
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
