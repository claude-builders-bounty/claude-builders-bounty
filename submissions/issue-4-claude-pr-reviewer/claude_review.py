#!/usr/bin/env python3
"""
claude-review — an AI pull-request reviewer powered by Claude.

Fetches a GitHub pull request's diff and asks Claude to produce a structured
Markdown review: a short summary, identified risks, improvement suggestions, and
a confidence score (Low / Medium / High).

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr owner/repo#123
    claude-review --pr https://github.com/owner/repo/pull/123 --post   # post as a PR comment via gh

Environment:
    ANTHROPIC_API_KEY   required — your Anthropic API key
    GITHUB_TOKEN        optional — raises GitHub API rate limits and reads private repos
    CLAUDE_REVIEW_MODEL optional — override the model (default: claude-opus-4-8)

Requires: pip install anthropic   (Python 3.8+; GitHub access uses the standard library)
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

DEFAULT_MODEL = os.environ.get("CLAUDE_REVIEW_MODEL", "claude-opus-4-8")
# Cap the diff we send so a giant PR can't blow the context window or the bill.
MAX_DIFF_CHARS = 120_000

SYSTEM_PROMPT = """\
You are a meticulous senior software engineer performing a pull-request review.
You are given a PR's title, description, and unified diff. Review only what the
diff changes — do not invent files or lines that are not present.

Respond with GitHub-flavored Markdown in EXACTLY this structure, and nothing else:

## Summary
A 2-3 sentence plain-language summary of what this PR changes.

## Identified risks
A bullet list of concrete risks: bugs, security issues, breaking changes, race
conditions, missing error handling, performance regressions. Reference file paths
and, where possible, the relevant lines/hunks. If you find none, write
"- No significant risks identified."

## Improvement suggestions
A bullet list of actionable suggestions (readability, tests, edge cases, naming,
simplification). If you have none, write "- No suggestions."

## Confidence score
One of: **Low**, **Medium**, or **High** — your confidence that this PR is safe
to merge as-is — followed by one sentence explaining the rating.

Be specific and terse. Prioritise correctness and security issues over style.\
"""


def parse_pr(ref):
    """Accept a full PR URL or 'owner/repo#123' and return (owner, repo, number)."""
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", ref.strip())
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    m = re.match(r"([^/]+)/([^/#]+)#(\d+)", ref.strip())
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    raise ValueError(
        f"Could not parse PR reference: {ref!r}\n"
        "Expected e.g. https://github.com/owner/repo/pull/123 or owner/repo#123"
    )


def _github_get(url, accept):
    req = urllib.request.Request(url, headers={
        "Accept": accept,
        "User-Agent": "claude-review",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        hint = ""
        if e.code in (401, 403):
            hint = " (set GITHUB_TOKEN to raise rate limits / access private repos)"
        elif e.code == 404:
            hint = " (check the PR exists and, for private repos, that GITHUB_TOKEN can read it)"
        raise SystemExit(f"GitHub API error {e.code} for {url}{hint}\n{detail}")


def fetch_pr(owner, repo, number):
    """Return (metadata dict, unified diff string, truncated bool)."""
    base = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    meta = json.loads(_github_get(base, "application/vnd.github+json"))
    diff = _github_get(base, "application/vnd.github.v3.diff")
    truncated = False
    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS]
        truncated = True
    return meta, diff, truncated


def build_prompt(meta, diff, truncated):
    title = meta.get("title") or "(no title)"
    body = (meta.get("body") or "").strip() or "(no description provided)"
    parts = [
        f"# PR #{meta.get('number')}: {title}",
        f"Author: {meta.get('user', {}).get('login', 'unknown')}  |  "
        f"Base: {meta.get('base', {}).get('ref')} ← Head: {meta.get('head', {}).get('ref')}  |  "
        f"+{meta.get('additions', '?')}/-{meta.get('deletions', '?')} across "
        f"{meta.get('changed_files', '?')} files",
        "",
        "## PR description",
        body,
        "",
        "## Unified diff",
    ]
    if truncated:
        parts.append(
            f"_(NOTE: diff truncated to the first {MAX_DIFF_CHARS:,} characters — "
            "review the portion shown and note that later hunks were not included.)_"
        )
    parts += ["```diff", diff, "```"]
    return "\n".join(parts)


def review(prompt, model):
    try:
        import anthropic
    except ImportError:
        raise SystemExit("The 'anthropic' package is required. Install it with:\n  pip install anthropic")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY is not set. Export it (do not hard-code it).")

    client = anthropic.Anthropic()
    # Stream so a large review can't hit an HTTP timeout; adaptive thinking lets
    # Claude reason as deeply as the diff warrants.
    with client.messages.stream(
        model=model,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        message = stream.get_final_message()

    if message.stop_reason == "refusal":
        raise SystemExit("Claude declined to review this diff (safety refusal).")

    text = "".join(b.text for b in message.content if b.type == "text").strip()
    usage = message.usage
    return text, usage


def post_comment(owner, repo, number, body):
    """Post the review as a PR comment via the gh CLI."""
    try:
        subprocess.run(
            ["gh", "pr", "comment", str(number), "--repo", f"{owner}/{repo}", "--body", body],
            check=True,
        )
    except FileNotFoundError:
        raise SystemExit("--post requires the GitHub CLI (gh). Install it or drop --post.")
    except subprocess.CalledProcessError as e:
        raise SystemExit(f"gh pr comment failed (exit {e.returncode}).")


def main():
    ap = argparse.ArgumentParser(
        description="AI pull-request reviewer powered by Claude.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--pr", required=True,
                    help="PR URL (https://github.com/owner/repo/pull/123) or owner/repo#123")
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"model to use (default: {DEFAULT_MODEL})")
    ap.add_argument("--post", action="store_true", help="post the review as a PR comment via gh")
    ap.add_argument("-o", "--output", help="also write the review to this file")
    args = ap.parse_args()

    owner, repo, number = parse_pr(args.pr)
    print(f"→ Fetching {owner}/{repo}#{number} …", file=sys.stderr)
    meta, diff, truncated = fetch_pr(owner, repo, number)
    prompt = build_prompt(meta, diff, truncated)

    print(f"→ Reviewing with {args.model} …", file=sys.stderr)
    body, usage = review(prompt, args.model)

    header = f"## 🤖 Claude review of #{number} — {meta.get('title')}\n\n"
    footer = (
        f"\n\n---\n*Generated by [claude-review]"
        f" using `{args.model}`. Advisory only — verify before merging.*"
    )
    full = header + body + footer

    print(full)
    print(
        f"\n(tokens — input: {usage.input_tokens}, output: {usage.output_tokens})",
        file=sys.stderr,
    )

    if args.output:
        with open(args.output, "w") as f:
            f.write(full + "\n")
        print(f"→ Wrote {args.output}", file=sys.stderr)

    if args.post:
        post_comment(owner, repo, number, full)
        print(f"→ Posted review to {owner}/{repo}#{number}", file=sys.stderr)


if __name__ == "__main__":
    main()
