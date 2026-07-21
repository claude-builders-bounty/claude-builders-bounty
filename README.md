# claude-review

A CLI agent that analyzes GitHub PR diffs and generates structured Markdown reviews.

## Quick Start

```bash
# 1. Install
git clone https://github.com/fitzerooqq/claude-review.git
cd claude-review

# 2. Review a PR
./claude-review.sh --pr https://github.com/owner/repo/pull/123
```

## Requirements

- GitHub CLI (`gh`) — authenticated
- `bash` 4+
- `awk`, `sed` (standard Unix tools)

## Usage

```bash
# Review a PR
./claude-review.sh --pr https://github.com/facebook/react/pull/12345

# Output is structured Markdown:
#
# ## PR Review: <title>
# ### Summary
# ### Changes by File
# ### Identified Risks
# ### Improvement Suggestions
# ### Confidence Score
```

## Claude Code Integration

Add to your `CLAUDE.md`:

```markdown
## Available Tools
- `claude-review` — analyzes PR diffs and generates structured reviews
```

## GitHub Action

Copy `.github/workflows/claude-review.yml` to your repo for auto-review on every PR.
