# Claude Builders Bounty 🤖

> A community bounty board for Claude Code builders — with automated weekly dev summaries.

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

| [#3](../../issues/3) | HOOK: Block destructive bash commands in Claude Code | $100 | 🟢 Open |
| [#4](../../issues/4) | AGENT: PR reviewer with structured Markdown output | $150 | 🟢 Open |
| [#5](../../issues/5) | WORKFLOW: n8n + Claude API — automated weekly dev summary | $200 | 🟢 Open |
| [#6](../../issues/6) | WORKFLOW: n8n + Claude Code — automated weekly dev summary | $200 | ✅ Done |

---

| [#5](../../issues/5) | WORKFLOW: n8n + Claude API — automated weekly dev summary | $200 | 🟢 Open |

---

## Rules

- Tasks must be related to Claude Code or AI tooling
- Every issue must have clear acceptance criteria before a bounty is activated
- Payment is handled by [Opire](https://opire.dev) (Stripe)
- Quality over speed — a solid PR beats a fast one


---

## Workflows

### Weekly Dev Summary (n8n)

Automatically generates a narrative summary of this repo's weekly activity using Claude API.

- **Trigger:** Every Friday at 5pm UTC
- **Sources:** GitHub commits, closed issues, merged PRs (past 7 days)
- **AI:** Claude Sonnet 4 (`claude-sonnet-4-20250514`)
- **Delivery:** Email or Discord/Slack webhook (configurable)
- **Languages:** English / French (configurable)
- **Setup:** See [`workflows/weekly-dev-summary/README.md`](workflows/weekly-dev-summary/README.md)
- **Workflow file:** [`workflows/weekly-dev-summary/weekly-dev-summary.json`](workflows/weekly-dev-summary/weekly-dev-summary.json)

*Started by the Claude builder community · March 2026 · MIT License*
- 🐦 X: [@ClaudeBounty](https://x.com/ClaudeBounty)
- 📧 Contact: claudebounty@gmail.com

---

*Started by the Claude builder community · March 2026 · MIT License*
