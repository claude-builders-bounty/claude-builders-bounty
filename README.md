# claude-review

A Claude Code sub-agent that reviews GitHub pull requests and posts structured comments.

## Usage

### CLI

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export GITHUB_TOKEN="ghp_..."  # optional, needed for private repos

python claude_review.py https://github.com/owner/repo/pull/123
# or via the wrapper script
./claude-review https://github.com/owner/repo/pull/123
```

Output to a file:

```bash
python claude_review.py https://github.com/owner/repo/pull/123 -o review.md
```

### GitHub Action

Add `.github/workflows/review.yml` to your repo (included in this repo) and set the `ANTHROPIC_API_KEY` secret.

## Output

The agent produces a structured Markdown review with:

- **Summary** — 2-3 sentence overview of the changes
- **Identified Risks** — potential bugs, regressions, or security concerns
- **Improvement Suggestions** — actionable recommendations
- **Confidence Score** — Low / Medium / High with justification

## Requirements

- Python 3.8+
- Anthropic API key ([get one here](https://console.anthropic.com/))
