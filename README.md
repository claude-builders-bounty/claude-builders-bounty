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

## Bounty #4: Claude PR Review Agent

This repository includes `claude-review`, a small Claude Code powered CLI that reviews a GitHub PR diff and returns a structured Markdown review comment.

### Features

- CLI usage: `claude-review --pr https://github.com/owner/repo/pull/123`
- Fetches the PR diff through the GitHub CLI (`gh pr diff`)
- Invokes Claude Code (`claude -p`) with a focused reviewer prompt
- Deterministic fallback mode for CI/tests: `--no-claude`
- Optional PR commenting: `--post-comment`
- Claude Code sub-agent prompt: `.claude/agents/pr-reviewer.md`

### Setup

Prerequisites:

- Python 3.10+
- GitHub CLI authenticated with access to the PR (`gh auth login`)
- Claude Code CLI installed and authenticated (`claude` on `PATH`)

Install locally:

```bash
pip install -e .
```

Generate a review:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Save to a file:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

Post as a PR comment:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
```

Use deterministic fallback mode without Claude Code:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --no-claude
```

### Output format

The generated comment always contains:

```markdown
## Summary
...

## Identified risks
- ...

## Improvement suggestions
- ...

## Confidence
Medium — ...
```

### Sample outputs

Two real PR sample reviews are included:

- `samples/cli-cli-13393-review.md` for https://github.com/cli/cli/pull/13393
- `samples/python-cpython-149710-review.md` for https://github.com/python/cpython/pull/149710

### Development

Run tests:

```bash
python -m pytest
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
