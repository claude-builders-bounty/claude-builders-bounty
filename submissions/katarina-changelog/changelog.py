#!/usr/bin/env python3
"""Generate a deterministic, categorized changelog using Git and Python stdlib."""
import argparse
import os
import pathlib
import re
import subprocess
import sys
import tempfile


def git(repo, *args, check=True):
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8")
    if check and result.returncode:
        raise ValueError(result.stderr.strip() or "Git command failed")
    return result


def render(repo):
    root = pathlib.Path(git(repo, "rev-parse", "--show-toplevel").stdout.strip())
    if git(root, "rev-parse", "--is-shallow-repository").stdout.strip() == "true":
        raise ValueError("History is shallow; run git fetch --unshallow --tags first.")
    head = git(root, "rev-parse", "HEAD").stdout.strip()
    tag_result = git(root, "describe", "--tags", "--abbrev=0", "HEAD", check=False)
    tag = tag_result.stdout.strip() if tag_result.returncode == 0 else None
    revision = f"{tag}..HEAD" if tag else "HEAD"
    records = git(root, "log", "--no-merges", "--reverse", "--format=%H%x00%s", revision, "--").stdout
    categories = {name: [] for name in ("Added", "Fixed", "Changed", "Removed")}
    for line in records.splitlines():
        sha, subject = line.split("\0", 1)
        match = re.match(r"^([a-z]+)(?:\([^)]*\))?!?:\s*(.*)$", subject, re.I)
        kind, title = (match.group(1).lower(), match.group(2)) if match else ("", subject)
        category = {"feat": "Added", "add": "Added", "fix": "Fixed", "bugfix": "Fixed", "remove": "Removed", "delete": "Removed"}.get(kind, "Changed")
        title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        title = re.sub(r"([\\`*_\[\]])", r"\\\1", title)
        if match and "!" in subject.split(":", 1)[0]:
            title = "**Breaking:** " + title
        categories[category].append(f"- {title} (`{sha[:12]}`)")
    date = git(root, "show", "-s", "--format=%cs", "HEAD").stdout.strip()
    since = f"since `{tag}`" if tag else "from all reachable history (no tag)"
    lines = ["# Changelog", "", f"## [Unreleased] - {date}", "", f"Commits {since}; source HEAD `{head}`. Merge commits are excluded.", ""]
    for category, entries in categories.items():
        lines.extend([f"### {category}", "", *(entries or ["- None."]), ""])
    return root, "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Git repository (default: current directory)")
    parser.add_argument("--output", default="CHANGELOG.md", help="Path relative to repository root")
    parser.add_argument("--overwrite", action="store_true", help="Explicitly replace an existing output")
    args = parser.parse_args()
    try:
        root, content = render(args.repo)
        output = pathlib.Path(args.output)
        if not output.is_absolute():
            output = root / output
        if output.exists() and not args.overwrite:
            if output.read_text(encoding="utf-8") == content:
                print(f"Unchanged: {output}")
                return 0
            raise ValueError("Output exists with different contents; use another --output or --overwrite.")
        output.parent.mkdir(parents=True, exist_ok=True)
        # Replace atomically so interrupted writes never leave a partial changelog.
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=output.parent, delete=False) as handle:
                temporary = pathlib.Path(handle.name)
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, output)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        print(f"Wrote {output}")
        return 0
    except (ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
