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

## Bounty #4: Claude Code PR review agent

This repository now includes `claude-review`, a small Python CLI that reviews a GitHub pull request diff and prints a structured Markdown review comment.

### What it outputs

- Summary of changes in 2–3 concise sentences
- Identified risks
- Improvement suggestions
- Confidence score: Low / Medium / High

### Usage

```bash
python3 claude_review.py --pr https://github.com/owner/repo/pull/123
```

Optional offline mode for tests or saved diffs:

```bash
python3 claude_review.py --pr https://github.com/owner/repo/pull/123 --diff-file path/to/pr.diff
```

### How it works

1. Parses the GitHub PR URL.
2. Fetches the public `.diff` from GitHub.
3. Applies deterministic static-review heuristics for risky changes such as `shell=True`, hard-coded secrets, dynamic execution, destructive commands, and missing test coverage signals.
4. Emits a paste-ready Markdown review.

No GitHub token is required for public pull requests.

### Sample outputs

Two real PR sample outputs are included:

- `samples/review-pr-1198.md`
- `samples/review-gh-cli-pr-10748.md`

### Run tests

```bash
python3 -m unittest tests/test_claude_review.py -v
```

Expected result:

```text
Ran 6 tests
OK
```
