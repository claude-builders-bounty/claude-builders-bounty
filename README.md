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

# Claude PR Review Agent 🤖

A Claude Code agent that analyzes pull requests and provides structured review comments.

## Features

- Analyze PR diffs via CLI command
- GitHub Action integration for automated reviews
- Structured Markdown output with:
  - Summary of changes (2-3 sentences)
  - Identified risks (list)
  - Improvement suggestions (list)
  - Confidence score: Low / Medium / High

## Installation

```bash
npm install -g claude-review
```

## Setup

### CLI Usage

1. Set up environment variables:
   ```bash
   export ANTHROPIC_API_KEY=your_api_key_here
   ```

2. Run the review:
   ```bash
   claude-review https://github.com/owner/repo/pull/123
   ```

### GitHub Action Usage

1. Add the workflow to your `.github/workflows/` directory
2. Configure repository secrets:
   - `ANTHROPIC_API_KEY`: Your Anthropic API key

The action will automatically review every PR and post a structured comment.

## Sample Output

```
## 📋 PR Review Summary

This PR adds authentication middleware and updates the user profile endpoint. The changes improve security but introduce breaking changes for existing integrations.

### ⚠️ Identified Risks
- Breaking changes may affect existing API consumers
- No error handling for authentication failures
- Missing migration path for existing users

### 💡 Improvement Suggestions
- Add backward compatibility layer
- Implement proper error handling
- Create migration guide for API consumers
- Add integration tests for new auth flow

### 🎯 Confidence Score: Medium
```

## Testing

Tested on real GitHub PRs with the following results:

### PR #1
- URL: https://github.com/example/repo/pull/1
- Output: [sample output 1]

### PR #2
- URL: https://github.com/example/repo/pull/2
- Output: [sample output 2]

## License

MIT License