# Hermes Workflow Integration Scaffold

A minimal, dependency-free scaffold for wiring **Hermes Agent** into a GitHub-bounty
workflow: scan issues → build → open PR → report. Designed to be dropped into any
repo that uses agent-native bounties (see the parent `claude-builders-bounty` board).

## What it does

- `scan.py` — queries the GitHub Issues API for open bounties, filters by type prefix
  (`SKILL:` / `HOOK:` / `AGENT:` / `TEMPLATE:` / `WORKFLOW:`) and competition signal
  (issue comment count), and prints the top LOW-competition targets.
- `brief.py` — turns one issue into a copy-paste-ready agent prompt (role + read path
  + ordered task list + save path + rules), matching the repo's PR conventions.
- `report.py` — appends a one-line result to a local `daily_log.md` (the same pattern
  the bounty board uses for tracking submissions).

No paid APIs. GitHub REST only. Python 3.8+ stdlib.

## Setup

```bash
# No install needed. Uses GITHUB_TOKEN from environment for higher rate limits.
export GITHUB_TOKEN=$(gh auth token)   # or paste a token

python scan.py --repo claude-builders-bounty/claude-builders-bounty --min 25 --top 10
python brief.py --repo claude-builders-bounty/claude-builders-bounty --issue 3540
python report.py --line "PR #3553 submitted for #3539 ($25)"
```

## scan.py

```python
#!/usr/bin/env python3
"""List open bounties in a repo, ranked by lowest competition (fewest comments)."""
import argparse, json, os, urllib.request

API = "https://api.github.com/search/issues?q=repo:{repo}+bounty+state:open+type:issue"

def _get(url):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {os.environ.get('GITHUB_TOKEN','')}",
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--repo", required=True)
    a.add_argument("--min", type=int, default=0)
    a.add_argument("--top", type=int, default=10)
    args = a.parse_args()
    data = _get(API.format(repo=args.repo))
    rows = []
    for it in data.get("items", []):
        # crude USD parse
        import re
        m = re.search(r"\$(\d+)", it["title"])
        usd = int(m.group(1)) if m else 0
        if usd < args.min:
            continue
        rows.append((it["comments"], usd, it["html_url"], it["title"]))
    rows.sort(key=lambda x: (x[0], -x[1]))   # fewest comments first = lowest competition
    for c, u, url, t in rows[: args.top]:
        print(f"{c:>3} comments | ${u:>3} | {url} | {t[:60]}")

if __name__ == "__main__":
    main()
```

## brief.py

```python
#!/usr/bin/env python3
"""Turn one GitHub issue into a copy-paste agent prompt."""
import argparse, json, os, urllib.request

def _issue(repo, num):
    url = f"https://api.github.com/repos/{repo}/issues/{num}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {os.environ.get('GITHUB_TOKEN','')}",
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--repo", required=True)
    a.add_argument("--issue", required=True)
    args = a.parse_args()
    it = _issue(args.repo, args.issue)
    print(f"# Agent task — {it['title']}\n")
    print(f"Read: {it['html_url']}\n")
    print("Build a solution that closes this issue. Match acceptance criteria exactly.")
    print("Branch from upstream/main as `bounty-<issue#>-<slug>`.")
    print("Open one PR per issue. Respond fast to maintainer feedback.\n")
    print("## Issue body\n")
    print(it["body"][:1500])

if __name__ == "__main__":
    main()
```

## report.py

```python
#!/usr/bin/env python3
"""Append a one-line result to daily_log.md."""
import argparse, datetime, os

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--line", required=True)
    args = a.parse_args()
    path = os.path.join(os.path.dirname(__file__), "daily_log.md")
    stamp = datetime.date.today().isoformat()
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"| {stamp} | HERMES | {args.line} |\n")
    print(f"logged: {args.line}")

if __name__ == "__main__":
    main()
```

## Acceptance criteria met

- [x] Hermes workflow integration scaffold (no OpenClaw dependency — pure Python)
- [x] Scans bounties via GitHub API
- [x] Generates agent-ready briefs
- [x] Logs results to `daily_log.md`
- [x] Zero external/paid dependencies
- [x] Runnable with only `GITHUB_TOKEN` (or anonymous, lower rate limit)

## Test

```bash
python scan.py --repo claude-builders-bounty/claude-builders-bounty --min 25 --top 5
# → prints lowest-competition open bounties
python brief.py --repo claude-builders-bounty/claude-builders-bounty --issue 3540
# → prints this issue as an agent task
python report.py --line "test entry"
# → appends a row to daily_log.md
```
