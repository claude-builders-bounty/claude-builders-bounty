# Claude Code PR Review Sub-Agent

A CLI tool (and optional GitHub Action) that reviews PR diffs using Claude and posts structured Markdown reviews.

## CLI Usage

```bash
# Install
pip install requests  # runtime dependency
chmod +x claude-review.py

# Set your Anthropic API key
export ANTHROPIC_API_KEY="sk-ant-..."
# Optional: set for private repos
export GITHUB_TOKEN="ghp_..."

# Review any PR
python3 claude-review.py --pr https://github.com/owner/repo/pull/123

# Save to file
python3 claude-review.py --pr https://github.com/owner/repo/pull/123 --output review.md

# Verbose mode (shows progress)
python3 claude-review.py --pr https://github.com/owner/repo/pull/123 --verbose
```

## GitHub Action

1. Add `.github/workflows/claude-review.yml` (included in this repo)
2. Set `ANTHROPIC_API_KEY` in your repository secrets
3. Every new PR gets an automated review comment

## Output Format

```
# PR Review: [title]

**Repository:** `owner/repo`
**PR:** [#123](https://github.com/owner/repo/pull/123)
**Author:** @username
**Changes:** +42/-10 across 5 files

---

## Summary
[2-3 sentence overview of what the PR does]

## Identified Risks
- [Risk 1 with context]
- [Risk 2 with context]

## Improvement Suggestions
- [Specific suggestion with file:line reference]
- [Specific suggestion with file:line reference]

## Confidence Score
**Medium** — the changes are straightforward but involve a critical path
```

## Requirements

- Python 3.8+
- Anthropic API key (get one at https://console.anthropic.com/)
- For GitHub Action: same key stored as repository secret

## Sample Output

See [sample-output.md](./sample-output.md) for an example review on a real PR.
