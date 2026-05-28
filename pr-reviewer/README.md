# Claude Code PR Reviewer Agent

CLI tool and GitHub Action that reviews PRs and posts structured Markdown comments.

## Features

- **CLI tool**: Review any PR from the command line
- **GitHub Action**: Automatic reviews on PR open/update
- **Structured output**: Summary, risks, suggestions, confidence score
- **Risk detection**: Credentials, code injection, TODO comments
- **Smart suggestions**: Missing tests, type hints, large PRs

## Installation

```bash
# Clone the repo
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty

# Set your GitHub token
export GITHUB_TOKEN=ghp_your_token_here
```

## CLI Usage

```bash
# Review a PR (prints to stdout)
python pr-reviewer/claude-review.py --pr https://github.com/owner/repo/pull/123

# Review and post as comment
python pr-reviewer/claude-review.py --pr https://github.com/owner/repo/pull/123 --post

# Save review to file
python pr-reviewer/claude-review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

## GitHub Action

Add to `.github/workflows/pr-review.yml`:

```yaml
name: PR Review

on:
  pull_request:
    types: [opened, synchronize]

permissions:
  contents: read
  pull-requests: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Run PR Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python pr-reviewer/claude-review.py \
            --pr "${{ github.event.pull_request.html_url }}" \
            --post
```

## Output Format

```markdown
## 🤖 PR Review

### Summary
PR modifies 3 file(s) with 45 additions and 12 deletions. Changes involve Python code.

### Risks
- ⚠️ TODO/FIXME/HACK comments found — unfinished work

### Suggestions
- 📝 Consider adding tests for the changes
- 📝 Consider adding type hints to Python code

### Confidence: Medium
```

## Risk Detection

| Pattern | Risk |
|---------|------|
| `eval()` / `exec()` | Code injection |
| `subprocess` + `shell=True` | Command injection |
| Hardcoded passwords/secrets | Credential exposure |
| TODO/FIXME/HACK | Unfinished work |
| `print()` without logging | Debug statements |
| Large deletions | Potential regression |

## Sample Outputs

See [samples/](samples/) directory for reviews of real PRs.

## Requirements

- Python 3.10+
- GitHub token with `repo` scope (for posting comments)
- `curl` (for API calls)

## License

MIT
