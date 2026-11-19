#!/usr/bin/env python3
"""
Generate a structured CHANGELOG from git history.
Works standalone or as the engine behind Claude Code skill.
"""

import os
import re
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple


CATEGORY_ORDER = ["Added", "Fixed", "Changed", "Removed"]

# Rules for mapping commit message types/prefixes to categories
CATEGORY_KEYWORDS = {
    "Added": [
        "feat",
        "feature",
        "add",
        "added",
        "create",
        "new",
        "support",
        "include",
    ],
    "Fixed": [
        "fix",
        "fixed",
        "bug",
        "hotfix",
        "patch",
        "repair",
        "correct",
        "resolve",
        "resolved",
    ],
    "Changed": [
        "change",
        "changed",
        "refactor",
        "perf",
        "update",
        "updated",
        "improve",
        "docs",
        "style",
        "chore",
        "build",
        "ci",
        "bump",
    ],
    "Removed": [
        "remove",
        "removed",
        "delete",
        "drop",
        "deprecate",
        "clean",
    ],
}


def run_git_command(args: List[str], cwd: Optional[str] = None) -> Tuple[int, str]:
    try:
        res = subprocess.run(
            ["git"] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            cwd=cwd,
        )
        return res.returncode, res.stdout.strip()
    except Exception as e:
        return 1, str(e)


def get_latest_tag(cwd: Optional[str] = None) -> Optional[str]:
    code, out = run_git_command(["describe", "--tags", "--abbrev=0"], cwd=cwd)
    if code == 0 and out:
        return out
    return None


def get_commits_since_tag(tag: Optional[str] = None, cwd: Optional[str] = None) -> List[Tuple[str, str, str]]:
    """
    Returns list of (short_hash, subject, author).
    """
    if tag:
        rev_range = f"{tag}..HEAD"
    else:
        rev_range = "HEAD"

    code, out = run_git_command(
        ["log", rev_range, "--no-merges", "--pretty=format:%h|%s|%an"],
        cwd=cwd,
    )
    if code != 0 or not out:
        return []

    commits = []
    for line in out.splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3:
            commits.append((parts[0].strip(), parts[1].strip(), parts[2].strip()))
    return commits


def categorize_commit(subject: str) -> str:
    """
    Categorizes commit into Added, Fixed, Changed, or Removed.
    Supports Conventional Commits (feat, fix, refactor, chore, docs, perf, etc.)
    and standard imperative prefixes (Add, Fix, Update, Remove...).
    """
    s = subject.strip()

    # 1. Check conventional commit prefix: `type(scope): description` or `type: description`
    conv_match = re.match(r"^([a-zA-Z0-9_\-]+)(?:\([^)]+\))?!?:", s)
    if conv_match:
        tag_type = conv_match.group(1).lower()
        if tag_type in ["feat", "feature"]:
            return "Added"
        elif tag_type in ["fix", "bugfix", "hotfix"]:
            return "Fixed"
        elif tag_type in ["remove", "revert"]:
            return "Removed"
        elif tag_type in ["chore", "docs", "perf", "refactor", "style", "test", "build", "ci"]:
            return "Changed"

    # 2. Check imperative starting verb: "Add ...", "Fix ...", "Remove ...", "Update ..."
    first_word_match = re.match(r"^([a-zA-Z]+)", s)
    if first_word_match:
        first_word = first_word_match.group(1).lower()
        for cat, keywords in CATEGORY_KEYWORDS.items():
            if first_word in keywords:
                return cat

    # 3. Fallback scan inside subject
    s_lower = s.lower()
    for cat in ["Fixed", "Removed", "Added", "Changed"]:
        for kw in CATEGORY_KEYWORDS[cat]:
            if re.search(r"\b" + re.escape(kw) + r"\b", s_lower):
                return cat

    return "Changed"


def clean_commit_message(subject: str) -> str:
    """
    Normalizes commit subject by removing conventional commit prefix if redundant,
    or capitalizing first letter nicely.
    """
    s = re.sub(r"^[a-zA-Z0-9_\-]+(?:\([^)]+\))?!?:[ ]*", "", subject).strip()
    if not s:
        s = subject
    if len(s) > 1:
        s = s[0].upper() + s[1:]
    return s


def build_changelog_section(
    version_title: str,
    date_str: str,
    commits: List[Tuple[str, str, str]],
) -> str:
    categorized: Dict[str, List[Tuple[str, str, str]]] = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
    }

    for short_hash, subject, author in commits:
        cat = categorize_commit(subject)
        cleaned = clean_commit_message(subject)
        categorized[cat].append((short_hash, cleaned, author))

    lines = [f"## [{version_title}] - {date_str}"]

    has_entries = False
    for cat in CATEGORY_ORDER:
        entries = categorized[cat]
        if entries:
            has_entries = True
            lines.append(f"\n### {cat}")
            for short_hash, cleaned, author in entries:
                lines.append(f"- {cleaned} ([`{short_hash}`])")

    if not has_entries:
        lines.append("\n_No notable changes._")

    return "\n".join(lines)


def generate_changelog(
    repo_path: Optional[str] = None,
    output_path: Optional[str] = None,
    next_version: Optional[str] = None,
) -> str:
    cwd = repo_path or os.getcwd()
    latest_tag = get_latest_tag(cwd=cwd)
    commits = get_commits_since_tag(latest_tag, cwd=cwd)

    today = datetime.now().strftime("%Y-%m-%d")
    version_label = next_version if next_version else ("Unreleased" if latest_tag else "Initial Release")

    new_section = build_changelog_section(version_label, today, commits)

    target_file = output_path or os.path.join(cwd, "CHANGELOG.md")
    
    header = (
        "# Changelog\n\n"
        "All notable changes to this project will be documented in this file.\n\n"
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).\n\n"
    )

    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            existing = f.read()

        # Insert after header if header exists, otherwise prepend
        if "# Changelog" in existing:
            prefix, remainder = existing.split("# Changelog", 1)
            # Find the first version heading `## [`
            split_pos = remainder.find("\n## [")
            if split_pos != -1:
                content = (
                    "# Changelog"
                    + remainder[:split_pos]
                    + "\n\n"
                    + new_section
                    + remainder[split_pos:]
                )
            else:
                content = existing.rstrip() + "\n\n" + new_section + "\n"
        else:
            content = header + new_section + "\n\n" + existing
    else:
        content = header + new_section + "\n"

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(content)

    return content


if __name__ == "__main__":
    repo_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    out_file = sys.argv[2] if len(sys.argv) > 2 else "CHANGELOG.md"
    print(f"Generating changelog for repository at '{repo_dir}' -> {out_file}...")
    res = generate_changelog(repo_path=repo_dir, output_path=out_file)
    print("Done! CHANGELOG generated successfully.")
