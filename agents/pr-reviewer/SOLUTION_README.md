# Solution README — Issue #4: PR Review Sub-Agent

## Bounty
**[$150 USD] AGENT: Claude Code sub-agent that reviews a PR and posts a structured comment**
[Issue #4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)

## Solution
`pr_review_agent.py` — A Python CLI that captures git diffs, slices them into logical per-file chunks, sends each to an LLM API for structured review, and outputs a professional `PR_REVIEW.md`.

## Usage
```bash
# Review changes against main branch
python3 pr_review_agent.py --base main --output PR_REVIEW.md

# Review with PR URL in header
python3 pr_review_agent.py --pr https://github.com/owner/repo/pull/123 --base main

# Review unstaged + staged changes (no base branch)
python3 pr_review_agent.py
```

## Architecture
1. **Diff Capture** — Runs `git diff base...HEAD` (or `git diff HEAD` for unstaged)
2. **Token-Limit Truncation** — Caps total diff at 50,000 chars; each file chunk capped at 8,000 chars
3. **Per-File Chunking** — Splits diff by `diff --git` boundaries into individual file reviews
4. **LLM Review** — Sends each chunk to Gemini (primary) or Groq (fallback) API
5. **Static Analysis Fallback** — If no API keys configured, performs heuristic checks (TODO/FIXME, secrets, debug prints)
6. **Report Generation** — Aggregates all file reviews into a structured `PR_REVIEW.md`

## API Configuration
Set one of these environment variables:
```bash
export GEMINI_API_KEY=your_gemini_key    # Primary (free tier)
export GROQ_API_KEY=your_groq_key        # Fallback (free tier)
```

If neither is set, the agent falls back to **static analysis mode** (no API calls).

## Output Format
```markdown
# 📋 Pull Request Review
**Generated:** 2026-07-18 16:00 UTC
**PR:** https://github.com/owner/repo/pull/123

## Summary
- Files reviewed: 5
- Files with errors: 0

## Detailed Review
### File: src/main.py
**Critical Issues:**
- None found

**Suggestions:**
- Consider extracting the validation logic into a helper function

**Positive Notes:**
- Clean error handling pattern
```

## Safety Features
- **Token-limit truncation**: Large diffs are truncated per-file (8K chars) and globally (50K chars) to prevent API boundary errors
- **Graceful fallback**: Static analysis runs without API keys
- **Timeout protection**: All API calls have 30-second timeouts
- **Error isolation**: One file's API failure doesn't block other files

## Testing
```bash
pytest tests/test_solutions/test_issue_4_pr_review.py -v
```
23 tests covering diff parsing, static review, report generation, and end-to-end with mocked git.
