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

## Included Bounty #3 package

This checkout includes the Claude Code `PreToolUse` safety hook in
`skills/block-destructive-hook/`:

- `block-destructive.sh` — protocol-aware hook that denies destructive Bash commands
- `command_parser.py` — structural classifier, including shell substitutions,
  `sh -c`/shell `-c`, and `eval` payloads
- `install.sh` — installs both files to `~/.claude/hooks/` and merges the Bash
  hook entry into `~/.claude/settings.json`
- `README.md` — package-specific registration and behavior documentation

From the package directory, install with:

```bash
cd skills/block-destructive-hook
./install.sh
```

Run the included protocol and regression checks from the repository root:

```bash
bash tests/test_block_destructive.sh
bash skills/block-destructive-hook/tests/test_block_destructive.sh
```

The first script is a fast smoke test of the classifier's acceptance-critical
paths; the second exercises the full JSON `PreToolUse` protocol against the
complete regression suite (shell wrappers, substitutions, brace expansion,
here-strings/heredocs, SQL clients, and more). Both must pass.

The hook is intentionally limited to blocking classified destructive commands;
safe commands remain neutral so Claude Code's normal permission flow applies.

## Community

- 🐦 X: [@ClaudeBounty](https://x.com/ClaudeBounty)
- 📧 Contact: claudebounty@gmail.com

---

*Started by the Claude builder community · March 2026 · MIT License*
