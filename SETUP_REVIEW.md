# claude-review — Quick Setup

## 3-Command Setup

```bash
# 1. Make executable
chmod +x claude-review.sh

# 2. Set your GitHub token (for higher API rate limits)
export GH_TOKEN="ghp_..."

# 3. Review any PR
bash claude-review.sh --pr https://github.com/owner/repo/pull/123
```

## Output Format

Structured Markdown with:
- **Summary** — 2–3 sentences on what changed
- **Risks** — TODO markers, debug statements, exposed secrets, large diffs
- **Suggestions** — splitting PRs, adding descriptions, creating follow-ups
- **Confidence** — Low / Medium / High based on risk count

## Requirements

- `curl`, `python3`, `grep` (standard Unix tools)
- GitHub token optional but recommended (avoids rate limiting)
