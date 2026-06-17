#!/usr/bin/env python3
"""changelog.py - Generate a structured CHANGELOG.md from git history.

Usage:
  python changelog.py                        # writes to CHANGELOG.md
  python changelog.py --output RELEASES.md   # custom output file
  python changelog.py --tag v1.0.0           # start from a specific tag
  python changelog.py --stdout               # print to stdout only

Categories (conventional commit -> changelog section):
  feat          ->  Added
  fix           ->  Fixed
  docs          ->  Documentation
  style         ->  Styling
  refactor/perf ->  Changed
  test          ->  Testing
  build/ci      ->  Build
  chore         ->  Maintenance
  revert/remove/deprecate ->  Removed
"""

import argparse
import datetime
import re
import subprocess
import sys
from collections import defaultdict


def git(*args: str) -> str:
    """Run a git command and return its stdout, or empty string on failure."""
    try:
        result = subprocess.run(
            ["git"] + list(args),
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def ensure_git_repo() -> None:
    if not git("rev-parse", "--git-dir"):
        print("error: not inside a git repository", file=sys.stderr)
        sys.exit(1)


def resolve_range(from_tag: str | None) -> str | None:
    if not from_tag:
        from_tag = git("describe", "--tags", "--abbrev=0") or None
    if from_tag and not git("rev-parse", "--verify", from_tag):
        print(f"error: tag '{from_tag}' does not exist", file=sys.stderr)
        sys.exit(1)
    return from_tag


def fetch_commits(range_tag: str | None) -> list:
    """Fetch commits as a list of (sha, epoch_ts, author, subject, refs)."""
    args = ["log", "--reverse", "--pretty=format:%H||%ct||%an||%s||%D"]
    if range_tag:
        args.append(f"{range_tag}..HEAD")
    raw = git(*args)
    if not raw:
        return []
    commits = []
    for line in raw.split("\n"):
        parts = line.split("||", 4)
        if len(parts) == 5:
            sha, epoch, author, subject, refs = parts
            try:
                ts = int(epoch)
            except ValueError:
                ts = 0
            commits.append((sha, ts, author, subject, refs))
    return commits


def epoch_to_date(epoch: int) -> str:
    return datetime.datetime.utcfromtimestamp(epoch).strftime("%Y-%m-%d")


def repo_url() -> str:
    url = git("remote", "get-url", "origin")
    if not url:
        return ""
    url = re.sub(r"git@([^:]+):", r"https://\1/", url)
    url = re.sub(r"\.git$", "", url)
    return url


def categorise(msg: str) -> str:
    """Categorise a commit message into a changelog section."""
    lower = msg.lower().lstrip()
    # Use regex matching per category
    if re.match(r"^feat(\(|!|:)", lower):
        return "Added"
    if re.match(r"^fix(\(|!|:)", lower):
        return "Fixed"
    if re.match(r"^docs(\(|!|:)", lower):
        return "Documentation"
    if re.match(r"^style(\(|!|:)", lower):
        return "Styling"
    if re.match(r"^refactor(\(|!|:)", lower) or re.match(r"^perf(\(|!|:)", lower):
        return "Changed"
    if re.match(r"^test(\(|!|:)", lower):
        return "Testing"
    if re.match(r"^build(\(|!|:)", lower) or re.match(r"^ci(\(|!|:)", lower):
        return "Build"
    if re.match(r"^chore(\(|!|:)", lower):
        return "Maintenance"
    if re.match(r"^revert(\(|!|:)", lower):
        return "Removed"
    if re.match(r"^(remove|deprecate)", lower):
        return "Removed"
    return "Uncategorised"


PREFIX_RE = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert|remove|deprecate)"
    r"(\([^)]*\))?!?:\s*",
    re.IGNORECASE,
)
BRACKET_RE = re.compile(r"^\[[^\]]*\][:\s]*")


def strip_prefix(msg: str) -> str:
    """Strip conventional-commit prefix and capitalise."""
    msg = PREFIX_RE.sub("", msg, count=1)
    msg = BRACKET_RE.sub("", msg, count=1)
    return msg.strip().capitalize()


def render_section(name: str, entries: list[str]) -> str:
    if not entries:
        return ""
    lines = [f"### {name}", ""]
    for e in entries:
        lines.append(e)
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate CHANGELOG.md from git history"
    )
    parser.add_argument("--output", "-o", default="CHANGELOG.md", help="output file")
    parser.add_argument("--tag", "-t", default=None, help="start from a specific tag")
    parser.add_argument("--stdout", "-s", action="store_true", help="print to stdout")
    args = parser.parse_args()

    ensure_git_repo()

    range_tag = resolve_range(args.tag)
    commits = fetch_commits(range_tag)

    if not commits:
        print("No commits found since the last tag.", file=sys.stderr)
        sys.exit(0)

    ver = git("describe", "--tags", "--abbrev=0") or "0.0.0"
    today = datetime.date.today().isoformat()
    url = repo_url()

    sections: dict[str, list[str]] = defaultdict(list)

    for sha, epoch, _author, subject, _refs in commits:
        cat = categorise(subject)
        pretty = strip_prefix(subject)

        if url:
            entry = f"- {pretty} ([{sha[:7]}]({url}/commit/{sha}))"
        else:
            entry = f"- {pretty} (`{sha[:7]}`)"
        sections[cat].append(entry)

    section_order = [
        "Added", "Fixed", "Changed", "Documentation",
        "Removed", "Styling", "Testing", "Build",
        "Maintenance", "Uncategorised",
    ]

    output_lines = ["# Changelog", ""]
    if range_tag:
        output_lines.append(f"## [{ver}] - {today}")
    else:
        output_lines.append(f"## {ver} - {today}")
    output_lines.append("")

    for name in section_order:
        rendered = render_section(name, sections.get(name, []))
        if rendered:
            output_lines.append(rendered)

    output = "\n".join(output_lines).rstrip("\n") + "\n"

    if args.stdout:
        sys.stdout.write(output)
    else:
        with open(args.output, "w", encoding="utf-8", newline="\n") as f:
            f.write(output)
        print(f"CHANGELOG written to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
