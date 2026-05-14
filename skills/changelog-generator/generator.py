# -*- coding: utf-8 -*-
"""
Git Changelog Generator Skill for Claude Code.
Generates a professional CHANGELOG.md from git history.
"""

import subprocess
import re
import sys
import argparse
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Optional

# --- Configuration ---

TYPES = {
    "feat": "🚀 Features",
    "fix": "🐛 Bug Fixes",
    "docs": "📚 Documentation",
    "style": "💎 Style",
    "refactor": "🔨 Refactor",
    "perf": "⚡ Performance",
    "test": "🚨 Tests",
    "build": "🛠️ Build",
    "ci": "⚙️ CI",
    "chore": "🧹 Chore",
    "revert": "⏪ Reverts",
}

COMMIT_PATTERN = re.compile(r"^(\w+)(?:\(([\w\-. ]+)\))?(!?): (.+)$")

class ChangelogGenerator:
    """Generates CHANGELOG.md from git history using Conventional Commits."""

    def __init__(self, since: Optional[str] = None, until: str = "HEAD", version: Optional[str] = None):
        self.since = since
        self.until = until
        self.version = version
        self.commits = defaultdict(list)

    def _get_commits(self) -> List[str]:
        """Fetch commit messages from git."""
        revision_range = f"{self.since}..{self.until}" if self.since else self.until
        cmd = ["git", "log", revision_range, "--pretty=format:%s"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding="utf-8")
            return result.stdout.splitlines()
        except subprocess.CalledProcessError as e:
            print(f"Error fetching git logs: {e.stderr}")
            return []

    def parse_commits(self):
        """Parse commit messages into categories."""
        raw_commits = self._get_commits()

        for msg in raw_commits:
            match = COMMIT_PATTERN.match(msg)
            if match:
                ctype, scope, breaking, subject = match.groups()
                category = TYPES.get(ctype, "Other")

                if breaking == "!":
                    category = "⚠️ BREAKING CHANGES"

                scope_prefix = f"**{scope}**: " if scope else ""
                self.commits[category].append(f"{scope_prefix}{subject}")
            else:
                self.commits["Other"].append(msg)

    def generate_markdown(self) -> str:
        """Generate the markdown content."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        version_header = f"## [{self.version}] - {date_str}" if self.version else f"## [Unreleased] - {date_str}"

        lines = [version_header, ""]

        # Sort categories to keep them consistent
        sorted_categories = sorted(self.commits.keys(), key=lambda x: (x == "Other", x))

        for category in sorted_categories:
            if not self.commits[category]:
                continue

            lines.append(f"### {category}")
            for entry in self.commits[category]:
                lines.append(f"- {entry}")
            lines.append("")

        return "\n".join(lines)

def main():
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    parser = argparse.ArgumentParser(description="Generate a CHANGELOG.md from git history.")
    parser.add_argument("--since", help="Start revision (tag, branch, or commit hash)")
    parser.add_argument("--until", default="HEAD", help="End revision (default: HEAD)")
    parser.add_argument("--version", help="Version name for this release")
    parser.add_argument("--output", help="Output file (default: stdout)")

    args = parser.parse_args()

    generator = ChangelogGenerator(since=args.since, until=args.until, version=args.version)
    generator.parse_commits()
    changelog = generator.generate_markdown()

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(changelog)
        print(f"Changelog written to {args.output}")
    else:
        print(changelog)

if __name__ == "__main__":
    main()
