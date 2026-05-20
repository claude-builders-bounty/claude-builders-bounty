---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a project's git history, categorizing commits into Added / Fixed / Changed / Removed sections following the Keep-a-Changelog format. Use whenever the user asks to produce, refresh, or release-cut a changelog.
---

# Generate Changelog

A Claude Code skill that produces a properly formatted `CHANGELOG.md` entry by reading the project's git history since the last release tag and classifying each commit into Keep-a-Changelog sections.

## When to use this skill

Trigger this skill whenever the user says any of:

- "generate a changelog"
- "update the changelog"
- "what's changed since v1.2.0?"
- "cut a release" / "prepare release notes"
- runs `/generate-changelog` in Claude Code

Also use it preemptively when the user runs `git tag` on a new release version — offer to generate the entry.

## What this skill does

1. Locates the last released version by reading the most recent annotated git tag.
2. Reads every commit between that tag and `HEAD`.
3. Classifies each commit into one of four buckets based on its message prefix:
   - **Added** — `feat:`, `feature:`, `add:`
   - **Fixed** — `fix:`, `bug:`, `bugfix:`, `hotfix:`
   - **Changed** — `refactor:`, `chore:`, `style:`, `perf:`, `docs:`, `ci:`, `build:`, `test:`
   - **Removed** — `revert:`, `remove:`, `deprecate:`
   - Unprefixed commits default to **Changed**.
4. Renders a new section at the top of `CHANGELOG.md` using Keep-a-Changelog formatting, with the version (next semver bump, asked from the user) and today's date.
5. Preserves all existing content in `CHANGELOG.md` (or creates the file with a Keep-a-Changelog header if it doesn't exist).

## Workflow

### Step 1 — Verify a git repository

```bash
git rev-parse --is-inside-work-tree
```

If this fails, stop and tell the user the skill must be run inside a git repo.

### Step 2 — Find the last release tag

```bash
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
```

- If `LAST_TAG` is empty, this is the first release — use the entire history: `RANGE=""`.
- Otherwise: `RANGE="${LAST_TAG}..HEAD"`.

### Step 3 — Read commits

```bash
git log ${RANGE} --no-merges --pretty=format:'%H%x09%s%x09%an'
```

Each line is `<sha>\t<subject>\t<author>`. Skip merge commits.

### Step 4 — Classify each commit

For each commit subject, lowercase the part before the first `:` and match against this table:

| Prefix | Section |
|--------|---------|
| `feat`, `feature`, `add` | Added |
| `fix`, `bug`, `bugfix`, `hotfix` | Fixed |
| `refactor`, `chore`, `style`, `perf`, `docs`, `ci`, `build`, `test` | Changed |
| `revert`, `remove`, `deprecate` | Removed |
| any other / no prefix | Changed |

Strip the prefix from the subject when rendering. Conventional-commit scope (`feat(api): …`) is preserved as a parenthetical.

### Step 5 — Ask the user for the new version

```
Last release: v1.2.3 (tag: v1.2.3, 2026-04-15)
12 commits since then.
What version should this changelog entry be tagged as?
  - patch:  v1.2.4
  - minor:  v1.3.0
  - major:  v2.0.0
```

Default to patch unless any commit is `feat:` (minor) or `BREAKING CHANGE:` (major).

### Step 6 — Render the section

Use this template, dropping any empty section:

```markdown
## [<VERSION>] - <YYYY-MM-DD>

### Added
- <subject> ([<short-sha>](../../commit/<full-sha>))

### Fixed
- <subject> ([<short-sha>](../../commit/<full-sha>))

### Changed
- <subject> ([<short-sha>](../../commit/<full-sha>))

### Removed
- <subject> ([<short-sha>](../../commit/<full-sha>))
```

### Step 7 — Write to CHANGELOG.md

- If the file exists, insert the new section directly after the top header (after the `# Changelog` line and any introductory blurb, before the first existing `## [...]` section).
- If it doesn't exist, create it with this header:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
```

### Step 8 — Show the diff

Run `git diff CHANGELOG.md` and show it to the user before they commit. Do not commit automatically.

## Bash fallback

A standalone `changelog.sh` is included for use outside Claude Code (CI pipelines, git hooks). Run it from the repo root:

```bash
./changelog.sh > NEW_SECTION.md
```

The bash script applies the same classification rules and prints the section to stdout. The user is responsible for splicing it into `CHANGELOG.md`.

## Edge cases

- **No tags exist** — Treat all commits as the first release. Ask the user for the initial version (default `0.1.0`).
- **No commits since last tag** — Tell the user there's nothing to release and stop.
- **Merge commits** — Skip them (`--no-merges`). The conventional-commit prefix on merge commits is rarely meaningful.
- **Reverts** — `revert:` commits go under Removed. If a `revert:` undoes a `feat:` in the same range, leave both in (the changelog is a record, not a balance sheet).
- **BREAKING CHANGE footer** — When a commit body contains `BREAKING CHANGE:`, prepend `**BREAKING:**` to the rendered subject in whichever section it landed.

## Example output

See `sample-output.md` in this skill directory for a real CHANGELOG entry generated from a public repo.
