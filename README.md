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


## Git history CHANGELOG generator

Requires Git and Bash 4 or later (on macOS, install a newer Bash rather than
using the system Bash 3.2).

### Setup and use

1. Copy `changelog.sh` into the repository whose history you want to document.
2. From that repository, run `bash changelog.sh`.
3. Review the generated `CHANGELOG.md` before publishing it.

The script includes commits since the nearest tag reachable from `HEAD`, including
lightweight tags. With no reachable tags, it includes the complete history.
It does not fetch remote history: fetch the desired commits/tags first if your
clone is shallow or outdated. Use `-o PATH` for a different output file, for example
`bash changelog.sh -o docs/CHANGELOG.md`. Existing output is replaced, not appended;
Git read failures leave it untouched.

Conventional prefixes (including scoped and breaking-change forms) and leading
action words map to `Added`, `Fixed`, and `Removed`. Other commits fall back to
`Changed`. These are message-based heuristics, not semantic analysis; review the
categories, particularly for repositories not using conventional commits. Each
entry includes its short commit ID. All four sections appear, even when empty.

### Validation and sample

Run `python3 -m unittest discover -s tests -v` for isolated Git fixture tests.
The checked-in [`CHANGELOG.md`](CHANGELOG.md) is a sample generated from this real
GitHub repository at upstream commit `1aeae2a` (two commits, no tags).
