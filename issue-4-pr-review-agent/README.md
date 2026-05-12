# PR Review Agent

A CLI tool that fetches a GitHub PR diff, performs static analysis, and outputs a structured Markdown review.

## Setup

**Prerequisites:** Python 3.10+ and [GitHub CLI](https://cli.github.com/) (`gh`)

```bash
# Authenticate with GitHub CLI
gh auth login

# No additional dependencies required — pure Python stdlib
```

## Usage

```bash
# Review a PR by URL
python review.py --pr https://github.com/owner/repo/pull/123

# Review using shorthand notation
python review.py --pr owner/repo/123

# Review a local diff file
python review.py --diff path/to/changes.diff

# Save output to file
python review.py --pr owner/repo/123 -o review.md

# Output as JSON (for programmatic use)
python review.py --pr owner/repo/123 --json
```

## Output Format

The review produces structured Markdown with:

- **Summary** — 2-3 sentence overview of the PR
- **Identified Risks** — security, quality, and performance findings
- **Improvement Suggestions** — actionable recommendations
- **Confidence Score** — Low / Medium / High based on findings and diff size

## What It Checks

| Category     | Checks                                                    |
|-------------|-----------------------------------------------------------|
| Security    | Hardcoded secrets, eval/exec, SQL injection, SSL bypass   |
| Quality     | Bare excepts, debug prints, TODOs, deprecated APIs        |
| Performance | SELECT *, long sleeps, inefficient loops                  |
| Config      | Debug mode, hardcoded localhost                           |

## Example Output

```markdown
## PR Review

### Summary

This PR modifies 3 file(s) with +45/-12 lines changed. Found 2 minor issue(s) — overall low risk.

**Files changed:** 3 | **Additions:** +45 | **Deletions:** -12

### Identified Risks

- **Medium**: 1 medium-severity issue(s) — consider addressing
  - [src/api.py:42] Bare except clause — catches all exceptions including KeyboardInterrupt

### Improvement Suggestions

- No test files changed — consider adding tests for the modified code.

### Confidence: High
```

## How It Works

1. Fetches PR diff and metadata via `gh` CLI
2. Parses the unified diff to track files and line numbers
3. Matches added lines against a set of regex patterns for common issues
4. Aggregates findings by severity and category
5. Generates structured Markdown review

## License

MIT
