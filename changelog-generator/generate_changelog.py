#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git commits since the latest tag."""

import argparse
import datetime as dt
import os
import re
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path
from urllib.parse import urlparse


CATEGORIES = OrderedDict(
    [
        ("Added", ("feat", "feature", "add", "added", "implement", "introduce", "new")),
        ("Fixed", ("fix", "fixed", "bug", "bugfix", "repair", "resolve", "patch")),
        ("Changed", ("change", "changed", "update", "updated", "refactor", "perf", "chore", "docs", "ci", "build", "test", "style")),
        ("Removed", ("remove", "removed", "delete", "deleted", "drop", "dropped", "deprecate", "deprecated")),
    ]
)


def run_git(repo, args, allow_failure=False):
    process = subprocess.run(
        ["git"] + args,
        cwd=str(repo),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    if process.returncode and not allow_failure:
        raise RuntimeError("git %s failed:\n%s" % (" ".join(args), process.stderr.strip()))
    return process.stdout.strip()


def require_git_repo(repo):
    if run_git(repo, ["rev-parse", "--is-inside-work-tree"], allow_failure=True) != "true":
        raise RuntimeError("%s is not a git repository" % repo)


def latest_tag(repo):
    tag = run_git(repo, ["describe", "--tags", "--abbrev=0"], allow_failure=True)
    return tag or None


def first_commit(repo):
    return run_git(repo, ["rev-list", "--max-parents=0", "HEAD"]).splitlines()[0]


def commit_range(repo, since):
    if since:
        return since, "%s..HEAD" % since

    tag = latest_tag(repo)
    if tag:
        return tag, "%s..HEAD" % tag

    root = first_commit(repo)
    return root[:12], "%s..HEAD" % root


def parse_remote_url(remote_url):
    if not remote_url:
        return None

    if remote_url.startswith("git@"):
        host_path = remote_url.split(":", 1)[1]
        if host_path.endswith(".git"):
            host_path = host_path[:-4]
        return "https://github.com/" + host_path

    parsed = urlparse(remote_url)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return remote_url[:-4] if remote_url.endswith(".git") else remote_url

    return None


def github_remote(repo):
    remote_url = run_git(repo, ["config", "--get", "remote.origin.url"], allow_failure=True)
    return parse_remote_url(remote_url)


def get_commits(repo, revision_range, include_merges=False):
    args = [
        "log",
        "--reverse",
        "--format=%H%x1f%s%x1f%b%x1e",
        revision_range,
    ]
    if not include_merges:
        args.insert(1, "--no-merges")

    raw = run_git(repo, args, allow_failure=True)
    commits = []
    for record in raw.split("\x1e"):
        record = record.strip()
        if not record:
            continue
        parts = record.split("\x1f")
        if len(parts) < 3:
            continue
        sha, subject, body = parts[0], parts[1].strip(), parts[2].strip()
        commits.append({"sha": sha, "subject": subject, "body": body})
    return commits


def normalize_subject(subject):
    return re.sub(r"^\w+(?:\([^)]+\))?!?:\s*", "", subject).strip()


def category_for(subject):
    lowered = subject.lower()
    prefix_match = re.match(r"^([a-z]+)(?:\([^)]+\))?!?:", lowered)
    first_word = re.match(r"^[a-z]+", lowered)
    signals = []
    if prefix_match:
        signals.append(prefix_match.group(1))
    if first_word:
        signals.append(first_word.group(0))

    for category, words in CATEGORIES.items():
        if any(signal in words for signal in signals):
            return category
    return "Changed"


def format_commit(commit, remote):
    subject = normalize_subject(commit["subject"])
    short_sha = commit["sha"][:7]
    if remote:
        return "- %s ([%s](%s/commit/%s))" % (subject, short_sha, remote, commit["sha"])
    return "- %s (%s)" % (subject, short_sha)


def render_changelog(repo, since=None, include_merges=False):
    range_label, revision_range = commit_range(repo, since)
    commits = get_commits(repo, revision_range, include_merges=include_merges)
    remote = github_remote(repo)

    categorized = OrderedDict((category, []) for category in CATEGORIES)
    for commit in commits:
        categorized[category_for(commit["subject"])].append(format_commit(commit, remote))

    today = dt.date.today().isoformat()
    lines = [
        "# Changelog",
        "",
        "## Unreleased - %s" % today,
        "",
        "_Generated from commits after `%s`._" % range_label,
        "",
    ]

    if not commits:
        lines.extend(["No unreleased changes found.", ""])
        return "\n".join(lines)

    for category, entries in categorized.items():
        if not entries:
            continue
        lines.append("### %s" % category)
        lines.extend(entries)
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history.")
    parser.add_argument("--repo", default=os.getcwd(), help="Path to the git repository. Defaults to current directory.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output file path, relative to the repository by default.")
    parser.add_argument("--since", help="Tag or revision to start from. Defaults to the latest git tag.")
    parser.add_argument("--include-merges", action="store_true", help="Include merge commits in the changelog.")
    parser.add_argument("--dry-run", action="store_true", help="Print changelog content without writing a file.")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    require_git_repo(repo)
    changelog = render_changelog(repo, since=args.since, include_merges=args.include_merges)

    if args.dry_run:
        print(changelog)
        return 0

    output = Path(args.output)
    if not output.is_absolute():
        output = repo / output
    output.write_text(changelog, encoding="utf-8")
    print("Wrote %s" % output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("error: %s" % exc, file=sys.stderr)
        raise SystemExit(1)
