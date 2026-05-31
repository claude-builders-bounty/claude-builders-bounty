#!/usr/bin/env python3
"""
changelog.py — Generate structured CHANGELOG.md from git history
Usage: python changelog.py [output_file]
Default output: CHANGELOG.md
"""
import os
import re
import subprocess
import sys
from datetime import date


def run_git(*args: str) -> str:
    """Run a git command and return stdout."""
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            check=True,
            cwd=os.getcwd(),
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Git error: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def categorize(commit_msg: str) -> str:
    """Categorize a commit message into Added/Fixed/Changed/Removed."""
    msg_lower = commit_msg.lower().lstrip()

    # Conventional commits
    if re.match(r'^feat(\(.*?\))?:', msg_lower) or re.match(r'^add', msg_lower) or re.match(r'^feature', msg_lower) or re.match(r'^new', msg_lower):
        return "Added"
    if re.match(r'^fix(\(.*?\))?:', msg_lower) or re.match(r'^bug', msg_lower) or re.match(r'^hotfix', msg_lower) or re.match(r'^patch', msg_lower) or re.match(r'^resolve', msg_lower):
        return "Fixed"
    if re.match(r'^remove', msg_lower) or re.match(r'^delete', msg_lower) or re.match(r'^drop', msg_lower) or re.match(r'^deprecate', msg_lower):
        return "Removed"
    # Default: Changed (includes chore, refactor, docs, style, perf, test, ci, build, etc.)
    return "Changed"


def clean_message(msg: str) -> str:
    """Clean up commit message for display."""
    # Remove conventional commit prefix like "feat:", "fix(scope):"
    msg = re.sub(r'^(feat|fix|chore|docs|style|refactor|perf|test|ci|build|revert)(\(.*?\))?:\s*', '', msg, flags=re.IGNORECASE)
    return msg.strip().capitalize()


def main():
    output_file = sys.argv[1] if len(sys.argv) > 1 else "CHANGELOG.md"

    # Verify git repo
    if not os.path.isdir(".git") and run_git("rev-parse", "--git-dir") == "":
        print("Error: not in a git repository", file=sys.stderr)
        sys.exit(1)

    # Get last tag
    last_tag = ""
    try:
        last_tag = run_git("describe", "--tags", "--abbrev=0")
    except SystemExit:
        pass

    if not last_tag:
        rev_range = "HEAD"
        new_version = "0.1.0"
        print("No tags found. Generating changelog from all commits.")
    else:
        rev_range = f"{last_tag}..HEAD"
        # Increment patch version
        parts = last_tag.lstrip("v").split(".")
        try:
            parts[-1] = str(int(parts[-1]) + 1)
        except ValueError:
            parts.append("1")
        new_version = "v" + ".".join(parts)
        print(f"Generating changelog from {last_tag} to HEAD.")

    # Get commits
    log_output = run_git(
        "log", "--no-merges",
        f"--pretty=format:%H||%s",
        rev_range
    )

    if not log_output:
        print("No new commits found since last tag.")
        today = date.today().isoformat()
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# Changelog\n\n")
            f.write(f"## [{new_version}] - {today}\n\n")
            f.write("No changes.\n")
        return

    # Categorize
    categories = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}

    for line in log_output.split("\n"):
        if not line.strip():
            continue
        if len(line) < 42:
            continue
        commit_hash = line[:40]
        commit_msg = line[42:]
        short_hash = commit_hash[:7]
        category = categorize(commit_msg)
        clean_msg = clean_message(commit_msg)
        categories[category].append(f"- {clean_msg} ({short_hash})")

    # Write CHANGELOG
    today = date.today().isoformat()
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Changelog\n\n")
        f.write(f"## [{new_version}] - {today}\n\n")

        for cat in ["Added", "Fixed", "Changed", "Removed"]:
            if categories[cat]:
                f.write(f"### {cat}\n")
                for item in categories[cat]:
                    f.write(f"{item}\n")
                f.write("\n")

    print(f"✅ Changelog generated at {output_file}")
    print(f"   Version: {new_version}")


if __name__ == "__main__":
    main()
