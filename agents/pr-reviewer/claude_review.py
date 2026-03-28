#!/usr/bin/env python3
"""
claude-review — Claude Code sub-agent that reviews a PR and posts structured output.

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr https://github.com/owner/repo/pull/123 --dry-run
    claude-review --pr https://github.com/owner/repo/pull/123 --post-comment

Exit codes:
    0 — low risk
    1 — medium risk
    2 — high risk
"""

import argparse
import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

MAX_DIFF_CHARS = 40_000   # truncate diffs beyond this
GENERATED_PATTERNS = [
    r"package-lock\.json$", r"yarn\.lock$", r"pnpm-lock\.yaml$",
    r"Cargo\.lock$", r"Gemfile\.lock$", r"poetry\.lock$",
    r"\.min\.js$", r"\.min\.css$", r"dist/", r"build/",
    r"__generated__", r"\.pb\.go$", r"_pb2\.py$",
]
SECURITY_PATTERNS = [
    r"auth", r"password", r"secret", r"token", r"cred", r"key",
    r"iam", r"permission", r"role", r"sudo", r"root", r"admin",
    r"sql", r"query", r"exec", r"eval", r"subprocess", r"shell",
    r"tls", r"ssl", r"cert", r"crypto",
]
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2",
    ".ttf", ".eot", ".pdf", ".zip", ".tar", ".gz", ".exe", ".dll", ".so",
}

