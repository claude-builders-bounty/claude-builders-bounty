# Claude Builders Bounty 🤖

> A community bounty board for Claude Code builders.

Building with Claude Code? Have tasks to delegate?
Want to get paid for contributing to AI projects?
You're in the right place.

## Claude PR reviewer

This repository also contains `claude-review`, a small command-line agent that
reviews a GitHub pull request with Claude Code and prints a structured Markdown
review. It does not post comments or modify repositories.

### Requirements

- Python 3.9 or newer
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed and
  authenticated (`claude login`)
- A GitHub token for private repositories or higher API rate limits. Set
  `GITHUB_TOKEN` (or `GH_TOKEN`) when needed.

### Installation

From a checkout of this repository:

```console
python -m pip install .
```

This installs the `claude-review` executable. For development, the command can
also be run without installation with `python -m claude_review`.

### Usage

```console
export GITHUB_TOKEN=github_pat_...
claude-review --pr https://github.com/owner/repository/pull/123
```

The command retrieves the pull-request metadata and unified diff through the
GitHub API, then invokes Claude Code in non-interactive mode. The default diff
limit is 250,000 bytes; it can be changed explicitly when reviewing a smaller
or larger change:

```console
claude-review \
  --pr https://github.com/owner/repository/pull/123 \
  --max-diff-bytes 500000 \
  --timeout 180
```

The output has exactly these sections:

```markdown
## Summary
Two or three sentences describing the change and its purpose.

## Identified risks
- A risk, or `None identified`.

## Improvement suggestions
- A suggested improvement, or `None identified`.

## Confidence
Medium
```

The reviewer treats pull-request text and diff contents as untrusted data. A
diff that is empty, too large, or accompanied by a GitHub API error is rejected
with a diagnostic on stderr. Claude output is also validated before it is
printed, so malformed output cannot be mistaken for a completed review.

To capture review artifacts for real public pull requests, redirect the output
to files after selecting PRs that are appropriate for your test run:

```console
claude-review --pr https://github.com/owner/repository/pull/123 > examples/pr-123.md
claude-review --pr https://github.com/owner/another-repository/pull/456 > examples/pr-456.md
```

The command requires network access to `api.github.com` and a working local
Claude Code installation. It intentionally has no automatic comment-posting
capability and requests only read access to GitHub data.

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
