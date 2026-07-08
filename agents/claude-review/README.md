# claude-review

Claude Code sub-agent that reviews PRs and posts structured Markdown comments.

## Usage
```bash
claude-review --pr https://github.com/owner/repo/pull/123 --github-token ghp_xxx
```

## Output
Structured review with: summary, checklist, file stats.