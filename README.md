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

## CHANGELOG Generator (#1)

A zero-dependency CLI and Claude Code skill that parses git history and conventional commits into a structured Keep a Changelog Markdown document.

### Setup & Usage (3 steps)

1. Clone repository and ensure Python 3 is installed.
2. Run `./changelog.sh --version 1.0.0` or `python3 bin/generate-changelog -o CHANGELOG.md`.
3. Include in Claude Code workflows via `skills/generate-changelog/SKILL.md`.

Run tests with `python3 -m unittest discover -s tests`.

Sample output: `examples/changelog-sample.md`.

### Reproduce the real-repository sample

The sample comes from [psf/requests](https://github.com/psf/requests), not
synthetic commits. It contains the 14 commits in
[`v2.32.4..v2.32.5`](https://github.com/psf/requests/compare/v2.32.4...v2.32.5):

- Baseline `v2.32.4`: `021dc729f0b71a3030cefdbec7fb57a0e80a6cfd`.
- Checked-out `v2.32.5`: `b25c87d7cb8d6a18a37fa12442b5f883f9e41741`.

From this repository's root:

```sh
git clone --no-tags --branch v2.32.5 https://github.com/psf/requests.git /tmp/requests-changelog-example
git -C /tmp/requests-changelog-example fetch origin refs/tags/v2.32.4:refs/tags/v2.32.4 refs/tags/v2.32.5:refs/tags/v2.32.5
python3 bin/generate-changelog --repo /tmp/requests-changelog-example --since-tag v2.32.4
```

The example's `Unreleased` heading uses the generator's run date, not the
upstream release date. The wrapper produces the same output with the same
arguments. Both entry points were exercised against this pinned history;
Requests' own code was not executed.

Invalid repositories or revision ranges exit nonzero. If Git history lookup
fails, an existing `--output` file is left untouched instead of being replaced
with a misleading empty changelog.
