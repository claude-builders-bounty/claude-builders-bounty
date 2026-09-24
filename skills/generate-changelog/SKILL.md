---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a project's git history, categorizing commits into Added / Fixed / Changed / Removed. Use when the user asks to "generate a changelog", "update the changelog", or "summarize commits since the last release".
---

# Generate Changelog

Create or update `CHANGELOG.md` from git history, using the last git tag as the
baseline (or full history if no tags exist).

## When to use

- The user says: "generate a changelog", "update CHANGELOG", "what changed since the last release".
- Before cutting a release.

## How to run

Run the bundled script from the repository root:

```bash
bash changelog.sh
```

Options:

| Flag | Effect |
|------|--------|
| `--stdout` | Print the section instead of writing `CHANGELOG.md` |
| `--from <ref>` | Use a specific base ref instead of the last tag |
| `--version <x.y.z>` | Label the new section with a version |
| `--out <path>` | Write to a custom path instead of `CHANGELOG.md` |

## Behavior

1. Finds the base ref: last git tag, or full history if none.
2. Reads non-merge commits in `<base>..HEAD`.
3. Categorizes each commit via Conventional Commits prefixes
   (`feat:` → Added, `fix:` → Fixed, `refactor:`/`docs:`/`chore:` → Changed,
   `remove:`/`revert:` → Removed), with a keyword fallback for plain messages.
4. Prepends a dated section to `CHANGELOG.md`, preserving prior history.

## Example

```bash
$ bash changelog.sh --version 1.3.0
Wrote CHANGELOG.md (range: v1.2.0, 2 added / 1 fixed / 1 changed / 1 removed)
```
