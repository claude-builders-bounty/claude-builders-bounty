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

---

## Bounty #4: `claude-review` PR reviewer agent

This repository includes a Claude Code PR review sub-agent and CLI that reviews a GitHub pull request and returns structured Markdown.

### Setup

1. Install Node.js 18 or newer.
2. From this repository, run:
   ```bash
   npm test
   ```
3. Optional: set `ANTHROPIC_API_KEY` to let Claude generate the final review. Without it, the CLI uses a deterministic fallback analyzer.
4. Optional: set `GITHUB_TOKEN` for higher GitHub API rate limits.

### CLI usage

```bash
npm run claude-review -- --pr https://github.com/owner/repo/pull/123
```

Write the review to a file:

```bash
npm run claude-review -- --pr https://github.com/owner/repo/pull/123 --output review.md
```

After `npm link`, the direct command is:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

The output always includes:

- `## Summary of changes`
- `## Identified risks`
- `## Improvement suggestions`
- `## Confidence score: Low|Medium|High`

### Claude Code sub-agent

The agent definition lives at `.claude/agents/pr-reviewer.md`.

Use it in Claude Code by asking the `pr-reviewer` sub-agent to review a PR URL. The agent runs the local CLI and keeps the final output concise and actionable.

### GitHub Action

The workflow at `.github/workflows/claude-review.yml` can run manually with a PR URL or automatically on pull request events. It writes the review to the GitHub Actions step summary and uploads `review.md` as an artifact.

### Verified sample outputs

Two real GitHub pull requests were used for verification:

- `examples/octocat-hello-world-pr-6.md`
- `examples/githubtraining-hellogitworld-pr-1.md`
