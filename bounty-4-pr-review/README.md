# Bounty 4 — PR Reviewer with Structured Output

A CLI tool and GitHub Action that reviews pull requests and produces structured Markdown output with Summary, Risks, Suggestions, and Confidence level.

## Setup (3 steps)

1. Ensure `gh` CLI is installed and authenticated:
   ```bash
   gh auth login
   ```

2. Make the script executable:
   ```bash
   chmod +x claude-review.sh
   ```

3. (Optional) Copy `.github/workflows/pr-review.yml` to your repo for automatic reviews on every PR.

## Usage

```bash
# By URL
./claude-review.sh --pr https://github.com/owner/repo/pull/123

# By owner/repo#number
./claude-review.sh --pr owner/repo#123

# By number (uses current repo)
./claude-review.sh --pr 123

# Write to file
./claude-review.sh --pr 123 --output review.md
```

## What it checks

| Category | Pattern | Why |
|----------|---------|-----|
| **Security** | Hardcoded secrets (passwords, API keys, tokens) | Credentials in code get leaked via git history |
| **Security** | Dynamic code execution patterns | Code injection vector |
| **Security** | innerHTML assignment | XSS vulnerability |
| **Security** | Raw PHP superglobals without validation | Input injection |
| **Security** | SQL string interpolation | SQL injection |
| **Debug** | console.log/debug/warn/error | Noise in production |
| **Debug** | var_dump/print_r/dd | PHP debug output |
| **Quality** | TODO/FIXME/HACK/XXX markers | Unfinished work |
| **Quality** | Empty catch blocks | Silent error swallowing |
| **Testing** | Source changes without test file changes | Missing test coverage |
| **Size** | 500+ lines added | Hard to review thoroughly |

## How it works

1. Parses the PR reference (URL, `owner/repo#N`, or just `N`)
2. Fetches PR metadata, diff, and file list via `gh api`
3. Scans the diff line-by-line with regex pattern matching (only `+` lines — additions)
4. Tallies issues and determines confidence:
   - **High**: 0 issues, under 300 additions
   - **Medium**: 1-2 issues, or 300-1000 additions
   - **Low**: 3+ issues, or 1000+ additions
5. Outputs structured Markdown

## Output structure

```markdown
# PR Review: #123

**PR title**
Author: @user | Branch: `feature` -> `main` | Files: N | +X / -Y

---

## Summary
2-3 sentence overview of the PR scope and detected issues.

## Risks
- List of detected risks with severity indicators

## Suggestions
- Actionable suggestions for each risk

## Confidence
**High / Medium / Low**
Explanation of the confidence level.
```

## GitHub Action

The included workflow (`.github/workflows/pr-review.yml`) runs automatically on PR open/sync/reopen and posts the review as a PR comment.

To install: copy the workflow file to your repo's `.github/workflows/` directory. No secrets needed beyond the default `GITHUB_TOKEN`.

## Sample outputs

- [Sample 1](samples/sample-output-1.md) — PR with hardcoded secrets and missing tests (Medium confidence)
- [Sample 2](samples/sample-output-2.md) — Clean PR with no issues (High confidence)
