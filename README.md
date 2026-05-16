# Claude Builders Bounty

> A community bounty board for Claude Code builders.

Building with Claude Code? Have tasks to delegate?
Want to get paid for contributing to AI projects?
You're in the right place.

---

## Bounty #4 Submission: Onyx PR Reviewer

This repository now includes **Onyx PR Reviewer**, a Claude Code sub-agent and CLI that reviews a GitHub pull request diff and returns a structured Markdown comment.

Onyx is the reviewer persona from BCC: concise, risk-aware, and designed to assist a human maintainer without pretending to make the merge decision.

### What it does

- Accepts a GitHub PR URL.
- Fetches PR metadata and the unified diff through the GitHub API.
- Scans for review risks such as command execution, workflow changes, credential-like additions, missing tests, migrations, and large diffs.
- Emits Markdown with:
  - Summary of changes
  - Identified risks
  - Improvement suggestions
  - Confidence score: Low / Medium / High
- Includes a GitHub Actions workflow that can post the review as a PR comment.

### Files

```text
claude-review                         # CLI entrypoint
claude-review.ps1                     # Windows PowerShell wrapper
claude_review_agent/reviewer.py       # Review engine
agents/onyx-pr-reviewer.md            # Claude Code sub-agent prompt
.github/workflows/onyx-pr-review.yml  # GitHub Action
samples/pr-139-review.md              # Real PR sample output
samples/pr-140-review.md              # Real PR sample output
```

### CLI usage

From the repository root:

```bash
python claude-review --pr https://github.com/owner/repo/pull/123
```

On Windows PowerShell:

```powershell
.\claude-review.ps1 --pr https://github.com/owner/repo/pull/123
```

Write the review to a file:

```bash
python claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

Use a saved diff instead of fetching from GitHub:

```bash
python claude-review --pr https://github.com/owner/repo/pull/123 --diff-file ./pr.diff
```

Review local changes against a base branch:

```bash
python claude-review --pr https://github.com/owner/repo/pull/123 --local-base origin/main
```

Set `GITHUB_TOKEN` for higher API limits when reviewing many PRs.

### GitHub Action

The included workflow runs on pull requests and posts the generated review as a comment:

```yaml
name: Onyx PR Review
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
permissions:
  contents: read
  issues: write
  pull-requests: write
```

It uses the repository-provided `GITHUB_TOKEN` and keeps permissions narrow.

### Sample outputs

The tool was tested on two real GitHub PRs:

- `https://github.com/claude-builders-bounty/claude-builders-bounty/pull/139` -> `samples/pr-139-review.md`
- `https://github.com/claude-builders-bounty/claude-builders-bounty/pull/140` -> `samples/pr-140-review.md`

### Design notes

This implementation is deterministic and dependency-light on purpose. It does not need paid model access to produce a useful first-pass review, but the `agents/onyx-pr-reviewer.md` prompt can be used by Claude Code to perform a deeper second pass when a maintainer wants model-assisted reasoning.

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

## Community

- X: [@ClaudeBounty](https://x.com/ClaudeBounty)
- Contact: claudebounty@gmail.com

---

*Started by the Claude builder community - March 2026 - MIT License*
