#!/usr/bin/env python3
"""Generate structured Markdown PR reviews from unified git diff content."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Tuple


@dataclass
class FileStats:
    path: str
    additions: int = 0
    deletions: int = 0
    headers: List[str] = field(default_factory=list)
    risk_flags: List[str] = field(default_factory=list)


RISK_RULES: List[Tuple[re.Pattern[str], str]] = [
    (re.compile(r"\.github/workflows/"), "CI workflow behavior changed"),
    (
        re.compile(
            r"\bauth\b|\boauth\b|\bsession\b|\bjwt\b|\bbearer\b|\baccess_token\b|\brefresh_token\b",
            re.IGNORECASE,
        ),
        "Authentication or token handling touched",
    ),
    (re.compile(r"\bmigration\b|\bschema\b|\bALTER TABLE\b|\bDROP TABLE\b", re.IGNORECASE), "Database schema/migration changes detected"),
    (re.compile(r"\bpanic\(|\braise\s+[A-Za-z]", re.IGNORECASE), "Error-path behavior changed"),
    (re.compile(r"\bdelete\b|\bremove\b|\brm\s+-rf\b", re.IGNORECASE), "Destructive operation keywords present"),
    (re.compile(r"\bsecret\b|\bpassword\b|\bapi[_-]?key\b", re.IGNORECASE), "Secret-handling code touched"),
]


def resolve_diff_url(pr_url: str) -> str:
    cleaned = pr_url.strip().rstrip("/")
    if cleaned.endswith(".diff"):
        return cleaned
    return f"{cleaned}.diff"


def fetch_diff(pr_url: str, timeout: float = 20.0) -> str:
    diff_url = resolve_diff_url(pr_url)
    req = urllib.request.Request(diff_url, headers={"User-Agent": "claude-review/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:  # nosec B310 - public HTTP fetch for explicit PR URL
            payload = response.read()
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Unable to fetch PR diff from {diff_url}: {exc}") from exc

    text = payload.decode("utf-8", errors="replace")
    if "diff --git" not in text:
        raise RuntimeError(f"Downloaded content from {diff_url} does not look like a git diff")
    return text


def parse_unified_diff(diff_text: str) -> Dict[str, FileStats]:
    files: Dict[str, FileStats] = {}
    current: FileStats | None = None

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) < 4:
                current = None
                continue
            path = parts[3][2:] if parts[3].startswith("b/") else parts[3]
            current = files.setdefault(path, FileStats(path=path))
            continue

        if current is None:
            continue

        if line.startswith("@@"):
            current.headers.append(line)
            continue

        if line.startswith("+++") or line.startswith("---"):
            continue

        if line.startswith("+"):
            current.additions += 1
            text = line[1:]
            for pattern, message in RISK_RULES:
                if pattern.search(current.path) or pattern.search(text):
                    if message not in current.risk_flags:
                        current.risk_flags.append(message)
            continue

        if line.startswith("-"):
            current.deletions += 1
            text = line[1:]
            for pattern, message in RISK_RULES:
                if pattern.search(current.path) or pattern.search(text):
                    if message not in current.risk_flags:
                        current.risk_flags.append(message)
            continue

        for pattern, message in RISK_RULES:
            if pattern.search(current.path) and message not in current.risk_flags:
                current.risk_flags.append(message)

    return files


def score_confidence(files: Dict[str, FileStats]) -> int:
    changed_files = len(files)
    churn = sum(item.additions + item.deletions for item in files.values())
    risk_count = len({flag for file_stat in files.values() for flag in file_stat.risk_flags})

    score = 86
    if changed_files > 20:
        score -= 18
    elif changed_files > 10:
        score -= 10
    elif changed_files > 5:
        score -= 6

    if churn > 1200:
        score -= 16
    elif churn > 500:
        score -= 10
    elif churn > 200:
        score -= 6

    score -= min(risk_count * 3, 15)
    return max(45, min(97, score))


def summary_sentences(pr_url: str, files: Dict[str, FileStats]) -> List[str]:
    changed_files = len(files)
    additions = sum(item.additions for item in files.values())
    deletions = sum(item.deletions for item in files.values())
    top_files = sorted(files.values(), key=lambda item: item.additions + item.deletions, reverse=True)[:3]
    top_desc = ", ".join(f"`{item.path}`" for item in top_files) if top_files else "no files"

    return [
        f"This review analyzed [{pr_url}]({pr_url}) and found {changed_files} changed file(s) ({additions} additions, {deletions} deletions).",
        f"The largest changes are in {top_desc}.",
        "The comments below focus on regression risk, missing coverage, and maintainability checks before merge.",
    ]


def identified_risks(files: Dict[str, FileStats]) -> List[str]:
    risks: List[str] = []
    for path in sorted(files):
        file_stat = files[path]
        file_churn = file_stat.additions + file_stat.deletions
        if file_churn > 180:
            risks.append(f"`{path}` has high churn ({file_churn} lines), which raises regression probability.")
        if file_stat.path.endswith((".sql", "schema.prisma")) and file_stat.deletions > 0:
            risks.append(f"`{path}` includes schema removals; verify backward compatibility and rollback plan.")
        for flag in file_stat.risk_flags:
            risks.append(f"`{path}`: {flag}.")

    if not risks:
        risks.append("No critical red flags detected from static diff signals; runtime behavior still needs targeted tests.")

    deduped: List[str] = []
    seen = set()
    for risk in risks:
        if risk not in seen:
            deduped.append(risk)
            seen.add(risk)
    return deduped[:8]


def improvement_suggestions(files: Dict[str, FileStats]) -> List[str]:
    suggestions: List[str] = []
    changed_files = len(files)

    if changed_files > 8:
        suggestions.append("Add a short architecture note in the PR description explaining why each major file group changed.")

    any_workflow = any(path.startswith(".github/workflows/") for path in files)
    if any_workflow:
        suggestions.append("Include one successful CI run link or screenshot proving workflow changes execute as intended.")

    any_tests = any("test" in path.lower() for path in files)
    if not any_tests:
        suggestions.append("Add or reference regression tests; none of the touched paths look test-focused.")

    high_churn_files = [fs.path for fs in files.values() if fs.additions + fs.deletions > 120]
    if high_churn_files:
        suggestions.append(f"Split high-churn changes into follow-up commits or call out risk areas: {', '.join(f'`{p}`' for p in high_churn_files[:3])}.")

    suggestions.append("Before merge, run lint/type/test commands and paste exact results in the PR conversation.")

    deduped: List[str] = []
    seen = set()
    for item in suggestions:
        if item not in seen:
            deduped.append(item)
            seen.add(item)
    return deduped[:6]


def render_markdown(pr_url: str, files: Dict[str, FileStats]) -> str:
    confidence = score_confidence(files)
    summary = summary_sentences(pr_url, files)
    risks = identified_risks(files)
    improvements = improvement_suggestions(files)

    file_lines = [
        f"- `{path}`: +{stats.additions}/-{stats.deletions}"
        for path, stats in sorted(
            files.items(), key=lambda item: item[1].additions + item[1].deletions, reverse=True
        )[:12]
    ]

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    sections = [
        "## Summary",
        *(f"- {line}" for line in summary),
        "",
        "## Identified Risks",
        *(f"- {line}" for line in risks),
        "",
        "## Improvement Suggestions",
        *(f"- {line}" for line in improvements),
        "",
        "## Confidence Score",
        f"- **{confidence}/100**",
        "",
        "## Diff Snapshot",
        *file_lines,
        "",
        f"_Generated by claude-review on {generated}_",
    ]
    return "\n".join(sections).strip() + "\n"


def write_output(markdown: str, output_path: str | None) -> None:
    if output_path:
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(markdown)
        return
    sys.stdout.write(markdown)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate structured Markdown review output from a PR diff")
    parser.add_argument("--pr", required=True, help="GitHub PR URL, e.g. https://github.com/org/repo/pull/123")
    parser.add_argument("--output", help="Path to write Markdown review output")
    parser.add_argument(
        "--diff-file",
        help="Use a local unified diff file instead of fetching over the network (useful for offline verification)",
    )
    parser.add_argument("--json-metrics", help="Optional path to write parsed diff metrics as JSON")
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    try:
        if args.diff_file:
            with open(args.diff_file, "r", encoding="utf-8") as handle:
                diff_text = handle.read()
        else:
            diff_text = fetch_diff(args.pr)

        files = parse_unified_diff(diff_text)
        if not files:
            raise RuntimeError("No changed files found in provided diff")

        markdown = render_markdown(args.pr, files)
        write_output(markdown, args.output)

        if args.json_metrics:
            payload = {
                "pr": args.pr,
                "files": [
                    {
                        "path": fs.path,
                        "additions": fs.additions,
                        "deletions": fs.deletions,
                        "risk_flags": fs.risk_flags,
                    }
                    for fs in sorted(files.values(), key=lambda item: item.path)
                ],
                "confidence": score_confidence(files),
            }
            with open(args.json_metrics, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)

        return 0
    except Exception as exc:  # pylint: disable=broad-exception-caught
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
