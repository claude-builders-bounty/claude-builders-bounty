# Claude Builders Bounty 🤖

> A community bounty board for Claude Code builders.

Building with Claude Code? Have tasks to delegate?
Want to get paid for contributing to AI projects?
You're in the right place.

---

## How it works

**To post a bounty**
1. Open a GitHub issue with a clear description and acceptance criteria
2. Comment `/opire create $XXX` in the issue to set the reward
3. Share the link — contributors will find it

**To claim a bounty**
1. Browse the open issues below
2. Comment `/opire try` in the issue you want to work on
3. Submit a PR — payment is automatic on merge ✅

---

## Active Bounties

| # | Task | Amount | Status |
|---|------|--------|--------|
| [#1](../../issues/1) | SKILL: Generate a CHANGELOG from git history | $50 | 🟢 Open |
| [#2](../../issues/2) | TEMPLATE: CLAUDE.md for a Next.js + SQLite project | $75 | 🟢 Open |
| [#3](../../issues/3) | HOOK: Block destructive bash commands in Claude Code | $100 | 🟢 Open |
| [#4](../../issues/4) | AGENT: PR reviewer with structured Markdown output | $150 | 🟢 Open |
| [#5](../../issues/5) | WORKFLOW: n8n + Claude API — automated weekly dev summary | $200 | 🟢 Open |

---

## Rules

- Tasks must be related to Claude Code or AI tooling
- Every issue must have clear acceptance criteria before a bounty is activated
- Payment is handled by [Opire](https://opire.dev) (Stripe)
- Quality over speed — a solid PR beats a fast one

---

## Community

- 🐦 X: [@ClaudeBounty](https://x.com/ClaudeBounty)
- 📧 Contact: claudebounty@gmail.com

---

*Started by the Claude builder community · March 2026 · MIT License*

# Claude PR Review Agent

This submission implements bounty #4: a Claude Code PR review agent that reads a pull request diff and returns a structured Markdown review comment.

## Setup

1. Use Python 3.10+.
2. Optional: install the Claude Code CLI and authenticate it. Without it, the CLI uses deterministic fallback analysis.
3. Optional for private repos or comment posting: export `GITHUB_TOKEN`.

## Usage

Review a public GitHub PR:

```bash
python bin/claude-review --pr https://github.com/owner/repo/pull/123
```

Post the structured review as a PR comment:

```bash
GITHUB_TOKEN=<token> python bin/claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
```

Review a local diff:

```bash
python bin/claude-review --diff-file change.diff
```

Force the Claude Code CLI engine:

```bash
python bin/claude-review --pr https://github.com/owner/repo/pull/123 --engine claude
```

## Output Format

The tool always emits these sections:

- `## Summary`: 2-3 sentences describing the change.
- `## Identified Risks`: concrete risks found in the diff.
- `## Improvement Suggestions`: actionable follow-up items.
- `## Confidence Score`: `Low`, `Medium`, or `High`.

## GitHub Action

The included workflow sample at `github-action/claude-review.yml` runs on pull requests and posts a structured review comment. Copy it to `.github/workflows/claude-review.yml` in the repository that should run the reviewer. It uses the same CLI and `GITHUB_TOKEN`, so no extra dependency is required for public PRs. If the Claude Code CLI is available in the runner, set `CLAUDE_REVIEW_ENGINE=claude`; otherwise `auto` falls back to deterministic analysis.

## Claude Code Sub-Agent

The reusable sub-agent prompt lives at `.claude/agents/pr-reviewer.md`. It delegates diff fetching and formatting enforcement to `bin/claude-review` while keeping the reviewer focused on behavioral risks, test gaps, and actionable suggestions.

## Verification

```bash
python -m unittest discover -s tests
python bin/claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/428 --output samples/claude-builders-bounty-428.md
python bin/claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/640 --output samples/claude-builders-bounty-640.md
```

Sample outputs from those two real GitHub PRs are included in `samples/`.
