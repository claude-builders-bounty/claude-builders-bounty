#!/usr/bin/env bash
# =============================================================================
# changelog.sh — Generate a structured CHANGELOG.md from git history
# =============================================================================
# Usage:
#   bash changelog.sh                        # Auto-detect last tag
#   bash changelog.sh --since-tag v1.0.0     # From a specific tag
#   bash changelog.sh --output CHANGELOG.md  # Custom output path
#   bash changelog.sh --repo /path/to/repo   # Target repository
# =============================================================================

set -e

OUTPUT="CHANGELOG.md"
REPO="${PWD}"
LIMIT=500

while [[ $# -gt 0 ]]; do
    case $1 in
        --since-tag|-t)  SINCE_TAG="$2"; shift 2 ;;
        --output|-o)     OUTPUT="$2"; shift 2 ;;
        --repo|-r)       REPO="$2"; shift 2 ;;
        --limit|-n)      LIMIT="$2"; shift 2 ;;
        *)               echo "Unknown: $1"; exit 1 ;;
    esac
done

python3 - << 'PYTHON_EOF'
import argparse, subprocess, re, sys, os
from datetime import datetime
from typing import List, Dict

def get_last_tag(path):
    r = subprocess.run(["git", "describe", "--tags", "--abbrev=0"],
        capture_output=True, text=True, timeout=10, cwd=path)
    return r.stdout.strip() if r.returncode == 0 else None

def get_commits(since_tag, limit, path):
    rng = f"{since_tag}..HEAD" if since_tag else "HEAD"
    r = subprocess.run(
        ["git", "log", rng, "--format=%H|%s|%an|%ai", f"-{limit}"],
        capture_output=True, text=True, timeout=30, cwd=path)
    if r.returncode != 0:
        r = subprocess.run(["git", "log", "--format=%H|%s|%an|%ai", f"-{limit}"],
            capture_output=True, text=True, timeout=30, cwd=path)
    commits = []
    for line in r.stdout.strip().split("\n"):
        if not line: continue
        p = line.split("|", 3)
        if len(p) >= 4:
            commits.append({"sha": p[0][:8], "message": p[1], "author": p[2], "date": p[3]})
    return commits

CONVENTIONAL = [
    (r"^feat(?:\([^)]*\))?[!:]?\s+", "Added"),
    (r"^fix(?:\([^)]*\))?[!:]?\s+", "Fixed"),
    (r"^docs?(?:\([^)]*\))?[!:]?\s+", "Changed"),
    (r"^style(?:\([^)]*\))?[!:]?\s+", "Changed"),
    (r"^refactor(?:\([^)]*\))?[!:]?\s+", "Changed"),
    (r"^perf(?:\([^)]*\))?[!:]?\s+", "Changed"),
    (r"^test(?:\([^)]*\))?[!:]?\s+", "Changed"),
    (r"^build(?:\([^)]*\))?[!:]?\s+", "Changed"),
    (r"^ci(?:\([^)]*\))?[!:]?\s+", "Changed"),
    (r"^chore(?:\([^)]*\))?[!:]?\s+", "Changed"),
    (r"^revert(?:\([^)]*\))?[!:]?\s+", "Changed"),
    (r"^remove(?:\([^)]*\))?[!:]?\s+", "Removed"),
    (r"^patch(?:\([^)]*\))?[!:]?\s+", "Fixed"),
]

FALLBACK = [
    (r"\badd(ed|s)?\b", "Added"), (r"\bnew\b", "Added"),
    (r"\bimplement(ed|ation)?\b", "Added"),
    (r"\bfix(ed|es)?\b", "Fixed"), (r"\bbug\b", "Fixed"),
    (r"\bchange[ds]?\b", "Changed"), (r"\bupdate[sd]?\b", "Changed"),
    (r"\bimprove[sd]?\b", "Changed"), (r"\brefactor\b", "Changed"),
    (r"\bdeprecat\w*\b", "Changed"), (r"\bremove[sd]?\b", "Removed"),
    (r"\bdelete[td]?\b", "Removed"), (r"\bsecurity\b", "Security"),
]

def categorize(msg):
    first = msg.strip().split("\n")[0]
    for pat, cat in CONVENTIONAL:
        if re.search(pat, first, re.IGNORECASE): return cat
    for pat, cat in FALLBACK:
        if re.search(pat, first, re.IGNORECASE): return cat
    return "Changed"

def build(commits):
    cats = {}
    for c in commits:
        c["category"] = categorize(c["message"])
        cats.setdefault(c["category"], []).append(c)
    order = ["Added", "Fixed", "Changed", "Removed", "Security"]
    lines = [f"# Changelog\n\n## [{datetime.now().strftime('%Y-%m-%d')}]\n"]
    for cat in order:
        if cat in cats:
            lines.append(f"### {cat}\n")
            for c in cats[cat]:
                msg = re.sub(r"^\w+(?:\([^)]+\))?[!:]?\s+", "",
                              c["message"].strip().split("\n")[0])
                lines.append(f"- {msg} ({c['sha']})\n")
            lines.append("\n")
            del cats[cat]
    for cat, lst in cats.items():
        lines.append(f"### {cat}\n")
        for c in lst:
            msg = re.sub(r"^\w+(?:\([^)]+\))?[!:]?\s+", "",
                          c["message"].strip().split("\n")[0])
            lines.append(f"- {msg} ({c['sha']})\n")
        lines.append("\n")
    return "".join(lines).strip() + "\n"

SINCE_TAG = None
if "--since-tag" in sys.argv:
    idx = sys.argv.index("--since-tag")
    SINCE_TAG = sys.argv[idx+1] if idx+1 < len(sys.argv) else None

OUTPUT = "CHANGELOG.md"
if "-o" in sys.argv:
    OUTPUT = sys.argv[sys.argv.index("-o")+1]

REPO = "."
if "-r" in sys.argv:
    REPO = sys.argv[sys.argv.index("-r")+1]

last_tag = SINCE_TAG or get_last_tag(REPO)
commits = get_commits(last_tag, LIMIT, REPO)
changelog = build(commits)

with open(OUTPUT, "w") as f:
    f.write(changelog)
print(f"✓ {OUTPUT} ({len(commits)} commits)")
