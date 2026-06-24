#!/usr/bin/env python3
"""
claude-pr-review — Claude Code sub-agent CLI wrapper

Reviews a GitHub PR and posts a structured comment using the Anthropic API.

Usage:
    python claude_review.py <PR_NUMBER> [--repo owner/repo] [--post] [--output FILE]

Examples:
    python claude_review.py 42
    python claude_review.py 42 --post
    python claude_review.py 42 --repo myorg/myrepo --post
    python claude_review.py 42 --output review.md
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("Error: anthropic package not installed. Run: pip install anthropic", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# GitHub helpers (require `gh` CLI to be authenticated)
# ---------------------------------------------------------------------------

def run_gh(args: list[str]) -> str:
    """Run a gh CLI command and return stdout."""
    result = subprocess.run(
        ["gh"] + args,
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh command failed: {result.stderr.strip()}")
    return result.stdout.strip()


def get_pr_metadata(pr_number: int, repo: str | None) -> dict:
    """Fetch PR title, author, stats, URL."""
    repo_args = ["--repo", repo] if repo else []
    raw = run_gh([
        "pr", "view", str(pr_number),
        "--json", "title,body,author,baseRefName,headRefName,additions,deletions,changedFiles,url,isDraft,state",
    ] + repo_args)
    return json.loads(raw)


def get_pr_diff(pr_number: int, repo: str | None) -> str:
    """Fetch the full unified diff for a PR."""
    repo_args = ["--repo", repo] if repo else []
    return run_gh(["pr", "diff", str(pr_number)] + repo_args)


def get_existing_comments(pr_number: int, repo: str | None) -> list[str]:
    """Return body text of all existing PR comments."""
    repo_args = ["--repo", repo] if repo else []
    raw = run_gh([
        "pr", "view", str(pr_number),
        "--json", "comments",
        "--jq", ".comments[].body",
    ] + repo_args)
    return [line for line in raw.splitlines() if line.strip()]


def post_comment(pr_number: int, body: str, repo: str | None) -> None:
    """Post a comment to the PR."""
    repo_args = ["--repo", repo] if repo else []
    run_gh(["pr", "comment", str(pr_number), "--body", body] + repo_args)


# ---------------------------------------------------------------------------
# Review generation via Claude API
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a thorough, constructive GitHub PR reviewer.
You receive a PR diff and metadata, and you produce a structured Markdown review comment.

Your review must use this exact template — fill in every section:

## 🤖 Automated PR Review

> Reviewed by pr-reviewer · PR #{number} · {title}

---

### Summary

<2–3 sentences: overall assessment. Mention what's done well, then the issues.>

**Verdict:** <✅ Approve / ⚠️ Approve with suggestions / 🚫 Request changes>

---

### Issues

<If no issues: "No issues found — the changes look clean.">

<For each issue:>
#### <emoji> [Severity] — [Short title]

**File:** `path/to/file.ext` (line N)  
**Problem:** <what the issue is and why it matters>  
**Suggested fix:**
```
<concrete fix>
```

Severity emojis: 🔴 Critical · 🟠 High · 🟡 Medium · 🔵 Low · 💡 Suggestion

---

### Checklist

| | Item |
|---|---|
| <✅ or ❌> | New code has corresponding tests |
| <✅ or ❌> | Error cases are handled |
| <✅ or ❌> | No secrets or credentials in code |
| <✅ or ❌> | Changes are backward-compatible |
| <✅ or ❌> | Commit messages are clear |

---

<details>
<summary>Stats</summary>

- Files changed: {changed_files}
- Additions: +{additions} / Deletions: -{deletions}
- Findings: <N critical, N high, N medium, N low, N suggestions>

</details>

Rules:
- Always include file + line number for each finding
- Be specific and suggest concrete fixes
- Do NOT invent issues that aren't in the diff
- Keep total length reasonable — prioritise Critical/High findings if space is tight
"""


