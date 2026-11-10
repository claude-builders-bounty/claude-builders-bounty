#!/usr/bin/env python3
"""
CHANGELOG Generator — Generates structured CHANGELOG.md from git history.

Supports conventional commits format (feat:, fix:, chore:, etc.)
Groups commits by version/tag or date range.

Usage:
    python changelog_generator.py [--repo PATH] [--since-tag TAG] [--output FILE] [--format markdown|json]
"""

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# --- Conventional Commit Types ---
COMMIT_TYPES = {
    "feat":     ("🚀 Features",        "feature"),
    "fix":      ("🐛 Bug Fixes",        "fix"),
    "docs":     ("📚 Documentation",    "docs"),
    "style":    ("💅 Styles",           "style"),
    "refactor": ("♻️  Refactoring",     "refactor"),
    "perf":     ("⚡ Performance",      "perf"),
    "test":     ("✅ Tests",            "test"),
    "build":    ("🏗️  Build System",    "build"),
    "ci":       ("🤖 CI/CD",           "ci"),
    "chore":    ("🔧 Chores",          "chore"),
    "revert":   ("⏪ Reverts",         "revert"),
    "security": ("🔒 Security",        "security"),
    "deprecate":("⚠️  Deprecations",   "deprecate"),
    "breaking": ("💥 Breaking Changes","breaking"),
}

OTHER_LABEL = "📝 Other Changes"

# Pattern: type(scope)!: description
CONVENTIONAL_RE = re.compile(
    r"^(?P<type>\w+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?\s*:\s*(?P<description>.+)$",
    re.IGNORECASE,
)

# Git log separator
LOG_SEP = "|||COMMIT|||"
GIT_FORMAT = f"{LOG_SEP}%H%n%h%n%d%n%s%n%b%n%ae%n%ai"


def run_git(args: list[str], cwd: str) -> str:
    """Run a git command and return stdout, raising on error."""
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")
    return result.stdout.strip()


def get_tags(repo: str) -> list[tuple[str, str]]:
    """Return list of (tag_name, commit_hash) sorted by version date descending."""
    try:
        raw = run_git(
            ["tag", "--sort=-version:refname", "--format=%(refname:short)|%(objectname:short)"],
            cwd=repo,
        )
    except RuntimeError:
        return []
    tags = []
    for line in raw.splitlines():
        line = line.strip()
        if "|" in line:
            name, sha = line.split("|", 1)
            tags.append((name.strip(), sha.strip()))
    return tags


def get_log(repo: str, rev_range: Optional[str] = None) -> str:
    """Fetch raw git log for a revision range."""
    args = ["log", f"--format={GIT_FORMAT}", "--no-merges"]
    if rev_range:
        args.append(rev_range)
    return run_git(args, cwd=repo)


def parse_log(raw: str) -> list[dict]:
    """Parse raw git log output into structured commit dicts."""
    commits = []
    blocks = raw.split(LOG_SEP)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.splitlines()
        if len(lines) < 6:
            continue
        sha_full   = lines[0].strip()
        sha_short  = lines[1].strip()
        refs_raw   = lines[2].strip()
        subject    = lines[3].strip()
        # body lines (may be empty) end before email and date
        email      = lines[-2].strip()
        date_str   = lines[-1].strip()
        body_lines = lines[4:-2]
        body       = "\n".join(l.strip() for l in body_lines if l.strip())

        # Parse date
        try:
            dt = datetime.fromisoformat(date_str)
        except ValueError:
            dt = datetime.now(tz=timezone.utc)

        # Extract tags/refs
        ref_tags = re.findall(r"tag:\s*([^\s,)]+)", refs_raw)

        # Parse conventional commit
        m = CONVENTIONAL_RE.match(subject)
        if m:
            ctype    = m.group("type").lower()
            scope    = m.group("scope") or ""
            breaking = bool(m.group("breaking"))
            desc     = m.group("description").strip()
        else:
            ctype    = "other"
            scope    = ""
            breaking = False
            desc     = subject

        # Detect BREAKING CHANGE in body
        if re.search(r"BREAKING[- ]CHANGE", body, re.IGNORECASE):
            breaking = True

        commits.append({
            "sha_full":  sha_full,
            "sha_short": sha_short,
            "tags":      ref_tags,
            "subject":   subject,
            "body":      body,
            "email":     email,
            "date":      dt,
            "type":      ctype,
            "scope":     scope,
            "breaking":  breaking,
            "desc":      desc,
        })
    return commits


