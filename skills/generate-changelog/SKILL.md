# generate-changelog

Generate a structured CHANGELOG.md from git history. Groups commits by type using conventional commit prefixes, organizes by version tag or date range, and outputs clean markdown.

## Usage

```
/generate-changelog
/generate-changelog --since v1.2.0
/generate-changelog --since 2026-03-01 --until 2026-03-26
```

## What it does

1. Reads git log (from last tag, or specified range)
2. Parses conventional commit prefixes (feat, fix, refactor, docs, chore, perf, test, ci, build)
3. Groups commits into sections (Added, Fixed, Changed, etc.)
4. Outputs a CHANGELOG.md entry with the version/date header

## Mapping

| Prefix | Section |
|--------|---------|
| feat | Added |
| fix | Fixed |
| refactor, perf | Changed |
| docs | Documentation |
| test | Tests |
| chore, ci, build | Maintenance |
| breaking, BREAKING CHANGE | Breaking Changes |
| (no prefix) | Other |

## Instructions for Claude

When the user runs `/generate-changelog`, execute the `generate-changelog.sh` script in this directory. Pass any arguments through. Read the output and write it to CHANGELOG.md (or append to existing). If the file already exists, prepend the new entry at the top, below any existing header.

If commits don't follow conventional commit format, do your best to categorize them by reading the message content. Group obvious bug fixes under Fixed, new functionality under Added, etc.

Don't include merge commits or commits that just say "merge" or "Merge branch".
