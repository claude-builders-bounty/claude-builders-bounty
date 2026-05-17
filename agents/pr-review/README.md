# PR Review Agent — Claude Code (Bounty #4)

> **$150 Bounty** — Automated PR review using Claude API, outputs structured Markdown.

---

## What This Does

Running `pr_review.py --pr <url>` will:

1. Fetch the PR diff and metadata via GitHub API
2. Send to **Claude Sonnet 4** (`claude-sonnet-4-20250514`) for analysis
3. Output a structured Markdown review with:
   - **Summary** of changes (2-3 sentences)
   - **Identified risks** (list, with severity)
   - **Improvement suggestions** (list, actionable)
   - **Confidence score**: Low / Medium / High

---

## Setup Instructions

### Step 1: Set Environment Variables
```bash
export GITHUB_TOKEN="ghp_xxx"          # GitHub Personal Access Token
export CLAude_API_KEY="sk-ant-xxx"     # Anthropic API Key
```

### Step 2: Run on a PR
```bash
python agents/pr-review/pr_review.py --pr https://github.com/owner/repo/pull/123
```

### Step 3: (Optional) Auto-post as Comment
```bash
python agents/pr-review/pr_review.py --pr <url> --post-comment
```

---

## GitHub Action (Automatic Reviews)

Add to your repo's `.github/workflows/pr-review.yml` (already included):

```yaml
name: PR Review
on: [pull_request]
```

The Action will automatically review every new PR and post the comment.

---

## Sample Output (Tested on 2 Real PRs)

### Test 1: PR #1584 (Bounty #3 Hook)
```markdown
## Summary
This PR adds a Python pre-tool-use hook that intercepts destructive bash commands...

## Identifed Risks
- **High**: Regex may not catch all variants of `rm -rf`
- **Medium**: No Windows path handling
- **Low**: Missing error handling for edge cases

## Improvement Suggestions
- Add unit tests for each blocked pattern
- Handle Windows paths (e.g., `del /Q /S`)
- Add configuration file for custom rules

## Confidence Score: **High**
```

### Test 2: PR #1587 (Bounty #5 n8n Workflow)
```markdown
## Summary
This PR adds an n8n workflow that generates weekly GitHub repo summaries...

## Identifed Risks
- **Medium**: Claude API key exposed in n8n UI
- **Low**: No error handling for API failures

## Improvement Suggestions
- Use n8n credentials store for API key
- Add retry logic for Claude API calls
- Include rate limiting

## Confidence Score: **Medium**
```

---

## Files

| File | Description |
|------|-------------|
| `agents/pr-review/pr_review.py` | Main Python script |
| `agents/pr-review/SKILL.md` | Claude Code skill definition |
| `.github/workflows/pr-review.yml` | GitHub Action workflow |
| `README.md` | This file |
| `sample_output_1.md` | Test output #1 |
| `sample_output_2.md` | Test output #2 |

---

## Notes

- **Model**: Uses `claude-sonnet-4-20250514` as required
- **Output**: Saved to `review_output.md` (or posted as PR comment)
- **Customization**: Edit the prompt in `pr_review.py` to change review style

---

**Created for:** [claude-builders-bounty/claude-builders-bounty #4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)  
**Bounty Amount:** $150  
**Status:** ✅ Ready for review
