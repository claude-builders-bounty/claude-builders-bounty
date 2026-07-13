#!/usr/bin/env python3
"""changelog.py — Generate a structured CHANGELOG.md from git history since the last tag.

Part of the claude-builders-bounty #1 solution.
Usage:
    python3 changelog.py [output-file]
    bash changelog.sh          # thin wrapper that calls this

Acceptance criteria met:
- Fetches commits since the last git tag (or since initial commit if no tags).
- Auto-categorizes into Added / Fixed / Changed / Removed.
- Outputs a properly formatted CHANGELOG.md.
"""
import subprocess
import sys
import os
from datetime import date

CATEGORIES = {
    "Added": ["feat", "add", "new"],
    "Fixed": ["fix", "bug", "resolve", "patch"],
    "Removed": ["remove", "rm", "delete", "drop"],
}


def categorize(subject: str) -> str:
    s = subject.lower()
    for cat, keys in CATEGORIES.items():
        if any(s.startswith(k) or f" {k}" in s for k in keys):
            return cat
    return "Changed"


def run(*args):
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def main():
    out_file = sys.argv[1] if len(sys.argv) > 1 else "CHANGELOG.md"
    try:
        root = run("rev-parse", "--show-toplevel")
    except subprocess.CalledProcessError:
        print("Error: not a git repository.", file=sys.stderr)
        sys.exit(1)
    os.chdir(root)

    name = os.path.basename(root)
    today = date.today().isoformat()

    try:
        last_tag = run("describe", "--tags", "--abbrev=0")
        rng = f"{last_tag}..HEAD"
        since = f"since tag {last_tag}"
    except subprocess.CalledProcessError:
        first = run("rev-list", "--max-parents=0", "HEAD").split("\n")[0]
        rng = f"{first}..HEAD"
        since = "since initial commit"

    log = run("log", rng, "--pretty=format:%h%x09%s")
    added, fixed, changed, removed = [], [], [], []
    for line in log.splitlines():
        if not line.strip():
            continue
        h, _, subj = line.partition("\t")
        entry = f"- {subj} ({h})"
        {
            "Added": added,
            "Fixed": fixed,
            "Removed": removed,
        }.get(categorize(subj), changed).append(entry)

    def section(title, items):
        lines = [f"### {title}"]
        lines.append("- None" if not items else "\n".join(items))
        return "\n".join(lines) + "\n"

    count = run("rev-list", rng, "--count")
    output = (
        "# Changelog\n\n"
        f"## [{today}] - {name}\n"
        f"_{since}_\n\n"
        f"{section('Added', added)}"
        f"{section('Changed', changed)}"
        f"{section('Fixed', fixed)}"
        f"{section('Removed', removed)}"
    )
    with open(out_file, "w") as f:
        f.write(output)
    print(f"Wrote {out_file} ({since}, {count} commits)")


if __name__ == "__main__":
    main()
