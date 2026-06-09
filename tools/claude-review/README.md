# claude-review

AI-powered GitHub PR reviewer. Fetches a pull request's diff, performs heuristic static analysis,
and outputs a structured Markdown review comment.

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
- A GitHub personal access token (read:repo scope) — optional but recommended to avoid rate limits

## Installation

```bash
git clone https://github.com/MAWXHUB/claude-review.git
cd claude-review
# No pip install needed — uses stdlib only
```

## Usage

```bash
# Basic usage
python3 claude_review.py --pr https://github.com/owner/repo/pull/42

# With GitHub token (avoids 60 req/h rate limit)
python3 claude_review.py --pr https://github.com/owner/repo/pull/42 --token ghp_xxx

# Via environment variable
export GITHUB_TOKEN=ghp_xxx
python3 claude_review.py --pr https://github.com/owner/repo/pull/42

# Write to file
python3 claude_review.py --pr https://github.com/owner/repo/pull/42 --output review.md

# JSON output (for programmatic use)
python3 claude_review.py --pr https://github.com/owner/repo/pull/42 --json
```

## Output Format

```markdown
## 🤖 Automated PR Review — [owner/repo#42](...)
**Author:** @user · **feature-branch** → **main** · *Generated: 2026-01-01 00:00 UTC*

### Summary
2–3 sentence plain-English summary of the changes.

### Stats
| Files changed | Additions | Deletions | File types |
...

### ⚠️ Identified Risks
- 🔴 [HIGH] `src/auth.py` — Possible hardcoded credential or secret
- 🟡 [MEDIUM] `app.js` — Empty .catch() silences all Promise errors
- 🔵 [LOW] `utils.py` — Debug print() left in code

### ✅ Positive Signals
- ✔ Tests present
- ✔ Type annotations used

### 💡 Improvement Suggestions
- Add unit tests for the new functionality
- Consider adding type annotations for better IDE support

### Confidence Score: High / Medium / Low
```

## Sample Outputs

See [`sample_review_1.md`](./sample_review_1.md) (tested on `promptpolish-ai/git-context#42`)
and [`sample_review_2.md`](./sample_review_2.md) (tested on `pallets/flask#6043`).

## GitHub Action

```yaml
# .github/workflows/pr-review.yml
name: AI PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - name: Run claude-review
        id: review
        run: |
          git clone https://github.com/MAWXHUB/claude-review.git /tmp/claude-review
          python3 /tmp/claude-review/claude_review.py \
            --pr "${{ github.event.pull_request.html_url }}" \
            --token "${{ secrets.GITHUB_TOKEN }}" \
            --output /tmp/review.md

      - name: Post review comment
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const body = fs.readFileSync('/tmp/review.md', 'utf8');
            github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body
            });
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
