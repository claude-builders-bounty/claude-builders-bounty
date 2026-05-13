#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import textwrap
from typing import Any

DEFAULT_MODEL = "claude-sonnet-4-20250514"
DEFAULT_MAX_FILES = 12
DEFAULT_MAX_PATCH_CHARS = 2500
DEFAULT_MAX_CONTEXT_CHARS = 16000
GITHUB_API_BASE = "https://api.github.com"
ANTHROPIC_VERSION = "2023-06-01"

PR_URL_RE = re.compile(
    r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)(?:[/?#].*)?$"
)


class ReviewError(RuntimeError):
    pass


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a structured Markdown review for a GitHub pull request."
    )
    parser.add_argument("--pr", required=True, help="GitHub pull request URL")
    parser.add_argument(
        "--output",
        help="Optional path for the generated Markdown review. Defaults to stdout.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("CLAUDE_REVIEW_MODEL", DEFAULT_MODEL),
        help=f"Anthropic model to use. Defaults to {DEFAULT_MODEL}.",
    )
    parser.add_argument(
        "--post-comment",
        action="store_true",
        help="Post the generated Markdown to the pull request as a comment.",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=DEFAULT_MAX_FILES,
        help="Maximum number of changed files to include in the review context.",
    )
    return parser.parse_args(argv)


def parse_pr_url(url: str) -> tuple[str, str, int]:
    match = PR_URL_RE.match(url.strip())
    if not match:
        raise ReviewError(f"Unsupported GitHub pull request URL: {url}")
    owner = match.group("owner")
    repo = match.group("repo")
    number = int(match.group("number"))
    return owner, repo, number


def run_curl(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    method: str = "GET",
    data: str | None = None,
) -> str:
    command = ["curl", "-fsSL", "-X", method]
    for key, value in (headers or {}).items():
        command.extend(["-H", f"{key}: {value}"])
    if data is not None:
        command.extend(["--data", data])
    command.append(url)

    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip()
        raise ReviewError(
            f"curl request failed for {url}: {stderr or exc.returncode}"
        ) from exc
    return result.stdout


def github_request(url: str, accept: str = "application/vnd.github+json") -> str:
    headers = {
        "Accept": accept,
        "User-Agent": "claude-review/1.0",
    }
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    return run_curl(url, headers=headers)


def github_post(url: str, payload: dict[str, Any]) -> str:
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        raise ReviewError("Missing GITHUB_TOKEN for GitHub write operations")

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "claude-review/1.0",
        "Authorization": f"Bearer {github_token}",
        "Content-Type": "application/json",
    }
    return run_curl(
        url,
        headers=headers,
        method="POST",
        data=json.dumps(payload),
    )


def fetch_json(url: str) -> Any:
    return json.loads(github_request(url))


def fetch_pr_details(owner: str, repo: str, number: int) -> dict[str, Any]:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{number}"
    data = fetch_json(url)
    if not isinstance(data, dict):
        raise ReviewError(f"Unexpected GitHub response for {url}")
    return data


def fetch_pr_files(owner: str, repo: str, number: int) -> list[dict[str, Any]]:
    page = 1
    files: list[dict[str, Any]] = []
    while True:
        url = (
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{number}/files"
            f"?per_page=100&page={page}"
        )
        batch = fetch_json(url)
        if not isinstance(batch, list):
            raise ReviewError(f"Unexpected GitHub response for {url}")
        if not batch:
            break
        files.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return files


