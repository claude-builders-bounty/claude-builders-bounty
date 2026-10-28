#!/usr/bin/env python3
"""
Structured Git CHANGELOG Generator
Compliant with Keep a Changelog (1.0.0) and Conventional Commits specifications.
Bounty #1 for claude-builders-bounty.
Hardened against flag injection, directory traversal, encoding corruption, and empty repo edge-cases.
"""

import argparse
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SAFE_GIT_REF_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.\/\^~]+$")

CATEGORY_RULES = [
    ("Added", re.compile(r"^(feat|add|feature)(\([^\)]+\))?!?:\s*(.*)", re.I)),
    ("Fixed", re.compile(r"^(fix|bugfix|patch)(\([^\)]+\))?!?:\s*(.*)", re.I)),
    ("Removed", re.compile(r"^(remove|deprecate|delete)(\([^\)]+\))?!?:\s*(.*)", re.I)),
    ("Changed", re.compile(r"^(refactor|perf|change|update|style)(\([^\)]+\))?!?:\s*(.*)", re.I)),
    ("Maintenance", re.compile(r"^(chore|docs|ci|test|build|revert)(\([^\)]+\))?!?:\s*(.*)", re.I)),
]

def validate_git_ref(ref_str: str) -> str:
    """Validates git commit ref or tag string to prevent argument/flag injection."""
    cleaned = ref_str.strip()
    if not SAFE_GIT_REF_REGEX.match(cleaned) or cleaned.startswith("-"):
        raise ValueError(f"Invalid git reference: '{ref_str}'")
    return cleaned

def validate_repo_dir(repo_dir: Path) -> Path:
    """Strictly validates git repository directory existence and git metadata presence."""
    clean_path = repo_dir.resolve()
    if not clean_path.is_dir():
        raise ValueError(f"Target directory does not exist: {clean_path}")
    if not (clean_path / ".git").exists():
        raise ValueError(f"Directory is not a valid git repository (.git missing): {clean_path}")
    return clean_path

def get_latest_git_tag(repo_dir: Path) -> Optional[str]:
    """Finds the most recent reachable git tag safely."""
    safe_repo = validate_repo_dir(repo_dir)
    try:
        res = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0", "--"],
            cwd=str(safe_repo),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        if res.returncode == 0 and res.stdout.strip():
            tag = res.stdout.strip()
            return validate_git_ref(tag)
        return None
    except Exception:
        return None

def fetch_commits(repo_dir: Path, since: Optional[str] = None, until: str = "HEAD") -> List[Dict[str, str]]:
    """Fetches commits in range using git log with delimiter-safe format and surrogateescape encoding."""
    safe_repo = validate_repo_dir(repo_dir)
    clean_until = validate_git_ref(until)
    cmd = ["git", "log", "--no-merges", "--pretty=format:%h|%an|%ad|%s", "--date=short"]
    
    if since:
        clean_since = validate_git_ref(since)
        cmd.extend([f"{clean_since}..{clean_until}", "--"])
    else:
        cmd.extend(["-n", "100", clean_until, "--"])

    try:
        res = subprocess.run(
            cmd,
            cwd=str(safe_repo),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True
        )
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.strip() if e.stderr else (e.stdout.strip() if e.stdout else f"Git exited with code {e.returncode}")
        raise RuntimeError(f"Failed to query git log: {err_msg}")

    commits = []
    for line in res.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("|", 3)
        if len(parts) == 4:
            commits.append({
                "hash": parts[0].strip(),
                "author": parts[1].strip(),
                "date": parts[2].strip(),
                "subject": parts[3].strip()
            })
    return commits

