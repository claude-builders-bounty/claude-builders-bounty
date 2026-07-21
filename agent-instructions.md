# claude-review: Claude Code Sub-Agent

This tool analyzes GitHub PR diffs and generates structured markdown reviews.

## Usage as CLI

```bash
./claude-review.sh --pr https://github.com/owner/repo/pull/123
```

## Usage as GitHub Action

Copy `.github/workflows/claude-review.yml` to your repo. It runs automatically on PR open/sync.

## Integration with Claude Code

Add to your `CLAUDE.md`:

```markdown
## Available Tools

### claude-review
A PR review agent that fetches PR diffs and generates structured reviews.

Usage: `claude-review --pr <pr-url>`
- Fetches PR metadata via GitHub CLI
- Analyzes file changes, additions/deletions, risks
- Outputs structured markdown: summary, risks, suggestions, confidence score
```

## Output Format

```markdown
## PR Review: <title>

**PR:** #<number> — **owner/repo**
**Total:** +additions/-deletions across N files

### Summary
<2-3 sentence summary>

### Changes by File
| File | Changes | Status |

### Identified Risks
- ⚠️ Risk description

### Improvement Suggestions
- 💡 Suggestion

### Confidence Score
**High/Medium/Low**
```
