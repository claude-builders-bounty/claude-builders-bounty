#!/usr/bin/env python3
"""List open bounties in a repo, ranked by lowest competition (fewest comments)."""
import argparse, json, os, re, urllib.request

API = "https://api.github.com/search/issues?q=repo:{repo}+bounty+state:open+type:issue"


def _get(url):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {os.environ.get('GITHUB_TOKEN', '')}",
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
        m = re.search(r"\$(\d+)", it["title"])
        usd = int(m.group(1)) if m else 0
        if usd < args.min:
            continue
        rows.append((it["comments"], usd, it["html_url"], it["title"]))
    rows.sort(key=lambda x: (x[0], -x[1]))  # fewest comments first = lowest competition
    for c, u, url, t in rows[: args.top]:
        print(f"{c:>3} comments | ${u:>3} | {url} | {t[:60]}")


if __name__ == "__main__":
    main()
