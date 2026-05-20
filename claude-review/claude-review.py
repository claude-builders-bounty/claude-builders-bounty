#!/usr/bin/env python3
"""
claude-review - AI-powered PR review CLI tool

Usage:
    claude-review --pr URL

Example:
    claude-review --pr https://github.com/owner/repo/pull/123
"""

import argparse
import subprocess
import json
import re
import sys
from dataclasses import dataclass
from typing import Optional


@dataclass
class PRMetadata:
    """PR metadata structure"""
    number: int
    title: str
    author: str
    base_branch: str
    head_branch: str
    state: str
    additions: int
    deletions: int
    changed_files: int
    url: str


@dataclass
class FileChange:
    """Individual file change"""
    filename: str
    status: str  # added, modified, removed, renamed
    additions: int
    deletions: int


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parse GitHub PR URL to extract owner, repo, and PR number."""
    # Match patterns like:
    # https://github.com/owner/repo/pull/123
    # https://github.com/owner/repo/pull/123/files
    pattern = r'github\.com/([^/]+)/([^/]+)/pull/(\d+)'
    match = re.search(pattern, url)
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {url}")
    return match.group(1), match.group(2), int(match.group(3))


def run_gh_command(args: list[str], check: bool = True) -> str:
    """Run gh CLI command and return output."""
    cmd = ["gh"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"gh command failed: {result.stderr}")
    return result.stdout


def get_pr_metadata(owner: str, repo: str, pr_number: int) -> PRMetadata:
    """Fetch PR metadata using gh CLI."""
    try:
        # Use gh pr view with JSON output
        output = run_gh_command([
            "pr", "view", str(pr_number),
            "--repo", f"{owner}/{repo}",
            "--json", "number,title,author,baseRefName,headRefName,state,additions,deletions,changedFiles,url"
        ])
        data = json.loads(output)
        return PRMetadata(
            number=data["number"],
            title=data["title"],
            author=data["author"]["login"],
            base_branch=data["baseRefName"],
            head_branch=data["headRefName"],
            state=data["state"],
            additions=data["additions"],
            deletions=data["deletions"],
            changed_files=data["changedFiles"],
            url=data["url"]
        )
    except Exception as e:
        raise RuntimeError(f"Failed to fetch PR metadata: {e}")


def get_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    """Fetch PR diff using gh CLI."""
    return run_gh_command([
        "pr", "diff", str(pr_number),
        "--repo", f"{owner}/{repo}"
    ])


def get_changed_files(owner: str, repo: str, pr_number: int) -> list[FileChange]:
    """Fetch list of changed files."""
    try:
        output = run_gh_command([
            "pr", "diff", str(pr_number),
            "--repo", f"{owner}/{repo}",
            "--name-only"
        ])
        # Also get file stats
        stats_output = run_gh_command([
            "api", f"repos/{owner}/{repo}/pulls/{pr_number}/files"
        ])
        files_data = json.loads(stats_output)
        
        changes = []
        for f in files_data:
            changes.append(FileChange(
                filename=f["filename"],
                status=f["status"],
                additions=f["additions"],
                deletions=f["deletions"]
            ))
        return changes
    except Exception:
        return []


def analyze_diff(diff: str, metadata: PRMetadata, files: list[FileChange]) -> dict:
    """Analyze the diff and generate review output."""
    
    # Initialize analysis result
    analysis = {
        "summary": "",
        "risks": [],
        "suggestions": [],
        "confidence": "Medium"
    }
    
    # Check for patterns in the diff
    has_secrets = bool(re.search(r'(password|secret|api_key|token|private_key)\s*[=:]\s*["\']?[^"\s\'<>&|]+', diff, re.IGNORECASE))
    has_debug_code = bool(re.search(r'(print\(|console\.log|debugger|TODO|FIXME|XXX|HACK)', diff, re.IGNORECASE))
    has_large_changes = metadata.additions > 500 or metadata.deletions > 500
    has_many_files = metadata.changed_files > 10
    
    # Detect file types
    file_extensions = set()
    for f in files:
        ext = f.filename.rsplit('.', 1)[-1] if '.' in f.filename else ''
        file_extensions.add(ext.lower())
    
    # Security checks
    security_patterns = [
        (r'sql.*\+.*\+', 'Potential SQL injection vulnerability'),
        (r'eval\s*\(', 'Use of eval() can be dangerous'),
        (r'exec\s*\(', 'Use of exec() can be dangerous'),
        (r'shell=True', 'Shell injection risk with shell=True'),
        (r'innerHTML\s*=', 'Potential XSS vulnerability with innerHTML'),
        (r'dangerouslySetInnerHTML', 'React XSS risk with dangerouslySetInnerHTML'),
    ]
    
    for pattern, risk in security_patterns:
        if re.search(pattern, diff, re.IGNORECASE):
            analysis["risks"].append(f"🚨 {risk}")
    
    if has_secrets:
        analysis["risks"].append("🚨 Potential hardcoded secrets or credentials detected")
    
    # Code quality checks
    if has_debug_code:
        analysis["risks"].append("⚠️ Debug statements or TODOs found in changes")
    
    if has_large_changes:
        analysis["risks"].append("⚠️ Large PR - consider splitting into smaller changes")
    
    if has_many_files:
        analysis["risks"].append("⚠️ Many files changed - verify all are necessary")
    
    # Empty/removed files check
    for f in files:
        if f.status == "removed":
            analysis["risks"].append(f"📄 File removed: {f.filename}")
    
    # Generate suggestions based on analysis
    if 'py' in file_extensions:
        analysis["suggestions"].append("Consider running `ruff check` or `pylint` for Python code quality")
        analysis["suggestions"].append("Ensure test coverage for new/modified functions")
    
    if 'js' in file_extensions or 'ts' in file_extensions:
        analysis["suggestions"].append("Consider running `eslint` for JavaScript/TypeScript quality")
    
    if 'go' in file_extensions:
        analysis["suggestions"].append("Run `go vet` and `golangci-lint` for Go code quality")
    
    if metadata.additions > 50:
        analysis["suggestions"].append("Consider adding/updating documentation for new functionality")
    
    if not files:
        analysis["suggestions"].append("No file changes detected - verify the PR URL is correct")
    
    # Generate summary
    file_list = ", ".join([f.filename for f in files[:5]])
    if len(files) > 5:
        file_list += f", and {len(files) - 5} more"
    
    change_direction = "adds" if metadata.additions > metadata.deletions else "removes"
    net_lines = abs(metadata.additions - metadata.deletions)
    
    summary = f"PR #{metadata.number} '{metadata.title}' by {metadata.author} "
    summary += f"{change_direction} {net_lines} net lines across {metadata.changed_files} file(s). "
    
    if files:
        summary += f"Key changes in: {file_list}."
    else:
        summary += "No file changes detected."
    
    analysis["summary"] = summary
    
    # Set confidence based on analysis quality
    if has_secrets or any('sql' in r.lower() or 'xss' in r.lower() for r in analysis["risks"]):
        analysis["confidence"] = "High"
    elif not files or not diff.strip():
        analysis["confidence"] = "Low"
    elif has_large_changes or has_many_files:
        analysis["confidence"] = "Low"
    else:
        analysis["confidence"] = "Medium"
    
    return analysis


def format_output(metadata: PRMetadata, analysis: dict, files: list[FileChange]) -> str:
    """Format the analysis as structured Markdown."""
    
    lines = [
        "# Code Review",
        "",
        f"**PR:** [{metadata.title}]({metadata.url})",
        f"**Author:** @{metadata.author}",
        f"**Branch:** {metadata.head_branch} → {metadata.base_branch}",
        f"**Changes:** +{metadata.additions} / -{metadata.deletions} across {metadata.changed_files} file(s)",
        "",
        "---",
        "",
        "## Summary",
        "",
        analysis["summary"],
        "",
    ]
    
    # Risks section
    if analysis["risks"]:
        lines.append("## Risks")
        lines.append("")
        for risk in analysis["risks"]:
            lines.append(f"- {risk}")
        lines.append("")
    else:
        lines.extend([
            "## Risks",
            "",
            "- No significant risks identified",
            "",
        ])
    
    # Suggestions section
    if analysis["suggestions"]:
        lines.append("## Suggestions")
        lines.append("")
        for suggestion in analysis["suggestions"]:
            lines.append(f"- {suggestion}")
        lines.append("")
    else:
        lines.extend([
            "## Suggestions",
            "",
            "- Review changes for correctness and edge cases",
            "",
        ])
    
    # Confidence section
    confidence = analysis["confidence"]
    confidence_emoji = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}
    lines.extend([
        "## Confidence",
        "",
        f"{confidence_emoji.get(confidence, '⚪')} **{confidence}**",
        "",
        "---",
        "",
        "*Generated by claude-review CLI tool*",
    ])
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="AI-powered PR review CLI tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
    claude-review --pr https://github.com/owner/repo/pull/123
        """
    )
    parser.add_argument(
        "--pr",
        required=True,
        help="GitHub PR URL to review"
    )
    parser.add_argument(
        "--output",
        choices=["stdout", "file"],
        default="stdout",
        help="Output destination (default: stdout)"
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory for output file (default: current directory)"
    )
    
    args = parser.parse_args()
    
    try:
        # Parse PR URL
        owner, repo, pr_number = parse_pr_url(args.pr)
        print(f"Fetching PR #{pr_number} from {owner}/{repo}...", file=sys.stderr)
        
        # Get PR metadata
        metadata = get_pr_metadata(owner, repo, pr_number)
        
        # Get PR diff
        diff = get_pr_diff(owner, repo, pr_number)
        
        # Get changed files
        files = get_changed_files(owner, repo, pr_number)
        
        # Analyze changes
        print("Analyzing changes...", file=sys.stderr)
        analysis = analyze_diff(diff, metadata, files)
        
        # Format output
        output = format_output(metadata, analysis, files)
        
        # Output result
        if args.output == "file":
            output_path = f"{args.output_dir}/pr-{pr_number}-review.md"
            with open(output_path, "w") as f:
                f.write(output)
            print(f"Review written to: {output_path}", file=sys.stderr)
        else:
            print(output)
        
        return 0
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())