REVIEW_PROMPT = """\
You are an expert code reviewer. Review the following GitHub pull request and produce a structured Markdown review.

## PR Metadata
{metadata}

## Diff (may be truncated for very large PRs)
```diff
{diff}
```

## Instructions
Produce ONLY the following sections — no preamble, no trailing text:

## Summary
2–3 sentences describing what this PR does and its overall quality.

## Risks
A bulleted list of concrete risks: security issues, breaking changes, race conditions, missing error handling, etc.
If none, write: `- No significant risks identified.`

## Suggestions
A bulleted list of actionable improvement suggestions (code quality, tests, docs, naming, perf).
If none, write: `- Looks good — no suggestions.`

## Verdict
**Confidence:** {confidence}

**Risk level:** [LOW | MEDIUM | HIGH] — one sentence explaining the rating.

**Recommendation:** [APPROVE | REQUEST_CHANGES | NEEDS_DISCUSSION]
"""

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Return (owner, repo, pr_number) from a GitHub PR URL."""
    m = re.match(
        r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url.strip()
    )
    if not m:
        sys.exit(f"ERROR: Cannot parse PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))


def gh(*args: str) -> str:
    """Run a gh CLI command and return stdout."""
    result = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.exit(f"ERROR running gh {' '.join(args)}:\n{result.stderr}")
    return result.stdout


def load_config(repo_root: Optional[Path] = None) -> dict:
    """Load .claude-review.yml if present."""
    paths = []
    if repo_root:
        paths.append(repo_root / ".claude-review.yml")
    paths.append(Path.cwd() / ".claude-review.yml")
    paths.append(Path.home() / ".claude-review.yml")
    for p in paths:
        if p.exists() and HAS_YAML:
            with open(p) as f:
                return yaml.safe_load(f) or {}
        elif p.exists():
            return {}  # yaml not available, skip
    return {}


def is_generated(filename: str) -> bool:
    return any(re.search(pat, filename) for pat in GENERATED_PATTERNS)


def is_binary(filename: str) -> bool:
    return Path(filename).suffix.lower() in BINARY_EXTENSIONS


def is_security_sensitive(filename: str) -> bool:
    low = filename.lower()
    return any(re.search(pat, low) for pat in SECURITY_PATTERNS)


# ──────────────────────────────────────────────────────────────────────────────
# PR data fetching
# ──────────────────────────────────────────────────────────────────────────────

def fetch_pr_metadata(owner: str, repo: str, number: int) -> dict:
    raw = gh("pr", "view", str(number),
             "--repo", f"{owner}/{repo}",
             "--json",
             "title,body,author,additions,deletions,changedFiles,"
             "baseRefName,headRefName,labels,reviews,state,url")
    return json.loads(raw)


def fetch_pr_diff(owner: str, repo: str, number: int) -> tuple[str, list[str]]:
    """Return (diff_text, list_of_changed_files)."""
    diff = gh("pr", "diff", str(number), "--repo", f"{owner}/{repo}")
    # Collect file names from diff headers
    files = re.findall(r"^diff --git a/(.+?) b/", diff, re.MULTILINE)
    return diff, files


def filter_diff(diff: str, files: list[str]) -> tuple[str, list[str], list[str]]:
    """
    Strip generated/binary file hunks from the diff.
    Returns (filtered_diff, skipped_generated, skipped_binary).
    """
    skipped_gen, skipped_bin = [], []
    chunks = re.split(r"(?=^diff --git )", diff, flags=re.MULTILINE)
    kept = []
    for chunk in chunks:
        if not chunk.strip():
            continue
        m = re.search(r"^diff --git a/(.+?) b/", chunk, re.MULTILINE)
        fname = m.group(1) if m else ""
        if is_binary(fname):
            skipped_bin.append(fname)
        elif is_generated(fname):
            skipped_gen.append(fname)
        else:
            kept.append(chunk)
    return "".join(kept), skipped_gen, skipped_bin


def truncate_diff(diff: str, max_chars: int = MAX_DIFF_CHARS) -> tuple[str, bool]:
    if len(diff) <= max_chars:
        return diff, False
    return diff[:max_chars] + "\n\n[... diff truncated — too large ...]", True


# ──────────────────────────────────────────────────────────────────────────────
# Confidence scoring
# ──────────────────────────────────────────────────────────────────────────────

def compute_confidence(meta: dict, files: list[str]) -> tuple[str, str]:
    """
    Return (confidence_label, risk_level) based on heuristics.
    confidence: High / Medium / Low
    risk:       LOW / MEDIUM / HIGH
    """
    additions = meta.get("additions", 0)
    deletions = meta.get("deletions", 0)
    changed = meta.get("changedFiles", 0)
    total_lines = additions + deletions

    has_tests = any(
        re.search(r"test|spec|__tests__|_test\.", f, re.IGNORECASE) for f in files
    )
    has_security = any(is_security_sensitive(f) for f in files)

    # Confidence: smaller & well-tested = higher confidence
    if total_lines < 100 and changed <= 5:
        confidence = "High"
    elif total_lines < 500 and changed <= 20:
        confidence = "Medium"
    else:
        confidence = "Low"

    # Risk level
    if has_security or (total_lines > 1000):
        risk = "HIGH"
    elif not has_tests and total_lines > 50:
        risk = "MEDIUM"
    elif total_lines > 200:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    return confidence, risk


# ──────────────────────────────────────────────────────────────────────────────
# LLM review
# ──────────────────────────────────────────────────────────────────────────────

def format_metadata(meta: dict) -> str:
    return "\n".join([
        f"Title: {meta.get('title', 'N/A')}",
        f"Author: {meta.get('author', {}).get('login', 'N/A')}",
        f"Base: {meta.get('baseRefName', '?')} ← {meta.get('headRefName', '?')}",
        f"Additions: +{meta.get('additions', 0)}  Deletions: -{meta.get('deletions', 0)}",
        f"Files changed: {meta.get('changedFiles', 0)}",
        f"Labels: {', '.join(l['name'] for l in meta.get('labels', [])) or 'none'}",
        f"State: {meta.get('state', 'N/A')}",
        f"URL: {meta.get('url', 'N/A')}",
    ])


def call_claude_api(prompt: str) -> str:
    """Use Anthropic SDK directly."""
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def call_claude_cli(prompt: str) -> str:
    """Fall back to `claude` CLI subprocess."""
    result = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "text"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.exit(f"ERROR calling claude CLI:\n{result.stderr}")
    return result.stdout


def get_review(prompt: str) -> str:
    if HAS_ANTHROPIC and os.environ.get("ANTHROPIC_API_KEY"):
        return call_claude_api(prompt)
    # Try claude CLI
    if subprocess.run(["which", "claude"], capture_output=True).returncode == 0:
        return call_claude_cli(prompt)
    sys.exit(
        "ERROR: No review backend available.\n"
        "Set ANTHROPIC_API_KEY (and install anthropic package) OR have `claude` CLI in PATH."
    )


# ──────────────────────────────────────────────────────────────────────────────
# Output assembly
# ──────────────────────────────────────────────────────────────────────────────

def assemble_review(
    review_body: str,
    meta: dict,
    skipped_gen: list[str],
    skipped_bin: list[str],
    truncated: bool,
    confidence: str,
    risk: str,
    config: dict,
) -> str:
    header = textwrap.dedent(f"""\
        <!-- claude-review -->
        > **Claude PR Review** — generated by [claude-review](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)
    """)

    notes = []
    if truncated:
        notes.append("⚠️ **Large diff** — review is based on first ~40 000 chars of the diff.")
    if skipped_gen:
        notes.append(f"🤖 **Skipped generated files:** {', '.join(f'`{f}`' for f in skipped_gen[:5])}" +
                     (f" (+{len(skipped_gen)-5} more)" if len(skipped_gen) > 5 else ""))
    if skipped_bin:
        notes.append(f"🖼️ **Skipped binary files:** {', '.join(f'`{f}`' for f in skipped_bin[:5])}" +
                     (f" (+{len(skipped_bin)-5} more)" if len(skipped_bin) > 5 else ""))

    notes_block = ("\n".join(notes) + "\n\n") if notes else ""
    footer = "\n\n---\n*Powered by Claude Sonnet · [claude-review](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)*"

    return header + "\n" + notes_block + review_body + footer


RISK_EXIT_CODE = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Claude Code PR reviewer with structured Markdown output.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Exit codes:
              0  low risk
              1  medium risk
              2  high risk
        """),
    )
    parser.add_argument("--pr", required=True, help="GitHub PR URL, e.g. https://github.com/owner/repo/pull/123")
    parser.add_argument("--post-comment", action="store_true", help="Post review as a PR comment via gh CLI")
    parser.add_argument("--dry-run", action="store_true", help="Print review but do NOT post comment")
    parser.add_argument("--output", help="Write review to this file (in addition to stdout)")
    parser.add_argument("--config", help="Path to .claude-review.yml config file")
    parser.add_argument("--max-diff", type=int, default=MAX_DIFF_CHARS,
                        help=f"Max diff chars before truncation (default: {MAX_DIFF_CHARS})")
    args = parser.parse_args()

    owner, repo, pr_number = parse_pr_url(args.pr)

    config = {}
    if args.config:
        if HAS_YAML:
            with open(args.config) as f:
                config = yaml.safe_load(f) or {}
    else:
        config = load_config()

    print(f"🔍  Fetching PR #{pr_number} from {owner}/{repo} …", file=sys.stderr)
    meta = fetch_pr_metadata(owner, repo, pr_number)

    print("📥  Fetching diff …", file=sys.stderr)
    diff_raw, files = fetch_pr_diff(owner, repo, pr_number)

    diff_filtered, skipped_gen, skipped_bin = filter_diff(diff_raw, files)
    diff_final, truncated = truncate_diff(diff_filtered, args.max_diff)

    confidence, risk = compute_confidence(meta, files)

    print(f"🤖  Calling Claude (confidence={confidence}, risk={risk}) …", file=sys.stderr)
    prompt = REVIEW_PROMPT.format(
        metadata=format_metadata(meta),
        diff=diff_final,
        confidence=confidence,
    )
    review_body = get_review(prompt)

    full_review = assemble_review(
        review_body, meta, skipped_gen, skipped_bin,
        truncated, confidence, risk, config,
    )

    print(full_review)

    if args.output:
        Path(args.output).write_text(full_review)
        print(f"\n✅  Review written to {args.output}", file=sys.stderr)

    if args.post_comment and not args.dry_run:
        print("💬  Posting comment to PR …", file=sys.stderr)
        gh("pr", "comment", str(pr_number),
           "--repo", f"{owner}/{repo}",
           "--body", full_review)
        print(f"✅  Comment posted to {args.pr}", file=sys.stderr)
    elif args.post_comment and args.dry_run:
        print("ℹ️   --dry-run set: skipping comment post.", file=sys.stderr)

    sys.exit(RISK_EXIT_CODE.get(risk, 0))


if __name__ == "__main__":
    main()
