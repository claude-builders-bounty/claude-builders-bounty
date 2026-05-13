#!/usr/bin/env python3
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse


@dataclass
class PullRequestRef:
    owner: str
    repo: str
    number: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a structured Markdown review for a GitHub pull request.")
    parser.add_argument("--pr", required=True, help="GitHub pull request URL, e.g. https://github.com/owner/repo/pull/123")
    parser.add_argument("--output", help="Optional output path for the Markdown review")
    parser.add_argument("--post-comment", action="store_true", help="Post the generated review to the pull request")
    return parser.parse_args()


def parse_pr_url(pr_url: str) -> PullRequestRef:
    parsed = urlparse(pr_url)
    path_parts = [part for part in parsed.path.split("/") if part]
    if parsed.netloc != "github.com" or len(path_parts) < 4 or path_parts[2] != "pull":
      raise ValueError(f"Unsupported PR URL: {pr_url}")
    return PullRequestRef(owner=path_parts[0], repo=path_parts[1], number=int(path_parts[3]))


def run_gh(args: list[str], cwd: str | None = None) -> str:
    gh_binary = shutil.which("gh") or shutil.which("gh.exe") or "C:\\Program Files\\GitHub CLI\\gh.exe"
    command = [gh_binary, *args]
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=True)
    return result.stdout


def get_pr_metadata(pr_ref: PullRequestRef) -> dict:
    output = run_gh(
        [
            "pr",
            "view",
            str(pr_ref.number),
            "--repo",
            f"{pr_ref.owner}/{pr_ref.repo}",
            "--json",
            "title,body,files,additions,deletions,changedFiles,author,url",
        ]
    )
    return json.loads(output)


def get_pr_diff(pr_ref: PullRequestRef) -> str:
    return run_gh(["pr", "diff", str(pr_ref.number), "--repo", f"{pr_ref.owner}/{pr_ref.repo}"])


def classify_paths(file_entries: Iterable[dict]) -> tuple[list[str], list[str]]:
    code_paths: list[str] = []
    test_paths: list[str] = []
    for file_entry in file_entries:
        path = file_entry["path"]
        if re.search(r"(^|/)(test|tests|__tests__|specs?)(/|$)", path) or re.search(r"(\.|_)(test|spec)\.", path):
            test_paths.append(path)
        else:
            code_paths.append(path)
    return code_paths, test_paths


def summarize_changes(metadata: dict, code_paths: list[str], test_paths: list[str]) -> str:
    changed = metadata["changedFiles"]
    additions = metadata["additions"]
    deletions = metadata["deletions"]
    top_code = ", ".join(code_paths[:3]) if code_paths else "configuration/docs only"
    summary_lines = [
        f"This PR updates `{changed}` file(s) in `{metadata['url'].split('/pull/')[0].split('github.com/')[-1]}` with `{additions}` additions and `{deletions}` deletions.",
        f"The main surface area is `{top_code}`.",
    ]
    if test_paths:
        summary_lines.append(f"Test coverage changed in `{len(test_paths)}` file(s), which lowers review risk.")
    else:
        summary_lines.append("No dedicated test files changed, so behavior should be verified carefully.")
    return " ".join(summary_lines)


def find_risks(metadata: dict, diff: str, code_paths: list[str], test_paths: list[str]) -> list[str]:
    risks: list[str] = []
    path_blob = "\n".join(code_paths)
    diff_upper = diff.upper()

    if not test_paths:
        risks.append("No explicit automated tests changed, which raises regression risk if runtime behavior changed.")
    if re.search(r"(^|\n)\+.*(SECRET|TOKEN|PASSWORD|API_KEY)", diff_upper):
        risks.append("The diff appears to introduce secret-like strings or credential variables that should be double-checked.")
    if any(part in path_blob for part in ["auth", "login", "session", "permission"]):
        risks.append("Authentication or authorization code changed, so edge-case access control should be reviewed closely.")
    if any(part in path_blob for part in ["schema", "migration", "sql", "db", "database"]):
        risks.append("Database-related changes can be hard to roll back and should be checked for migration safety.")
    if re.search(r"\b(delete|drop|truncate|remove)\b", diff, re.IGNORECASE):
        risks.append("Destructive operations or removal-oriented logic appear in the diff and deserve a careful rollback review.")
    if metadata["changedFiles"] >= 10:
        risks.append("The PR spans many files, which can hide cross-file integration mistakes.")
    if not risks:
        risks.append("No obvious high-risk patterns stood out from the diff, but a quick manual smoke test is still recommended.")
    return risks


