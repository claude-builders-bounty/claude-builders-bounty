#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""
import subprocess, sys, re
from datetime import datetime

def run(cmd):
    return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()

def main():
    # Determine range: since last tag, or all commits
    try:
        last_tag = run(["git", "describe", "--tags", "--abbrev=0"])
        rng = f"{last_tag}..HEAD"
        header = f"## Unreleased (since {last_tag})"
    except subprocess.CalledProcessError:
        rng = "HEAD"
        header = "## All commits"

    log = run(["git", "log", rng, "--pretty=format:%H|%s|%ad", "--date=short"])
    if not log:
        print("No commits found.")
        return

    cats = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}
    for line in log.splitlines():
        sha, msg, date = line.split("|", 2)
        low = msg.lower()
        if low.startswith("feat") or "add" in low:
            cats["Added"].append((sha[:7], msg, date))
        elif low.startswith("fix") or "fix" in low:
            cats["Fixed"].append((sha[:7], msg, date))
        elif "remove" in low or "delete" in low:
            cats["Removed"].append((sha[:7], msg, date))
        else:
            cats["Changed"].append((sha[:7], msg, date))

    out = ["# Changelog", "", header, ""]
    for name in ["Added", "Fixed", "Changed", "Removed"]:
        if cats[name]:
            out.append(f"### {name}")
            for sha, msg, date in cats[name]:
                out.append(f"- {msg} ({sha}, {date})")
            out.append("")
    result = "\n".join(out)
    with open("CHANGELOG.md", "w", encoding="utf-8") as f:
        f.write(result)
    print(result)

if __name__ == "__main__":
    main()
