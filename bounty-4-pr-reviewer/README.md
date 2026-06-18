# claude-review — Claude Code PR Reviewer

A CLI tool that takes any GitHub PR URL, fetches the diff, and returns a structured Markdown review powered by Claude `claude-sonnet-4-20250514`.

## Setup (3 steps)

**1. Install (no dependencies — stdlib only)**
```bash
curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/bounty-4-pr-reviewer/claude_review.py
chmod +x claude_review.py
```

**2. Set environment variables**
```bash
export GITHUB_TOKEN=ghp_...      # GitHub Personal Access Token (read:repo scope)
export ANTHROPIC_API_KEY=sk-ant-api03-...
```

**3. Run**
```bash
python claude_review.py --pr https://github.com/owner/repo/pull/123
```

## Usage

```bash
# Print review to stdout
python claude_review.py --pr https://github.com/owner/repo/pull/42

# Save to file
python claude_review.py --pr https://github.com/owner/repo/pull/42 --output review.md
```

## Output format

Every review contains four sections:

```markdown
## Claude Code PR Review
**PR:** <url>  **Model:** `claude-sonnet-4-20250514`

### Summary
2–3 sentences describing the change.

### Risks
- Risk 1
- Risk 2

### Improvement Suggestions
- Suggestion 1

### Confidence Score
**High** / **Medium** / **Low**  
Rationale: one sentence.
```

## Sample outputs

- [`sample_output_pr2912.md`](sample_output_pr2912.md) — review of a CLAUDE.md template PR
- [`sample_output_pr2913.md`](sample_output_pr2913.md) — review of a Claude Code safety hook PR

## Requirements

- Python 3.8+ (stdlib only — no pip install needed)
- GitHub PAT with `repo` scope
- Anthropic API key (`sk-ant-api03-...`)
