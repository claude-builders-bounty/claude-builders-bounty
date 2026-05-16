#!/usr/bin/env python3
"""
changelog.py — Generate structured CHANGELOG.md from git history.

Features:
- Fetches commits since last git tag (or from beginning if no tags)
- Auto-categorizes into Added / Fixed / Changed / Removed / Deprecated / Security
- Uses Conventional Commits parsing (feat:, fix:, chore:, docs:, refactor:, etc.)
- Falls back to semantic analysis for non-standard messages
- Outputs pretty markdown to stdout
- Optional: --write writes to CHANGELOG.md
- Optional: --version VERSION overrides auto-detection
"""

import subprocess
import re
import sys
import os
from datetime import datetime
from collections import OrderedDict

# ─── Categories ───────────────────────────────────────────────
CATEGORY_MAP = OrderedDict([
    ("Added",       ["feat", "feature", "add", "implement", "create", "introduce", "new"]),
    ("Fixed",       ["fix", "bugfix", "bug", "hotfix", "resolve", "correct", "patch"]),
    ("Changed",     ["refactor", "refact", "update", "improve", "change", "modify", "migrate", "redesign"]),
    ("Deprecated",  ["deprecat", "sunset", "phase-out"]),
    ("Removed",     ["remove", "delete", "drop", "eliminate", "strip"]),
    ("Security",    ["security", "vuln", "cve", "audit", "secure", "sanitize"]),
    ("Performance", ["perf", "performance", "optimize", "speed", "fast", "latency"]),
    ("Documentation", ["docs", "doc", "readme", "comment", "documentation"]),
    ("Infrastructure", ["ci", "cd", "build", "dep", "deploy", "docker", "infra", "chore(ci)"]),
])

# ─── Git Helpers ──────────────────────────────────────────────

def run_git(*args):
    """Run git command, return stdout or None."""
    try:
        r = subprocess.run(["git"] + list(args), capture_output=True, text=True, timeout=30)
        return r.stdout.strip() if r.returncode == 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None

def get_last_tag():
    """Return the most recent tag reachable from HEAD."""
    return run_git("describe", "--tags", "--abbrev=0")

def get_commits_since(ref="HEAD"):
    """Get commit log since ref. Returns list of dicts."""
    last_tag = get_last_tag()
    if last_tag:
        log_range = f"{last_tag}..HEAD"
    else:
        log_range = "--all"
    
    raw = run_git(
        "log", log_range,
        "--format=%H|||%an|||%ae|||%ai|||%s|||%b",
        "--no-merges"
    )
    if not raw:
        return []
    
    commits = []
    for line in raw.split("\n"):
        if not line.strip():
            continue
        parts = line.split("|||", 5)
        if len(parts) < 5:
            continue
        c = {
            "hash": parts[0][:8],
            "author": parts[1],
            "email": parts[2],
            "date": parts[3],
            "subject": parts[4],
            "body": parts[5] if len(parts) > 5 else "",
        }
        commits.append(c)
    return commits

# ─── Classification ───────────────────────────────────────────

def classify_commit(subject):
    """Classify commit into a category."""
    subject_lower = subject.lower()
    
    # Conventional commit parsing: feat(scope): message
    conv_match = re.match(r'^(\w+)(?:\([^)]*\))?!?\s*:\s*(.*)', subject_lower)
    prefix = conv_match.group(1) if conv_match else ""
    
    for category, keywords in CATEGORY_MAP.items():
        # Check prefix first (most reliable for conventional commits)
        if prefix and prefix in keywords:
            return category
    
    # Fall back to keyword matching in full subject
    for category, keywords in CATEGORY_MAP.items():
        for kw in keywords:
            if kw in subject_lower:
                return category
    
    return "Changed"  # default

# ─── Formatter ────────────────────────────────────────────────

