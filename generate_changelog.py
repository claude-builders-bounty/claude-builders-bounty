#!/usr/bin/env python3
"""Generate a reviewable changelog from local Git history; Python 3.9+."""
import argparse
import re
import subprocess
import sys
from pathlib import Path

SECTIONS = ("Added", "Fixed", "Changed", "Removed")


def git(repo, *args):
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True,
        encoding="utf-8", errors="replace", check=False,
    )
    if result.returncode:
        raise ValueError(result.stderr.strip() or "Git command failed")
    return result.stdout.strip()


def category(subject):
    match = re.match(r"^([a-z]+)(?:\([^\r\n]*\))?!?:\s*(.+)$", subject, re.I)
    if match:
        kind = match.group(1).lower()
        return {"feat": "Added", "fix": "Fixed", "remove": "Removed",
                "removed": "Removed", "delete": "Removed"}.get(kind, "Changed")
    verb = subject.split(maxsplit=1)[0].lower().rstrip(":") if subject else ""
    return {"add": "Added", "added": "Added", "fix": "Fixed", "fixed": "Fixed",
            "remove": "Removed", "removed": "Removed", "delete": "Removed",
            "deleted": "Removed"}.get(verb, "Changed")


def escape(text):
    # Render commit subjects as text, never Markdown links or embedded HTML.
    text = " ".join(text.split())
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"([\\`*_{}\[\]()#!|])", r"\\\1", text)


def generate(repo, since=None):
    head = git(repo, "rev-parse", "--verify", "HEAD^{commit}")
    if since is None:
        result = subprocess.run(
            ["git", "-C", str(repo), "describe", "--tags", "--abbrev=0", head],
            capture_output=True, encoding="utf-8", errors="replace",
        )
        since = result.stdout.strip() if result.returncode == 0 else None
    base = git(repo, "rev-parse", "--verify", "--end-of-options", since + "^{commit}") if since else None
    if base:
        ancestor = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", base, head], capture_output=True)
        if ancestor.returncode != 0:
            raise ValueError("The base revision must be an ancestor of HEAD")
    revision = base + ".." + head if base else head
    hashes = git(repo, "rev-list", "--reverse", revision, "--").splitlines()
    grouped = {name: [] for name in SECTIONS}
    for commit in hashes:
        subject = git(repo, "show", "-s", "--format=%s", commit)
        grouped[category(subject)].append(f"- {escape(subject) or '(empty subject)'} (`{commit[:12]}`)")
    lines = ["# Changelog", "", "## [Unreleased]", "",
             "Generated from committed history; review classifications before publishing.", "",
             f"Head: `{head}`.", ""]
    if base:
        lines += [f"Base: {escape(since)} (`{base}`), exclusive.", ""]
    else:
        lines += ["No reachable tag found; includes all commits reachable from HEAD.", ""]
    for name in SECTIONS:
        lines += [f"### {name}", ""] + (grouped[name] or ["- None."]) + [""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Local repository (default: current directory)")
    parser.add_argument("--since", help="Explicit ancestor tag or commit, excluded from output")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output relative to current directory, or - for stdout")
    parser.add_argument("--force", action="store_true", help="Replace an existing output file")
    args = parser.parse_args()
    try:
        content = generate(Path(args.repo), args.since)
        if args.output == "-":
            sys.stdout.write(content)
        else:
            # Exclusive creation prevents accidentally replacing release history.
            with Path(args.output).open("w" if args.force else "x", encoding="utf-8", newline="\n") as out:
                out.write(content)
            print(f"Wrote {args.output}", file=sys.stderr)
    except (ValueError, OSError) as exc:
        print(f"changelog: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