def generate_review(metadata: dict, diff: str, existing_comments: list[str]) -> str:
    """Call the Anthropic API to generate the review comment."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable not set")

    client = anthropic.Anthropic(api_key=api_key)

    # Build context for the model
    existing_note = ""
    if existing_comments:
        existing_note = (
            "\n\nExisting review comments (do not repeat these findings):\n"
            + "\n---\n".join(existing_comments[:3])  # limit context
        )

    user_message = (
        f"PR #{metadata['number'] if 'number' in metadata else '?'}: {metadata['title']}\n"
        f"Author: {metadata['author']['login']}\n"
        f"Base: {metadata['baseRefName']} ← Head: {metadata['headRefName']}\n"
        f"Files changed: {metadata['changedFiles']} | "
        f"+{metadata['additions']} / -{metadata['deletions']}\n"
        f"\nPR description:\n{metadata.get('body', '(none)')}\n"
        f"{existing_note}\n"
        f"\n--- DIFF START ---\n{diff[:40000]}\n--- DIFF END ---"
        # cap diff at 40k chars to stay within context
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT.format(
            number=metadata.get("number", "?"),
            title=metadata["title"],
            changed_files=metadata["changedFiles"],
            additions=metadata["additions"],
            deletions=metadata["deletions"],
        ),
        messages=[{"role": "user", "content": user_message}],
    )

    return response.content[0].text


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Review a GitHub PR and optionally post a structured comment.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("pr_number", type=int, help="Pull request number to review")
    parser.add_argument("--repo", metavar="OWNER/REPO",
                        help="GitHub repository (default: auto-detected from git remote)")
    parser.add_argument("--post", action="store_true",
                        help="Post the review as a PR comment (requires gh CLI)")
    parser.add_argument("--output", metavar="FILE",
                        help="Save the review to a Markdown file")
    parser.add_argument("--no-existing", action="store_true",
                        help="Skip fetching existing comments")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print(f"🔍 Fetching PR #{args.pr_number}...", file=sys.stderr)

    try:
        metadata = get_pr_metadata(args.pr_number, args.repo)
    except RuntimeError as e:
        print(f"❌ Could not fetch PR metadata: {e}", file=sys.stderr)
        sys.exit(1)

    # Guard: don't review drafts
    if metadata.get("isDraft"):
        print("⚠️  PR is a draft — skipping review. Remove draft status first.", file=sys.stderr)
        sys.exit(0)

    # Guard: only review open PRs
    if metadata.get("state") != "OPEN":
        print(f"⚠️  PR is {metadata.get('state', 'unknown')} — only open PRs are reviewed.", file=sys.stderr)
        sys.exit(0)

    print(f"   Title: {metadata['title']}", file=sys.stderr)
    print(f"   Files: {metadata['changedFiles']} changed, "
          f"+{metadata['additions']}/-{metadata['deletions']}", file=sys.stderr)

    try:
        diff = get_pr_diff(args.pr_number, args.repo)
    except RuntimeError as e:
        print(f"❌ Could not fetch diff: {e}", file=sys.stderr)
        sys.exit(1)

    if not diff.strip():
        print("⚠️  Diff is empty — nothing to review.", file=sys.stderr)
        sys.exit(0)

    existing_comments: list[str] = []
    if not args.no_existing:
        try:
            existing_comments = get_existing_comments(args.pr_number, args.repo)
        except RuntimeError:
            pass  # non-fatal

    print("🤖 Generating review with Claude...", file=sys.stderr)

    try:
        review = generate_review(metadata, diff, existing_comments)
    except RuntimeError as e:
        print(f"❌ Review generation failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Output to stdout always
    print("\n" + "=" * 60)
    print(review)
    print("=" * 60 + "\n")

    # Optionally save to file
    if args.output:
        Path(args.output).write_text(review, encoding="utf-8")
        print(f"📄 Review saved to {args.output}", file=sys.stderr)

    # Optionally post to GitHub
    if args.post:
        print(f"📤 Posting comment to PR #{args.pr_number}...", file=sys.stderr)
        try:
            post_comment(args.pr_number, review, args.repo)
            print(f"✅ Review posted → {metadata['url']}", file=sys.stderr)
        except RuntimeError as e:
            print(f"❌ Failed to post comment: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(
            f"💡 Run with --post to publish this review to PR #{args.pr_number}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
