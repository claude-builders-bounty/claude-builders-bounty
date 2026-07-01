# 🤖 claude-review

An AI-powered CLI tool that reviews GitHub Pull Requests and produces structured Markdown feedback.

**Part of the [Claude Builders Bounty](https://github.com/claude-builders-bounty/claude-builders-bounty) — \$150 bounty for PR review sub-agent** ([issue #4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4))

## Features

- 🔍 Fetches PR diff, metadata, and commits from GitHub
- 🤖 Analyzes code using DeepSeek (or any OpenAI-compatible API)
- 📋 Structured output: Summary + Risks + Suggestions + Confidence Score
- 🚀 Works as CLI or GitHub Action
- 📦 Zero dependencies (pure Python stdlib)

## Usage

### CLI

```bash
export GITHUB_TOKEN="ghp_..."
export DEEPSEEK_API_KEY="sk-..."

# Review a PR and print to stdout
python claude_review.py --pr https://github.com/owner/repo/pull/123

# Save to file
python claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

### GitHub Action

Add the workflow (`.github/workflows/claude-review.yml`) to your repo and set `DEEPSEEK_API_KEY` in repository secrets.

Then comment `/review` on any PR to trigger an automated review.

## Output Format

```markdown
## Summary
2-3 sentences describing what the PR does.

## Identified Risks
- Security: ...
- Performance: ...
- Maintainability: ...

## Improvement Suggestions
1. ...
2. ...

## Confidence Score: Medium
```

## Example Outputs

See the [`examples/`](./examples/) directory for sample reviews on real PRs.

## Requirements

- Python 3.10+
- `GITHUB_TOKEN` environment variable
- `DEEPSEEK_API_KEY` environment variable (or any OpenAI-compatible API)

## License

MIT
