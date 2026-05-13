# Claude Builders Bounty

**Earn money building open-source tools for Claude Code.**

Claim a GitHub issue → build the tool → open a PR → get paid automatically on merge via Stripe.

🌐 **[claude-bounty-site.vercel.app](https://claude-bounty-site.vercel.app)**

---

## 💰 Open Bounties

| # | Task | Reward | Status |
|---|------|--------|--------|
| [#1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1) | **CHANGELOG skill** — auto-generate CHANGELOG from git history using Claude Code | $50 | 🟢 Open |
| [#2](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2) | **CLAUDE.md template** — sensible defaults for Next.js + SQLite SaaS projects | $75 | 🟢 Open |
| [#3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3) | **Destructive bash blocker hook** — prevent `rm -rf`, `DROP TABLE`, etc. before they run | $100 | 🟢 Open |
| [#4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4) | **Claude Code PR review sub-agent** — reads open PRs and posts structured review comments | $150 | 🟢 Open |
| [#5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5) | **n8n + Claude Code weekly dev summary** — automated workflow that generates and sends a weekly digest | $200 | 🟢 Open |

**Total pool: $575** — more bounties coming as these get claimed.
## Deliverable for Issue #1

### Files
- `changelog.sh` (executable Bash script)
- `.claude/commands/generate-changelog` (optional Claude Code command shim)
- `docs/changelog-sample.md` (sample output)

### Setup and usage (3 steps)
```bash
chmod +x changelog.sh
./changelog.sh
cat CHANGELOG.md
```

If you use Claude Code, you can also run:
```bash
/generate-changelog
```

This generates a `CHANGELOG.md` file using commits since the latest tag, grouped into
`Added`, `Fixed`, `Changed`, and `Removed`.

---

## 🚀 How it works

### For builders

1. **Browse issues** — each open issue is a paid task with a clear spec
2. **Claim it** — comment `/assign` on the issue to reserve it (one per person at a time)
3. **Fork & build** — implement the tool, skill, hook, or workflow described
4. **Open a PR** — include tests, a demo GIF or output, and a short description
5. **Get paid** — payment is sent automatically via [Opire](https://opire.dev) + Stripe once your PR is merged

No invoices. No waiting. Payment on merge.

### For sponsors

Want to add a bounty? [Open an issue](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/new) with:
- A clear description of what you want built
- The reward amount you're offering
- Acceptance criteria

---

## 📦 What can be bounty-funded?

- **Skills** (`.claude/skills/`) — reusable workflows invoked by Claude Code
- **Hooks** (pre/post tool hooks) — validation, safety checks, formatting
- **CLAUDE.md templates** — project-specific context files
- **Sub-agents** — specialized agents for code review, testing, deployment
- **MCP integrations** — tools that connect Claude Code to external services
- **Automation workflows** — n8n, Make, Zapier workflows that integrate Claude Code

---

## 🛠 Stack

- **Payments**: [Opire](https://opire.dev) (bounty management) + Stripe
- **Issues**: GitHub Issues (bounty tracking)
- **Landing**: [claude-bounty-site.vercel.app](https://claude-bounty-site.vercel.app)

---

## 📬 Stay updated

- Twitter: [@ClaudeBounty](https://twitter.com/ClaudeBounty)
- GitHub Discussions: [Announcements](https://github.com/claude-builders-bounty/claude-builders-bounty/discussions)

---

*Built with Claude Code · Bounties paid via Opire + Stripe*
