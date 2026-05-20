from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PR_URL_RE = re.compile(r"https://github\.com/([^/\s]+)/([^/\s]+)/pull/(\d+)")


@dataclass(frozen=True)
class PullRequestRef:
    owner: str
    repo: str
    number: int

    @property
    def repo_name(self) -> str:
        return f"{self.owner}/{self.repo}"

    @property
    def url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repo}/pull/{self.number}"


def parse_pr_url(value: str) -> PullRequestRef:
    match = PR_URL_RE.fullmatch(value.strip())
    if not match:
        raise ValueError("Expected a GitHub PR URL like https://github.com/owner/repo/pull/123")
    owner, repo, number = match.groups()
    return PullRequestRef(owner=owner, repo=repo, number=int(number))


def run_command(args: list[str], *, input_text: str | None = None) -> str:
    try:
        process = subprocess.run(
            args,
            input=input_text,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            encoding="utf-8",
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"Command not found: {args[0]}") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip()
        raise RuntimeError(f"Command failed: {' '.join(args)}\n{stderr}") from exc
    return process.stdout


def load_pr_context(ref: PullRequestRef) -> dict[str, Any]:
    metadata_json = run_command(
        [
            "gh",
            "pr",
            "view",
            str(ref.number),
            "--repo",
            ref.repo_name,
            "--json",
            "title,author,baseRefName,headRefName,additions,deletions,changedFiles,files,url,body",
        ]
    )
    metadata = json.loads(metadata_json)
    diff = run_command(["gh", "pr", "diff", str(ref.number), "--repo", ref.repo_name])
    return {"ref": ref, "metadata": metadata, "diff": diff}


def truncate_diff(diff: str, limit: int = 20000) -> str:
    if len(diff) <= limit:
        return diff
    omitted = len(diff) - limit
    return diff[:limit] + f"\n\n[diff truncated: {omitted} characters omitted]\n"


def build_prompt(context: dict[str, Any]) -> str:
    ref: PullRequestRef = context["ref"]
    metadata = context["metadata"]
    diff = truncate_diff(context["diff"])
    files = metadata.get("files") or []
    file_summary = "\n".join(
        f"- {item.get('path')} (+{item.get('additions', 0)}/-{item.get('deletions', 0)})"
        for item in files[:80]
    )
    return f"""You are a Claude Code pull request reviewer.

Review this PR diff and return only a structured Markdown review comment with exactly these sections:

## Summary
2-3 concise sentences describing the change.

## Identified Risks
Bulleted list. Use "- None found." if no material risks are visible.

## Improvement Suggestions
Bulleted list. Give actionable, code-review style suggestions.

## Confidence
Low, Medium, or High, followed by one short reason.

Repository: {ref.repo_name}
Pull request: {ref.url}
Title: {metadata.get('title', '')}
Author: {(metadata.get('author') or {}).get('login', '')}
Base: {metadata.get('baseRefName', '')}
Head: {metadata.get('headRefName', '')}
Changed files: {metadata.get('changedFiles', 0)}
Additions: {metadata.get('additions', 0)}
Deletions: {metadata.get('deletions', 0)}

Files:
{file_summary}

Diff:
```diff
{diff}
```
"""


def run_claude_review(prompt: str) -> str:
    if shutil.which("claude") is None:
        raise RuntimeError("Claude Code CLI was not found. Install it or use --backend heuristic.")
    return run_command(["claude", "-p", prompt]).strip()


