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

## Generate a structured changelog (bounty #1)

1. Install Git, Bash and Python 3.8+; clone this repository. No Python packages or API calls are needed.
2. Run `bash changelog.sh --repo /path/to/project` from this checkout, or use the absolute path to `changelog.sh` from any directory.
3. Review the generated `CHANGELOG.md` in the target repository root before committing it.

`--stdout` prints the document without writing a file. `--output notes.md` writes to a path relative to your current directory. The output is a generated **Unreleased snapshot**; running again replaces the output file, including any manual content in it. Use a separate output path if you maintain historical release notes manually.

The range is the nearest tag reachable from HEAD, as selected by `git describe --tags --abbrev=0`, exclusive, through HEAD. Annotated and lightweight tags work; unrelated branch tags are ignored. With no reachable tag, all HEAD history is included. Merge commits are omitted while their individual commits remain included. An empty repository or a tag at HEAD produces four empty sections. The script reads local history only; fetch the intended history/tags yourself when working with a shallow clone.

Conventional `feat` commits become **Added**, `fix`/`bugfix`/`hotfix` become **Fixed**, and `remove`/`delete`/`drop` become **Removed**. Other types become **Changed**. Common initial verbs such as Add, Fix and Remove provide the same categorization for non-conventional subjects. Scopes are retained; `!` is marked as a breaking change. This is deterministic subject-based categorization, not semantic analysis of diffs or commit bodies. Subjects are escaped as literal Markdown and each entry includes a commit identifier.

Run the seven real-Git integration tests with `python3 -m unittest discover -s tests -v`. A generated [real-repository sample](examples/git-context-CHANGELOG.md) and its [reproduction instructions](examples/README.md) are included.
