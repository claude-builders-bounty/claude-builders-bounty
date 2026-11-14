"""
Structured CHANGELOG Generator from Git History
Outputs standardized Keep a Changelog Markdown format from git commits or JSON commit dumps.
"""
import sys
import re
import json
from datetime import datetime
from typing import List, Dict, Any

def parse_commits(commit_lines: List[str]) -> Dict[str, List[str]]:
    categories = {"Added": [], "Changed": [], "Fixed": [], "Security": [], "Other": []}
    for line in commit_lines:
        line = line.strip()
        if not line:
            continue
        msg = re.sub(r'^[a-f0-9]{7,40}\s+', '', line)
        lower = msg.lower()
        if lower.startswith(("feat", "add", "new")):
            categories["Added"].append(msg)
        elif lower.startswith(("fix", "bug", "patch")):
            categories["Fixed"].append(msg)
        elif lower.startswith(("sec", "auth", "vuln")):
            categories["Security"].append(msg)
        elif lower.startswith(("refactor", "change", "update", "perf")):
            categories["Changed"].append(msg)
        else:
            categories["Other"].append(msg)
    return categories

def generate_markdown(version: str, categories: Dict[str, List[str]], release_date: str = None) -> str:
    if not release_date:
        release_date = datetime.now().strftime("%Y-%m-%d")
    md = [f"## [{version}] - {release_date}\\n"]
    for cat, items in categories.items():
        if items:
            md.append(f"### {cat}")
            for item in items:
                md.append(f"- {item}")
            md.append("")
    return "\\n".join(md).strip()

if __name__ == "__main__":
    sample = [
        "a1b2c3d feat: add automated bounty hunter pipeline",
        "d4e5f6g fix: resolve rate-limit header parsing in GitHub search",
        "h7i8j9k security: add sanitize check for PR titles"
    ]
    parsed = parse_commits(sample)
    print(generate_markdown("1.0.0", parsed))