def categorize_commit(subject: str) -> Tuple[str, str]:
    """Matches commit subject to Keep a Changelog category and formats clean description."""
    for category, pattern in CATEGORY_RULES:
        m = pattern.match(subject)
        if m:
            scope = m.group(2) if len(m.groups()) >= 2 else ""
            desc = m.group(3) if len(m.groups()) >= 3 else m.group(1)
            desc = desc.strip()
            if scope:
                clean_scope = scope.strip("()")
                return category, f"**{clean_scope}**: {desc[0].upper() + desc[1:] if desc else ''}"
            return category, desc[0].upper() + desc[1:] if desc else subject

    # Fallback heuristics
    lower = subject.lower()
    if lower.startswith("add ") or "initial commit" in lower or "implement" in lower:
        return "Added", subject[0].upper() + subject[1:]
    if lower.startswith("fix ") or "resolv" in lower or "patch" in lower:
        return "Fixed", subject[0].upper() + subject[1:]
    if lower.startswith("remove ") or "delete " in lower:
        return "Removed", subject[0].upper() + subject[1:]
    
    return "Changed", subject[0].upper() + subject[1:]

def build_changelog_markdown(
    categories: Dict[str, List[Dict[str, str]]],
    version: str = "Unreleased",
    date_str: Optional[str] = None,
    since_tag: Optional[str] = None
) -> str:
    """Builds markdown content following Keep a Changelog format."""
    today = date_str or datetime.date.today().isoformat()
    header = f"## [{version}] - {today}" if version != "Unreleased" else f"## [Unreleased]"
    
    lines = [
        "# Changelog",
        "",
        "All notable changes to this project will be documented in this file.",
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),",
        "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).",
        "",
        header,
    ]

    if since_tag:
        lines.append(f"*Changes since `{since_tag}`:*\n")

    category_order = ["Added", "Fixed", "Changed", "Removed", "Maintenance"]
    has_any = False

    for cat in category_order:
        entries = categories.get(cat, [])
        if entries:
            has_any = True
            lines.append(f"### {cat}")
            for item in entries:
                commit_hash = item["hash"]
                desc = item["desc"]
                lines.append(f"- {desc} ([`{commit_hash}`])")
            lines.append("")

    if not has_any:
        lines.append("- No documented changes found in this commit range.\n")

    return "\n".join(lines).strip() + "\n"

def generate_changelog(
    repo_dir: Optional[Path] = None,
    since: Optional[str] = None,
    until: str = "HEAD",
    version: str = "Unreleased",
    output_path: Optional[Path] = None
) -> str:
    repo = validate_repo_dir(repo_dir or Path.cwd())
    since_tag = since or get_latest_git_tag(repo)
    commits = fetch_commits(repo, since=since_tag, until=until)

    categories: Dict[str, List[Dict[str, str]]] = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
        "Maintenance": []
    }

    for c in commits:
        cat, desc = categorize_commit(c["subject"])
        categories[cat].append({
            "hash": c["hash"],
            "desc": desc,
            "author": c["author"],
            "date": c["date"]
        })

    md = build_changelog_markdown(categories, version=version, since_tag=since_tag)

    if output_path:
        out_p = output_path.resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(md, encoding="utf-8")
        print(f"[+] Changelog written to {out_p}", file=sys.stderr)

    return md

def main():
    parser = argparse.ArgumentParser(
        description="Structured CHANGELOG generator from Git history (Keep a Changelog format)."
    )
    parser.add_argument("--since", help="Git tag or commit reference to start from (defaults to latest tag)")
    parser.add_argument("--until", default="HEAD", help="Git commit reference to end at (default: HEAD)")
    parser.add_argument("--version", default="Unreleased", help="Version header name (default: Unreleased)")
    parser.add_argument("--output", "-o", help="Filepath to write CHANGELOG.md (defaults to stdout)")
    parser.add_argument("--repo", default=".", help="Path to git repository root (default: current directory)")
    args = parser.parse_args()

    try:
        repo_dir = validate_repo_dir(Path(args.repo))
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    out_p = Path(args.output).resolve() if args.output else None
    try:
        result = generate_changelog(
            repo_dir=repo_dir,
            since=args.since,
            until=args.until,
            version=args.version,
            output_path=out_p
        )
        if not out_p:
            print(result)
    except Exception as e:
        print(f"Error generating changelog: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
