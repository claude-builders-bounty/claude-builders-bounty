#!/usr/bin/env python3
"""claude-review.py — PR review agent (no LLM required).

Fetches a GitHub pull request's metadata + diff via the API and produces a
structured Markdown review: a short summary, identified risks, improvement
suggestions, and a confidence score.

Usage:
  python claude-review.py --pr https://github.com/owner/repo/pull/123
  python claude-review.py --pr owner/repo#123 --token $GITHUB_TOKEN
  python claude-review.py --pr 123 -r owner/repo        # short form

Auth: set GITHUB_TOKEN (or GITHUB_PAT) env var, or pass --token.
Public PRs work without a token (rate-limited).
"""
import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error

API = "https://api.github.com"
DIFF_HEADERS = {"Accept": "application/vnd.github.v3.diff"}
JSON_HEADERS = {"Accept": "application/vnd.github+json"}

# Heuristic signals ---------------------------------------------------------
TEST_RE = re.compile(r"(^|/)(test|tests|spec|specs|__tests__)/|"
                     r"\.(test|spec)\.(js|ts|py|jsx|tsx)$", re.I)
SECRET_RE = re.compile(
    r"(?i)(aws_secret_access_key|AKIA[0-9A-Z]{16}|"
    r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|"
    r"ghp_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]+|"
    r"sk_(live|test)_[A-Za-z0-9]+)")
DANGER_RE = re.compile(
    r"(?i)(\beval\s*\(|\bexec\s*\(|os\.system\(|subprocess[^)]*shell\s*=\s*True|"
    r"pickle\.loads\(|child_process\.exec\(|eval\(req|\byaml\.load\()")
TODO_RE = re.compile(r"^\s*[+-]\s*.*\b(TODO|FIXME|HACK|XXX)\b", re.M)
SQLCONCAT_RE = re.compile(
    r"(?i)(f[\"'].*SELECT|SELECT.*\{|\"\.format\(.*SELECT|%\s*\(.*SELECT|"
    r"\+.*SELECT|SELECT.*\+)", re.S)
MIGRATION_RE = re.compile(r"(^|/)(migrations?|db/migrate|schema\.(sql|prisma)|"
                         r"alembic|flyway|liquibase)", re.I)
DEP_FILES = re.compile(r"(^|/)(package\.json|requirements\.txt|pyproject\.toml|"
                       r"yarn\.lock|poetry\.lock|Pipfile|go\.mod|Gemfile|"
                       r"build\.gradle|composer\.json)$", re.I)
BREAKING_RE = re.compile(r"(?i)\b(BREAKING|major version|v\d+\.\d+\.\d+)\b")


def api_get(url, token, as_json=True):
    headers = dict(JSON_HEADERS if as_json else DIFF_HEADERS)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    headers["User-Agent"] = "claude-review-agent"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code} for {url}: {e.reason}")
    return json.loads(data) if as_json else data


def parse_pr_ref(ref, repo_arg):
    # URL form
    m = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", ref or "")
    if m:
        return m.group(1), m.group(2), m.group(3)
    # owner/repo#num
    m = re.match(r"([^/\s]+)/([^/#\s]+)#(\d+)$", ref or "")
    if m:
        return m.group(1), m.group(2), m.group(3)
    # num with -r owner/repo
    if re.fullmatch(r"\d+", ref or "") and repo_arg:
        o, r = repo_arg.split("/")
        return o, r, ref
    raise SystemExit("Could not parse PR reference. Use a URL or owner/repo#num.")


def added_lines(diff):
    return [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]


