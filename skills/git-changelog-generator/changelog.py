#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def get_latest_tag() -> str | None:
    try:
        output = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        return output if output else None
    except subprocess.CalledProcessError:
        return None


def get_git_commits(since_tag: str | None = None) -> list[str]:
    rev_range = f"{since_tag}..HEAD" if since_tag else "HEAD"
    try:
        output = subprocess.check_output(
            ["git", "log", rev_range, "--no-merges", "--pretty=format:%s"],
            stderr=subprocess.DEVNULL,
            text=True
        )
        return [line.strip() for line in output.splitlines() if line.strip()]
    except subprocess.CalledProcessError:
        return []


def categorize_commits(commits: list[str]) -> dict[str, list[str]]:
    categories = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": []
    }

    rules = [
        ("Added", r"^(?:feat|feature|add)(?:\([^\)]+\))?!?:?\s+(.*)$"),
        ("Fixed", r"^(?:fix|bugfix|patch|hotfix)(?:\([^\)]+\))?!?:?\s+(.*)$"),
        ("Removed", r"^(?:remove|drop|deprecate|delete)(?:\([^\)]+\))?!?:?\s+(.*)$"),
        ("Changed", r"^(?:refactor|perf|change|update|chore|docs|style|test|ci|build)(?:\([^\)]+\))?!?:?\s+(.*)$")
    ]

    for msg in commits:
        matched = False
        for cat, pattern in rules:
            m = re.match(pattern, msg, re.IGNORECASE)
            if m:
                clean_msg = m.group(1).strip() if m.groups() else msg
                # Capitalize first letter of bullet
                if clean_msg:
                    clean_msg = clean_msg[0].upper() + clean_msg[1:]
                categories[cat].append(clean_msg or msg)
                matched = True
                break

        if not matched:
            # Fallback heuristic
            lower = msg.lower()
            if any(k in lower for k in ("fix", "bug", "patch")):
                categories["Fixed"].append(msg)
            elif any(k in lower for k in ("add", "new", "feat")):
                categories["Added"].append(msg)
            elif any(k in lower for k in ("remove", "delete", "drop")):
                categories["Removed"].append(msg)
            else:
                categories["Changed"].append(msg)

    return categories


def format_markdown(categories: dict[str, list[str]], tag_name: str | None = None, date_str: str | None = None) -> str:
    date_formatted = date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    version_title = f"[{tag_name or 'Unreleased'}] - {date_formatted}"

    lines = [f"## {version_title}\n"]

    section_order = ["Added", "Changed", "Fixed", "Removed"]
    has_entries = False

    for section in section_order:
        entries = categories.get(section, [])
        if entries:
            has_entries = True
            lines.append(f"### {section}")
            for item in entries:
                lines.append(f"- {item}")
            lines.append("")

    if not has_entries:
        lines.append("- No significant changes recorded.\n")

    return "\n".join(lines).strip() + "\n"


def generate_changelog(output_path: str = "CHANGELOG.md", custom_tag: str | None = None, dry_run: bool = False) -> str:
    latest_tag = custom_tag or get_latest_tag()
    commits = get_git_commits(latest_tag)
    categories = categorize_commits(commits)
    new_section = format_markdown(categories, latest_tag)

    if dry_run:
        return new_section

    target_file = Path(output_path)
    existing_content = ""
    header = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n"

    if target_file.exists():
        existing_content = target_file.read_text(encoding="utf-8")
        if existing_content.startswith("# Changelog"):
            # Strip header to prepend new release section
            body = re.sub(r"^#\s+Changelog\s*\n+(?:[^\n]+\n+)*", "", existing_content, count=1)
            full_content = f"{header}{new_section}\n{body.strip()}\n"
        else:
            full_content = f"{header}{new_section}\n{existing_content.strip()}\n"
    else:
        full_content = f"{header}{new_section}"

    target_file.write_text(full_content, encoding="utf-8")
    return new_section


def main():
    parser = argparse.ArgumentParser(description="Generate structured CHANGELOG from git history.")
    parser.add_argument("-o", "--output", default="CHANGELOG.md", help="Output file path (default: CHANGELOG.md)")
    parser.add_argument("-t", "--tag", default=None, help="Specific git tag to start diff from")
    parser.add_argument("--dry-run", action="store_true", help="Print changelog markdown to stdout without writing")

    args = parser.parse_args()
    section = generate_changelog(output_path=args.output, custom_tag=args.tag, dry_run=args.dry_run)

    if args.dry_run:
        sys.stdout.write(section)
    else:
        sys.stdout.write(f"Updated {args.output} successfully.\n")


if __name__ == "__main__":
    main()
