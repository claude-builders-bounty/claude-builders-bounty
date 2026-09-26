#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history.

Stack: Python (cross-platform). Categories commits since the last git tag
into Added / Fixed / Changed / Removed and writes a Keep-a-Changelog style
CHANGELOG.md.

Usage:
    python changelog.py [project_dir] [output_file]
Default: current directory, CHANGELOG.md
"""
import datetime
import re
import subprocess
import sys
from pathlib import Path

CATEGORY_PATTERNS = {
    "Added": re.compile(r"^(feat|feature|add|new|introduce)[(:]", re.I),
    "Fixed": re.compile(r"^(fix|bugfix|bug|hotfix|patch)[(:]", re.I),
    "Removed": re.compile(r"^(remove|delete|drop|deprecate|breaking|refactor!)[(:]", re.I),
}
CLEAN_RE = re.compile(r"^\w+(\([^)]*\))?!?:\s?(.*)$", re.DOTALL)


def git(repo: Path, *args: str) -> str:
    r = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return r.stdout.strip()


def main() -> int:
    project = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    output = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else project / "CHANGELOG.md"

    if git(project, "rev-parse", "--is-inside-work-tree") != "true":
        print(f"ERROR: '{project}' is not a git repository.", file=sys.stderr)
        return 1

    last_tag = git(project, "describe", "--tags", "--abbrev=0")
    base_spec = f"{last_tag}..HEAD" if last_tag else "HEAD"
    range_desc = f"since {last_tag}" if last_tag else "full history (no tags found)"
    print(f"Changelog range: {range_desc}", file=sys.stderr)

    log = git(project, "log", "--pretty=format:%h|%s", base_spec)
    if not log:
        output.write_text("# Changelog\n\n_(no commits in the selected range)_\n", encoding="utf-8")
        print(f"Wrote {output} (no commits).", file=sys.stderr)
        return 0

    sections = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}
    for line in log.splitlines():
        if "|" not in line:
            continue
        hash_, subject = line.split("|", 1)
        category = "Changed"
        for cat, pattern in CATEGORY_PATTERNS.items():
            if pattern.match(subject):
                category = cat
                break
        if "!:" in subject and category == "Changed":
            category = "Removed"
        match = CLEAN_RE.match(subject)
        clean = match.group(2) if match else subject
        sections[category].append(
            f"* {clean} ([{hash_}](https://github.com/user/repo/commit/{hash_}))"
        )

    today = datetime.date.today().isoformat()
    lines = [
        "# Changelog",
        "",
        "All notable changes to this project are documented in this file,",
        "generated automatically from git history.",
        "",
        f"## [Unreleased] - {today}",
        "",
        f"_Range: {range_desc}_",
        "",
    ]
    for cat in ("Added", "Fixed", "Changed", "Removed"):
        lines.append(f"### {cat}")
        if sections[cat]:
            lines.extend(sections[cat])
        else:
            lines.append(f"- No {cat.lower()} in this range.")
        lines.append("")

    output.write_text("\n".join(lines), encoding="utf-8")
    counts = ", ".join(f"{k.lower()} {len(v)}" for k, v in sections.items())
    print(f"Wrote {output} ({counts}).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())