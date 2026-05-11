# Claude Builders Bounty

> A community bounty board for Claude Code builders.

Building with Claude Code? Have tasks to delegate?
Want to get paid for contributing to AI projects?
You're in the right place.

---

## How it works

**To post a bounty**
1. Open a GitHub issue with a clear description and acceptance criteria
2. Comment `/opire create $XXX` in the issue to set the reward
3. Share the link - contributors will find it

**To claim a bounty**
1. Browse the open issues below
2. Comment `/opire try` in the issue you want to work on
3. Submit a PR - payment is automatic on merge

---

## Active Bounties

| # | Task | Amount | Status |
|---|------|--------|--------|
| [#1](../../issues/1) | SKILL: Generate a CHANGELOG from git history | $50 | Open |
| [#2](../../issues/2) | TEMPLATE: CLAUDE.md for a Next.js + SQLite project | $75 | Open |
| [#3](../../issues/3) | HOOK: Block destructive bash commands in Claude Code | $100 | Open |
| [#4](../../issues/4) | AGENT: PR reviewer with structured Markdown output | $150 | Open |
| [#5](../../issues/5) | WORKFLOW: n8n + Claude API - automated weekly dev summary | $200 | Open |

---

## Rules

- Tasks must be related to Claude Code or AI tooling
- Every issue must have clear acceptance criteria before a bounty is activated
- Payment is handled by [Opire](https://opire.dev) (Stripe)
- Quality over speed - a solid PR beats a fast one

---

## Bounty #4: Claude PR Reviewer Agent

This repository includes a Claude Code PR reviewer agent plus a dependency-free
CLI that turns a GitHub pull request diff into a structured Markdown review.

### What is included

- `.claude/agents/pr-reviewer.md` - Claude Code sub-agent instructions.
- `claude-review` - executable wrapper for the CLI.
- `tools/claude_review.py` - dependency-free review generator.
- `.github/workflows/claude-review.yml` - manual GitHub Action that can post a PR comment.
- `samples/` - two example review outputs generated from real GitHub PRs.
- `tests/` - unit tests for URL parsing, diff summarization, and output sections.

### Local usage

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

On Windows:

```powershell
python .\tools\claude_review.py --pr https://github.com/owner/repo/pull/123
```

The default mode is deterministic and works without any API key. If you have
Claude Code installed and want the final review drafted by Claude, use:

```bash
./claude-review --pr https://github.com/owner/repo/pull/123 --use-claude
```

Useful options:

```bash
./claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
./claude-review --diff-file local.diff
./claude-review --pr https://github.com/owner/repo/pull/123 --prompt-only
./claude-review --pr https://github.com/owner/repo/pull/123 --json
```

### GitHub Action usage

Run **Claude PR Review** manually from the Actions tab and provide:

- `pr_url`: the pull request URL to review.
- `post_comment`: set to `true` if the workflow should comment on the PR.

The workflow writes the review to the job summary. When `post_comment` is true,
it also posts the generated Markdown as a PR comment using `gh pr comment`.

### Output format

Every review uses the required structure:

```markdown
## Summary

## Identified risks

## Improvement suggestions

## Confidence
```

The confidence value is always `High`, `Medium`, or `Low`.

---

## Community

- X: [@ClaudeBounty](https://x.com/ClaudeBounty)
- Contact: claudebounty@gmail.com

---

*Started by the Claude builder community - March 2026 - MIT License*
