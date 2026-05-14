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

## Claude PR Review Agent

This repository includes a small PR review agent for bounty [#4](../../issues/4). It fetches a GitHub pull request, inspects the diff metadata, and prints a structured Markdown review with the required sections:

- Summary
- Risks
- Suggestions
- Confidence score

### Setup

1. Install the GitHub CLI (`gh`) or set `GITHUB_TOKEN` for API access. If `gh` is not on `PATH`, set `GH_BIN=/path/to/gh`.
2. Make the script executable: `chmod +x claude-review`.
3. Run it against a public PR:

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

Optional file output:

```bash
./claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

Post the review as a PR comment:

```bash
./claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
```

The repository also includes `workflows/claude-review.yml`, a ready-to-copy GitHub Actions workflow that runs the same agent on pull requests or through `workflow_dispatch`.

### Sample Outputs

Two sample reviews from real GitHub PRs are included:

- [`samples/review-1033.md`](samples/review-1033.md)
- [`samples/review-1356.md`](samples/review-1356.md)

### Verification

```bash
python3 -m unittest discover -s tests
./claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1033 --output /tmp/review-1033.md
./claude-review --pr https://github.com/moleculerjs/moleculer/pull/1356 --output /tmp/review-1356.md
./claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1033 --post-comment
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
