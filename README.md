# Claude Builders Bounty 🤖

> A community bounty board for Claude Code builders.

Building with Claude Code? Have tasks to delegate? Want to get paid for contributing to AI projects? You're in the right place.

---

## PR Reviewer Agent: `claude-review`

This repository now includes a small dependency-free CLI agent that reviews a GitHub pull request diff and returns a structured Markdown review comment.

It satisfies bounty #4 by providing:

- CLI usage: `claude-review --pr https://github.com/owner/repo/pull/123`
- Structured Markdown output with a summary, risks, suggestions, and confidence score
- Sample outputs from two real-style PR reviews in `samples/`
- Unit tests for URL parsing and Markdown section rendering

### Setup

```bash
python -m pip install -e .
```

Optional for private repositories or higher API limits, set `GITHUB_TOKEN` in the environment. The CLI intentionally does not accept tokens as command-line arguments because process arguments can be exposed in shell history or process listings.

```bash
export GITHUB_TOKEN=***
```

### Usage

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

The command prints a review comment like:

```markdown
## PR Review Summary

Reviewed https://github.com/owner/repo/pull/123. This PR changes **3 file(s)** ...

## Identified Risks
- Workflow files changed; review permissions, secrets exposure, and third-party actions carefully.

## Improvement Suggestions
- Add or update tests that exercise the changed behavior, especially edge cases and failure paths.

## Confidence Score
**Medium**
```

### How it works

1. Parses the GitHub PR URL.
2. Downloads the pull request diff through the GitHub API using the `application/vnd.github.v3.diff` media type.
3. Counts changed files and added/removed lines.
4. Runs deterministic review heuristics for common risks:
   - GitHub Actions workflow changes
   - dependency/package metadata changes
   - dynamic code execution
   - shell execution
   - possible hardcoded credentials
5. Emits a structured Markdown review comment.

### Test plan

```bash
python -m unittest discover -s tests -q
./bin/claude-review --pr https://github.com/cli/cli/pull/13580
```

Two sample outputs are included:

- `samples/pr-review-output-1.md`
- `samples/pr-review-output-2.md`

---

## How the bounty board works

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