def file_categories(files: list[dict[str, Any]]) -> set[str]:
    categories: set[str] = set()
    for item in files:
        path = str(item.get("path") or "")
        lower = path.lower()
        if lower.endswith((".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".rb")):
            categories.add("application code")
        if lower.endswith((".md", ".mdx", ".txt")):
            categories.add("documentation")
        if ".github/workflows/" in lower or lower.endswith((".yml", ".yaml")):
            categories.add("automation/configuration")
        if "test" in lower or lower.endswith(("_test.py", ".spec.ts", ".test.ts", ".test.tsx")):
            categories.add("tests")
        if lower.endswith((".json", ".toml", ".lock")):
            categories.add("metadata/configuration")
    return categories


def heuristic_review(context: dict[str, Any]) -> str:
    ref: PullRequestRef = context["ref"]
    metadata = context["metadata"]
    files = metadata.get("files") or []
    categories = sorted(file_categories(files)) or ["repository files"]
    changed = int(metadata.get("changedFiles") or len(files))
    additions = int(metadata.get("additions") or 0)
    deletions = int(metadata.get("deletions") or 0)
    paths = [str(item.get("path") or "") for item in files]

    risks: list[str] = []
    suggestions: list[str] = []

    if changed > 20 or additions + deletions > 1000:
        risks.append("Large diff size may hide behavior changes that need more focused review.")
    if "application code" in categories:
        risks.append("Runtime behavior depends on environment assumptions that static diff review cannot fully verify.")
        suggestions.append("Document required CLIs, environment variables, and failure behavior for the new code path.")
    if any(".github/workflows/" in path for path in paths):
        risks.append("Workflow changes can expose token permissions or secret handling issues.")
        suggestions.append("Use least-privilege `permissions:` in the workflow and document required secrets.")
    if any(path.endswith((".py", ".js", ".ts", ".tsx")) for path in paths) and not any(
        "test" in path.lower() for path in paths
    ):
        risks.append("Code changes do not appear to include corresponding tests in the diff.")
        suggestions.append("Add focused tests or sample outputs for the primary success and failure paths.")
    if any(path.lower().endswith((".md", ".mdx")) for path in paths):
        if "application code" not in categories:
            risks.append("Documentation-only changes may drift from executable behavior if examples are not tested.")
        suggestions.append("Keep examples executable or clearly mark them as illustrative to avoid stale docs.")
    if any(path.lower().endswith((".json", ".toml", ".yml", ".yaml")) for path in paths):
        suggestions.append("Validate structured files in CI so syntax errors are caught before merge.")

    if not risks:
        risks.append("None found from the diff alone.")
    if not suggestions:
        suggestions.append("Add a short verification note to the PR description with the exact commands run.")

    confidence = "High"
    confidence_reason = "the diff is small and the touched files are easy to inspect."
    if changed > 20 or additions + deletions > 1000:
        confidence = "Low"
        confidence_reason = "the diff is broad and should be reviewed in smaller slices."
    elif additions + deletions > 400 or "application code" in categories:
        confidence = "Medium"
        confidence_reason = "the review is based on static diff signals and should be paired with tests."

    title = metadata.get("title") or f"PR #{ref.number}"
    category_text = ", ".join(categories)
    return f"""## Summary
This PR, "{title}", changes {changed} file(s) with +{additions}/-{deletions} lines. The diff mainly touches {category_text}. Review should focus on whether the implementation, documentation, and verification steps stay aligned.

## Identified Risks
{chr(10).join(f"- {item}" for item in risks)}

## Improvement Suggestions
{chr(10).join(f"- {item}" for item in suggestions)}

## Confidence
{confidence} - {confidence_reason}
"""


def choose_backend(requested: str) -> str:
    if requested == "auto":
        return "claude" if shutil.which("claude") else "heuristic"
    return requested


def post_comment(ref: PullRequestRef, body: str) -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".md") as temp:
        temp.write(body)
        temp_path = temp.name
    try:
        run_command(["gh", "pr", "comment", str(ref.number), "--repo", ref.repo_name, "--body-file", temp_path])
    finally:
        Path(temp_path).unlink(missing_ok=True)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Review a GitHub PR and emit a structured Markdown comment.")
    parser.add_argument("--pr", required=True, help="GitHub PR URL, for example https://github.com/owner/repo/pull/123")
    parser.add_argument(
        "--backend",
        choices=("auto", "claude", "heuristic"),
        default=os.environ.get("CLAUDE_REVIEW_BACKEND", "auto"),
        help="Review backend. auto uses Claude Code if installed, otherwise heuristic.",
    )
    parser.add_argument("--post-comment", action="store_true", help="Post the generated review to the PR with gh.")
    parser.add_argument("--output", help="Write the Markdown review to a file instead of only stdout.")
    parser.add_argument("--print-prompt", action="store_true", help="Print the Claude prompt and exit.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        ref = parse_pr_url(args.pr)
        context = load_pr_context(ref)
        prompt = build_prompt(context)
        if args.print_prompt:
            print(prompt)
            return 0

        backend = choose_backend(args.backend)
        review = run_claude_review(prompt) if backend == "claude" else heuristic_review(context)
        review = review.strip() + "\n"

        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(review, encoding="utf-8")

        if args.post_comment:
            post_comment(ref, review)

        print(review, end="")
        return 0
    except Exception as exc:
        print(f"claude-review: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