def build_review_context(
    pr: dict[str, Any], files: list[dict[str, Any]], max_files: int
) -> str:
    selected_files = files[:max_files]
    lines = [
        f"Repository: {pr['base']['repo']['full_name']}",
        f"Pull request: #{pr['number']}",
        f"Title: {pr['title']}",
        f"Author: {pr['user']['login']}",
        f"State: {pr['state']}",
        f"Merged: {bool(pr.get('merged'))}",
        f"Base branch: {pr['base']['ref']}",
        f"Head branch: {pr['head']['ref']}",
        f"Commits: {pr['commits']}",
        f"Changed files: {pr['changed_files']}",
        f"Additions: {pr['additions']}",
        f"Deletions: {pr['deletions']}",
        "",
        "PR description:",
        (pr.get("body") or "(empty)")[:3000],
        "",
        "Changed files and diff excerpts:",
    ]

    remaining_context_chars = DEFAULT_MAX_CONTEXT_CHARS
    for file_data in selected_files:
        header = (
            f"- {file_data['filename']} "
            f"({file_data['status']}, +{file_data['additions']}/-{file_data['deletions']}, "
            f"{file_data['changes']} changes)"
        )
        lines.append(header)
        remaining_context_chars -= len(header)

        patch = file_data.get("patch") or ""
        if not patch:
            lines.append("  [No textual diff available]")
            remaining_context_chars -= 30
            continue

        excerpt = patch[:DEFAULT_MAX_PATCH_CHARS]
        if len(patch) > DEFAULT_MAX_PATCH_CHARS:
            excerpt += "\n... [truncated]"

        if remaining_context_chars <= 0:
            lines.append("  [Additional diff content omitted due to context budget]")
            break

        excerpt = excerpt[:remaining_context_chars]
        lines.append("```diff")
        lines.append(excerpt)
        lines.append("```")
        remaining_context_chars -= len(excerpt)

    omitted_count = max(0, len(files) - len(selected_files))
    if omitted_count:
        lines.append("")
        lines.append(f"Omitted files: {omitted_count}")

    return "\n".join(lines)


def call_anthropic(model: str, prompt: str) -> dict[str, Any]:
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    if not api_key:
        raise ReviewError("Missing ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN")

    base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
    url = f"{base_url}/v1/messages"

    payload = {
        "model": model,
        "max_tokens": 900,
        "temperature": 0,
        "system": textwrap.dedent(
            """
            You are a senior software engineer performing a pull request review.
            You cannot browse, fetch URLs, or call tools. Use only the provided metadata and diff context.
            Return JSON only. Follow this schema exactly:
            {
              "summary": "2-3 sentences grounded in the diff",
              "risks": ["specific risk 1", "specific risk 2"],
              "suggestions": ["specific suggestion 1", "specific suggestion 2"],
              "confidence": "Low|Medium|High"
            }

            Rules:
            - Be specific and cite concrete behaviors implied by the diff.
            - Do not invent files or code that are not present in the provided context.
            - If there are no material risks or no worthwhile suggestions, return an empty list for that field.
            - Keep the summary concise.
            """
        ).strip(),
        "messages": [{"role": "user", "content": prompt}],
    }

    headers = {
        "content-type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
    }
    data = json.loads(
        run_curl(
            url,
            headers=headers,
            method="POST",
            data=json.dumps(payload),
        )
    )
    if not isinstance(data, dict):
        raise ReviewError("Unexpected Anthropic API response")
    return data


def extract_text(response: dict[str, Any]) -> str:
    content = response.get("content")
    if isinstance(content, str):
        return content.strip()
    if not isinstance(content, list):
        completion = response.get("completion")
        if isinstance(completion, str) and completion.strip():
            return completion.strip()
        raise ReviewError("Missing text blocks in Anthropic API response")
    text_parts: list[str] = []
    for block in content:
        if isinstance(block, str):
            text_parts.append(block)
        elif isinstance(block, dict):
            if block.get("type") == "text" and isinstance(block.get("text"), str):
                text_parts.append(block["text"])
            elif isinstance(block.get("content"), str):
                text_parts.append(block["content"])
    text = "".join(text_parts).strip()
    if not text:
        raise ReviewError("Anthropic API returned no text content")
    return text


def parse_review_json(text: str) -> dict[str, Any]:
    start = text.find("{")
    if start == -1:
        raise ReviewError(f"Failed to locate JSON object in response: {text}")
    decoder = json.JSONDecoder()
    try:
        review, _ = decoder.raw_decode(text[start:])
    except json.JSONDecodeError as exc:
        raise ReviewError(f"Failed to decode review JSON: {exc}") from exc
    if not isinstance(review, dict):
        raise ReviewError("Review response is not a JSON object")
    return review


def normalize_review(review: dict[str, Any]) -> dict[str, Any]:
    summary = str(review.get("summary", "")).strip()
    risks = review.get("risks", [])
    suggestions = review.get("suggestions", [])
    confidence = str(review.get("confidence", "")).strip().title()

    if not summary:
        raise ReviewError("Review summary is missing")
    if confidence not in {"Low", "Medium", "High"}:
        raise ReviewError(f"Invalid confidence score: {confidence}")
    if not isinstance(risks, list):
        raise ReviewError("Review risks must be a list")
    if not isinstance(suggestions, list):
        raise ReviewError("Review suggestions must be a list")

    clean_risks = [str(item).strip() for item in risks if str(item).strip()]
    clean_suggestions = [str(item).strip() for item in suggestions if str(item).strip()]

    return {
        "summary": summary,
        "risks": clean_risks,
        "suggestions": clean_suggestions,
        "confidence": confidence,
    }


