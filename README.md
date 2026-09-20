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

## Security Hooks (Issue #3)

### Pre-Tool-Use Security Hook: Block Destructive Bash Commands

Intercepts dangerous bash commands (`rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without `WHERE`) before execution and logs blocked attempts to `~/.claude/hooks/blocked.log`.

#### Quick Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/block_destructive.py -o ~/.claude/hooks/block_destructive.py && chmod +x ~/.claude/hooks/block_destructive.py
```

#### Running Tests

```bash
python3 -m unittest discover -s tests
```

---

## Workflows (Issue #5)

### Weekly Dev Summary (n8n + Claude Code)

Automated n8n workflow (`workflows/weekly_dev_summary.json`) that fetches commits, closed issues, and merged PRs from GitHub API every Friday at 5 PM, summarizes them with Claude API (`claude-sonnet-4-20250514`), and sends the update via Discord/Slack webhook in English or French.

#### Quick Setup (5 Steps)

1. **Import**: Import `workflows/weekly_dev_summary.json` into n8n.
2. **Configure**: Edit the **Set Configuration** node with your `GITHUB_OWNER`, `GITHUB_REPO`, `WEBHOOK_URL`, `ANTHROPIC_API_KEY`, and `LANGUAGE` (`EN`/`FR`).
3. **Schedule**: Confirm trigger is set for **Friday 5:00 PM**.
4. **Test**: Run workflow to test GitHub fetching, Claude summarization, and webhook delivery.
5. **Activate**: Switch workflow toggle to **Active**.

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
