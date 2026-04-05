# claude-review — AI PR Review Agent

CLI tool that fetches a GitHub PR diff and uses Claude to produce a structured Markdown review with summary, risks, suggestions, and confidence score.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key"
```

Requires the [GitHub CLI (`gh`)](https://cli.github.com/) authenticated.

## Usage

```bash
python3 claude_review.py --pr https://github.com/owner/repo/pull/123
```

### Output

Structured Markdown with:
- **Summary** — 2-3 sentence overview of the PR
- **Risks** — identified issues or concerns
- **Suggestions** — improvement recommendations
- **Confidence** — Low / Medium / High with justification

### Example

```bash
python3 claude_review.py --pr https://github.com/owner/repo/pull/42 > review.md
```

## Configuration

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| Model | `claude-3-5-haiku-20241022` (hardcoded for cost efficiency) |

## Sample Outputs

See [sample-review-1.md](sample-review-1.md) and [sample-review-2.md](sample-review-2.md) for real PR reviews.
