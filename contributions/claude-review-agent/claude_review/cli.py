"""CLI entry point for claude-review."""

import sys

import click

from .formatter import format_github_comment, format_markdown
from .github_client import GitHubClient, parse_pr_url
from .reviewer import Reviewer


@click.command()
@click.argument("pr_url", metavar="PR_URL")
@click.option(
    "--model",
    default="claude-sonnet-4-20250514",
    help="Claude model to use for review.",
    show_default=True,
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["full", "comment"]),
    default="full",
    help="Output format: 'full' for detailed Markdown, 'comment' for compact GitHub comment.",
    show_default=True,
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default=None,
    help="Save output to file instead of stdout.",
)
@click.option(
    "--post-comment",
    is_flag=True,
    default=False,
    help="Post the review as a comment on the PR (requires GITHUB_TOKEN with write access).",
)
@click.version_option(package_name="claude-review")
def main(pr_url: str, model: str, output_format: str, output: str, post_comment: bool):
    """Review a GitHub pull request using Claude AI.

    PR_URL: GitHub PR URL (https://github.com/owner/repo/pull/123) or short form (owner/repo#123)

    Examples:

        claude-review https://github.com/facebook/react/pull/28000

        claude-review owner/repo#42 --format comment

        claude-review https://github.com/org/repo/pull/1 --post-comment
    """
    try:
        owner, repo, number = parse_pr_url(pr_url)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    click.echo(f"🔍 Fetching PR #{number} from {owner}/{repo}...", err=True)

    try:
        gh = GitHubClient()
        pr = gh.fetch_pr(owner, repo, number)
    except Exception as e:
        click.echo(f"Error fetching PR: {e}", err=True)
        sys.exit(1)

    click.echo(f"📝 Reviewing: {pr.title} ({pr.files_changed} files, +{pr.additions}/-{pr.deletions})", err=True)
    click.echo(f"🤖 Using model: {model}", err=True)

    try:
        reviewer = Reviewer(model=model)
        result = reviewer.review(pr)
    except Exception as e:
        click.echo(f"Error during review: {e}", err=True)
        sys.exit(1)

    # Format output
    if output_format == "comment":
        formatted = format_github_comment(pr, result)
    else:
        formatted = format_markdown(pr, result)

    # Output
    if output:
        with open(output, "w") as f:
            f.write(formatted)
        click.echo(f"✅ Review saved to {output}", err=True)
    else:
        click.echo(formatted)

    # Post as comment if requested
    if post_comment:
        _post_comment(gh, owner, repo, number, format_github_comment(pr, result))

    click.echo(f"✅ Done! Confidence: {result.confidence}", err=True)


def _post_comment(gh: GitHubClient, owner: str, repo: str, number: int, body: str):
    """Post review as a PR comment."""
    if not gh.token:
        click.echo("⚠️  Cannot post comment: GITHUB_TOKEN not set.", err=True)
        return

    url = f"{gh.API_BASE}/repos/{owner}/{repo}/issues/{number}/comments"
    resp = gh.session.post(url, json={"body": body})
    if resp.status_code == 201:
        click.echo("💬 Comment posted successfully!", err=True)
    else:
        click.echo(f"⚠️  Failed to post comment: {resp.status_code} {resp.text}", err=True)


if __name__ == "__main__":
    main()
