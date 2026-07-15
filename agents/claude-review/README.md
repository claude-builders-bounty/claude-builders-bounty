# claude-review — Claude Code PR Review Agent

CLI tool that reviews GitHub PRs and returns structured Markdown.

## Usage

```bash
./claude-review.py --pr https://github.com/owner/repo/pull/123
```

## Output Format

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score (Low/Medium/High)

## Dependencies

- Python 3.8+
- GitHub token in keychain or `GH_TOKEN` env var
