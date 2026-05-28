from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence
from urllib.parse import urlparse

from .reviewer import ReviewInput, render_review


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="Review a GitHub pull request and emit a structured Markdown comment.",
    )
    parser.add_argument("--pr", required=True, help="GitHub pull request URL")
    parser.add_argument(
        "--output",
        help="Optional path to write the Markdown review. Defaults to stdout.",
    )
    parser.add_argument(
        "--offline-fixture",
        help="Read PR metadata and diff from a JSON fixture instead of GitHub.",
    )
    args = parser.parse_args(argv)

    try:
        pr_input = load_fixture(args.offline_fixture) if args.offline_fixture else fetch_pr(args.pr)
    except ReviewError as exc:
        print(f"claude-review: {exc}", file=sys.stderr)
        return 1

    review = render_review(pr_input)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(review, encoding="utf-8")
    else:
        print(review)

    return 0


class ReviewError(RuntimeError):
    pass


@dataclass(frozen=True)
class PullRequestRef:
    owner: str
    repo: str
    number: int

    @property
    def repository(self) -> str:
        return f"{self.owner}/{self.repo}"


def parse_pr_url(url: str) -> PullRequestRef:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if parsed.netloc not in {"github.com", "www.github.com"}:
        raise ReviewError("--pr must be a GitHub pull request URL")
    if len(parts) != 4 or parts[2] != "pull":
        raise ReviewError("--pr must look like https://github.com/owner/repo/pull/123")
    try:
        number = int(parts[3])
    except ValueError as exc:
        raise ReviewError("pull request number must be numeric") from exc
    return PullRequestRef(parts[0], parts[1], number)


def fetch_pr(url: str) -> ReviewInput:
    ref = parse_pr_url(url)
    metadata = run_gh_json(
        [
            "pr",
            "view",
            str(ref.number),
            "--repo",
            ref.repository,
            "--json",
            "number,title,author,additions,deletions,changedFiles,baseRefName,headRefName,body,url",
        ]
    )
    diff = run_gh_text(["pr", "diff", str(ref.number), "--repo", ref.repository])
    return ReviewInput.from_payload(metadata, diff)


def load_fixture(path: str) -> ReviewInput:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise ReviewError(f"cannot read fixture {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ReviewError(f"invalid fixture JSON {path}: {exc}") from exc

    diff = str(payload.pop("diff", ""))
    return ReviewInput.from_payload(payload, diff)


def run_gh_json(args: list[str]) -> dict[str, object]:
    raw = run_gh_text(args)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ReviewError(f"GitHub CLI returned invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ReviewError("GitHub CLI returned an unexpected JSON shape")
    return data


def run_gh_text(args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["gh", *args],
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ReviewError("GitHub CLI `gh` is required for live PR reviews") from exc

    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise ReviewError(f"GitHub CLI failed: {detail}")
    return result.stdout
