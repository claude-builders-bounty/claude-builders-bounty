# Claude Review

> 🤖 Claude Code sub-agent that reviews GitHub PRs and posts structured comments

[![npm version](https://badge.fury.io/js/claude-review.svg)](https://badge.fury.io/js/claude-review)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

`claude-review` is a CLI tool that leverages Claude AI to automatically review GitHub Pull Requests and generate structured, actionable feedback.

## Features

- ✅ **CLI-based**: Simple command-line interface
- ✅ **Structured Output**: Summary, Risks, Suggestions, and Confidence Score
- ✅ **Multiple Formats**: Console, Markdown, or JSON output
- ✅ **File Export**: Save reviews to files
- ✅ **Claude Sonnet 4**: Powered by the latest Claude model

## Installation

### Prerequisites

- Node.js 18.0.0 or higher
- GitHub Personal Access Token
- Anthropic API Key

### Setup

```bash
# Clone the repository
git clone https://github.com/claude-builders-bounty/claude-review.git
cd claude-review

# Install dependencies
npm install

# Build the project
npm run build

# Create .env file with your credentials
cat > .env << EOF
GITHUB_TOKEN=your_github_token_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
EOF
```

### Getting Credentials

1. **GitHub Token**: 
   - Go to https://github.com/settings/tokens
   - Create a token with `repo` scope
   - Copy the token

2. **Anthropic API Key**:
   - Go to https://console.anthropic.com/
   - Create an API key
   - Copy the key

## Usage

### Basic Usage

```bash
# Review a PR
npm start -- --pr https://github.com/owner/repo/pull/123

# Or after building
./dist/cli.js --pr https://github.com/owner/repo/pull/123
```

### Output Formats

```bash
# Console output (default)
claude-review --pr https://github.com/owner/repo/pull/123

# Markdown output
claude-review --pr https://github.com/owner/repo/pull/123 --output markdown

# JSON output
claude-review --pr https://github.com/owner/repo/pull/123 --output json
```

### Save to File

```bash
# Save review to file
claude-review --pr https://github.com/owner/repo/pull/123 --output markdown --file review.md
```

### Verbose Mode

```bash
# Show detailed progress
claude-review --pr https://github.com/owner/repo/pull/123 --verbose
```

## Output Structure

The tool generates a structured review with:

### 📋 Summary
2-3 sentences describing what the PR does and why.

### ⚠️ Identified Risks
List of potential issues:
- Security concerns
- Potential bugs
- Breaking changes
- Performance issues

### 💡 Improvement Suggestions
Recommendations for:
- Code quality improvements
- Maintainability
- Testing
- Documentation

### Confidence Score
- **Low**: Limited information or high uncertainty
- **Medium**: Moderate certainty with some assumptions
- **High**: Clear understanding with concrete findings

## Sample Outputs

See the `sample-outputs/` directory for examples of real PR reviews.

### Example Output

```markdown
## 🤖 Claude Code Review

> **PR**: #123 - Add user authentication
> **Author**: @developer
> **Branch**: `feature/auth` → `main`

### 📋 Summary

This PR implements JWT-based user authentication with login, registration, and token refresh endpoints. The implementation includes password hashing, session management, and basic rate limiting.

### ⚠️ Identified Risks

- **Security**: JWT secret is hardcoded in config (should use environment variable)
- **Missing validation**: No email format validation on registration
- **Rate limiting**: Only applied to login, not registration

### 💡 Improvement Suggestions

- Move JWT_SECRET to environment variables
- Add email validation using a library like `validator.js`
- Apply rate limiting to registration endpoint to prevent spam
- Add unit tests for auth middleware

### ✅ Confidence: High
```

## GitHub Action Integration

You can use this tool in a GitHub Action:

```yaml
name: Claude PR Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - run: npm install
      
      - name: Run Claude Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          npm run build
          ./dist/cli.js --pr ${{ github.event.pull_request.html_url }} --output markdown --file review.md
      
      - name: Post Review Comment
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const review = fs.readFileSync('review.md', 'utf8');
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: review
            });
```

## Development

### Build

```bash
npm run build
```

### Test

```bash
npm test
```

## API Reference

### CLI Options

| Option | Description | Required |
|--------|-------------|----------|
| `-p, --pr <url>` | GitHub PR URL to review | Yes |
| `-o, --output <format>` | Output format (markdown, json, console) | No (default: console) |
| `-f, --file <path>` | Save output to file | No |
| `-v, --verbose` | Show verbose output | No |

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | Yes |
| `ANTHROPIC_API_KEY` | Anthropic API Key | Yes |

## Architecture

```
claude-review/
├── src/
│   ├── cli.ts          # CLI entry point
│   ├── github.ts       # GitHub API client
│   ├── reviewer.ts     # Claude AI integration
│   └── formatter.ts    # Output formatting
├── dist/               # Compiled JavaScript
├── sample-outputs/     # Example reviews
├── package.json
├── tsconfig.json
└── README.md
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Claude AI](https://www.anthropic.com/claude)
- Powered by [Anthropic SDK](https://github.com/anthropics/anthropic-sdk-typescript)
- GitHub API via [Octokit](https://github.com/octokit/octokit.js)

---

**Bounty**: This project was created for the [Claude Builders Bounty](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4) - $150
