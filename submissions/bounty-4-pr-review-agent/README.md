# Claude Code PR Review Agent

🤖 A Claude Code sub-agent that reviews GitHub PRs and posts structured comments.

## Features

- 🔍 Analyzes PR diffs using Claude AI
- 📝 Generates structured Markdown reviews
- 💬 Posts reviews as GitHub comments
- 🖥️ CLI and GitHub Action support
- 🎯 Confidence scoring (Low/Medium/High)

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd claude-pr-review

# Install dependencies
npm install

# Build
npm run build
```

## Configuration

Set environment variables:

```bash
export GITHUB_TOKEN=your_github_token
export ANTHROPIC_API_KEY=your_anthropic_api_key
```

## CLI Usage

```bash
# Review a PR (console output)
npx claude-review --pr https://github.com/owner/repo/pull/123

# Review and post comment to GitHub
npx claude-review --pr https://github.com/owner/repo/pull/123 --post-comment

# Output as markdown
npx claude-review --pr https://github.com/owner/repo/pull/123 --output markdown
```

## GitHub Action Usage

Add to your workflow:

```yaml
name: PR Review
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
      - uses: your-org/claude-pr-review@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Review Output Format

Reviews include:

### Summary
2-3 sentence overview of the changes

### Identified Risks
- ⚠️ Potential issues or concerns

### Improvement Suggestions
- 💡 Recommendations for improvement

### Confidence Score
🟢 High / 🟡 Medium / 🔴 Low

## Example Output

```
════════════════════════════════════════════════════════════
  CLAUDE CODE PR REVIEW
════════════════════════════════════════════════════════════

📝 SUMMARY
This PR adds user authentication with JWT tokens and 
implements rate limiting on the login endpoint.

⚠️  RISKS
  • JWT secret is hardcoded in config
  • Rate limiting might be too aggressive for mobile users

💡 SUGGESTIONS
  • Move JWT secret to environment variable
  • Consider adding rate limit exemptions for internal IPs

🎯 CONFIDENCE: High
════════════════════════════════════════════════════════════
```

## Testing

Tested on real GitHub PRs:

1. [Example PR #1 - Feature Addition](examples/example1.md)
2. [Example PR #2 - Bug Fix](examples/example2.md)

## License

MIT
