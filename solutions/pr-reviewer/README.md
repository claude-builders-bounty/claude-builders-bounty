# Claude Code PR Reviewer Agent

A command-line tool and GitHub Action that analyzes pull requests and generates structured Markdown reviews using the Claude API.

## Installation

### CLI Usage

```bash
# Clone or download
git clone https://github.com/your-repo/claude-pr-reviewer.git
cd claude-pr-reviewer

# Install dependencies
pip install -r requirements.txt

# Set API key
export ANTHROPIC_API_KEY="your-api-key"
```

### GitHub Action

Add to your workflow:

```yaml
name: PR Review
on:
  pull_request:
    types: [opened]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Claude PR Review
        uses: your-org/claude-pr-reviewer@v1
        with:
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Usage

### CLI

```bash
# Review a PR by URL
claude-review --pr https://github.com/owner/repo/pull/123

# Review by repo and number
claude-review --repo owner/repo --pr-number 123

# Review local diff file
claude-review --local path/to/diff.patch

# Post review as comment
claude-review --pr https://github.com/owner/repo/pull/123 --post

# Save to file
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

### GitHub Action

The action automatically:
1. Fetches the PR diff
2. Sends to Claude API for analysis
3. Posts structured review as a PR comment

## Output Format

Reviews follow this structured Markdown format:

```markdown
## Summary
This PR refactors the authentication module to use JWT tokens
instead of session cookies, improving scalability for distributed
deployments. Changes affect auth.py, middleware.py, and config.py.

## Risks Identified
- Token expiration handling may cause edge case failures
- Missing rate limiting on token refresh endpoint
- Config migration required before deployment

## Suggestions for Improvement
- Add integration tests for token refresh flow
- Implement rate limiting on `/auth/refresh`
- Add deployment migration guide in README

## Confidence Score
Medium
```

## Sample Reviews

### Review #1: Feature Addition
```markdown
## Summary
This PR adds a new WebSocket connection handler for real-time
notifications. It introduces a new handler class and modifies
the existing event dispatcher to support push notifications.

## Risks Identified
- WebSocket connections may accumulate without proper cleanup
- Missing connection timeout configuration
- No authentication on WebSocket handshake

## Suggestions for Improvement
- Add connection idle timeout (suggest 30s)
- Implement heartbeat mechanism for connection health
- Validate auth token during WebSocket upgrade request

## Confidence Score
Medium
```

### Review #2: Bug Fix
```markdown
## Summary
This PR fixes a race condition in the file upload handler where
concurrent uploads could overwrite each other's metadata. The
fix adds a mutex lock around metadata writes.

## Risks Identified
- Lock acquisition timeout not configured (potential deadlock)
- No test for concurrent upload scenario
- Lock may affect upload throughput

## Suggestions for Improvement
- Add configurable lock timeout (default 5s)
- Create integration test for concurrent uploads
- Consider using file-specific locks instead of global lock

## Confidence Score
High (The fix addresses the root cause correctly)
```

## Requirements

- Python 3.8+
- `anthropic` Python package
- GitHub CLI (`gh`) for posting comments (optional)
- ANTHROPIC_API_KEY environment variable

## Configuration

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Claude API key |
| `CLAUDE_MODEL` | Model to use (default: claude-sonnet-4-20250514) |
| `MAX_DIFF_SIZE` | Max diff size in bytes (default: 15000) |

## License

MIT