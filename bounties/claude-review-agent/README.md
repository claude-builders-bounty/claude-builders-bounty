# Claude Code PR Review Agent

A Python-based PR review agent that analyzes GitHub pull request diffs and posts structured Markdown review comments.

## Quick Start

1. **Review any PR via URL:**
   ```bash
   python claude-review.py --pr https://github.com/owner/repo/pull/123
   ```

2. **Review by repo + number:**
   ```bash
   python claude-review.py --pr 123 --repo owner/repo
   ```

3. **Review a local diff:**
   ```bash
   python claude-review.py --diff /path/to/diff.patch
   ```

4. **Save output to file:**
   ```bash
   python claude-review.py --pr 123 --repo owner/repo -o review.md
   ```

## Output Format

The agent generates a structured Markdown review with:

- **Summary** — 2–3 sentences describing the PR scope
- **Identified Risks** — list of potential issues
- **Improvement Suggestions** — actionable recommendations
- **Confidence Score** — Low / Medium / High
- **File Summary Table** — per-file change stats

## GitHub Actions Integration

Copy `.github/workflows/claude-review.yml` to your repo to enable automatic PR reviews on every pull request.

## Sample Output

See `SAMPLE_REVIEW.md` for an example review of PR #2820.

## Requirements

- Python 3.8+
- Internet access to fetch PR diffs from GitHub API

## Claiming the Bounty

This submission addresses Issue #4 for the $150 Claude Code Agent bounty.