def group_by_version(repo: str, since_tag: Optional[str] = None) -> list[dict]:
    """
    Group commits into version sections based on tags.
    Returns list of version dicts ordered newest first.
    """
    tags = get_tags(repo)

    # Build ranges: (version_name, range_spec, date)
    ranges = []

    if not tags:
        # No tags — single "Unreleased" section
        raw = get_log(repo, rev_range=None if not since_tag else f"{since_tag}..HEAD")
        commits = parse_log(raw)
        date = commits[0]["date"] if commits else datetime.now(tz=timezone.utc)
        return [{"version": "Unreleased", "date": date.date().isoformat(), "commits": commits}]

    # Build version ranges from newest to oldest
    # tags is already sorted newest→oldest
    tag_names = [t[0] for t in tags]

    # First section: HEAD..latest_tag (Unreleased changes)
    try:
        unreleased_raw = get_log(repo, rev_range=f"{tag_names[0]}..HEAD")
        unreleased_commits = parse_log(unreleased_raw)
        if unreleased_commits:
            ranges.append({
                "version": "Unreleased",
                "date":    datetime.now(tz=timezone.utc).date().isoformat(),
                "commits": unreleased_commits,
            })
    except RuntimeError:
        pass

    # Apply --since-tag filter: only include this tag and newer (stop before older tags)
    end_idx = len(tag_names)  # exclusive — process all tags by default
    if since_tag and since_tag in tag_names:
        end_idx = tag_names.index(since_tag) + 1  # include the since_tag itself

    # For each tag, range is (prev_tag..tag)
    for i in range(0, end_idx):
        tag = tag_names[i]
        if i + 1 < len(tag_names):
            prev_tag = tag_names[i + 1]
            rev_range = f"{prev_tag}..{tag}"
        else:
            rev_range = tag  # from beginning to this tag

        try:
            raw = get_log(repo, rev_range=rev_range)
            commits = parse_log(raw)
        except RuntimeError:
            commits = []

        # Get tag date
        try:
            date_str = run_git(
                ["log", "-1", "--format=%ai", tag],
                cwd=repo
            )
            tag_date = datetime.fromisoformat(date_str.strip()).date().isoformat()
        except Exception:
            tag_date = "Unknown"

        ranges.append({"version": tag, "date": tag_date, "commits": commits})

    return ranges


