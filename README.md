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

## Generate a changelog

Create a release-note draft from local Git commit subjects:

1. Install Git 2+, Bash and Python 3.9+.
2. Copy `changelog.sh` and `generate_changelog.py` into your project's root.
3. In that project, run `bash changelog.sh` and review `CHANGELOG.md`.

The script selects the nearest tag reachable from `HEAD`, including lightweight
and annotated tags, and includes only commits after that tag. If no reachable tag
exists, it uses all available history. Fetch the history and tags you want before
running it in a shallow clone. Commits appear oldest first within each category.
An already tagged `HEAD` produces four empty sections.

Conventional subjects beginning with `feat:`, `feature:` or `add:` go under Added;
`fix:`, `bugfix:` and `hotfix:` go under Fixed; `remove:`, `delete:` and `drop:` go
under Removed. Scope and breaking-change markers, such as `feat(api)!:`, work too.
Other conventional types go under Changed. Their prefix is removed from the entry.
Plain subjects starting with add, introduce or implement (including past tense)
go under Added; fix or resolve go under Fixed; remove, delete or drop go under
Removed. Other subjects go under Changed. Each entry includes its commit hash.
Review these mechanical categories before publishing release notes.

Existing changelogs are preserved. After reviewing an existing draft, explicitly
replace it with `bash changelog.sh --overwrite`. To keep authored release history,
write a separate draft and copy the relevant entries yourself:

```bash
bash /path/to/changelog.sh --repo "/path/to/project" --output release-draft.md
```

The default output is the repository root's `CHANGELOG.md`. A relative `--output`
path is relative to your current directory. Non-Git directories, repositories
without commits and unwritable outputs return a nonzero status with a diagnostic.
Identical history produces identical output.

### Example and checks

[Sample output](example/CHANGELOG.md) comes from the five commits after `v0.2.1`
in [rxi/vec](https://github.com/rxi/vec), pinned at
`20e84224ceb29a8f76d2b9d0ccfc547258a14ec5`.
[Provenance](example/provenance.json) records the tag commit and bundled history
digest. The bundled repository is MIT licensed; its notice is retained in
[vec-LICENSE](example/vec-LICENSE).

Run from this solution's root with Git, Bash and Python installed:

```bash
python3 -m unittest discover -s tests -v
bash -n changelog.sh
python3 tests/verify_example.py
```

The tests create temporary Git repositories and invoke the Bash entry point. The
example check clones the bundled public history into a temporary directory,
follows the three setup steps, checks stdout and exit status, and compares the
generated Markdown byte for byte with the sample. It needs no network connection.
