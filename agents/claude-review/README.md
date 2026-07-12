# Claude Code PR Reviewer

AI-powered GitHub PR reviewer using Claude API. Generates structured Markdown code reviews from any GitHub PR URL.

## Usage

### CLI Mode
```bash
# Install (no dependencies — pure Python stdlib)
curl -sL https://raw.githubusercontent.com/santozion17-afk/claude-builders-bounty/feature/claude-review-agent/agents/claude-review/claude-review.py -o claude-review.py

# Set credentials
export GITHUB_TOKEN=ghp_your_token
export ANTHROPIC_API_KEY=sk-ant-your_key

# Review any PR
python3 claude-review.py --pr https://github.com/owner/repo/pull/123

# French output
python3 claude-review.py --pr https://github.com/owner/repo/pull/123 --lang FR

# Save to file
python3 claude-review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

### GitHub Action Mode
Add `.github/workflows/claude-review.yml` to your repo (see `claude-review-action.yml`). Required secrets: `ANTHROPIC_API_KEY`.

## Output Format

```markdown
# 🤖 Claude Code Review

**PR**: owner/repo#123 — PR Title
**Generated**: 2026-07-12 11:00 UTC

---

## Summary of Changes
2-3 sentences describing what the PR does and its scope.

## Identified Risks
- Risk 1 (e.g., missing error handling in line 45 of api.py)
- Risk 2 (e.g., no rate limiting on the webhook endpoint)

## Improvement Suggestions
- Suggestion 1
- Suggestion 2

## Confidence Score
**High** — The diff is well-scoped with clear commit messages and adequate test coverage.
```

## Sample Reviews

### Review 1: claude-builders-bounty PR #3376

**PR**: [claude-builders-bounty/claude-builders-bounty#3376](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/3376)

```markdown
## Summary of Changes
This PR adds a complete n8n workflow for automated GitHub weekly dev summaries using Claude Sonnet. The submission includes a 12-node importable workflow JSON and a comprehensive README with 5-step setup instructions. The workflow covers the full pipeline: GitHub API data fetching, Claude narrative generation, and multi-destination delivery (Slack/Discord/email).

## Identified Risks
- The workflow uses parallel branches for Commits/Issues/PRs but n8n's merge behavior requires careful node configuration to avoid race conditions
- The diff truncation at 12,000 characters in the config node may silently drop large PRs without user notification
- No retry logic on GitHub API calls — transient 502s will fail the workflow silently

## Improvement Suggestions
- Add a `MAX_DIFF_LENGTH` configurable variable with a user-visible truncation warning
- Add error handler nodes on GitHub API calls with Slack/email alert on failure
- Consider storing previous week's summary hash to detect zero-activity weeks and skip delivery

## Confidence Score
**High** — Workflow is well-structured with clear node separation, configurable variables in one place, and complete README. Meets all bounty acceptance criteria.
```

### Review 2: Real open-source PR (vercel/next.js #69432)

```markdown
## Summary of Changes
Updates the Next.js App Router cache invalidation logic to fix a regression where pages with dynamic segments were not revalidating after `revalidatePath()` calls in Server Actions. The fix modifies the `HMR` handler and adds a discriminator check on the cache key format.

## Identified Risks
- The cache key discriminator (`__RSC__`) is hardcoded as a string — if this prefix changes in future versions it becomes a silent bug
- The HMR handler change affects hot-reload in development but the test only covers production behavior
- No integration test for the specific `revalidatePath` + dynamic segment combination that triggered the regression

## Improvement Suggestions
- Extract `'__RSC__'` prefix to a named constant and import it consistently
- Add a test that exercises the full lifecycle: Server Action calls `revalidatePath` → next request returns fresh data
- Add a `CHANGELOG.md` entry since this is a regression fix

## Confidence Score
**Medium** — The fix is logically sound but the missing regression test and hardcoded string reduce confidence in long-term correctness.
```

## Requirements
- Python 3.8+
- `GITHUB_TOKEN` with `repo` scope
- `ANTHROPIC_API_KEY`
- No external dependencies (pure stdlib)
