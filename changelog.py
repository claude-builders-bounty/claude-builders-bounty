#!/usr/bin/env python3
"""Generate CHANGELOG.md from git history using Conventional Commits."""

import argparse, os, re, subprocess, sys
from collections import OrderedDict, defaultdict
from datetime import date

# prefix -> section mapping
SECTION_MAP = OrderedDict([
    ("added",   ["feat", "feature"]),
    ("fixed",   ["fix", "bug", "bugfix", "hotfix", "patch"]),
    ("changed", ["refactor", "perf", "performance", "optimize", "update",
                  "upgrade", "deps", "migrate"]),
    ("removed", ["remove", "revert", "deprecate", "delete", "drop"]),
    ("docs",    ["docs", "doc", "documentation"]),
    ("test",    ["test", "tests", "testing"]),
    ("ci",      ["ci", "cd", "build", "chore", "devops"]),
])

SKIP_PREFIXES = {"merge", "wip", "initial"}

SECTION_HEADING = {
    "added": "Added", "fixed": "Fixed", "changed": "Changed",
    "removed": "Removed", "docs": "Documentation",
    "test": "Tests", "ci": "CI & Build",
}


def _git(args, cwd=None):
    r = subprocess.run(["git"] + args, capture_output=True, text=True, cwd=cwd)
    if r.returncode != 0:
        print(f"git error: {r.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return r.stdout


def _parse_log(raw):
    commits = []
    for block in raw.strip().split("\n\n\n"):
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n")
        meta = lines[0].split("|", 4)
        if len(meta) < 4:
            continue
        commits.append({
            "hash": meta[0][:8],
            "author": meta[1],
            "date": meta[2],
            "subject": meta[3],
            "body": "\n".join(lines[1:]).strip(),
        })
    return commits


def _categorize(subject):
    subject = subject.strip()
    m = re.match(r"^(\w+)(?:\([^)]*\))?(!)?:\s*(.*)$", subject, re.IGNORECASE)
    if not m:
        return "changed", subject, False
    prefix = m.group(1).lower()
    is_breaking = bool(m.group(2))
    msg = m.group(3).strip()

    if prefix in SKIP_PREFIXES:
        return "skip", msg or subject, is_breaking
    for section, prefixes in SECTION_MAP.items():
        if prefix in prefixes:
            return section, msg or subject, is_breaking
    return "changed", msg or subject, is_breaking


def _has_breaking(body):
    return bool(body and re.search(r"BREAKING[-\s]CHANGE\s*:", body, re.IGNORECASE))


def _fmt(subject, body, is_breaking):
    entry = f"- {subject}"
    if is_breaking:
        entry = f"- **BREAKING**: {subject}"
    if body:
        para = body.split("\n\n")[0].strip()
        para = re.sub(r"BREAKING[-\s]CHANGE:.*", "", para).strip()
        if para:
            entry += f"\n  {para}"
    return entry


def last_tag(cwd=None):
    try:
        r = subprocess.run(["git", "describe", "--tags", "--abbrev=0", "HEAD"],
                           capture_output=True, text=True, cwd=cwd)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def get_commits(since=None, until=None, cwd=None):
    if since is None:
        tag = last_tag(cwd)
        if tag:
            since_ref, since_desc = tag, f"tag {tag}"
        else:
            # count commits, cap at 100
            try:
                cnt = int(_git(["rev-list", "--count", "HEAD"], cwd).strip())
            except Exception:
                cnt = 0
            if cnt == 0:
                print("No commits found.", file=sys.stderr)
                return []
            since_ref = f"HEAD~{min(cnt, 100)}"
            since_desc = f"last {min(cnt, 100)} commits"
    elif re.match(r"^\d{4}-\d{2}-\d{2}$", since):
        since_ref, since_desc = since, since
    elif re.match(r"^HEAD~?\d*$", since):
        since_ref, since_desc = since, since
    else:
        # might be a tag or rev
        try:
            subprocess.run(["git", "rev-parse", "--verify", f"refs/tags/{since}"],
                           capture_output=True, cwd=cwd, check=True)
            since_ref, since_desc = since, f"tag {since}"
        except subprocess.CalledProcessError:
            since_ref, since_desc = since, since

    # confirm repo has commits
    try:
        cnt = int(_git(["rev-list", "--count", "HEAD"], cwd).strip())
        if cnt == 0:
            print("No commits found.", file=sys.stderr)
            return []
    except Exception:
        pass

    fmt = "--format=%h|%an|%ad|%s%n%b%n%n%n"
    args = ["log", "--no-merges"]
    if re.match(r"^\d{4}", since_ref):
        args.append(f"--after={since_ref}")
        if until:
            args.append(f"--before={until}")
    else:
        args.append(f"{since_ref}..HEAD")
    args.extend([fmt, "--date=short"])

    commits = _parse_log(_git(args, cwd))
    print(f"Found {len(commits)} commit(s) since {since_desc}.", file=sys.stderr)
    return commits


def build(commits, version="Unreleased", date_str=None):
    sections = defaultdict(list)
    breaking = []

    for c in commits:
        section, msg, bp = _categorize(c["subject"])
        if section == "skip":
            continue
        bb = _has_breaking(c["body"])
        entry = _fmt(msg, c["body"], bp or bb)
        (breaking if (bp or bb) else sections[section]).append(entry)

    lines = ["# Changelog", ""]
    h = f"## {version}"
    if date_str or version.lower() != "unreleased":
        h += f" — {date_str or date.today().isoformat()}"
    lines.append(h)
    lines.append("")

    if breaking:
        lines.append("### ⚠ Breaking Changes")
        lines.append("")
        lines.extend(breaking)
        lines.append("")

    for key in ["added", "fixed", "changed", "removed", "docs", "test", "ci"]:
        entries = sections.get(key)
        if not entries:
            continue
        lines.append(f"### {SECTION_HEADING[key]}")
        lines.append("")
        lines.extend(entries)
        lines.append("")

    if not breaking and not any(sections.values()):
        lines.append("_No notable changes._")
        lines.append("")

    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history.")
    p.add_argument("--since", "-s", help="Tag or date (YYYY-MM-DD). Default: last tag.")
    p.add_argument("--until", "-u", help="End date. Requires --since as date.")
    p.add_argument("--output", "-o", help="Output file (default: stdout).")
    p.add_argument("--version", "-v", default="Unreleased", help="Version string.")
    p.add_argument("--repo", "-r", help="Path to git repo (default: cwd).")
    p.add_argument("--date", "-d", help="Release date (default: today for versions).")
    args = p.parse_args()

    commits = get_commits(since=args.since, until=args.until,
                          cwd=os.path.abspath(args.repo) if args.repo else None)
    if not commits:
        return

    changelog = build(commits, version=args.version, date_str=args.date)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(changelog + "\n")
        print(f"Written to {args.output}")
    else:
        print(changelog)


if __name__ == "__main__":
    main()
