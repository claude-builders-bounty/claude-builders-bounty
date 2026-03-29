# PR Reviewer Agent

Automated PR review agent using Claude Code that analyzes pull requests and posts structured Markdown reviews.

## Features

✅ **CLI Tool**: `claude-review --pr <URL>`  
✅ **GitHub Action**: Automated reviews on every PR  
✅ **Structured Output**: Summary, risks, suggestions, confidence score  
✅ **Tested**: Sample outputs included  

## Quick Start

### Option 1: CLI

```bash
# Install
curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/pr-reviewer-agent/claude-review
chmod +x claude-review

# Review a PR
./claude-review --pr https://github.com/owner/repo/pull/123
```

### Option 2: GitHub Action

Add `.github/workflows/pr-review.yml` to your repo:

```yaml
name: Automated PR Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Claude Review
        uses: claude-builders-bounty/pr-reviewer-agent@main
        with:
          pr_url: ${{ github.event.pull_request.html_url }}
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Usage

```bash
claude-review --pr <GITHUB_PR_URL> [--output <FILE>]

Arguments:
  --pr     GitHub PR URL (required)
  --output Output file (default: auto-generated in .claude-reviews/)

Environment:
  CLAUDE_BIN   Path to Claude Code binary (default: claude)
  OUTPUT_DIR   Directory for review outputs (default: .claude-reviews)
  ANTHROPIC_API_KEY  Claude API key (required)
```

## Output Format

```markdown
## Summary
2-3 sentences describing what this PR does and its overall impact.

## Changes Overview
- Added new authentication middleware
- Updated user model schema
- Fixed typo in README

## Identified Risks
- Missing input validation on line 42
- Potential SQL injection in query builder (lines 78-82)
- No error handling for API timeout

## Improvement Suggestions
- Add unit tests for new middleware
- Consider using parameterized queries
- Document the new API endpoints

## Confidence Score
**Medium** - Good implementation but needs test coverage
```

## Requirements

- GitHub CLI (`gh`) - auto-installed if missing
- Claude Code CLI or Oracle CLI
- Anthropic API key

## Sample Reviews

### Example 1: Feature Addition
**PR:** Add user authentication  
**Confidence:** High  

```markdown
## Summary
This PR introduces JWT-based authentication for the API, including middleware for route protection and token refresh logic.

## Changes Overview
- Added auth middleware (middleware/auth.js)
- Implemented JWT token generation and validation
- Created /auth/login and /auth/refresh endpoints

## Identified Risks
- Token secret is hardcoded in config.js (line 12) - should use environment variable
- No rate limiting on /auth/login endpoint - vulnerable to brute force
- Refresh tokens don't expire - security concern

## Improvement Suggestions
- Move JWT_SECRET to .env file
- Add rate limiting with express-rate-limit
- Implement refresh token rotation
- Add integration tests for auth flow

## Confidence Score
**High** - Well-structured implementation, risks are addressable with minor changes
```

### Example 2: Bug Fix
**PR:** Fix memory leak in WebSocket handler  
**Confidence:** Medium  

```markdown
## Summary
Fixes a memory leak caused by orphaned WebSocket event listeners by properly cleaning up listeners on connection close.

## Changes Overview
- Added cleanup logic in WebSocket close handler
- Refactored event listener registration
- Updated connection pool management

## Identified Risks
- Fix addresses symptoms but root cause (circular references) remains
- No test coverage for the fix
- Changes affect hot path (performance concern)

## Improvement Suggestions
- Use WeakMap for connection references to break circular deps
- Add memory profiling tests to CI
- Benchmark WebSocket throughput before/after
- Consider using ws library's built-in cleanup

## Confidence Score
**Medium** - Fix is directionally correct but needs performance validation
```

## Configuration

Create `~/.claude-review.yml`:

```yaml
severity_levels:
  critical: ["security", "data-loss"]
  high: ["performance", "breaking-change"]
  medium: ["style", "documentation"]
  low: ["typo", "formatting"]

auto_post_comment: true
confidence_threshold: "medium"
```

## Testing

Run against sample PRs:

```bash
# Test with a real PR
./claude-review --pr https://github.com/microsoft/vscode/pull/12345

# Test with local diff
git diff main..feature-branch | ./claude-review --stdin
```

## Limitations

- Requires Anthropic API access
- Large diffs (>10k lines) may be truncated
- Does not execute or test code
- Confidence scores are heuristic-based

## License

MIT - use freely, modify as needed.

## Author

Built for the Claude Builders Bounty community.
