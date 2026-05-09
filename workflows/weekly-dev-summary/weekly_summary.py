#!/usr/bin/env python3
"""weekly_summary — Python equivalent of the n8n workflow.

Same logic as workflow.json: fetch the last 7 days of GitHub activity,
hand it to Claude, deliver a Markdown summary to Slack or Discord.

Useful as:
- A reference implementation a reviewer can read top-to-bottom
- A way to generate sample output without standing up n8n
- A drop-in fallback if your team prefers cron + Python over n8n

Usage
-----
    weekly_summary.py --repo pallets/click --destination print
    weekly_summary.py --repo owner/repo --destination discord
    weekly_summary.py --repo owner/repo --destination slack --language fr
    weekly_summary.py --repo owner/repo --destination print --no-llm  # heuristic-only

Env vars
--------
    GITHUB_TOKEN          required for non-public repos / higher rate limits
    ANTHROPIC_API_KEY     required unless --no-llm
    DISCORD_WEBHOOK_URL   required when --destination discord
    SLACK_WEBHOOK_URL     required when --destination slack
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

GITHUB_API = "https://api.github.com"
ANTHROPIC_API = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-20250514"
USER_AGENT = "weekly-dev-summary/1.0 (+github.com/claude-builders-bounty)"


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------


@dataclass
class WeekData:
    repo: str
    since: datetime
    until: datetime
    commits: list[dict[str, Any]] = field(default_factory=list)
    closed_issues: list[dict[str, Any]] = field(default_factory=list)
    merged_prs: list[dict[str, Any]] = field(default_factory=list)

    @property
    def counts(self) -> dict[str, int]:
        return {
            "commits": len(self.commits),
            "closed_issues": len(self.closed_issues),
            "merged_prs": len(self.merged_prs),
        }


# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------


def _gh_get(path: str, params: dict[str, str], token: str | None) -> Any:
    url = f"{GITHUB_API}{path}?{urllib.parse.urlencode(params)}"
    headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def fetch_week(repo: str, since: datetime, until: datetime, token: str | None) -> WeekData:
    since_iso = since.isoformat().replace("+00:00", "Z")
    until_iso = until.isoformat().replace("+00:00", "Z")

    raw_commits = _gh_get(
        f"/repos/{repo}/commits",
        {"since": since_iso, "until": until_iso, "per_page": "100"},
        token,
    )
    raw_issues = _gh_get(
        f"/repos/{repo}/issues",
        {"state": "closed", "since": since_iso, "per_page": "100"},
        token,
    )
    raw_prs = _gh_get(
        f"/repos/{repo}/pulls",
        {"state": "closed", "sort": "updated", "direction": "desc", "per_page": "50"},
        token,
    )

    # Drop merge commits (parents > 1) — they double-count work that's also in PRs
    commits = [
        {
            "sha": c["sha"][:7],
            "url": c["html_url"],
            "message": c["commit"]["message"].split("\n", 1)[0],
            "author": (c.get("author") or {}).get("login")
            or c["commit"]["author"]["name"],
        }
        for c in raw_commits
        if len(c.get("parents") or []) <= 1
        and c["commit"]["author"]["date"] >= since_iso
    ]

    # The /issues endpoint returns PRs too — exclude them
    issues = [
        {
            "number": i["number"],
            "url": i["html_url"],
            "title": i["title"],
            "closer": (i.get("closed_by") or {}).get("login"),
        }
        for i in raw_issues
        if not i.get("pull_request") and i.get("closed_at") and i["closed_at"] >= since_iso
    ]

    merged_prs = [
        {
            "number": p["number"],
            "url": p["html_url"],
            "title": p["title"],
            "author": (p.get("user") or {}).get("login"),
            "additions": p.get("additions"),
            "deletions": p.get("deletions"),
        }
        for p in raw_prs
        if p.get("merged_at") and p["merged_at"] >= since_iso
    ]

    return WeekData(
        repo=repo,
        since=since,
        until=until,
        commits=commits,
        closed_issues=issues,
        merged_prs=merged_prs,
    )


# ---------------------------------------------------------------------------
# Claude
# ---------------------------------------------------------------------------


SYSTEM_TEMPLATE = (
    "You are a release-notes writer for engineering teams. Produce a "
    "Markdown weekly summary in {lang_word} with sections: 1) Overview "
    "(2-3 sentences on themes), 2) Highlights (3-5 most-impactful items), "
    "3) By the numbers (counts + notable PR sizes), 4) What to watch "
    "(risk or follow-up). No fluff. No emoji headers. "
    "Cite items as [#NUMBER](URL) or [`SHA`](URL)."
)


def llm_summary(week: WeekData, language: str, api_key: str, model: str = DEFAULT_MODEL) -> str:
    lang_word = "French" if language == "fr" else "English"
    body = {
        "model": model,
        "max_tokens": 1200,
        "system": [
            {
                "type": "text",
                "text": SYSTEM_TEMPLATE.format(lang_word=lang_word),
                "cache_control": {"type": "ephemeral"},
            }
        ],
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Repo: {week.repo}\n"
                    f"Window: {week.since.isoformat()} -> {week.until.isoformat()}\n"
                    f"Counts: commits={week.counts['commits']}, "
                    f"merged_prs={week.counts['merged_prs']}, "
                    f"closed_issues={week.counts['closed_issues']}\n\n"
                    f"Merged PRs JSON:\n{json.dumps(week.merged_prs)[:8000]}\n\n"
                    f"Closed issues JSON:\n{json.dumps(week.closed_issues)[:4000]}\n\n"
                    f"Commits JSON (deduped, no merges):\n{json.dumps(week.commits)[:6000]}"
                ),
            }
        ],
    }
    req = urllib.request.Request(
        ANTHROPIC_API,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    parts = data.get("content") or []
    return "".join(p.get("text", "") for p in parts if p.get("type") == "text").strip()


def heuristic_summary(week: WeekData, language: str) -> str:
    """Fallback summary when no API key is available. Less narrative, but
    deterministic — useful for sample generation and CI smoke tests."""
    fr = language == "fr"
    have_diff_stats = any(p.get("additions") is not None for p in week.merged_prs)

    lines = []
    lines.append("## " + ("Aperçu" if fr else "Overview"))
    if fr:
        lines.append(
            f"Cette semaine sur `{week.repo}` : {week.counts['merged_prs']} PR fusionnées, "
            f"{week.counts['commits']} commits (hors merges), "
            f"{week.counts['closed_issues']} issues fermées."
        )
    else:
        lines.append(
            f"This week on `{week.repo}`: {week.counts['merged_prs']} PRs merged, "
            f"{week.counts['commits']} commits (excluding merges), "
            f"{week.counts['closed_issues']} issues closed."
        )
    lines.append("")

    lines.append("## " + ("À retenir" if fr else "Highlights"))
    if have_diff_stats:
        highlights = sorted(
            week.merged_prs,
            key=lambda p: (p.get("additions") or 0) + (p.get("deletions") or 0),
            reverse=True,
        )[:5]
    else:
        # Fall back to most-recent merges when the list endpoint didn't return diff stats
        highlights = week.merged_prs[:5]
    for pr in highlights:
        size_clause = ""
        if pr.get("additions") is not None and pr.get("deletions") is not None:
            size_clause = f" (+{pr['additions']} / -{pr['deletions']})"
        author_clause = f" @{pr['author']}" if pr.get("author") else ""
        lines.append(
            f"- [#{pr['number']}]({pr['url']}) — {pr['title']}{size_clause}{author_clause}"
        )
    if not highlights:
        lines.append(
            "_" + ("Aucun PR fusionné cette semaine." if fr else "No PRs merged this week.") + "_"
        )
    lines.append("")

    lines.append("## " + ("Chiffres" if fr else "By the numbers"))
    lines.append(f"- {'Commits' if not fr else 'Commits'} : **{week.counts['commits']}**")
    lines.append(f"- {'Merged PRs' if not fr else 'PR fusionnées'} : **{week.counts['merged_prs']}**")
    lines.append(f"- {'Closed issues' if not fr else 'Issues fermées'} : **{week.counts['closed_issues']}**")
    if have_diff_stats and highlights:
        biggest = highlights[0]
        size = (biggest.get("additions") or 0) + (biggest.get("deletions") or 0)
        lines.append(
            f"- {'Largest PR' if not fr else 'Plus gros PR'} : [#{biggest['number']}]({biggest['url']}) "
            f"({size} {'lines changed' if not fr else 'lignes changées'})"
        )
    lines.append("")

    lines.append("## " + ("À surveiller" if fr else "What to watch"))
    if week.counts["closed_issues"] == 0 and week.counts["commits"] > 0:
        lines.append(
            "- "
            + (
                "Pas d'issues fermées cette semaine malgré l'activité — vérifier le triage."
                if fr
                else "Zero issues closed despite active commits — check triage backlog."
            )
        )
    elif week.counts["merged_prs"] > 10:
        lines.append(
            "- "
            + (
                "Volume de fusions élevé — confirmer que la CI et les release notes suivent."
                if fr
                else "High merge volume — confirm CI and release notes are keeping up."
            )
        )
    else:
        lines.append(
            "- " + ("Rien d'alarmant à signaler." if fr else "No follow-ups flagged.")
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Delivery
# ---------------------------------------------------------------------------


def post_discord(webhook: str, content: str) -> None:
    truncated = content if len(content) <= 1900 else content[:1900] + "\n_(truncated)_"
    body = json.dumps({"content": truncated}).encode("utf-8")
    req = urllib.request.Request(
        webhook,
        data=body,
        method="POST",
        headers={"content-type": "application/json", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status >= 300:
            raise RuntimeError(f"Discord rejected webhook ({resp.status})")


def post_slack(webhook: str, content: str) -> None:
    body = json.dumps({"text": content}).encode("utf-8")
    req = urllib.request.Request(
        webhook,
        data=body,
        method="POST",
        headers={"content-type": "application/json", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status >= 300:
            raise RuntimeError(f"Slack rejected webhook ({resp.status})")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Iterable[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="weekly-summary", description=__doc__.split("\n\n")[0])
    p.add_argument("--repo", required=True, help="GitHub repo (owner/name)")
    p.add_argument("--language", choices=("en", "fr"), default="en")
    p.add_argument(
        "--destination",
        choices=("print", "discord", "slack"),
        default="print",
        help="Where to send the summary",
    )
    p.add_argument("--days", type=int, default=7, help="Lookback window in days (default: 7)")
    p.add_argument("--no-llm", action="store_true", help="Use deterministic heuristic summary instead of Claude API")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--dump-aggregated", help="Path to write aggregated JSON (debugging / sample fixtures)")
    p.add_argument("--output", help="Write the rendered Markdown to this file (UTF-8). Stdout still receives it unless --quiet.")
    p.add_argument("--quiet", action="store_true", help="Suppress stdout when --output is set")
    args = p.parse_args(list(argv) if argv is not None else None)

    until = datetime.now(timezone.utc).replace(microsecond=0)
    since = until - timedelta(days=args.days)

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    try:
        week = fetch_week(args.repo, since, until, token)
    except urllib.error.HTTPError as exc:
        sys.stderr.write(f"GitHub error {exc.code}: {exc.read().decode('utf-8', 'replace')[:200]}\n")
        return 1

    if args.dump_aggregated:
        from pathlib import Path

        Path(args.dump_aggregated).write_text(
            json.dumps(
                {
                    "repo": week.repo,
                    "since": week.since.isoformat(),
                    "until": week.until.isoformat(),
                    "counts": week.counts,
                    "commits": week.commits,
                    "closed_issues": week.closed_issues,
                    "merged_prs": week.merged_prs,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        sys.stderr.write(f"Wrote aggregated JSON to {args.dump_aggregated}\n")

    if args.no_llm:
        summary_md = heuristic_summary(week, args.language)
    else:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            sys.stderr.write("ANTHROPIC_API_KEY not set; falling back to heuristic summary\n")
            summary_md = heuristic_summary(week, args.language)
        else:
            try:
                summary_md = llm_summary(week, args.language, api_key, args.model)
            except urllib.error.HTTPError as exc:
                sys.stderr.write(
                    f"Anthropic error {exc.code}; falling back to heuristic summary\n"
                )
                summary_md = heuristic_summary(week, args.language)

    if args.language == "fr":
        header = (
            f"**Résumé hebdomadaire — {week.repo}**\n"
            f"_Semaine du {week.since.date().isoformat()} au {week.until.date().isoformat()}_\n\n"
        )
    else:
        header = (
            f"**Weekly summary — {week.repo}**\n"
            f"_Week of {week.since.date().isoformat()} to {week.until.date().isoformat()}_\n\n"
        )
    body = header + summary_md

    if args.output:
        from pathlib import Path

        Path(args.output).write_text(body + "\n", encoding="utf-8")
        sys.stderr.write(f"Wrote {args.output}\n")

    if args.destination == "print":
        if not (args.output and args.quiet):
            sys.stdout.write(body + "\n")
    elif args.destination == "discord":
        webhook = os.environ.get("DISCORD_WEBHOOK_URL")
        if not webhook:
            sys.stderr.write("error: DISCORD_WEBHOOK_URL not set\n")
            return 2
        post_discord(webhook, body)
        sys.stderr.write("posted to Discord\n")
    elif args.destination == "slack":
        webhook = os.environ.get("SLACK_WEBHOOK_URL")
        if not webhook:
            sys.stderr.write("error: SLACK_WEBHOOK_URL not set\n")
            return 2
        post_slack(webhook, body)
        sys.stderr.write("posted to Slack\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
