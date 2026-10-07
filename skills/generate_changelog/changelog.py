#!/usr/bin/env python3
"""Git CHANGELOG Generator.

Fetches commits since the last git tag (or initial commit) and categorizes
them into Added, Fixed, Changed, and Removed sections based on Conventional Commits.
"""

from pathlib import Path
import re
import subprocess
import sys


def get_last_tag(repo_path: Path) -> str | None:
    """Get the latest git tag name, or None if no tags exist."""
    res = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if res.returncode == 0:
        return res.stdout.strip()
    return None


def get_git_commits(repo_path: Path, since_tag: str | None = None) -> list[str]:
    """Fetch git commit subject lines since the given tag or all commits."""
    if since_tag:
        cmd = ["git", "log", f"{since_tag}..HEAD", "--oneline", "--no-merges", "--pretty=format:%s"]
    else:
        cmd = ["git", "log", "--oneline", "--no-merges", "--pretty=format:%s"]

    res = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
    if res.returncode != 0 or not res.stdout.strip():
        return []
    return [line.strip() for line in res.stdout.strip().splitlines() if line.strip()]


def categorize_commit(commit_msg: str) -> tuple[str, str]:
    """Categorize commit message into (Category, FormattedMessage)."""
    # Clean up commit hash if present
    msg = re.sub(r"^[0-9a-f]{7,40}\s+", "", commit_msg)

    lowered = msg.lower()

    if re.match(r"^(feat|add|added|feature)(\([^)]+\))?:", lowered) or "add " in lowered or "feat:" in lowered:
        category = "Added"
    elif re.match(r"^(fix|fixed|bugfix)(\([^)]+\))?:", lowered) or "fix" in lowered or "bug" in lowered:
        category = "Fixed"
    elif re.match(r"^(remove|removed|delete|deleted)(\([^)]+\))?:", lowered) or "remove" in lowered or "deprecate" in lowered:
        category = "Removed"
    else:
        category = "Changed"

    # Format commit text cleanly
    cleaned = re.sub(r"^(feat|fix|docs|style|refactor|test|chore|perf|build|ci|revert)(\([^)]+\))?:\s*", "", msg, flags=re.IGNORECASE)
    cleaned = cleaned[0].upper() + cleaned[1:] if cleaned else msg
    return category, cleaned


def generate_changelog_markdown(commits: list[str], tag: str | None = None) -> str:
    """Generate Markdown formatted CHANGELOG content."""
    categories: dict[str, list[str]] = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
    }

    for commit in commits:
        cat, msg = categorize_commit(commit)
        categories[cat].append(msg)

    lines = ["# CHANGELOG", ""]
    scope = f"since tag `{tag}`" if tag else "from full git history"
    lines.append(f"Auto-generated structured changelog {scope}.")
    lines.append("")

    for cat in ["Added", "Fixed", "Changed", "Removed"]:
        items = categories[cat]
        if items:
            lines.append(f"## {cat}")
            for item in items:
                lines.append(f"- {item}")
            lines.append("")

    return "\n".join(lines).strip() + "\n"


def main():
    repo_path = Path.cwd()
    if len(sys.argv) > 1:
        repo_path = Path(sys.argv[1]).resolve()

    tag = get_last_tag(repo_path)
    commits = get_git_commits(repo_path, since_tag=tag)

    if not commits:
        sys.stderr.write("No commits found to generate CHANGELOG.\n")
        sys.exit(1)

    changelog_content = generate_changelog_markdown(commits, tag=tag)

    output_path = repo_path / "CHANGELOG.md"
    output_path.write_text(changelog_content, encoding="utf-8")
    print(f"Successfully generated CHANGELOG.md ({len(commits)} commits processed).")


if __name__ == "__main__":
    main()