def find_suggestions(metadata: dict, diff: str, code_paths: list[str], test_paths: list[str]) -> list[str]:
    suggestions: list[str] = []
    if not test_paths:
        suggestions.append("Add or document at least one focused verification step so reviewers can confirm the intended behavior quickly.")
    if metadata["changedFiles"] > 6:
        suggestions.append("Consider calling out the highest-risk files in the PR description to speed up maintainer review.")
    if re.search(r"TODO|FIXME", diff):
        suggestions.append("Resolve or explain the remaining TODO/FIXME markers before merge.")
    if not re.search(r"README|docs?|example", "\n".join(code_paths), re.IGNORECASE):
        suggestions.append("If the change affects user workflows, include a short usage note or example in the PR description.")
    if not suggestions:
        suggestions.append("The implementation looks focused; the best next step is a quick reviewer-oriented validation note in the PR body.")
    return suggestions


def derive_confidence(metadata: dict, risks: list[str], test_paths: list[str]) -> str:
    if metadata["changedFiles"] <= 5 and test_paths and len(risks) <= 2:
        return "High"
    if metadata["changedFiles"] <= 10:
        return "Medium"
    return "Low"


def render_markdown(pr_ref: PullRequestRef, metadata: dict, summary: str, risks: list[str], suggestions: list[str], confidence: str) -> str:
    risk_lines = "\n".join(f"- {item}" for item in risks)
    suggestion_lines = "\n".join(f"- {item}" for item in suggestions)
    return f"""## Claude Review

**PR**: {metadata["title"]} ([#{pr_ref.number}]({metadata["url"]}))
**Author**: @{metadata["author"]["login"]}

### Summary of Changes
{summary}

### Identified Risks
{risk_lines}

### Improvement Suggestions
{suggestion_lines}

### Confidence
{confidence}
"""


def write_output(markdown: str, output_path: str | None) -> None:
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")
    else:
        sys.stdout.write(markdown)


def post_comment(pr_ref: PullRequestRef, markdown: str) -> None:
    temp_path = Path(os.getenv("TEMP", ".")) / f"claude-review-{pr_ref.number}.md"
    temp_path.write_text(markdown, encoding="utf-8")
    try:
        run_gh(
            [
                "pr",
                "comment",
                str(pr_ref.number),
                "--repo",
                f"{pr_ref.owner}/{pr_ref.repo}",
                "--body-file",
                str(temp_path),
            ]
        )
    finally:
        temp_path.unlink(missing_ok=True)


def main() -> int:
    args = parse_args()
    pr_ref = parse_pr_url(args.pr)
    metadata = get_pr_metadata(pr_ref)
    diff = get_pr_diff(pr_ref)
    code_paths, test_paths = classify_paths(metadata["files"])
    summary = summarize_changes(metadata, code_paths, test_paths)
    risks = find_risks(metadata, diff, code_paths, test_paths)
    suggestions = find_suggestions(metadata, diff, code_paths, test_paths)
    confidence = derive_confidence(metadata, risks, test_paths)
    markdown = render_markdown(pr_ref, metadata, summary, risks, suggestions, confidence)
    write_output(markdown, args.output)
    if args.post_comment:
        post_comment(pr_ref, markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
