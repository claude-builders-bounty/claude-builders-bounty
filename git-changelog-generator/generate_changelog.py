#!/usr/bin/env python3
"""
Automated Git History to Structured CHANGELOG.md Generator
Author: Rushikesh Garad (github.com/rushikeshgarad2024-dev)
"""
import subprocess
import re
from datetime import datetime

def generate_changelog(output_file="CHANGELOG.md"):
    # Get git commits
    try:
        git_log = subprocess.check_output(
            ["git", "log", "--pretty=format:%h|||%s|||%an|||%ad", "--date=short"],
            universal_newlines=True
        ).strip().split('\n')
    except Exception as e:
        print(f"Error reading git log: {e}")
        return

    features = []
    fixes = []
    docs = []
    refactors = []
    others = []

    for line in git_log:
        if not line.strip(): continue
        parts = line.split("|||")
        if len(parts) < 4: continue
        hash_val, subject, author, date = parts

        if re.match(r'^feat(\(.*\))?:', subject, re.I):
            features.append(f"- **{subject}** ([`{hash_val}`]) - {author}")
        elif re.match(r'^fix(\(.*\))?:', subject, re.I):
            fixes.append(f"- **{subject}** ([`{hash_val}`]) - {author}")
        elif re.match(r'^docs(\(.*\))?:', subject, re.I):
            docs.append(f"- **{subject}** ([`{hash_val}`]) - {author}")
        elif re.match(r'^refactor(\(.*\))?:', subject, re.I):
            refactors.append(f"- **{subject}** ([`{hash_val}`]) - {author}")
        else:
            others.append(f"- {subject} ([`{hash_val}`]) - {author}")

    today = datetime.now().strftime("%Y-%m-%d")
    changelog_content = f"# Changelog 📋\n\nAll notable changes to this project will be documented in this file.\n\n## [Unreleased] - {today}\n\n"

    if features:
        changelog_content += "### 🚀 Features & Enhancements\n" + "\n".join(features) + "\n\n"
    if fixes:
        changelog_content += "### 🐛 Bug Fixes\n" + "\n".join(fixes) + "\n\n"
    if docs:
        changelog_content += "### 📚 Documentation\n" + "\n".join(docs) + "\n\n"
    if refactors:
        changelog_content += "### ⚡ Refactoring & Performance\n" + "\n".join(refactors) + "\n\n"
    if others:
        changelog_content += "### 🔧 Other Changes\n" + "\n".join(others) + "\n\n"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(changelog_content)
    print(f"Successfully generated structured {output_file}!")

if __name__ == "__main__":
    generate_changelog()
