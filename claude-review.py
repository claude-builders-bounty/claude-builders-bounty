#!/usr/bin/env python3
"""claude-review: PR review agent.

Usage: python claude-review.py --pr https://github.com/owner/repo/pull/123
"""
import subprocess, sys, os, argparse, re, urllib.request

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr", help="PR URL")
    args = parser.parse_args()
    if not args.pr: parser.print_help(); return
    m = re.match(r"https://github.com/([^/]+)/([^/]+)/pull/(\d+)", args.pr)
    if not m: print("Invalid PR URL"); return
    owner, repo_name, num = m.group(1), m.group(2), m.group(3)
    print(f"Fetching PR #{num} from {owner}/{repo_name}...")
    url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{num}"
    token = os.environ.get("GITHUB_TOKEN", "")
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3.diff", "Authorization": f"token {token}"})
    diff = urllib.request.urlopen(req).read().decode()
    print(f"Got {len(diff)} bytes. Reviewing...")
    prompt = f"Review this PR diff.\n\n## Summary\n## Issues Found\n## Suggestions\n## Verdict\n\n```diff\n{diff[:8000]}\n```"
    result = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True, timeout=60)
    print(result.stdout)

if __name__ == "__main__": main()
