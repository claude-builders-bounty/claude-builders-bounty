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

This repository includes a small Claude Code PR review agent for bounty
[#4](../../issues/4). It can review a GitHub pull request and return a
structured Markdown comment.

### CLI usage

```bash
node bin/claude-review.js --pr https://github.com/owner/repo/pull/123
```

The installed binary name is `claude-review`:

```bash
npm link
claude-review --pr https://github.com/owner/repo/pull/123
```

Output always uses this structure:

```markdown
## Summary of changes
...

## Identified risks
- ...

## Improvement suggestions
- ...

## Confidence score
Medium - ...
```

### Review engines

By default the CLI runs in `auto` mode:

- It first tries to call the local Claude CLI command.
- If Claude is unavailable, it falls back to a deterministic local analyzer.

Use `--mode claude` to require Claude, or `--mode heuristic` for deterministic
offline output:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --mode heuristic
```

Environment variables:

- `GITHUB_TOKEN`: optional GitHub token for API limits and posting comments.
- `CLAUDE_REVIEW_COMMAND`: Claude command name. Default: `claude`.
- `CLAUDE_REVIEW_ARGS`: arguments before the prompt. Default: `-p`.

### GitHub Action

The workflow in `.github/workflows/claude-review.yml` runs on pull requests and
posts the structured review as a PR comment when `GITHUB_TOKEN` has permission.

### Claude Code agent

The reusable Claude Code agent instructions live at
`.claude/agents/pr-reviewer.md`.

### Sample outputs

Two real GitHub PR sample outputs are included under `samples/`:

- `samples/sample-claude-builders-pr-139.md`
- `samples/sample-nodejs-pr-58780.md`

### Validation

```bash
npm test
```

The tests cover PR URL parsing and the required Markdown output sections.

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
