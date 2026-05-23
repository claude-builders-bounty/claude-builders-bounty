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

## PR Reviewer Agent

This repository includes a Claude Code PR reviewer for bounty
[#4](../../issues/4). It can be used as a local CLI, a Claude Code project
subagent, or a GitHub Action.

### CLI

Install locally:

```bash
python -m pip install -e .
```

Review a GitHub pull request:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Write the review to a file:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --output pr-review.md
```

The output is structured Markdown with:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: Low / Medium / High

Set `GITHUB_TOKEN` if you need higher GitHub rate limits or access to private
pull requests.

### Claude Code subagent

The project subagent lives at `.claude/agents/pr-reviewer.md`. Claude Code
discovers project subagents from `.claude/agents/`, so after cloning this repo
you can ask Claude Code to use the `pr-reviewer` agent on a PR diff.

### GitHub Action

The workflow at `.github/workflows/claude-review.yml` runs on pull requests and
posts the generated Markdown review as a PR comment. It can also be run manually
with a `workflow_dispatch` PR URL.

### Sample outputs

See [docs/sample-outputs.md](docs/sample-outputs.md) for two reviews generated
from real public GitHub pull requests.

### Tests

```bash
python -m unittest discover -s tests
```

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
