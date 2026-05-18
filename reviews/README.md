# Claude PR Reviewer

Generate a structured Markdown review for a public GitHub pull request.

## Setup

```bash
python claude-review.py --pr https://github.com/owner/repo/pull/123
```

## Output

The CLI prints:

- a 2-3 sentence summary of the change surface
- identified risks
- improvement suggestions
- a confidence score: Low, Medium, or High

For Claude Code usage, use `agents/pr-reviewer.md` as the sub-agent instruction file and feed it the CLI output or the original PR URL.

## Examples

```bash
python claude-review.py --pr https://github.com/Scottcjn/Rustchain/pull/5654
python claude-review.py --pr https://github.com/Scottcjn/Rustchain/pull/5652
```

Sample outputs are included in:

- `reviews/sample-rustchain-5654.md`
- `reviews/sample-rustchain-5652.md`
