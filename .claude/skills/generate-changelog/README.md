# generate-changelog

Generates a structured `CHANGELOG.md` from your project's real git history —
no fabricated entries, no dependencies beyond Git + Bash.

## Quick Start

1. Copy the `.claude/skills/generate-changelog/` directory into your repo (or
   use it directly from here if you're already in this repo).
2. Run `/generate-changelog` in Claude Code, or from your repository root:
   ```bash
   bash .claude/skills/generate-changelog/changelog.sh
   ```
3. Review the `## Unreleased` section of the resulting `CHANGELOG.md`.

## What it does

- Validates you're inside a git work tree; exits with an error (no file
  written) if not.
- Finds the latest reachable tag (`git describe --tags --abbrev=0`) and
  analyzes `<tag>..HEAD`. If there's no tag, it analyzes the full reachable
  history instead and says so.
- Collects non-merge commits and categorizes each one:
  - **Added** — `feat:`, `feat(scope):`, `add:`, `added:`
  - **Fixed** — `fix:`, `fix(scope):`, `bugfix:`, `fixed:`, `hotfix:`
  - **Removed** — `remove:`, `removed:`, `delete:`, `deleted:`
  - **Changed** — everything else meaningful: `refactor:`, `perf:`, `docs:`,
    `style:`, `test:`, `build:`, `ci:`, `chore:`, and any commit that doesn't
    follow conventional-commit syntax at all (nothing is discarded just for
    lacking a prefix — it's kept, verbatim, under Changed).
- Strips the `type(scope):` prefix from the displayed entry and capitalizes
  the first letter; issue references like `#123` are left untouched. Nothing
  is invented — every line comes directly from a real commit subject.
- Writes only non-empty `###` sections, in the order Added / Fixed / Changed
  / Removed, with exactly one trailing newline.

## No tags yet?

That's fine — the script analyzes full history from the repository root
instead of erroring out, and tells you it's doing so.

## Existing `CHANGELOG.md`?

Safe. The script only ever replaces the `## Unreleased` section; every past
`## <version>` release section — including its internal formatting, such as
blank lines — is preserved exactly as written. Running it twice in a row
with no new commits produces an identical file — it's idempotent and never
duplicates entries.

## No new commits since the last tag?

The script prints `No commits found since <tag>.` and exits `0` without
touching `CHANGELOG.md` at all.

## Sample output

See [`sample-output/CHANGELOG.md`](sample-output/CHANGELOG.md) — real output
generated from a genuine, unmodified 17-commit window of
[`nestjs/nest`](https://github.com/nestjs/nest)'s public git history
(selected via a local-only tag to keep the sample readable; every commit
subject shown is real and untouched). It also runs cleanly against this
repository's own history — see the PR description for that output.

## Tests

From your repository root:

```bash
bash .claude/skills/generate-changelog/tests/test_changelog.sh
```

(or `bash tests/test_changelog.sh` if you're already inside this directory)

Builds disposable temporary git repositories (own local identity, never your
global git config) and covers: tag detection, the no-tag fallback,
conventional-commit categorization for all four categories, non-conventional
commits falling back to Changed, history preservation, idempotency, the
zero-new-commits case, punctuation and issue references in messages,
one-commit repos, merge-commit exclusion, and that commit text containing
`$(...)`/backtick command substitution or a leading `-` is always treated as
inert data and never executed or parsed as a flag.
