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

## Review a public pull request

Install Python 3.9+ and [Claude Code](https://code.claude.com/docs/en/overview) version 2.1.248 or later. Sign in with `claude auth login` and check `claude auth status`. Put the executable `claude-review` on your PATH. On Windows, run `python claude-review` or use a Bash shell that supports executable scripts.

```bash
claude-review --pr https://github.com/pallets/click/pull/2581
```

The command sends only the diff to a named Claude Code review agent. The agent runs in an empty temporary directory in restricted mode, with no built-in tools or MCP servers. It returns an evidence-limited Markdown review on standard output. By default the command only reads GitHub. Use `--post` explicitly to publish one issue comment. Supply a `GH_TOKEN` authorized to comment in the target repository for that step. A token is optional for public reads and is removed from the agent environment. The command checks both base and head revisions before and after fetching the diff and again before posting. Diffs above 96,000 bytes must be divided into smaller PRs or reviewed separately.

`--facts-only` checks GitHub access and prints the same Markdown layout using patch counts. This mode runs without a model and cannot post a comment. The two [Click #2941](examples/click-2941.md) and [Click #2581](examples/click-2581.md) examples came from this mode. In the second PR the code change passes `re.ASCII` as the named `flags` argument to `re.sub`. This is a useful check for a reviewer because the fourth positional argument limits the number of replacements. In the first PR the changed line edits the documented Python entry point. A reviewer should verify it matches the example's module layout.

Run `python3 tests/test_review.py` for local formatting, credential isolation, revision and validation checks.

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
