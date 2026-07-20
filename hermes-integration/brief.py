#!/usr/bin/env python3
"""Turn one GitHub issue into a copy-paste agent prompt."""
import argparse, json, os, urllib.request


def _issue(repo, num):
    url = f"https://api.github.com/repos/{repo}/issues/{num}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {os.environ.get('GITHUB_TOKEN', '')}",
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
