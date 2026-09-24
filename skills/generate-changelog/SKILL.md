---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commit history since the last tag. Use when asked to create or update a changelog, write release notes, or run /generate-changelog.
allowed-tools: Bash, Read, Write
---

# Generate Changelog

Run the bundled script from the repository root:

```bash
bash changelog.sh
```

Or invoke the skill script directly:

```bash
bash skills/generate-changelog/changelog.sh
```

## Options

- `--since <tag>` — start from a specific tag instead of the latest
- `--version <name>` — override the release header (e.g. `1.2.0`)
- `--output <file>` — write to a different file (default: `CHANGELOG.md`)
- `--preview` — print to stdout without writing a file
- `--append` — prepend a new release section to an existing `CHANGELOG.md`

Repeated `--append` runs with the same `--version` replace that version's generated section rather than duplicating it.

## Behavior

1. Detects the nearest tag along the first-parent mainline (or uses `--since`)
2. Validates that the repository has commits and the selected tag resolves to an ancestor of `HEAD`
3. Collects commits after that tag
4. Categorizes conventional commits into **Breaking**, **Added**, **Fixed**, **Changed**, and **Removed**
5. Writes a Keep a Changelog-style `CHANGELOG.md`

## Classification

| Commit prefix | Section |
|---------------|---------|
| `feat:`, `add:`, `implement:`, `create:`, `new:` | Added |
| `fix:`, `bug:`, `bugfix:`, `hotfix:`, `patch:`, `resolve:` | Fixed |
| `update:`, `change:`, `refactor:`, `migrate:`, `perf:`, `docs:`, `chore:`, `ci:`, `test:` | Changed |
| `remove:`, `delete:`, `deprecate:`, `drop:` | Removed |
| `feat!:`, `fix!:` (breaking suffix) | Breaking + primary section |

Unrecognized commit subjects are retained under **Uncategorized**, with a manual-review note. Known change prefixes still map to **Changed**. Classification uses the commit prefix or leading word; it does not infer meaning from the diff, so review the generated notes before publishing. Literal backslash sequences in subjects are preserved.

Shallow repositories are rejected before output is written because their release history may be incomplete. Fetch full history and tags before retrying. Empty repositories and invalid or unrelated release boundaries also fail without replacing output.

Automatic release boundaries follow the first-parent history, so a tag on a merged topic branch cannot hide unreleased mainline changes. Commit collection still includes non-merge commits from merged branches. Use `--since <tag>` to select a different ancestor explicitly.
