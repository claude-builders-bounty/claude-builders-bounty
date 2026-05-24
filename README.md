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

## Tools

### `claude-review`

`claude-review` is a focused local PR review CLI for issue
[#4](../../issues/4). It does not call the Claude API, does not require API
secrets, and never posts comments or pushes changes. Instead it fetches pull
request metadata and a unified diff, runs deterministic heuristics, and prints
structured Markdown.

Install locally from this repository:

```bash
python3 -m pip install -e .
```

Review a pull request:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

The command prefers the GitHub CLI when `gh` is installed and authenticated:

```bash
gh pr view https://github.com/owner/repo/pull/123 --json ...
gh pr diff https://github.com/owner/repo/pull/123
```

If `gh` is unavailable or fails, it falls back to unauthenticated GitHub REST
requests for public repositories. Private repositories require working `gh`
access.

Output sections:

- `Summary of Changes`: PR identity, author, state, branch, line counts, and
  changed areas.
- `Risks`: deterministic flags for size, missing tests, security-sensitive
  paths, migrations, CI/workflow edits, dependency files, binary diffs, and
  deletions.
- `Improvement Suggestions`: practical follow-ups based on the detected risks.
- `Confidence`: `Low`, `Medium`, or `High` based on diff visibility, size, and
  risk profile.

Sample outputs for real public PRs are in
[docs/sample-outputs.md](docs/sample-outputs.md).

Run the smoke tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

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
