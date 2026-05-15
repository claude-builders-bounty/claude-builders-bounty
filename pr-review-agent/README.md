
# Claude PR Review Agent

`claude-review` — CLI tool that reviews a GitHub PR and produces a structured Markdown (or JSON) report.

## Installation

```bash
pip install requests
python claude-review.py --pr https://github.com/owner/repo/pull/123
```

No Claude API key needed — uses rule-based analysis of PR metadata and file changes.

## Usage

```bash
# Basic: Markdown output to stdout
python claude-review.py --pr https://github.com/vercel/next.js/pull/70000

# With auth (for private repos or higher rate limits)
python claude-review.py --pr https://github.com/owner/repo/pull/123 --token ghp_xxx

# JSON output (for programmatic use)
python claude-review.py --pr https://github.com/owner/repo/pull/123 --json

# Save to file
python claude-review.py --pr https://github.com/owner/repo/pull/123 -o review.md
```

## Output Format

The review includes:

- **Summary** — 2-3 sentence overview of the PR
- **Statistics** — files changed, additions, deletions table
- **Identified Risks** — list of potential issues (large PR, security files, migrations, etc.)
- **Improvement Suggestions** — actionable recommendations (add tests, verify deps, etc.)
- **Confidence Score** — Low / Medium / High
- **Files Changed** — full list of modified files

## Testing

```bash
# Test 1: Real PR (public repo)
python claude-review.py --pr https://github.com/vercel/next.js/pull/70000 -o sample-1.md

# Test 2: Another real PR
python claude-review.py --pr https://github.com/facebook/react/pull/30000 -o sample-2.md

# Test 3: JSON output
python claude-review.py --pr https://github.com/vercel/next.js/pull/70000 --json -o sample-3.json
```

## Sample Outputs

See `sample-1.md` and `sample-2.md` for real PR review outputs.

## File Structure

```
pr-review-agent/
├── README.md
├── claude-review.py
├── sample-1.md
└── sample-2.md
```

## Requirements

- Python 3.8+
- `requests` (`pip install requests`)
- GitHub token (optional, for higher rate limits)
