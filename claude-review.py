#!/usr/bin/env python3
"""
claude-review — Claude Code PR-review sub-agent.

Takes a GitHub PR (URL or number), fetches the diff, and produces a structured
Markdown review: summary, risks, improvement suggestions, and a confidence score.

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --pr owner/repo#123
  claude-review --repo owner/repo --pr 123

Requires `gh` CLI (authenticated) for private repos; public repos work without it.
"""
import argparse, re, subprocess, sys, json, os

def parse_pr(ref):
    """Parse a PR reference into (owner, repo, number)."""
    # forms: full URL, owner/repo#N, or owner/repo (with --pr N)
    if ref.startswith("http"):
        m = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", ref)
        if m:
            return m.group(1), m.group(2), int(m.group(3))
    m = re.match(r"([^/\s]+)/([^#\s]+)#(\d+)", ref)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    raise ValueError(f"Cannot parse PR reference: {ref}")

def get_diff(owner, repo, num):
    """Fetch the PR diff via gh CLI (works for private repos when authenticated)."""
    ref = f"{owner}/{repo}#{num}"
    try:
        r = subprocess.run(["gh", "pr", "diff", str(num), "--repo", f"{owner}/{repo}"],
                           capture_output=True, text=True, timeout=60)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout
    except Exception:
        pass
    # fallback: GitHub API (public repos)
    import urllib.request
    url = f"https://github.com/{owner}/{repo}/pull/{num}.diff"
    req = urllib.request.Request(url, headers={"User-Agent": "claude-review", "Accept": "application/vnd.github.v3.diff"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode()
    except Exception as e:
        raise RuntimeError(f"Could not fetch diff for {ref}: {e}")

def analyze(diff):
    """Analyze a diff and return structured findings."""
    files = []
    additions = 0
    deletions = 0
    current_file = None
    for line in diff.splitlines():
        if line.startswith("diff --git"):
            m = re.search(r"b/(\S+)", line)
            current_file = m.group(1) if m else "unknown"
            files.append(current_file)
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1
    files = sorted(set(files))

    risks = []
    suggestions = []
    lowered = diff.lower()

    # Risk patterns
    if re.search(r"\brm\s+-rf\b|\bshutil\.rmtree\b", lowered):
        risks.append("Destructive file deletion (rm -rf / shutil.rmtree) present — verify it is scoped safely.")
    if re.search(r"\bexec\s*\(|\beval\s*\(|\bsubprocess\.(call|run|Popen).*shell\s*=\s*True", lowered):
        risks.append("Shell command injection risk (exec/eval or shell=True) — validate inputs are sanitized.")
    if re.search(r"password\s*=|secret\s*=|api[_-]?key\s*=\s*['\"]", lowered):
        risks.append("Hardcoded credential(s) detected — move to environment variables or a secrets manager.")
    if re.search(r"SELECT .* (WHERE|JOIN)|DROP TABLE|DELETE FROM|TRUNCATE", lowered) and "where" not in lowered:
        risks.append("Unsafe SQL (DROP/TRUNCATE/DELETE without WHERE) — confirm it is not reachable from user input.")
    if re.search(r"except\s*:\s*pass", lowered) or re.search(r"except\s+Exception\s*:\s*pass", lowered):
        risks.append("Bare exception swallowing (except: pass) hides errors — consider logging.")

    # Suggestion patterns
    if not re.search(r"test_|_test\.|\.spec\.", " ".join(files).lower()) and not any("test" in f.lower() for f in files):
        suggestions.append("No test files in this PR — consider adding tests for the changed behavior.")
    if len(files) > 15:
        suggestions.append(f"Large PR ({len(files)} files) — consider splitting into smaller, reviewable changes.")
    if additions + deletions > 1000:
        suggestions.append(f"Large diff ({additions}+/{deletions}-) — increases review risk; consider breaking it up.")
    if re.search(r"TODO|FIXME|HACK", diff):
        suggestions.append("TODO/FIXME markers present — follow up on these before merging if they affect behavior.")
    if not re.search(r"\.md\b|README", lowered) and len(files) > 1:
        suggestions.append("No documentation update for a multi-file change — consider updating docs/README.")

    # Confidence score (heuristic)
    if not risks and len(files) <= 5 and additions + deletions <= 200:
        confidence = "High"
    elif len(risks) <= 1 and len(files) <= 10:
        confidence = "Medium"
    else:
        confidence = "Low"

    return {
        "files": files,
        "additions": additions,
        "deletions": deletions,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence,
    }

def render(owner, repo, num, analysis):
    lines = []
    lines.append(f"# PR Review: {owner}/{repo}#{num}")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"Changes {len(analysis['files'])} file(s), "
                 f"+{analysis['additions']}/-{analysis['deletions']} lines.")
    if analysis["files"]:
        lines.append("Files touched:")
        for f in analysis["files"]:
            lines.append(f"- `{f}`")
    lines.append("")
    lines.append("## Identified Risks")
    if analysis["risks"]:
        for r in analysis["risks"]:
            lines.append(f"- {r}")
    else:
        lines.append("- No high-risk patterns detected.")
    lines.append("")
    lines.append("## Improvement Suggestions")
    if analysis["suggestions"]:
        for s in analysis["suggestions"]:
            lines.append(f"- {s}")
    else:
        lines.append("- None — the change looks clean.")
    lines.append("")
    lines.append(f"## Confidence Score: {analysis['confidence']}")
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser(description="Claude Code PR-review sub-agent")
    ap.add_argument("--pr", help="PR URL or owner/repo#N")
    ap.add_argument("--repo", help="owner/repo (used with a numeric --pr)")
    args = ap.parse_args()

    if args.pr and (args.pr.isdigit()):
        num = int(args.pr)
        if not args.repo:
            sys.exit("--repo owner/repo is required when --pr is numeric")
        owner, repo = args.repo.split("/")
    else:
        owner, repo, num = parse_pr(args.pr)

    diff = get_diff(owner, repo, num)
    analysis = analyze(diff)
    print(render(owner, repo, num, analysis))

if __name__ == "__main__":
    main()
