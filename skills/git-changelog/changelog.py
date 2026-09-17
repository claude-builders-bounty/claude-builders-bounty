#!/usr/bin/env python3
"""Generate a reviewable changelog from local Git history. Python 3.10+, Git."""
from __future__ import annotations
import argparse
import html
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile

START = "<!-- generate-changelog:start -->"
END = "<!-- generate-changelog:end -->"
SECTIONS = ("Added", "Fixed", "Changed", "Removed")
CONVENTIONAL = re.compile(r"^(?P<kind>[a-z][a-z0-9_-]*)(?:\((?P<scope>[^)\r\n]+)\))?(?P<breaking>!)?:\s*(?P<text>.+)$", re.I)

class ChangelogError(Exception):
    """User-facing input or repository error."""

def git(repo: Path, *args: str, allowed: tuple[int, ...] = (0,)) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "--no-pager", *args],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C", "GIT_TERMINAL_PROMPT": "0"},
            timeout=60, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ChangelogError(f"Cannot run Git: {exc}") from exc
    if result.returncode not in allowed:
        message = result.stderr.decode("utf-8", "replace").strip()
        raise ChangelogError(message or f"Git exited with {result.returncode}")
    return result.stdout.decode("utf-8", "replace")

def markdown(text: str) -> str:
    """Render commit text literally, without interpreting HTML or Markdown."""
    text = " ".join(text.split())
    text = html.escape(text, quote=False)
    return re.sub(r"([\\`*_{}\[\]()#+.!|>~-])", r"\\\1", text)

def categorize(subject: str, body: str = "") -> tuple[str, str, bool]:
    match = CONVENTIONAL.match(subject)
    if match:
        kind = match.group("kind").lower()
        message = match.group("text")
        if match.group("scope"):
            message = f"{match.group('scope')}: {message}"
        breaking = bool(match.group("breaking"))
    else:
        kind = subject.split(maxsplit=1)[0].lower().rstrip(":") if subject else ""
        message = subject
        breaking = False
    if kind in {"feat", "feature", "add", "added", "adds", "introduce", "introduces"}:
        section = "Added"
    elif kind in {"fix", "fixes", "fixed", "bugfix", "hotfix", "repair", "repairs"}:
        section = "Fixed"
    elif kind in {"remove", "removed", "removes", "delete", "deleted", "drop", "drops"}:
        section = "Removed"
    else:
        section = "Changed"
    breaking = breaking or bool(re.search(r"(?mi)^BREAKING[ -]CHANGE:\s*\S", body))
    return section, message, breaking

def resolve_commit(repo: Path, reference: str) -> str:
    # --end-of-options keeps even a hostile reference out of Git's option parser.
    value = git(repo, "rev-parse", "--verify", "--end-of-options", reference + "^{commit}").strip()
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", value):
        raise ChangelogError("Git returned an invalid commit identifier")
    return value

def generate(repo: Path, since: str | None = None, all_history: bool = False) -> str:
    git(repo, "rev-parse", "--git-dir")
    if git(repo, "rev-parse", "--is-shallow-repository").strip() == "true":
        raise ChangelogError("Shallow history cannot establish a complete release range. Fetch complete history and tags first; this tool never fetches implicitly.")
    head = git(repo, "rev-parse", "--verify", "--quiet", "HEAD", allowed=(0, 1)).strip()
    base = None
    label = "all reachable history"
    if not head:
        if since:
            raise ChangelogError("An empty repository has no commit to compare with --since")
    elif since:
        base = resolve_commit(repo, since)
        result = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", base, head],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        if result.returncode != 0:
            raise ChangelogError("--since must resolve to an ancestor of HEAD")
        label = "since " + markdown(since)
    elif not all_history:
        tag = git(repo, "describe", "--tags", "--abbrev=0", head, allowed=(0, 128)).strip()
        if tag:
            base = resolve_commit(repo, tag)
            label = "since tag " + markdown(tag)
    grouped: dict[str, list[str]] = {section: [] for section in SECTIONS}
    count = 0
    if head:
        revision = f"{base}..{head}" if base else head
        # NUL-delimited fields preserve tabs, multiline bodies and unusual subjects.
        raw = git(repo, "log", "--no-merges", "--reverse", "--topo-order",
                  "--format=%H%x00%s%x00%b%x00", revision, "--")
        chunks = raw.split("\0")
        for offset in range(0, len(chunks) - 2, 3):
            sha, subject, body = chunks[offset].strip(), chunks[offset+1], chunks[offset+2]
            if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", sha):
                raise ChangelogError("Cannot parse Git log record")
            section, message, breaking = categorize(subject, body)
            prefix = "**Breaking:** " if breaking else ""
            grouped[section].append(f"- {prefix}{markdown(message)} (`{sha[:12]}`)")
            count += 1
    lines = [START, "## [Unreleased]", "", f"Range: {label}; {count} non-merge commit(s).", ""]
    for section in SECTIONS:
        lines += [f"### {section}", "", *(grouped[section] or ["_None._"]), ""]
    lines += [END]
    return "\n".join(lines) + "\n"