def render_markdown(sections: list[dict], repo_url: Optional[str] = None) -> str:
    """Render version sections as Markdown CHANGELOG."""
    lines = ["# Changelog", ""]
    lines += [
        "> Generated automatically from git history.",
        "> Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) "
        "and [Conventional Commits](https://www.conventionalcommits.org/).",
        "",
    ]

    for sec in sections:
        version = sec["version"]
        date    = sec["date"]
        commits = sec["commits"]

        if not commits:
            continue

        # Section header with optional link
        if repo_url and version != "Unreleased":
            lines.append(f"## [{version}]({repo_url}/releases/tag/{version}) — {date}")
        else:
            lines.append(f"## {version} — {date}")
        lines.append("")

        # Group commits by type
        by_type: dict[str, list[dict]] = defaultdict(list)
        for c in commits:
            by_type[c["type"]].append(c)

        # Breaking changes first
        breaking = [c for c in commits if c["breaking"]]
        if breaking:
            lines.append("### 💥 Breaking Changes")
            lines.append("")
            for c in breaking:
                scope_str = f"**{c['scope']}:** " if c["scope"] else ""
                lines.append(f"- {scope_str}{c['desc']} ([`{c['sha_short']}`])")
            lines.append("")

        # Render each known type
        rendered_shas = {c["sha_full"] for c in breaking}
        for type_key, (label, _) in COMMIT_TYPES.items():
            if type_key == "breaking":
                continue
            group = [c for c in by_type.get(type_key, []) if c["sha_full"] not in rendered_shas]
            if not group:
                continue
            lines.append(f"### {label}")
            lines.append("")
            for c in group:
                scope_str = f"**{c['scope']}:** " if c["scope"] else ""
                commit_ref = f"([`{c['sha_short']}`])"
                if c["body"]:
                    lines.append(f"- {scope_str}{c['desc']} {commit_ref}")
                    for body_line in c["body"].splitlines():
                        if body_line.strip():
                            lines.append(f"  > {body_line.strip()}")
                else:
                    lines.append(f"- {scope_str}{c['desc']} {commit_ref}")
                rendered_shas.add(c["sha_full"])
            lines.append("")

        # Other / unrecognized types
        others = [c for c in commits if c["sha_full"] not in rendered_shas]
        if others:
            lines.append(f"### {OTHER_LABEL}")
            lines.append("")
            for c in others:
                lines.append(f"- {c['desc']} ([`{c['sha_short']}`])")
                rendered_shas.add(c["sha_full"])
            lines.append("")

    return "\n".join(lines)


def render_json(sections: list[dict]) -> str:
    """Render version sections as structured JSON."""
    output = []
    for sec in sections:
        version_data = {
            "version":  sec["version"],
            "date":     sec["date"],
            "commits":  [],
        }
        for c in sec["commits"]:
            version_data["commits"].append({
                "sha":      c["sha_short"],
                "type":     c["type"],
                "scope":    c["scope"],
                "breaking": c["breaking"],
                "desc":     c["desc"],
                "body":     c["body"],
                "email":    c["email"],
                "date":     c["date"].isoformat(),
            })
        output.append(version_data)
    return json.dumps(output, indent=2, default=str)


def detect_repo_url(repo: str) -> Optional[str]:
    """Try to detect the remote origin URL for linking commits."""
    try:
        url = run_git(["config", "--get", "remote.origin.url"], cwd=repo)
        # Convert SSH → HTTPS
        url = re.sub(r"^git@([^:]+):", r"https://\1/", url)
        url = url.removesuffix(".git")
        return url
    except RuntimeError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a structured CHANGELOG from git history.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--repo", "-r",
        default=".",
        help="Path to the git repository (default: current directory)",
    )
    parser.add_argument(
        "--since-tag", "-s",
        dest="since_tag",
        default=None,
        help="Only include versions from this tag forward",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["markdown", "json"],
        default="markdown",
        dest="fmt",
        help="Output format: markdown (default) or json",
    )
    parser.add_argument(
        "--no-emoji",
        action="store_true",
        help="Strip emoji from markdown output",
    )
    parser.add_argument(
        "--repo-url",
        default=None,
        help="Remote repository URL for hyperlinks (auto-detected if omitted)",
    )
    args = parser.parse_args()

    repo = str(Path(args.repo).resolve())

    # Validate it's a git repo
    try:
        run_git(["rev-parse", "--git-dir"], cwd=repo)
    except RuntimeError:
        print(f"ERROR: '{repo}' is not a git repository.", file=sys.stderr)
        return 1

    # Detect URL for links
    repo_url = args.repo_url or detect_repo_url(repo)

    # Gather & group commits
    sections = group_by_version(repo, since_tag=args.since_tag)

    # Render
    if args.fmt == "json":
        output = render_json(sections)
    else:
        output = render_markdown(sections, repo_url=repo_url)
        if args.no_emoji:
            # Strip common emoji via regex
            output = re.sub(
                r"[\U00010000-\U0010ffff\U00002600-\U000027FF\U0001F300-\U0001FAFF]",
                "",
                output,
            )

    # Write output
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"✅ CHANGELOG written to: {args.output}", file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
