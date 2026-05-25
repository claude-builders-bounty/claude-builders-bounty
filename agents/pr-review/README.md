# PR Review Agent 🤖

A structured PR review agent that analyzes GitHub Pull Requests and produces a formatted Markdown review with risks, suggestions, and confidence scoring.

## Features

- **CLI mode**: `./review.py --pr https://github.com/owner/repo/pull/123`
- **GitHub Action**: One-click PR review automation via workflow
- **Structured Output**:
  - 📋 Summary of changes (2–3 sentences)
  - ⚠️ Identified risks (hardcoded secrets, SQL injection, dangerous functions, etc.)
  - ✅ Positive highlights
  - 💡 Improvement suggestions (type hints, list comprehensions, naming, etc.)
  - 🔢 Confidence score (Low / Medium / High)

## Quick Start

### CLI

```bash
# Install dependencies (none — pure Python 3.10+ stdlib)
chmod +x agents/pr-review/review.py

# Review any public GitHub PR
python agents/pr-review/review.py --pr https://github.com/psf/requests/pull/6789

# Review a PR in the local repository
python agents/pr-review/review.py --local 42

# Save output to a file
python agents/pr-review/review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

### GitHub Action

Add to `.github/workflows/pr-review.yml`:

```yaml
name: PR Review Agent
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run PR Review
        uses: ./agents/pr-review
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

Then reference the action as a local action in your repository, or copy the `agents/pr-review/` directory into your own repo.

## How It Works

1. Fetches the PR diff via `gh` CLI or raw GitHub URL
2. Parses per-file changes with pattern-based analysis:
   - **Security patterns**: hardcoded secrets, SQL injection, dangerous functions
   - **Code quality**: bare except clauses, debug prints, TODO markers
   - **Best practices**: type hints, list comprehensions, magic numbers
3. Generates structured Markdown with findings grouped by severity
4. Outputs to stdout or a file (ready to post as a PR comment)

## Sample Output

See the [examples](./examples/) directory for real PR reviews:

- [CPython PR #128934](./examples/cpython-128934.md)
- [FastAPI PR #13456](./examples/fastapi-13456.md)

## Tested On

- [psf/requests #6789](https://github.com/psf/requests/pull/6789)
- [fastapi/fastapi #13456](https://github.com/fastapi/fastapi/pull/13456)

## Requirements

- Python 3.10+
- `gh` CLI (optional — falls back to raw HTTP)
- No third-party Python packages
