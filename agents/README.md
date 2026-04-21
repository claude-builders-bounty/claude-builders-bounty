# Claude Code PR Review Agent

## Overview

Automated PR review agent that analyzes GitHub pull request diffs using Claude API and posts structured, constructive code review comments.

## Features

- 🤖 **AI-Powered Review**: Uses Claude Sonnet 4 for intelligent code analysis
- 📊 **Structured Output**: Organized review with summary, issues, suggestions, and recommendation
- 🔗 **GitHub Integration**: Fetches PR diff via GitHub API
- 💬 **Auto-Post**: Optionally posts review as PR comment
- 📁 **File Support**: Can analyze diff files directly
- ⚡ **Fast**: Complete review in 30-60 seconds

## Installation

### Step 1: Copy Agent Script

```bash
# Create agents directory
mkdir -p ~/.claude/agents

# Copy the agent
cp claude_review.py ~/.claude/agents/claude_review.py

# Make executable
chmod +x ~/.claude/agents/claude_review.py
```

### Step 2: Set Environment Variables

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
export GITHUB_TOKEN="ghp_your_github_token_here"
export ANTHROPIC_API_KEY="sk-ant-your_anthropic_key_here"
```

### Step 3: Create Alias (Optional)

```bash
alias claude-review='python3 ~/.claude/agents/claude_review.py'
```

## Usage

### Review a GitHub PR

```bash
# Full URL
claude-review --pr https://github.com/owner/repo/pull/123

# Post review as comment
claude-review --pr https://github.com/owner/repo/pull/123 --post

# Save review to file
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

### Review a Diff File

```bash
# From file
claude-review --diff changes.diff --repo owner/repo

# From git command
git diff main feature-branch | claude-review --diff /dev/stdin --repo owner/repo
```

### Command Line Options

```
--pr URL        GitHub PR URL to review
--diff FILE     Path to diff file (alternative to --pr)
--repo OWNER/REPO  Repository in format owner/repo (required with --diff)
--post          Post review as comment on PR
--output FILE   Save review to file instead of posting
--help          Show help message
```

## Example Output

```markdown
## 🤖 Automated PR Review by Claude

**PR:** #123 - Add user authentication
**Author:** @johndoe
**Changes:** 5 files, +234 -56

---

## Summary

This PR implements user authentication using NextAuth.js with GitHub OAuth provider. The implementation follows best practices and includes proper error handling.

## ✅ Positive Aspects

- Clean separation of concerns
- Proper error handling with try-catch
- Good test coverage
- Follows project conventions

## ⚠️ Potential Issues

### Security
- **Line 45**: API key exposed in client-side code. Move to server-side.
- **Line 78**: Missing rate limiting on login endpoint.

### Performance
- **Line 123**: Database query in loop. Consider batching.

## 💡 Suggestions

1. Add TypeScript types for user objects
2. Consider using React Query for data fetching
3. Add loading states for better UX

## 🎯 Recommendation

**Needs Changes** - Please address the security concerns before merging.

---

*This review was generated automatically by Claude Code PR Review Agent.*
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Yes | GitHub personal access token with `repo` scope |
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key for Claude |
| `CLAUDE_MODEL` | No | Model to use (default: `claude-sonnet-4-20250514`) |

### GitHub Token Setup

1. Go to https://github.com/settings/tokens
2. Create new token with scopes: `repo`, `read:user`
3. Copy the token and set as `GITHUB_TOKEN` environment variable

### Anthropic API Key Setup

1. Go to https://console.anthropic.com
2. Get your API key
3. Set as `ANTHROPIC_API_KEY` environment variable

## Integration with Claude Code

### As a Custom Command

Add to `~/.claude/commands.json`:

```json
{
  "commands": [
    {
      "name": "review-pr",
      "command": "python3 ~/.claude/agents/claude_review.py --pr {args} --post"
    }
  ]
}
```

Then use in Claude Code:
```
/review-pr https://github.com/owner/repo/pull/123
```

### As a Hook

Add to `~/.claude/hooks.json` for automatic PR reviews:

```json
{
  "hooks": [
    {
      "name": "auto_pr_review",
      "event": "on-pr-open",
      "command": "python3 ~/.claude/agents/claude_review.py --pr {pr_url} --post"
    }
  ]
}
```

## Cost Estimation

- **Claude API**: ~$0.01-0.03 per review (depending on PR size)
- **GitHub API**: Free (within rate limits)
- **Monthly Cost**: ~$0.30-0.90 for 30 reviews

## Troubleshooting

### "GITHUB_TOKEN is required"

Set the environment variable:
```bash
export GITHUB_TOKEN="ghp_your_token"
```

### "ANTHROPIC_API_KEY is required"

Set the environment variable:
```bash
export ANTHROPIC_API_KEY="sk-ant-your_key"
```

### "Invalid GitHub PR URL"

Ensure the URL format is correct:
```
https://github.com/owner/repo/pull/123
```

### Rate Limiting

GitHub API rate limit: 5000 requests/hour (authenticated)
- Wait and retry after limit resets
- Consider using GitHub App for higher limits

## Security Notes

⚠️ **Token Security**: Never commit your tokens to version control. Use environment variables or a secrets manager.

⚠️ **Code Review**: This agent provides automated suggestions but should not replace human code review. Always have a human review critical changes.

## Testing

### Test with Sample PR

```bash
# Use a public PR for testing
claude-review --pr https://github.com/owner/repo/pull/123 --output test-review.md
```

### Test with Local Diff

```bash
# Create a test diff
git diff HEAD~1 > test.diff

# Review the diff
claude-review --diff test.diff --repo owner/repo
```

## License

MIT License - See repository LICENSE

## Bounty Information

This agent resolves **Issue #4** ($150 Bounty) from claude-builders-bounty.

**Acceptance Criteria Met:**
- ✅ Claude Code agent that takes PR diff as input
- ✅ Analyzes with Claude API
- ✅ Returns structured markdown review
- ✅ Command-line interface: `claude-review --pr URL`
- ✅ Posts review as PR comment (optional)
