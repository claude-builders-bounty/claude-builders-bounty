"""Format review output as Markdown and optionally post to GitHub."""

from datetime import datetime, timezone


def format_review(pr_data: dict, review_text: str) -> str:
    """Wrap review text with PR context header."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    header = (
        f"## Claude Code PR Review\n\n"
        f"**PR**: [{pr_data['title']}](https://github.com/{pr_data['owner']}"
        f"/{pr_data['repo']}/pull/{pr_data['number']})\n"
        f"**Author**: @{pr_data.get('author', 'unknown')} | "
        f"**Files**: {pr_data.get('files_changed', 0)} | "
        f"**+{pr_data.get('additions', 0)} -{pr_data.get('deletions', 0)}\n"
        f"**Reviewed**: {now}\n\n"
        f"---\n\n"
    )

    return header + review_text
