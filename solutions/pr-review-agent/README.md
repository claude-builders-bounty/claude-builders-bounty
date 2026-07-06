# claude-review — AI PR Review Agent

A Claude Code sub-agent that reviews a GitHub PR diff and returns a structured Markdown review comment.

## Requirements

- Bash 4+
- curl
- GitHub API access (public repos)

## Installation

```bash
# 1-step install
curl -sL -o /usr/local/bin/claude-review \
  https://raw.githubusercontent.com/dev-nana27/claude-review/main/claude-review.sh
chmod +x /usr/local/bin/claude-review

# 2-step: or clone and symlink
git clone https://github.com/dev-nana27/claude-review.git
ln -s "$(pwd)/claude-review/claude-review.sh" ~/.local/bin/claude-review
```

## Usage

```bash
# Review a GitHub PR
claude-review --pr https://github.com/owner/repo/pull/123

# Review a local diff file
claude-review --diff /path/to/changes.diff

# Get help
claude-review --help
```

## Output Format

```
## 🔍 Code Review Report

### 📋 Summary of Changes
- Files changed: 5
- Lines added: 142
- Lines removed: 89

### ⚠️ Identified Risks
| Risk Level | Finding | Line |
|-----------|---------|------|
| 🔴 Critical | Destructive command detected | +rm -rf /tmp/cache |
| 🟡 Medium | Dynamic code execution | +eval "$user_input" |

### 💡 Improvement Suggestions
- 🏗️ **Configuration:** Found 2 hardcoded values

### 📊 Confidence Score: High
```

## Why This Approach

Instead of a heavy GitHub Action setup (which requires repo-level permissions),
this agent works as a **standalone CLI tool** that:
1. Fetches the PR diff via GitHub's public API (no token needed for public repos)
2. Analyzes it for common code quality issues
3. Outputs structured Markdown that can be posted as a PR comment
4. Can be integrated into any CI/CD pipeline or used interactively

## Testing

Tested on real GitHub PRs:
- [Example PR 1](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1) (internal test)
- GitHub public API confirmed working for diff retrieval

## License

MIT
