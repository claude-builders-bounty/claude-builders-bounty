#!/usr/bin/env python3
"""Generate a reviewable Markdown changelog using only Python's standard library."""

import argparse
import html
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


CATEGORIES = ("Added", "Fixed", "Changed", "Removed")
TYPES = {
    "feat": "Added", "feature": "Added", "add": "Added", "added": "Added",
    "fix": "Fixed", "fixed": "Fixed", "bugfix": "Fixed", "hotfix": "Fixed",
    "remove": "Removed", "removed": "Removed", "delete": "Removed",
}
CONVENTIONAL = re.compile(r"^([a-z][a-z0-9_-]*)(?:\([^()]*\))?!?:\s+", re.I)


class ChangelogError(Exception):
    """A user-facing error, without a traceback or partial output."""


def git(repo, *args, allow_failure=False):
    """Pass arguments directly: commit text and revision names are never shell code."""
    try:
        result = subprocess.run(
            ["git", "--no-pager", "-C", str(repo), *args],
            capture_output=True, encoding="utf-8", errors="replace", timeout=60,
        )
    except FileNotFoundError as exc:
        raise ChangelogError("Git is required and must be on PATH.") from exc
    except subprocess.TimeoutExpired as exc:
        raise ChangelogError("Git exceeded the 60-second command timeout.") from exc
    if result.returncode and not allow_failure:
        raise ChangelogError(result.stderr.strip() or "Git command failed.")
    return result


def resolve_commit(repo, ref):
    result = git(repo, "rev-parse", "--verify", "--end-of-options",
                 ref + "^{commit}", allow_failure=True)
    if result.returncode:
        raise ChangelogError("Cannot resolve revision {!r} to a commit.".format(ref))
    return result.stdout.strip()


def category(subject):
    conventional = CONVENTIONAL.match(subject)
    if conventional:
        return TYPES.get(conventional.group(1).lower(), "Changed")
    first_word = subject.partition(" ")[0].lower()
    for words, group in (
        (("add", "added", "adds", "create", "introduce"), "Added"),
        (("fix", "fixed", "fixes", "resolve", "repair"), "Fixed"),
        (("remove", "removed", "removes", "delete", "drop"), "Removed"),
    ):
        if first_word in words:
            return group
    return "Changed"


def markdown_text(text):
    # Keep untrusted commit subjects as text, not HTML, links or Markdown controls.
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", text)
    text = html.escape(text, quote=False)
    return re.sub(r"([\\`*_{}\[\]()!#|])", r"\\\1", text)


def generate(repo, since=None, until="HEAD", include_merges=False):
    root_result = git(repo, "rev-parse", "--show-toplevel", allow_failure=True)
    if root_result.returncode:
        raise ChangelogError("--repo must name a non-bare Git working tree.")
    root = Path(root_result.stdout.rstrip("\n"))
    if git(root, "rev-parse", "--is-shallow-repository").stdout.strip() == "true":
        raise ChangelogError("Shallow history is incomplete. Fetch full history and tags first.")
    head = resolve_commit(root, until)
    label = since
    if since is None:
        reachable = git(root, "tag", "--merged", head).stdout.splitlines()
        if reachable:
            label = git(root, "describe", "--tags", "--abbrev=0", head).stdout.strip()
            base = resolve_commit(root, "refs/tags/" + label)
        else:
            base = None
    else:
        base = resolve_commit(root, since)
    if base:
        ancestor = git(root, "merge-base", "--is-ancestor", base, head, allow_failure=True)
        if ancestor.returncode:
            raise ChangelogError("The --since revision must be an ancestor of --until.")

    revision_range = base + ".." + head if base else head
    args = ["log", "--reverse", "--topo-order", "--encoding=UTF-8", "--no-notes",
            "--no-show-signature", "-z", "--format=%H%x00%s"]
    if not include_merges:
        args.append("--no-merges")
    # Only validated object IDs enter the revision range; '--' ends revision parsing.
    fields = git(root, *args, revision_range, "--").stdout.split("\0")
    if fields[-1] == "":
        fields.pop()
    if len(fields) % 2:
        raise ChangelogError("Unexpected Git log record format.")
    groups = {name: [] for name in CATEGORIES}
    for sha, subject in zip(fields[::2], fields[1::2]):
        if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", sha):
            raise ChangelogError("Unexpected commit identifier in Git output.")
        groups[category(subject)].append("- {} (`{}`)".format(markdown_text(subject), sha[:12]))

    lines = ["# Changelog", "", "## Unreleased", ""]
    if base:
        lines.append("Commits after **{}** (`{}`) through `{}`.".format(
            markdown_text(label), base, head))
    else:
        lines.append("No reachable tags; includes all history through `{}`.".format(head))
    lines.extend(["", "Merge commits {}. Entries use oldest-first topological order within each category.".format(
        "included" if include_merges else "excluded"), ""])
    for name in CATEGORIES:
        lines.extend(["### " + name, "", *(groups[name] or ["_No changes._"]), ""])
    return root, "\n".join(lines), len(fields) // 2


def write_output(path, content, force=False):
    if path.is_symlink():
        raise ChangelogError("Refusing to replace a symbolic-link output.")
    if path.exists() and not force:
        raise ChangelogError("Output exists; use --force to replace it, or --output - to preview.")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if force:
            os.replace(temporary, path)
        else:
            # An atomic, no-clobber publication even if another process creates path.
            os.link(temporary, path)
    except FileExistsError as exc:
        raise ChangelogError("Output already exists; it was not overwritten.") from exc
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Git working tree (default: current directory)")
    parser.add_argument("--since", help="Exclusive ancestor tag/commit; default: nearest reachable tag")
    parser.add_argument("--until", default="HEAD", help="Inclusive end revision (default: HEAD)")
    parser.add_argument("--output", default="CHANGELOG.md", help="Path relative to repo root; '-' for stdout")
    parser.add_argument("--force", action="store_true", help="Replace an existing output; reject symlink output")
    parser.add_argument("--include-merges", action="store_true", help="Also include merge commit subjects")
    options = parser.parse_args(argv)
    try:
        root, document, count = generate(options.repo, options.since, options.until,
                                         options.include_merges)
        if options.output == "-":
            sys.stdout.write(document)
        else:
            path = Path(options.output)
            if not path.is_absolute():
                path = root / path
            write_output(path, document, options.force)
            print("Wrote {} ({} commits).".format(path, count), file=sys.stderr)
        return 0
    except (ChangelogError, OSError) as exc:
        print("error: {}".format(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
