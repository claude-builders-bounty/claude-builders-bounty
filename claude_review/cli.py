"""CLI entry point for claude-review."""

import click
import os
from .reviewer import review_pr
from . import __version__

@click.command()
@click.option("--pr", required=True, help="GitHub PR URL")
@click.option("--token", default=None, help="GitHub token")
@click.option("--model", default="gemma4:e4b", help="LLM model")
@click.option("--output", "-o", default=None, help="Write output to file")
@click.version_option(version=__version__)
def main(pr, token, model, output):
    """Review a GitHub PR and output structured Markdown."""
    token = token or os.environ.get("GITHUB_TOKEN", "")
    result = review_pr(pr, token=token, model=model)
    if output:
        with open(output, "w") as f:
            f.write(result)
        click.echo(f"Review written to {output}")
    else:
        click.echo(result)

if __name__ == "__main__":
    main()