def integrate(previous: str, generated: str) -> str:
    starts, ends = previous.count(START), previous.count(END)
    if starts or ends:
        if starts != 1 or ends != 1 or previous.index(START) > previous.index(END):
            raise ChangelogError("Existing generated markers are malformed; the file was not changed")
        left, right = previous.index(START), previous.index(END) + len(END)
        return previous[:left] + generated.rstrip("\n") + previous[right:]
    if not previous:
        return "# Changelog\n\n" + generated
    heading = re.match(r"\A(?:\ufeff)?#\s+Changelog[^\n]*(?:\n|$)", previous, flags=re.I)
    if heading:
        return previous[:heading.end()].rstrip("\n") + "\n\n" + generated + "\n" + previous[heading.end():].lstrip("\n")
    return "# Changelog\n\n" + generated + "\n" + previous

def write_changelog(destination: Path, generated: str) -> bool:
    if destination.is_symlink():
        raise ChangelogError("Output is a symlink; select its intended regular-file destination explicitly")
    try:
        exists = destination.exists()
        old = destination.read_bytes() if exists else b""
        old_text = old.decode("utf-8")
        rendered = integrate(old_text, generated).encode("utf-8")
        if old == rendered:
            return False
        parent = destination.parent
        if not parent.is_dir():
            raise ChangelogError(f"Output directory does not exist: {parent}")
        mode = stat.S_IMODE(destination.stat().st_mode) if exists else 0o644
        with tempfile.NamedTemporaryFile(dir=parent, prefix=".changelog-", delete=False) as handle:
            temporary = Path(handle.name)
            try:
                handle.write(rendered)
                handle.flush()
                os.fsync(handle.fileno())
                os.chmod(temporary, mode)
                # Catch intervening changes instead of silently replacing them.
                if destination.is_symlink() or destination.exists() != exists or (exists and destination.read_bytes() != old):
                    raise ChangelogError("Output changed while generating; retry after reconciling that edit")
                os.replace(temporary, destination)
            finally:
                if temporary.exists():
                    temporary.unlink()
        return True
    except (OSError, UnicodeError) as exc:
        raise ChangelogError(f"Cannot update {destination}: {exc}") from exc

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Existing local Git checkout (default: cwd)")
    range_group = parser.add_mutually_exclusive_group()
    range_group.add_argument("--since", help="Ancestor tag or commit, excluded from output")
    range_group.add_argument("--all-history", action="store_true", help="Ignore tags and include all reachable history")
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--stdout", action="store_true", help="Print without creating or changing files")
    output_group.add_argument("--output", type=Path, help="Destination (default: REPO/CHANGELOG.md); relative paths are relative to cwd")
    args = parser.parse_args(argv)
    try:
        repo = args.repo.resolve(strict=True)
        generated = generate(repo, args.since, args.all_history)
        if args.stdout:
            sys.stdout.write("# Changelog\n\n" + generated)
        else:
            path = args.output.absolute() if args.output else repo / "CHANGELOG.md"
            changed = write_changelog(path, generated)
            print(f"{'Updated' if changed else 'Unchanged'} {path}")
        return 0
    except (ChangelogError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"changelog: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