def analyze(pr, diff):
    risks, suggestions = [], []
    added = added_lines(diff)
    n_added = len(added)

    size = pr.get("additions", 0) + pr.get("deletions", 0)
    changed = pr.get("changed_files", 0)
    if size > 500 or changed > 20:
        risks.append(f"Large change: +{pr.get('additions')}/"
                     f"-{pr.get('deletions')} across {changed} files. "
                     "Higher chance of hidden defects; consider splitting.")
        suggestions.append("Split into smaller, focused PRs (<~400 lines) for easier review.")
    elif size == 0:
        risks.append("PR has no diff content (possibly docs-only or empty).")

    # Test coverage
    files = [f.get("filename", "") for f in pr.get("files", [])]
    has_tests = any(TEST_RE.search(f) for f in files)
    if not has_tests and size > 0:
        risks.append("No test files detected in the diff.")
        suggestions.append("Add unit/integration tests covering the new behavior.")
    else:
        suggestions.append("Tests present — good. Confirm they fail without the fix.")

    # Secrets
    secret_hits = set()
    for ln in added:
        s = SECRET_RE.search(ln)
        if s:
            secret_hits.add(s.group(0)[:12] + "…")
    if secret_hits:
        risks.append("Possible secret/credential committed: "
                     + ", ".join(sorted(secret_hits)))
        suggestions.append("Rotate the exposed secret and load it from env/secret manager.")

    # Dangerous patterns
    danger_hits = set(DANGER_RE.findall(" ".join(added)))
    if danger_hits:
        risks.append("Dangerous API usage detected (eval/exec/os.system/"
                     "shell=True/pickle.loads/yaml.load): "
                     + ", ".join(sorted(danger_hits)[:5]))
        suggestions.append("Avoid dynamic execution; use safe parsers and "
                           "subprocess without shell=True.")

    # SQL injection via string concatenation
    if SQLCONCAT_RE.search(" ".join(added)):
        risks.append("Possible SQL built via string concatenation/f-string "
                     "— injection risk.")
        suggestions.append("Use parameterized queries / an ORM.")

    # TODO/FIXME in added lines
    todos = len(TODO_RE.findall(diff))
    if todos:
        risks.append(f"{todos} TODO/FIXME/HACK marker(s) introduced in the diff.")
        suggestions.append("Resolve or track the TODOs before merge.")

    # Migrations / schema
    if any(MIGRATION_RE.search(f) for f in files):
        risks.append("Schema/migration file changed — verify backward compatibility "
                     "and a rollback path.")
        suggestions.append("Add a down-migration and test on a copy of production data.")

    # Dependencies
    if any(DEP_FILES.search(f) for f in files):
        risks.append("Dependency manifest changed — new/updated packages can "
                     "introduce CVEs or license issues.")
        suggestions.append("Pin versions and run `npm audit` / `pip-audit`.")

    # Breaking
    if BREAKING_RE.search(pr.get("title", "") + " " + (pr.get("body") or "")):
        risks.append("Title/body mentions a breaking or major change — confirm "
                     "consumers are notified.")
        suggestions.append("Document the migration path for breaking changes.")

    if not risks:
        risks.append("No high-signal risks detected by static heuristics.")

    # Confidence
    if size <= 60 and has_tests and not secret_hits and not danger_hits:
        confidence = "High"
    elif size > 800 or secret_hits or danger_hits:
        confidence = "Low"
    else:
        confidence = "Medium"

    return risks, suggestions, confidence


def render_markdown(pr, risks, suggestions, confidence):
    title = pr.get("title", "")
    num = pr.get("number")
    url = pr.get("html_url", "")
    merged = pr.get("merged_at")
    state = "merged" if merged else pr.get("state")
    lines = []
    lines.append(f"## Review: PR #{num} — {title}")
    lines.append("")
    lines.append(f"**Status:** {state} · **Diff:** "
                 f"+{pr.get('additions',0)}/-{pr.get('deletions',0)} · "
                 f"**Files:** {pr.get('changed_files',0)} · "
                 f"**Commits:** {pr.get('commits',0)}")
    lines.append("")
    # Summary (2–3 sentences)
    s = (f"This PR {pr.get('title','').strip().lower()} "
         f"and modifies {pr.get('changed_files',0)} file(s) "
         f"(+{pr.get('additions',0)}/-{pr.get('deletions',0)}). "
         f"Heuristic static analysis found {len(risks)} risk signal(s); "
         f"see details below. "
         f"This is an automated, rule-based review (no LLM), so it focuses on "
         f"structural and security patterns rather than semantics.")
    lines.append("### Summary")
    lines.append("")
    lines.append(s)
    lines.append("")
    lines.append("### Identified risks")
    lines.append("")
    for r in risks:
        lines.append(f"- {r}")
    lines.append("")
    lines.append("### Improvement suggestions")
    lines.append("")
    for s in suggestions:
        lines.append(f"- {s}")
    lines.append("")
    lines.append(f"### Confidence: **{confidence}**")
    lines.append("")
    lines.append(f"*Source: `claude-review` agent · {url}*")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr", help="PR URL or owner/repo#num or just the number")
    ap.add_argument("-r", "--repo", help="owner/repo (when --pr is just a number)")
    ap.add_argument("--token", default=os.environ.get("GITHUB_TOKEN")
                    or os.environ.get("GITHUB_PAT"))
    ap.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = ap.parse_args()

    owner, repo, num = parse_pr_ref(args.pr, args.repo)
    base = f"{API}/repos/{owner}/{repo}/pulls/{num}"
    pr = api_get(base, args.token)
    diff = api_get(base, args.token, as_json=False)
    # enrich with files
    pr["files"] = api_get(f"{base}/files?per_page=100", args.token)

    risks, suggestions, confidence = analyze(pr, diff)
    if args.format == "json":
        print(json.dumps({"risks": risks, "suggestions": suggestions,
                          "confidence": confidence, "pr": {
                              "number": pr.get("number"),
                              "title": pr.get("title"),
                              "additions": pr.get("additions"),
                              "deletions": pr.get("deletions"),
                              "changed_files": pr.get("changed_files")}}, indent=2))
    else:
        print(render_markdown(pr, risks, suggestions, confidence))


if __name__ == "__main__":
    main()
