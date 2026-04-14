# claude-review — AI-Powered PR Review Agent

A Claude Code agent that reviews pull requests and posts structured review comments.

## Features

- **CLI tool**: Run `claude-review --pr <url>` to review any GitHub PR
- **GitHub Action**: Automatically reviews PRs when opened/updated
- **Structured output**: Summary, risks, suggestions, confidence score
- **Multiple models**: Supports any Claude model via `--model` flag

## CLI Usage

### Prerequisites
- `claude` CLI (from [Claude Code](https://docs.anthropic.com/en/docs/claude-code)) **OR** `ANTHROPIC_API_KEY` env var
- `gh` CLI (GitHub CLI, for authenticated API access)

### Install
```bash
# Copy the script
cp claude-review.sh /usr/local/bin/claude-review
chmod +x /usr/local/bin/claude-review
```

### Examples
```bash
# Review a PR (uses claude CLI)
claude-review --pr https://github.com/owner/repo/pull/123

# Use specific model
claude-review --pr https://github.com/owner/repo/pull/123 --model claude-3-5-sonnet

# Save review to file
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md

# Use API key directly (no claude CLI needed)
export ANTHROPIC_API_KEY=sk-ant-...
claude-review --pr https://github.com/owner/repo/pull/123
```

## GitHub Action

Add to your repo's `.github/workflows/pr-review.yml`:

1. Set `ANTHROPIC_API_KEY` in your repo's Secrets
2. The action will automatically review new PRs

### Configuration
- Edit the model in the workflow file (default: `claude-sonnet-4-20250514`)
- Triggers on `pull_request` opened and synchronize events

## Output Format

```
## Summary
(2-3 sentences describing the PR)

## Risks
- Potential SQL injection in user query parameter
- Race condition in concurrent file writes

## Improvement Suggestions
- Add input validation for the email field
- Consider using a connection pool for database access
- Extract magic numbers to named constants

## Confidence Score
Medium

## Details
(Detailed analysis with file and line references)
```

## Sample Output

Tested on real PRs:

### PR: arakoodev/EdgeChains#449 (AWS Comprehend PII)
```
## Summary
This PR adds AWS Comprehend as a utility for PII redaction in the EdgeChains JS SDK.
It implements detectEntities, detectPiiEntities, and redactText methods.

## Risks
- AWS credentials must be properly configured; missing credentials will throw at runtime
- Large text inputs may exceed Comprehend API limits (batchSize handling needed)

## Improvement Suggestions
- Add retry logic for AWS API throttling
- Consider caching Comprehend results for repeated inputs
- Add unit tests with mocked AWS responses

## Confidence Score
Medium

## Details
The implementation follows the existing utility pattern in EdgeChains...
```

## How It Works

1. **Fetches PR diff** via `gh` CLI or GitHub API
2. **Fetches PR metadata** (title, author, stats)
3. **Sends to Claude** with a structured prompt
4. **Outputs** the review in Markdown format

## License
MIT
