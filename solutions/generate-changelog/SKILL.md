---
name: generate-changelog
description: >
  Generate a structured CHANGELOG.md from this project's git history.
  Fetches commits since the last git tag, auto-categorises them into
  Added / Fixed / Changed / Removed, and writes a clean Markdown file.
  Call this skill whenever the user asks to generate, update, or refresh
  the project changelog.
---

# generate-changelog

Creates a `CHANGELOG.md` (or updates one in place) by parsing `git log`
since the last tag and classifying each commit by type.

## Usage inside Claude Code

Run the bundled shell script:

```bash
bash changelog.sh
```

Optional arguments:

```bash
bash changelog.sh CHANGELOG.md --from v1.2.0 --to HEAD
```

| Argument | Default | Description |
|----------|---------|-------------|
| `output_file` | `CHANGELOG.md` | Where to write the output |
| `--from <ref>` | last git tag | Start of the commit range |
| `--to <ref>` | `HEAD` | End of the commit range |

## Slash command

When invoked via `/generate-changelog`, Claude Code runs:

```bash
bash changelog.sh
```

and then shows the resulting `CHANGELOG.md` in the editor.

## Categorisation rules

Commits are matched in this order (first match wins):

| Category | Conventional prefix or keyword |
|----------|-------------------------------|
| **Added** | `feat`, `add`, `implement`, `new feature` |
| **Fixed** | `fix`, `bug`, `patch`, `hotfix`, `resolve`, `repair` |
| **Removed** | `remove`, `drop`, `delete`, `deprecat` |
| **Changed** | `refactor`, `chore`, `style`, `perf`, `ci`, `build`, `docs`, `test`, `update`, `change`, `improve`, `bump`, `rename` |
| **Other** | everything else |

Conventional-commit scopes are stripped in the output:
`feat(api): add endpoint` → `feat: add endpoint`.

## Requirements

- `bash` 3+ (macOS default works)
- `git` in PATH
- A git repository with at least one commit
