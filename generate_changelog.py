#!/usr/bin/env python3
"""Generate an Unreleased changelog from local Git history; no dependencies."""

import argparse
import html
import re
import subprocess
import sys
from pathlib import Path


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")
PREFIX = re.compile(r"^([a-z]+)(?:\([^)]*\))?!?:\s*", re.IGNORECASE)
TYPES = {
    "feat": "Added", "feature": "Added", "add": "Added",
    "fix": "Fixed", "bugfix": "Fixed", "hotfix": "Fixed",
    "remove": "Removed", "delete": "Removed", "drop": "Removed",
}


def git(repo, *args, check=True):
    return subprocess.run(
        ["git", "-c", "i18n.logOutputEncoding=utf-8", "-C", str(repo), *args], check=check, capture_output=True,
        encoding="utf-8", errors="replace",
    )


def markdown(text):
    text = html.escape(text, quote=False).replace("\\", "\\\\")
    return re.sub(r"([`*_\[\]#|])", r"\\\1", text)


def category(subject):
    match = PREFIX.match(subject)
    if match:
        return TYPES.get(match[1].lower(), "Changed")
    # Plain subjects use their leading verb; ambiguous messages stay Changed.
    word = subject.split(maxsplit=1)[0].lower() if subject else ""
    if word in ("add", "adds", "added", "introduce", "implement"):
        return "Added"
    if word in ("fix", "fixes", "fixed", "resolve", "repair"):
        return "Fixed"
    if word in ("remove", "removes", "removed", "delete", "drop"):
        return "Removed"
    return "Changed"


def generate(repo):
    root = Path(git(repo, "rev-parse", "--show-toplevel").stdout.strip())
    git(root, "rev-parse", "--verify", "HEAD")
    if git(root, "rev-parse", "--is-shallow-repository").stdout.strip() == "true":
        raise ValueError("Shallow history: run git fetch --unshallow --tags first.")
    tag = git(root, "describe", "--tags", "--abbrev=0", "HEAD", check=False)
    base = tag.stdout.strip() if tag.returncode == 0 else None
    revision = f"{base}..HEAD" if base else "HEAD"
    log = git(root, "log", "--reverse", "--no-merges", "--format=%H%x09%s", revision, "--")
    groups = {name: [] for name in CATEGORIES}
    for line in log.stdout.splitlines():
        sha, _, subject = line.partition("\t")
        subject = " ".join(subject.split())
        groups[category(subject)].append(f"- {markdown(subject)} (`{sha[:12]}`)")
    note = (f"Changes since tag **{markdown(base)}**."
            if base else "No reachable tag; includes all non-merge commits through HEAD.")
    lines = ["# Changelog", "", "## [Unreleased]", "", note, ""]
    for name, entries in groups.items():
        lines.extend([f"### {name}", "", *(entries or ["_None._"]), ""])
    return root, "\n".join(lines)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Git working tree (default: current directory)")
    parser.add_argument("--output", help="Output path, or - for stdout (default: repository CHANGELOG.md)")
    parser.add_argument("--force", action="store_true", help="Replace an existing output file")
    args = parser.parse_args()
    try:
        root, content = generate(args.repo)
        if args.output == "-":
            sys.stdout.write(content)
        else:
            output = Path(args.output) if args.output else root / "CHANGELOG.md"
            with output.open("w" if args.force else "x", encoding="utf-8", newline="\n") as stream:
                stream.write(content)
            print(f"Wrote {output}")
    except FileExistsError:
        parser.exit(1, "Error: output already exists; use --output for a new file or --force to replace it.\n")
    except subprocess.CalledProcessError as error:
        parser.exit(1, f"Git error: {error.stderr.strip()}\n")
    except (OSError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
