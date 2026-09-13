#!/usr/bin/env python3
"""Generate a deterministic changelog from reachable Git history (stdlib only)."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def git(repo, *args, optional=False):
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True,
        encoding="utf-8", errors="replace", check=False,
    )
    if result.returncode and not optional:
        raise ValueError(result.stderr.strip() or "Git command failed")
    return result.stdout.strip() if result.returncode == 0 else None


def category(subject, body):
    match = re.match(r"^([a-z]+)(?:\([^\n)]*\))?(!)?:\s*(.*)$", subject)
    kind, breaking, message = match.groups() if match else ("", "", subject)
    if kind in ("remove", "removed") or re.match(r"(?i)^(remove|delete|drop)\b", message):
        group = "Removed"
    elif kind in ("feat", "add", "added") or re.match(r"(?i)^add\b", message):
        group = "Added"
    elif kind in ("fix", "fixed") or re.match(r"(?i)^(fix|resolve)\b", message):
        group = "Fixed"
    else:
        group = "Changed"
    if breaking or re.search(r"(?m)^BREAKING[ -]CHANGE:", body):
        message = "BREAKING: " + message
    # Keep untrusted commit subjects as text, not active Markdown/HTML.
    message = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    message = re.sub(r"([\\`*_\[\]])", r"\\\1", message)
    return group, message


def generate(repo):
    git(repo, "rev-parse", "--show-toplevel")
    head = git(repo, "rev-parse", "--verify", "HEAD", optional=True)
    groups = {name: [] for name in ("Added", "Fixed", "Changed", "Removed")}
    if head:
        tag = git(repo, "describe", "--tags", "--abbrev=0", "HEAD", optional=True)
        base = git(repo, "rev-parse", tag + "^{commit}") if tag else None
        revision = base + ".." + head if base else head
        hashes = git(repo, "rev-list", "--reverse", revision).splitlines()
        for sha in hashes:
            text = git(repo, "show", "-s", "--format=%s%n%b", sha)
            subject, _, body = text.partition("\n")
            group, message = category(subject, body)
            groups[group].append("- {} (`{}`)".format(message, sha[:12]))
    lines = ["# Changelog", "", "## [Unreleased]", ""]
    for name, entries in groups.items():
        if entries:
            lines.extend(["### " + name, "", *entries, ""])
    if not any(groups.values()):
        lines.extend(["No changes since the latest reachable tag (or repository is empty).", ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Repository to read (default: current directory)")
    parser.add_argument("-o", "--output", default="CHANGELOG.md", help="Destination, relative to current directory; '-' for stdout")
    parser.add_argument("--force", action="store_true", help="Replace an existing destination")
    args = parser.parse_args()
    try:
        content = generate(args.repo)
        if args.output == "-":
            sys.stdout.write(content)
            return 0
        output = Path(args.output)
        if output.is_symlink():
            raise ValueError("Refusing to write through a symlink")
        if args.force:
            # Write completely before atomically replacing the destination.
            tmp_name = None
            try:
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=output.parent, delete=False) as tmp:
                    tmp_name = tmp.name
                    tmp.write(content)
                os.replace(tmp_name, output)
            finally:
                if tmp_name and os.path.exists(tmp_name):
                    os.unlink(tmp_name)
        else:
            with output.open("x", encoding="utf-8") as stream:
                stream.write(content)
        return 0
    except (OSError, ValueError) as error:
        print("changelog: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
