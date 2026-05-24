# claude-review — PR Review Agent

Analyse any GitHub PR diff and get a structured Markdown review with risks, suggestions, and confidence scoring.

## Features

- **Zero external deps** — uses `gh` CLI, no API keys needed
- **Structured review** — summary, risks, suggestions, file breakdown
- **Secret detection** — hardcoded API keys, tokens, passwords
- **Code quality checks** — `eval()`, `exec()`, SQL injection patterns, bare excepts
- **GitHub Action** — auto-reviews every PR as a comment
- **Deterministic** — same diff always produces the same review

## Usage

### CLI

```bash
# By URL
python claude-review.py --pr https://github.com/owner/repo/pull/123

# By shorthand
python claude-review.py --pr owner/repo/123

# From repo root, by number
python claude-review.py --pr 123

# Post the review as a PR comment
python claude-review.py --pr 123 --post

# Save to file
python claude-review.py --pr 123 --output review.md
```

### GitHub Action

Copy `.github/workflows/claude-review.yml` to your project's `.github/workflows/` directory. It automatically posts a review comment on every PR.

## Output

The tool produces a structured Markdown report with these sections:

- **Summary** — 2–3 sentence overview of what the PR does
- **Overview** — file count, additions/deletions, issue count, confidence
- **Identified Risks** — high-severity issues (secrets, dangerous APIs)
- **Improvement Suggestions** — medium-severity issues (code quality)
- **Files Changed** — per-file breakdown
- **Confidence** — Low / Medium / High based on analysis depth

## Sample Outputs

Tested on real PRs:

| PR | Result |
|----|--------|
| [PR #2028](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2028) | [sample-output-2028.md](sample-output-2028.md) |
| [PR #2029](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2029) | [sample-output-2029.md](sample-output-2029.md) |

## Requirements

- Python 3.8+
- `gh` CLI authenticated (`gh auth status`)