def format_changelog(commits, version=None, repo_url=None):
    """Build CHANGELOG.md content."""
    now = datetime.now().strftime("%Y-%m-%d")
    
    if not version:
        tag = get_last_tag()
        version = tag if tag else "Unreleased"
    
    lines = ["# Changelog", "", f"All notable changes to this project will be documented in this file.", ""]
    lines.append(f"## [{version}] - {now}")
    lines.append("")
    
    # Group by category
    grouped = OrderedDict()
    for cat in CATEGORY_MAP:
        grouped[cat] = []
    grouped["Changed"] = []  # default bucket
    
    for c in commits:
        cat = classify_commit(c["subject"])
        # Clean up the subject for display
        display = c["subject"]
        # Remove conventional commit prefix for readability
        display = re.sub(r'^\w+(\([^)]*\))?!?\s*:\s*', '', display)
        # Capitalize
        if display and display[0].islower():
            display = display[0].upper() + display[1:]
        
        entry = f"- {display} ([{c['hash']}]({repo_url + '/commit/' + c['hash'] if repo_url else '#' + c['hash']}))"
        grouped.setdefault(cat, []).append(entry)
    
    # Write grouped output
    total = 0
    for cat, entries in grouped.items():
        if entries:
            lines.append(f"### {cat}")
            lines.append("")
            lines.extend(entries)
            lines.append("")
            total += len(entries)
    
    if total == 0:
        lines.append("_No significant changes._")
        lines.append("")
    
    return "\n".join(lines)

# ─── CLI ──────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate structured CHANGELOG.md from git history")
    parser.add_argument("--write", "-w", action="store_true", help="Write to CHANGELOG.md")
    parser.add_argument("--version", "-v", help="Override version string")
    parser.add_argument("--repo-url", "-u", help="Repo URL for commit links (auto-detected if omitted)")
    parser.add_argument("--sample", "-s", action="store_true", help="Generate sample output for demo")
    args = parser.parse_args()
    
    # Auto-detect repo URL
    repo_url = args.repo_url
    if not repo_url and not args.sample:
        remote = run_git("remote", "get-url", "origin")
        if remote:
            # Convert SSH to HTTPS
            remote = re.sub(r'^git@([^:]+):', r'https://\1/', remote)
            remote = re.sub(r'\.git$', '', remote)
            repo_url = remote
    
    if args.sample:
        # Generate sample output for demo/testing
        sample_commits = [
            {"hash": "a1b2c3d4", "author": "Dev", "email": "", "date": "2026-05-15", "subject": "feat: add AI-powered commit categorization", "body": ""},
            {"hash": "e5f6g7h8", "author": "Dev", "email": "", "date": "2026-05-14", "subject": "fix: handle empty git repos gracefully", "body": ""},
            {"hash": "i9j0k1l2", "author": "Dev", "email": "", "date": "2026-05-13", "subject": "docs: update README with examples", "body": ""},
            {"hash": "m3n4o5p6", "author": "Dev", "email": "", "date": "2026-05-12", "subject": "refactor: simplify classification logic", "body": ""},
            {"hash": "q7r8s9t0", "author": "Dev", "email": "", "date": "2026-05-11", "subject": "perf: reduce memory usage for large repos", "body": ""},
            {"hash": "u1v2w3x4", "author": "Dev", "email": "", "date": "2026-05-10", "subject": "ci: add automated release workflow", "body": ""},
            {"hash": "y5z6a7b8", "author": "Dev", "email": "", "date": "2026-05-09", "subject": "fix: handle merge commits without messages", "body": ""},
        ]
        changelog = format_changelog(sample_commits, version="1.0.0", repo_url=repo_url or "https://github.com/example/repo")
    
    commits = get_commits_since()
    if not commits and not args.sample:
        print("No commits found. Are you in a git repo with history?", file=sys.stderr)
        sys.exit(1)
    
    if not args.sample:
        changelog = format_changelog(commits, version=args.version, repo_url=repo_url)
    
    if args.write:
        with open("CHANGELOG.md", "w") as f:
            f.write(changelog)
        print(f"✅ Written to CHANGELOG.md ({len(commits) if not args.sample else 7} commits)")
    else:
        print(changelog)

if __name__ == "__main__":
    main()
