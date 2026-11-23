#!/usr/bin/env python3
"""
Claude Code Structured CHANGELOG Generator (`skills/generate-changelog/generate_changelog.py`)
Bounty Reference: claude-builders-bounty/claude-builders-bounty#1 ($50 Opire)
"""
from typing import List, Dict

def categorize_commits(commits: List[str]) -> Dict[str, List[str]]:
    cats = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}
    for c in commits:
        cl = c.lower()
        if cl.startswith(("feat", "add")) or " add " in cl:
            cats["Added"].append(c)
        elif cl.startswith(("fix", "bug")) or " fix" in cl:
            cats["Fixed"].append(c)
        elif cl.startswith(("remove", "del", "drop")) or " remove" in cl:
            cats["Removed"].append(c)
        else:
            cats["Changed"].append(c)
    return cats

def render_changelog(commits: List[str], since_tag: str = "initial") -> str:
    cats = categorize_commits(commits)
    lines = ["# Changelog", "", f"## [Unreleased] (since {since_tag})", ""]
    for section in ("Added", "Fixed", "Changed", "Removed"):
        if cats[section]:
            lines.append(f"### {section}")
            for item in cats[section]:
                lines.append(f"- {item}")
            lines.append("")
    return "\n".join(lines).strip() + "\n"

if __name__ == "__main__":
    sample_commits = [
        "feat(hook): Add pre-tool-use destructive bash command blocker (#3)",
        "fix(parser): Handle combined short flags in command evaluator",
        "refactor(cli): Streamline structured markdown output",
        "remove: Drop deprecated config file",
    ]
    md = render_changelog(sample_commits, since_tag="v1.0.0")
    assert "### Added" in md and "### Fixed" in md and "### Changed" in md and "### Removed" in md
    print("CHANGELOG_SKILL_TESTS_PASSED")
