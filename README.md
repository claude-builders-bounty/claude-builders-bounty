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

## Changelog generator (#1)

Requirements: Git, Bash, and Python 3.8 or newer. No packages or API keys needed.

### Setup and run

1. Clone this repository: `git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git`
2. Enter it: `cd claude-builders-bounty`
3. Generate a changelog: `bash changelog.sh --repo /path/to/your/project`

This writes `CHANGELOG.md` in the target repository. You can also run
`python3 generate_changelog.py --repo /path/to/your/project` directly.
Use `--output -` to preview on stdout, `--output /path/to/draft.md` to choose a
file, or `--force` to explicitly replace existing output. Existing changelogs
are preserved unless you request replacement; historical releases are not merged.
Paths containing spaces should be quoted.

The generator reads non-merge commits after the nearest tag reachable from
`HEAD` (`git describe --tags --abbrev=0 HEAD`), supporting both lightweight and
annotated tags. Without a reachable tag it reads the whole history. Fetch the
tags first if they are missing locally. Shallow clones are rejected because
their tag boundary can be incomplete: use `git fetch --unshallow --tags`.
An empty commit range produces four empty sections; a repository without
commits reports an error. The script does not make network requests.

| Commit subject | Category |
|---|---|
| `feat:`, `feature:`, `add:` | Added |
| `fix:`, `bugfix:`, `hotfix:` | Fixed |
| `remove:`, `delete:`, `drop:` | Removed |
| Other prefixes or ambiguous messages | Changed |

Conventional Commit scopes and breaking markers are supported, such as
`feat(cli)!:`. Plain messages beginning with Add/Introduce/Implement,
Fix/Resolve/Repair, or Remove/Delete/Drop follow the corresponding category.
Classification uses commit subjects, so review the generated draft before
publishing. Subjects are escaped for Markdown; entries retain their commit hash.
Repeated runs over the same history produce identical output.

### Verification and real repository sample

Run `python3 -m unittest -v test_changelog.py` for temporary Git repository checks
covering tag boundaries, categories, escaping, Unicode, paths with spaces,
empty history, overwrite protection, and incomplete shallow history.

[`examples/CHANGELOG.md`](examples/CHANGELOG.md) was generated from this public
GitHub repository at commit
[`1aeae2a`](https://github.com/claude-builders-bounty/claude-builders-bounty/commit/1aeae2a).
That revision has two commits and no tags. To reproduce without changing your
current checkout, run these from this repository (choose an unused sample path):

```bash
git worktree add --detach ../changelog-sample 1aeae2a
bash changelog.sh --repo ../changelog-sample --output -
```

---

## Community

- 🐦 X: [@ClaudeBounty](https://x.com/ClaudeBounty)
- 📧 Contact: claudebounty@gmail.com

---

*Started by the Claude builder community · March 2026 · MIT License*
