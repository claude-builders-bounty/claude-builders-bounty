from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlparse


@dataclass(frozen=True)
class PullRequestRef:
    owner: str
    repo: str
    number: int

    @property
    def slug(self) -> str:
        return f"{self.owner}/{self.repo}"


def parse_pr_url(value: str) -> PullRequestRef:
    """Parse https://github.com/owner/repo/pull/123 or owner/repo#123."""
    shorthand = re.fullmatch(r"([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)#(\d+)", value.strip())
    if shorthand:
        owner, repo, number = shorthand.groups()
        return PullRequestRef(owner, repo, int(number))

    parsed = urlparse(value)
    if parsed.netloc.lower() != "github.com":
        raise ValueError("PR URL must point to github.com")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 4 or parts[2] != "pull" or not parts[3].isdigit():
        raise ValueError("Expected URL format: https://github.com/owner/repo/pull/123")
    return PullRequestRef(parts[0], parts[1], int(parts[3]))


def run_command(args: list[str], *, input_text: str | None = None, timeout: int = 120) -> str:
    env = os.environ.copy()
    # Hermes gateway/profile runs often set HOME to a profile sandbox. Let callers opt into
    # the real user's gh auth without hard-coding it for everyone.
    if "GH_HOME" in env:
        env["HOME"] = env["GH_HOME"]
    result = subprocess.run(
        args,
        input=input_text,
        text=True,
        capture_output=True,
        timeout=timeout,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Command failed ({' '.join(args)}): {detail}")
    return result.stdout


def fetch_pr_diff(ref: PullRequestRef) -> str:
    return run_command(["gh", "pr", "diff", str(ref.number), "--repo", ref.slug], timeout=180)


def build_prompt(ref: PullRequestRef, diff: str) -> str:
    clipped = diff
    max_chars = int(os.getenv("CLAUDE_REVIEW_MAX_DIFF_CHARS", "60000"))
    if len(clipped) > max_chars:
        clipped = clipped[:max_chars] + "\n\n[Diff truncated for review. Focus on visible changes.]\n"

    return textwrap.dedent(
        f"""
        You are a senior code reviewer. Review this GitHub pull request diff and return ONLY a structured Markdown review comment.

        Pull request: https://github.com/{ref.slug}/pull/{ref.number}

        Required format:
        ## Summary
        2-3 sentences summarizing the intent and implementation.

        ## Identified risks
        - List concrete correctness, security, reliability, testing, compatibility, or maintenance risks.
        - If there are no material risks, say "No material risks identified from the visible diff."

        ## Improvement suggestions
        - List actionable suggestions.
        - Include test/documentation suggestions when relevant.

        ## Confidence
        Low / Medium / High, followed by one short reason.

        Diff:
        ```diff
        {clipped}
        ```
        """
    ).strip()


def call_claude(prompt: str, model: str | None = None) -> str:
    args = ["claude", "-p", prompt]
    if model:
        args.extend(["--model", model])
    return run_command(args, timeout=300).strip()


def heuristic_review(ref: PullRequestRef, diff: str) -> str:
    """Deterministic fallback for local tests or machines without Claude Code."""
    added = len(re.findall(r"^\+(?!\+\+\+)", diff, flags=re.MULTILINE))
    removed = len(re.findall(r"^-(?!---)", diff, flags=re.MULTILINE))
    files = re.findall(r"^diff --git a/(.*?) b/", diff, flags=re.MULTILINE)
    touched = ", ".join(files[:5]) if files else "the visible files"

    risks: list[str] = []
    suggestions: list[str] = []
    if re.search(r"password|secret|token|api[_-]?key", diff, re.IGNORECASE):
        risks.append("The diff contains credential-related terms; verify no secrets or tokens are committed.")
    if not re.search(r"test|spec|pytest|vitest|unittest", "\n".join(files), re.IGNORECASE):
        risks.append("No obvious test files are visible in the diff, so regression coverage may be incomplete.")
    if added + removed > 500:
        risks.append("The diff is large enough that splitting it could make review and rollback safer.")
    if not risks:
        risks.append("No material risks identified from the visible diff.")

    suggestions.append("Run the repository's automated test and lint commands before merge.")
    if not re.search(r"README|docs?|\.md$", "\n".join(files), re.IGNORECASE):
        suggestions.append("Add or update documentation if the change affects user-facing behavior.")
    suggestions.append("Ask for focused review on the highest-risk files touched by this PR.")

    confidence = "Medium" if files else "Low"
    reason = "based on diff metadata and lightweight static checks" if files else "because no file-level diff metadata was available"

    risk_lines = "\n".join(f"- {risk}" for risk in risks)
    suggestion_lines = "\n".join(f"- {suggestion}" for suggestion in suggestions)
    return (
        "## Summary\n"
        f"This PR updates {touched}. The visible diff adds {added} lines and removes {removed} lines, "
        "so the main review focus should be correctness, regression coverage, and maintainability "
        "of the touched files.\n\n"
        "## Identified risks\n"
        f"{risk_lines}\n\n"
        "## Improvement suggestions\n"
        f"{suggestion_lines}\n\n"
        "## Confidence\n"
        f"{confidence} — {reason}."
    )


def validate_review(markdown: str) -> list[str]:
    required = ["## Summary", "## Identified risks", "## Improvement suggestions", "## Confidence"]
    missing = [section for section in required if section not in markdown]
    if not re.search(r"## Confidence\s*(?:\n|\r\n)+\s*(Low|Medium|High)\b", markdown, re.IGNORECASE):
        missing.append("Confidence value Low/Medium/High")
    return missing


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a structured Claude Code review for a GitHub PR.")
    parser.add_argument("--pr", required=True, help="GitHub PR URL, e.g. https://github.com/owner/repo/pull/123")
    parser.add_argument("--model", default=os.getenv("CLAUDE_REVIEW_MODEL"), help="Optional Claude Code model name")
    parser.add_argument("--diff-file", help="Read a saved diff instead of calling gh pr diff")
    parser.add_argument("--output", help="Write Markdown review to this file")
    parser.add_argument("--post-comment", action="store_true", help="Post the generated review as a PR comment with gh")
    parser.add_argument("--no-claude", action="store_true", help="Use deterministic fallback reviewer instead of invoking Claude Code")
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        ref = parse_pr_url(args.pr)
        if args.diff_file:
            with open(args.diff_file, "r", encoding="utf-8") as handle:
                diff = handle.read()
        else:
            diff = fetch_pr_diff(ref)

        if args.no_claude:
            review = heuristic_review(ref, diff)
        else:
            try:
                review = call_claude(build_prompt(ref, diff), model=args.model)
            except Exception as exc:
                print(f"Claude Code invocation failed, using deterministic fallback: {exc}", file=sys.stderr)
                review = heuristic_review(ref, diff)

        missing = validate_review(review)
        if missing:
            raise RuntimeError("Generated review is missing required sections: " + ", ".join(missing))

        if args.output:
            with open(args.output, "w", encoding="utf-8") as handle:
                handle.write(review + "\n")
        else:
            print(review)

        if args.post_comment:
            run_command(["gh", "pr", "comment", str(ref.number), "--repo", ref.slug, "--body", review], timeout=120)
            print(f"Posted review comment to https://github.com/{ref.slug}/pull/{ref.number}", file=sys.stderr)
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