def build_fallback_review(pr: dict[str, Any], files: list[dict[str, Any]]) -> dict[str, Any]:
    risks: list[str] = []
    suggestions: list[str] = []

    filenames = [str(item.get("filename", "")) for item in files]
    lower_names = [name.lower() for name in filenames]
    patch_blob = "\n".join(str(item.get("patch") or "") for item in files).lower()

    if any(token in name for name in lower_names for token in ("auth", "permission", "token", "session")):
        risks.append("Authentication or authorization-related files changed; verify access control and failure paths.")
    if any(token in name for name in lower_names for token in ("workflow", ".github/", "deploy", "ci")):
        risks.append("Automation or deployment files changed; verify secret handling and execution scope.")
    if any(token in name for name in lower_names for token in ("sql", "migration", "schema", "db/")):
        risks.append("Database-related files changed; confirm migration safety and data compatibility.")
    if "todo" in patch_blob or "fixme" in patch_blob or "hack" in patch_blob:
        risks.append("The diff introduces TODO/FIXME/HACK markers that may indicate unfinished work.")
    if not risks:
        risks.append("No obvious material risks detected from filenames and diff excerpts.")

    has_tests = any(
        any(token in name for token in ("test", "spec", "__tests__"))
        for name in lower_names
    )
    if not has_tests:
        suggestions.append("Add or update focused tests that cover the changed behavior.")
    suggestions.append("Include exact verification commands in the PR description for reviewers.")

    changed_files = pr.get("changed_files", len(files))
    additions = pr.get("additions", 0)
    deletions = pr.get("deletions", 0)
    confidence = "High"
    if changed_files > 8 or additions + deletions > 400:
        confidence = "Medium"
    if changed_files > 20 or additions + deletions > 1200:
        confidence = "Low"

    summary = (
        f"This PR changes {changed_files} file(s) with {additions} additions and {deletions} deletions. "
        f"It appears to focus on {', '.join(filenames[:3]) or 'the provided diff excerpts'}, "
        "and this review was generated from deterministic fallback analysis because the model response was unavailable."
    )

    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence,
    }


def render_markdown(pr_url: str, pr: dict[str, Any], review: dict[str, Any]) -> str:
    risks = review["risks"] or ["None identified from the provided diff."]
    suggestions = review["suggestions"] or ["No concrete improvement suggestions."]

    lines = [
        f"# Review for {pr['base']['repo']['full_name']}#{pr['number']}",
        "",
        f"Source PR: {pr_url}",
        "",
        "## Summary",
        review["summary"],
        "",
        "## Identified Risks",
    ]
    lines.extend(f"- {item}" for item in risks)
    lines.extend(["", "## Improvement Suggestions"])
    lines.extend(f"- {item}" for item in suggestions)
    lines.extend(["", "## Confidence", review["confidence"], ""])
    return "\n".join(lines)


def build_prompt(pr_url: str, context: str) -> str:
    return textwrap.dedent(
        f"""
        Review this pull request using only the provided context and return JSON only.

        {context}
        """
    ).strip()


def write_output(markdown: str, output_path: str | None) -> None:
    if output_path:
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(markdown)
        return
    sys.stdout.write(markdown)


def post_pr_comment(owner: str, repo: str, number: int, markdown: str) -> None:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{number}/comments"
    github_post(url, {"body": markdown})


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    owner, repo, number = parse_pr_url(args.pr)
    pr = fetch_pr_details(owner, repo, number)
    files = fetch_pr_files(owner, repo, number)
    context = build_review_context(pr, files, args.max_files)
    prompt = build_prompt(args.pr, context)
    try:
        response = call_anthropic(args.model, prompt)
        review_text = extract_text(response)
        review_json = parse_review_json(review_text)
        review = normalize_review(review_json)
    except ReviewError:
        review = build_fallback_review(pr, files)
    markdown = render_markdown(args.pr, pr, review)
    write_output(markdown, args.output)
    if args.post_comment:
        post_pr_comment(owner, repo, number, markdown)
        sys.stderr.write(f"Posted review comment to {args.pr}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
