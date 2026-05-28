# 🔍 PR Review Agent

CLI tool and GitHub Action that reviews pull requests using Claude Code.

**Bounty:** [#4 — $150](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)

## Features

- **CLI mode:** `claude-review --pr https://github.com/owner/repo/pull/123`
- **GitHub Action:** Auto-reviews PRs on open/sync
- **Structured output:** Summary, Risks, Suggestions, Confidence score
- **Works with:** Claude Code CLI or Anthropic API

## Installation

```bash
# Clone
git clone https://github.com/RomuloGatto/claude-builders-bounty.git

# Make executable
chmod +x claude-builders-bounty/pr-review-agent/claude-review.sh

# (Optional) Add to PATH
ln -s $(pwd)/claude-builders-bounty/pr-review-agent/claude-review.sh /usr/local/bin/claude-review
```

## Usage

### CLI

```bash
# Review a PR
claude-review --pr https://github.com/owner/repo/pull/123

# Save to file
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

### GitHub Action

Copy `.github/workflows/pr-review.yml` to your repo and add `ANTHROPIC_API_KEY` as a repository secret.

## Requirements

- `gh` (GitHub CLI) — authenticated
- `claude` (Claude Code CLI) — OR — `ANTHROPIC_API_KEY` environment variable
- `python3` — for JSON parsing

## Output Format

```markdown
# PR Review: owner/repo#123

**PR:** Title
**Author:** @username
**Changes:** +100 / -50 across 10 files

---

### Summary
2-3 sentence summary of changes.

### Risks
- Risk 1
- Risk 2

### Suggestions
- Suggestion 1
- Suggestion 2

### Confidence: High
Explanation of confidence level.

---
*Reviewed by claude-review on 2026-05-28*
```

## Acceptance Criteria

- [x] Works via CLI: `claude-review --pr URL`
- [x] GitHub Action workflow included
- [x] Structured Markdown output (Summary, Risks, Suggestions, Confidence)
- [x] Tested on real PRs (see sample outputs below)
- [x] README with setup and usage

## Sample Outputs

See `samples/` directory for real PR reviews.

## License

MIT
