#!/usr/bin/env python3
"""Generate a structured Markdown review from a GitHub PR diff."""

import json
import os
import re
import sys


def main():
    if len(sys.argv) < 5:
        print("Usage: review.py <diff_file> <pr_num> <pr_json> <pr_url>")
        sys.exit(1)

    diff_file = sys.argv[1]
    pr_num = sys.argv[2]
    pr_data_raw = sys.argv[3]
    pr_url = sys.argv[4]

    try:
        pr_data = json.loads(pr_data_raw)
    except json.JSONDecodeError:
        pr_data = {}

    pr_title = pr_data.get("title", "Untitled")
    pr_author = (
        pr_data.get("author", {}).get("login", "unknown")
        if isinstance(pr_data.get("author"), dict)
        else "unknown"
    )
    pr_additions = pr_data.get("additions", 0)
    pr_deletions = pr_data.get("deletions", 0)
    pr_files = pr_data.get("changedFiles", 0)

    with open(diff_file, "r", errors="replace") as f:
        diff_text = f.read()

    file_diffs = re.split(r"^diff --git ", diff_text, flags=re.MULTILINE)

    changed_file_list = []
    total_added = 0
    total_removed = 0
    risks = []
    improvements = []

    for fd in file_diffs[1:]:
        first_line = fd.split("\n")[0] if "\n" in fd else ""
        header_match = re.search(r"b/(.+)", first_line)
        filename = header_match.group(1) if header_match else "unknown"
        changed_file_list.append(filename)

        added = len(re.findall(r"^\+(?!\+)", fd, re.MULTILINE))
        removed = len(re.findall(r"^-(?!-)", fd, re.MULTILINE))
        total_added += added
        total_removed += removed

        lower_fn = filename.lower()

        if any(k in lower_fn for k in ["migration", "schema", ".sql"]):
            risks.append(
                f"- **{filename}**: Database schema/migration change — verify backward compatibility and rollback plan"
            )
        if any(
            k in lower_fn
            for k in ["auth", "password", "token", "session", "secret", "credential"]
        ):
            risks.append(
                f"- **{filename}**: Auth/security-related change — verify no credentials are exposed or hardcoded"
            )
        if any(k in lower_fn for k in ["config", "env", ".env"]):
            risks.append(
                f"- **{filename}**: Configuration change — verify no secrets committed"
            )
        if re.search(r"(TODO|FIXME|HACK|XXX)", fd):
            improvements.append(
                f"- **{filename}**: Contains TODO/FIXME markers — consider resolving before merge"
            )
        if re.search(r"console\.(log|debug|warn|error)\(", fd):
            improvements.append(
                f"- **{filename}**: Contains console.log statements — remove before production"
            )
        if re.search(r"catch\s*\(\s*\w*\s*\)\s*\{\s*\}", fd):
            risks.append(
                f"- **{filename}**: Empty catch block detected — errors may be silently swallowed"
            )
        if re.search(r":\s*any\b", fd):
            improvements.append(
                f"- **{filename}**: Uses `any` type — replace with specific type"
            )

    if total_added + total_removed > 500:
        risks.append(
            "- **Large PR**: This PR changes 500+ lines. Consider breaking into smaller PRs for easier review."
        )

    if total_added + total_removed < 100:
        confidence = "High"
    elif total_added + total_removed < 500:
        confidence = "Medium"
    else:
        confidence = "Low"

    print(f"# PR Review: #{pr_num}")
    print()
    print(f"**PR**: {pr_url}")
    print(f"**Title**: {pr_title}")
    print(f"**Author**: @{pr_author}")
    print(f"**Changes**: +{pr_additions} / -{pr_deletions} across {pr_files} file(s)")
    print()
    print("---")
    print()
    print("## Summary")
    print()
    if len(changed_file_list) <= 3:
        print(
            f"This PR modifies {len(changed_file_list)} file(s), authored by @{pr_author}."
        )
    else:
        print(
            f"This PR modifies {len(changed_file_list)} files across +{pr_additions} additions and -{pr_deletions} deletions, authored by @{pr_author}."
        )
    if changed_file_list:
        key_files = ", ".join(changed_file_list[:5])
        suffix = (
            f" and {len(changed_file_list) - 5} more."
            if len(changed_file_list) > 5
            else "."
        )
        print(f"Key files: {key_files}{suffix}")
    print()
    print("---")
    print()
    print("## Identified Risks")
    print()
    if risks:
        for r in risks:
            print(r)
    else:
        print("- No significant risks detected.")
    print()
    print("---")
    print()
    print("## Improvement Suggestions")
    print()
    if improvements:
        for i in improvements:
            print(i)
    else:
        print("- No specific improvements suggested.")
    print()
    print("---")
    print()
    print(f"## Confidence: {confidence}")
    print()
    if confidence == "Low":
        print(
            f"This PR is large ({total_added + total_removed} lines changed). Manual review is strongly recommended."
        )
    elif confidence == "Medium":
        print(
            "This PR is moderately sized. The automated review covers common patterns but may miss domain-specific issues."
        )
    else:
        print(
            "This PR is small and focused. The review is likely comprehensive for common issues."
        )


if __name__ == "__main__":
    main()
