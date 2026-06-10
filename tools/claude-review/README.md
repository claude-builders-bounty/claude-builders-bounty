# claude-review

GitHub PR reviewer for structured Markdown review comments. It fetches a pull request's diff, performs heuristic static analysis, and produces a review summary with risks, positive signals, suggestions, and confidence.

## Features

- Zero external dependencies (pure Python 3.8+ stdlib)
- Detects 15+ risk patterns (hardcoded secrets, eval, shell injection, bare except, XSS, etc.)
- Identifies positive signals (tests, type annotations, logging, error handling)
- Generates improvement suggestions
- Confidence score: **High / Medium / Low**
- Works as CLI or importable module
- Optional `--json` output for programmatic use
- Optional `--output` flag to write to file

## Requirements

- Python 3.8+
- Optional `GITHUB_TOKEN` environment variable for private repositories or higher GitHub API limits

## Installation

The tool is included in this repository under `tools/claude-review` and uses only the Python standard library.

## Usage

```bash
# Basic usage
python3 tools/claude-review/claude_review.py --pr https://github.com/owner/repo/pull/42

# With GitHub token via environment variable
export GITHUB_TOKEN=your-token-here
python3 tools/claude-review/claude_review.py --pr https://github.com/owner/repo/pull/42

# Write to file
python3 tools/claude-review/claude_review.py --pr https://github.com/owner/repo/pull/42 --output review.md

# JSON output (for programmatic use)
python3 tools/claude-review/claude_review.py --pr https://github.com/owner/repo/pull/42 --json
```

## Output Format

```markdown
## Automated PR Review — [owner/repo#42](...)
**Author:** @user · **feature-branch** → **main** · *Generated: 2026-01-01 00:00 UTC*

### Summary
2-3 sentence plain-English summary of the changes.

### Stats
| Files changed | Additions | Deletions | File types |
...

### Identified Risks
- [HIGH] `src/auth.py` — Possible hardcoded credential or secret
- [MEDIUM] `app.js` — Empty .catch() silences all Promise errors
- [LOW] `utils.py` — Debug print() left in code

### Positive Signals
- Tests present
- Type annotations used

### Improvement Suggestions
- Add unit tests for the new functionality
- Consider adding type annotations for better IDE support

### Confidence Score: High / Medium / Low
```

## Sample Outputs

See [`sample_review_1.md`](./sample_review_1.md) (tested on `promptpolish-ai/git-context#42`) and [`sample_review_2.md`](./sample_review_2.md) (tested on `pallets/flask#6043`).

## GitHub Action

```yaml
name: Structured PR Review
on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read

    steps:
      - uses: actions/checkout@v4

      - name: Run claude-review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python3 tools/claude-review/claude_review.py \
            --pr "${{ github.event.pull_request.html_url }}" \
            --output /tmp/review.md

      - name: Post or update review comment
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const marker = '<!-- structured-pr-review -->';
            const body = `${marker}\n${fs.readFileSync('/tmp/review.md', 'utf8')}`;
            const comments = await github.paginate(github.rest.issues.listComments, {
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              per_page: 100,
            });
            const existing = comments.find((comment) =>
              comment.user?.type === 'Bot' && comment.body?.includes(marker)
            );
            if (existing) {
              await github.rest.issues.updateComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                comment_id: existing.id,
                body,
              });
            } else {
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.issue.number,
                body,
              });
            }
```

## Risk Patterns Detected

| Pattern | Severity |
|---------|----------|
| Hardcoded credentials/secrets | HIGH |
| `eval()` usage | HIGH |
| `subprocess` with `shell=True` | HIGH |
| `pickle.loads()` | HIGH |
| `exec()` | HIGH |
| `dangerouslySetInnerHTML` | MEDIUM |
| `.innerHTML =` / `document.write()` | MEDIUM |
| Bare `except:` | MEDIUM |
| Empty `.catch()` | MEDIUM |
| `os.system()` | MEDIUM |
| Debugger breakpoints | MEDIUM |
| TODO/FIXME/HACK | LOW |
| `console.log` / debug `print()` | LOW |
| `SELECT *` | LOW |
| Long `sleep()` | LOW |

## License

MIT
