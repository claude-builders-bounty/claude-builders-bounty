"""CLI entry point for claude-review."""

import argparse
import json
import os
import sys

# ANSI color codes
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"

    @classmethod
    def disable(cls):
        for attr in ["RESET", "BOLD", "DIM", "RED", "GREEN", "YELLOW", "BLUE", "MAGENTA", "CYAN"]:
            setattr(cls, attr, "")


def colorize_markdown(text: str) -> str:
    """Add terminal colors to markdown review output."""
    lines = text.split("\n")
    result = []
    for line in lines:
        if line.startswith("### "):
            result.append(f"\n{Colors.BOLD}{Colors.CYAN}{line}{Colors.RESET}")
        elif line.startswith("## "):
            result.append(f"\n{Colors.BOLD}{Colors.MAGENTA}{line}{Colors.RESET}")
        elif line.startswith("# "):
            result.append(f"\n{Colors.BOLD}{Colors.BLUE}{line}{Colors.RESET}")
        elif line.strip().startswith("- ") or line.strip().startswith("* "):
            if any(kw in line.lower() for kw in ["risk", "bug", "vuln", "error", "issue", "⚠"]):
                result.append(f"  {Colors.YELLOW}{line.strip()}{Colors.RESET}")
            elif any(kw in line.lower() for kw in ["suggest", "improve", "consider", "💡"]):
                result.append(f"  {Colors.GREEN}{line.strip()}{Colors.RESET}")
            else:
                result.append(f"  {Colors.DIM}{line.strip()}{Colors.RESET}")
        elif "**high**" in line.lower():
            result.append(f"{Colors.GREEN}{line}{Colors.RESET}")
        elif "**medium**" in line.lower():
            result.append(f"{Colors.YELLOW}{line}{Colors.RESET}")
        elif "**low**" in line.lower():
            result.append(f"{Colors.RED}{line}{Colors.RESET}")
        else:
            result.append(line)
    return "\n".join(result)


def print_header(pr_url: str):
    """Print a styled header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}╔══════════════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}║  🤖 Claude PR Review Agent                              ║{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}╚══════════════════════════════════════════════════════════╝{Colors.RESET}")
    print(f"\n{Colors.DIM}Reviewing: {pr_url}{Colors.RESET}\n")


def main():
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="🤖 AI-powered Pull Request Reviewer using Claude",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --pr owner/repo#123 --focus security
  claude-review --pr https://github.com/o/r/pull/1 --format json --output review.json
  claude-review --pr https://github.com/o/r/pull/1 --verbose
        """,
    )
    parser.add_argument(
        "--pr",
        required=True,
        help="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123) or shorthand (owner/repo#123)",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--output", "-o",
        help="Save output to file instead of stdout",
    )
    parser.add_argument(
        "--focus",
        choices=["security", "performance", "style", "bugs", "architecture"],
        help="Focus the review on a specific aspect",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-20250514",
        help="Claude model to use (default: claude-sonnet-4-20250514)",
    )
    parser.add_argument(
        "--github-token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub token for private repos (default: $GITHUB_TOKEN)",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("ANTHROPIC_API_KEY"),
        help="Anthropic API key (default: $ANTHROPIC_API_KEY)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed analysis process",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
    )

    args = parser.parse_args()

    # Disable colors if requested or not a TTY
    if args.no_color or not sys.stdout.isatty() or args.output:
        Colors.disable()

    # Validate API key
    if not args.api_key:
        print(f"{Colors.RED}Error: ANTHROPIC_API_KEY not set.{Colors.RESET}", file=sys.stderr)
        print("Set it via: export ANTHROPIC_API_KEY=sk-ant-...", file=sys.stderr)
        print("Or pass: --api-key sk-ant-...", file=sys.stderr)
        sys.exit(1)

    # Import here to avoid slow startup for --help
    from .github_client import GitHubClient, parse_pr_url
    from .reviewer import Reviewer

    # Parse PR URL
    try:
        owner, repo, number = parse_pr_url(args.pr)
    except ValueError as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}", file=sys.stderr)
        sys.exit(1)

    if not args.output:
        print_header(args.pr)

    # Fetch PR data
    if args.verbose or not args.output:
        print(f"{Colors.CYAN}📡 Fetching PR data from GitHub...{Colors.RESET}", file=sys.stderr)

    gh = GitHubClient(token=args.github_token)
    try:
        pr = gh.get_pr_info(owner, repo, number)
    except Exception as e:
        print(f"{Colors.RED}Error fetching PR: {e}{Colors.RESET}", file=sys.stderr)
        sys.exit(1)

    if args.verbose or not args.output:
        print(f"{Colors.GREEN}✓ Fetched: \"{pr.title}\" by @{pr.author}{Colors.RESET}", file=sys.stderr)
        print(f"  {Colors.DIM}{pr.changed_files} files, +{pr.additions}/-{pr.deletions}{Colors.RESET}", file=sys.stderr)

    # Generate review
    if args.verbose or not args.output:
        focus_str = f" (focus: {args.focus})" if args.focus else ""
        print(f"\n{Colors.CYAN}🧠 Analyzing with Claude{focus_str}...{Colors.RESET}", file=sys.stderr)

    reviewer = Reviewer(api_key=args.api_key, model=args.model)
    try:
        review_md = reviewer.review(pr, focus=args.focus, verbose=args.verbose)
    except Exception as e:
        print(f"{Colors.RED}Error generating review: {e}{Colors.RESET}", file=sys.stderr)
        sys.exit(1)

    # Format output
    if args.format == "json":
        review_json = reviewer.review_to_json(pr, review_md)
        output = json.dumps(review_json, indent=2, ensure_ascii=False)
    else:
        # Wrap with PR header
        header = f"# 🤖 Claude Review: {pr.title}\n\n"
        header += f"> **PR**: [{pr.owner}/{pr.repo}#{pr.number}]({pr.url or args.pr})  \n"
        header += f"> **Author**: @{pr.author}  \n"
        header += f"> **Branch**: `{pr.head_branch}` → `{pr.base_branch}`  \n"
        header += f"> **Stats**: +{pr.additions} / -{pr.deletions} across {pr.changed_files} file(s)  \n\n"
        header += "---\n\n"
        output = header + review_md

    # Output
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"{Colors.GREEN}✅ Review saved to: {args.output}{Colors.RESET}", file=sys.stderr)
    else:
        if args.format == "markdown" and sys.stdout.isatty():
            print(colorize_markdown(output))
        else:
            print(output)
        print(f"\n{Colors.DIM}{'─'*60}{Colors.RESET}", file=sys.stderr)
        print(f"{Colors.GREEN}✅ Review complete.{Colors.RESET}", file=sys.stderr)


if __name__ == "__main__":
    main()
