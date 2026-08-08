# Claude Builders Bounty

> A community bounty board for Claude Code builders.

Building with Claude Code? Have tasks to delegate? Want to get paid for contributing to AI projects? You are in the right place.

## How it works

**To post a bounty**
1. Open a GitHub issue with a clear description and acceptance criteria.
2. Comment `/opire create $XXX` in the issue to set the reward.
3. Share the link so contributors can find it.

**To claim a bounty**
1. Browse the open issues below.
2. Comment `/opire try` in the issue you want to work on.
3. Submit a PR; payment is automatic on merge.

## Active Bounties

| # | Task | Amount | Status |
|---|------|--------|--------|
| [#1](../../issues/1) | SKILL: Generate a CHANGELOG from git history | $50 | Open |
| [#2](../../issues/2) | TEMPLATE: CLAUDE.md for a Next.js + SQLite project | $75 | Open |
| [#3](../../issues/3) | HOOK: Block destructive bash commands in Claude Code | $100 | Open |
| [#4](../../issues/4) | AGENT: PR reviewer with structured Markdown output | $150 | Open |
| [#5](../../issues/5) | WORKFLOW: n8n + Claude API - automated weekly dev summary | $200 | Open |

## Rules

- Tasks must be related to Claude Code or AI tooling.
- Every issue must have clear acceptance criteria before a bounty is activated.
- Payment is handled by [Opire](https://opire.dev) (Stripe).
- Quality over speed: a solid PR beats a fast one.

## Prepared implementations

### CHANGELOG generator (#1)

1. Run `python3 scripts/changelog.py --repo /path/to/project` (or `bash scripts/changelog.sh`).
2. The script reads commits after the latest tag and writes `CHANGELOG.md`.
3. Use `--stdout` to preview the generated document.

It categorizes conventional commit subjects into `Added`, `Fixed`, `Changed`, and `Removed`. See [`examples/sample-CHANGELOG.md`](examples/sample-CHANGELOG.md) for the output from a real repository run.

### Destructive-command hook (#3)

1. Copy `.claude/settings.json` and `.claude/hooks/block-destructive.py` into the project.
2. Start Claude Code; the `PreToolUse` hook is loaded automatically.
3. Review blocked attempts in `~/.claude/hooks/blocked.log`.

The hook denies `rm -rf`, `DROP TABLE`, `TRUNCATE`, forced `git push`, and `DELETE FROM` statements without a `WHERE` clause while leaving safe commands to the normal permission flow.

## Community

- Contact: claudebounty@gmail.com

*Started by the Claude builder community - March 2026 - MIT License*
