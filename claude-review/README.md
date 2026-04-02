# Claude Review 🤖

An AI-powered PR review agent that analyzes pull requests and provides structured review comments using Claude.

## Features

- **CLI Tool**: Review any GitHub PR from the command line
- **GitHub Action**: Automatically reviews PRs on open, sync, or reopen
- **Structured Output**: 
  - Summary of changes (2-3 sentences)
  - Identified risks (list)
  - Improvement suggestions (list)
  - Confidence score: Low / Medium / High

## Prerequisites

- Node.js 18+ 
- [Anthropic API Key](https://console.anthropic.com/) (for Claude access)
- GitHub Personal Access Token (for posting comments)

## Installation

### CLI Installation

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty/claude-review
npm install
npm run build
```

Or use directly with npx:

```bash
npx --yes @claude-builders-bounty/claude-review --pr https://github.com/owner/repo/pull/123
```

### Add to PATH

```bash
export PATH="$PATH:/path/to/claude-review/bin"
# Add to ~/.bashrc or ~/.zshrc for permanence
```

## Usage

### CLI

```bash
# Review a PR and print to stdout
claude-review --pr https://github.com/owner/repo/pull/123

# Review and post as PR comment
claude-review --pr https://github.com/owner/repo/pull/123 --post

# With explicit token
claude-review --pr https://github.com/owner/repo/pull/123 --post --token ghp_xxx
```

### Environment Variables

```bash
export ANTHROPIC_API_KEY="sk-ant-..."   # Required - Claude API key
export GITHUB_TOKEN="ghp_..."          # Optional - for posting comments
```

### GitHub Action

Add to your repository as `.github/workflows/claude-review.yml`:

```yaml
name: Claude PR Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '22'

      - name: Install claude-review
        run: |
          git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
          cd claude-builders-bounty/claude-review
          npm install
          npm run build

      - name: Run Review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          cd claude-review
          node dist/index.js --pr "${{ github.event.pull_request.html_url }}" --post
```

Set `ANTHROPIC_API_KEY` in your repository's GitHub Secrets.

## Output Format

The review produces structured Markdown:

```markdown
## 🔍 Claude PR Review

**PR:** #123 **Feature: Add new login flow**
**Author:** @octocat
**Files:** 5 | **+234** / **-89**

---

### Summary
This PR introduces a new OAuth2-based authentication system that replaces the legacy session-based login. It maintains backward compatibility while adding support for SSO providers.

### Identified Risks
- Token refresh logic may cause race conditions under heavy load
- No rate limiting on authentication endpoints
- Session storage schema change requires migration

### Improvement Suggestions
- Add unit tests for the OAuth2 callback handler
- Consider implementing token rotation for enhanced security
- Add logging for failed authentication attempts

### Confidence Score
🟡 Medium

---

*Reviewed by [Claude](https://claude.ai) via claude-review*
```

## Example Reviews

See the [`samples/`](samples/) directory for example reviews on real PRs.

## License

MIT
