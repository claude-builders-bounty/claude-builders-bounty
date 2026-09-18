#!/usr/bin/env python3
"""Generate reproducible release notes from local Git history (Python 3.9+)."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

START = "<!-- generated-changelog:start -->"
END = "<!-- generated-changelog:end -->"
CATEGORIES = ("Added", "Fixed", "Changed", "Removed")


def git(repo, *args):
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, check=False
    )
    if result.returncode:
        raise ValueError(result.stderr.decode("utf-8", "replace").strip() or "Git failed")
    return result.stdout.decode("utf-8", "replace").strip("\r\n")


def category(subject):
    match = re.match(r"^([a-z]+)(?:\([^\r\n]*?\))?!?:\s", subject, re.I)
    kind = match.group(1).lower() if match else subject.split(" ", 1)[0].lower()
    return {
        "feat": "Added", "feature": "Added", "add": "Added", "added": "Added",
        "fix": "Fixed", "fixed": "Fixed", "bugfix": "Fixed",
        "remove": "Removed", "removed": "Removed", "delete": "Removed",
    }.get(kind, "Changed")


def escape(text):
    # Commit messages are untrusted Markdown, not executable markup or directives.
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"[\x00-\x1f\x7f]", " ", text)
    return re.sub(r"([\\`*_{}\[\]()!#|])", r"\\\1", text)


def render(repo):
    root = Path(git(repo, "rev-parse", "--show-toplevel"))
    if git(root, "rev-parse", "--is-shallow-repository") == "true":
        raise ValueError("Shallow history: fetch full history and release tags before generating notes")
    head = git(root, "rev-parse", "--verify", "HEAD^{commit}")
    # Tags on merged topic branches must not hide unreleased mainline commits.
    tags = git(root, "tag", "--merged", head)
    base = None
    if tags:
        result = subprocess.run(
            ["git", "-C", str(root), "describe", "--tags", "--first-parent", "--abbrev=0", head],
            capture_output=True, check=False,
        )
        if result.returncode == 0:
            tag = result.stdout.decode("utf-8", "replace").strip()
            base = git(root, "rev-parse", "--verify", tag + "^{commit}")
        elif result.returncode != 128:
            raise ValueError("Could not find the release boundary")
    revision = f"{base}..{head}" if base else head
    raw = git(root, "log", "-z", "--format=%H%x00%s", revision, "--")
    records = raw.split("\0") if raw else []
    if records and records[-1] == "":
        records.pop()
    if len(records) % 2:
        raise ValueError("Unexpected Git log framing")
    groups = {name: [] for name in CATEGORIES}
    for index in range(0, len(records), 2):
        sha, subject = records[index:index + 2]
        groups[category(subject)].append(f"- {escape(subject)} (`{sha}`)")
    lines = [START, "## [Unreleased]", "", f"Head: `{head}`",
             f"Base: `{base}`" if base else "Base: no release tag on the first-parent history; all commits included.", ""]
    for name, entries in groups.items():
        lines.extend([f"### {name}", "", *(entries or ["- None."]), ""])
    lines.append(END)
    return root, "\n".join(lines) + "\n"


def update(path, section):
    if path.is_symlink():
        raise ValueError("Refusing to replace a symlink")
    old = path.read_bytes() if path.exists() else b""
    if old:
        starts, ends = old.count(START.encode()), old.count(END.encode())
        if starts != 1 or ends != 1:
            raise ValueError("Existing file is not uniquely managed; use --stdout to review and merge manually")
        start, end = old.index(START.encode()), old.index(END.encode())
        if start >= end:
            raise ValueError("Invalid managed-section marker order")
        # Preserve all handwritten bytes outside the managed markers.
        new = old[:start] + section.rstrip("\n").encode() + old[end + len(END):]
    else:
        new = b"# Changelog\n\n" + section.encode()
    if old == new:
        return
    descriptor, temp = tempfile.mkstemp(prefix=".changelog-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(new)
        if path.exists():
            os.chmod(temp, path.stat().st_mode)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, help="Output path relative to repository root (default CHANGELOG.md)")
    parser.add_argument("--stdout", action="store_true", help="Print notes without modifying any file")
    args = parser.parse_args()
    if args.stdout and args.output:
        parser.error("--stdout and --output cannot be combined")
    try:
        root, section = render(args.repo)
        if args.stdout:
            sys.stdout.buffer.write(("# Changelog\n\n" + section).encode())
        else:
            output = args.output or Path("CHANGELOG.md")
            update(output if output.is_absolute() else root / output, section)
    except (ValueError, OSError) as error:
        print(f"changelog: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
