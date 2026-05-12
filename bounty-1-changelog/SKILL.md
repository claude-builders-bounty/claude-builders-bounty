---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history, auto-categorizing commits into Added/Fixed/Changed/Removed sections based on conventional commit prefixes or keyword heuristics.
---

# Generate Changelog

You are generating a structured CHANGELOG.md from git commit history. Follow these steps precisely.

## Step 1: Determine the version range

Run this command to find the latest git tag:

```bash
git describe --tags --abbrev=0 2>/dev/null
```

- If a tag is found, store it as `LAST_TAG`. The new version heading will reference commits "since `LAST_TAG`".
- If no tag exists (command fails), you will use the entire commit history. Note this in your process.

## Step 2: Fetch commits

If `LAST_TAG` was found:
```bash
git log ${LAST_TAG}..HEAD --pretty=format:"%h %s" --no-merges
```

If no tag exists:
```bash
git log --pretty=format:"%h %s" --no-merges
```

Also get the current date:
```bash
date +%Y-%m-%d
```

And attempt to determine the next version. If the last tag looks like a semver (e.g. v1.2.3), suggest the next patch version. Otherwise use "Unreleased".

## Step 3: Categorize each commit

For each commit message, assign it to exactly one category using these rules in priority order:

### Primary: Conventional Commit Prefixes
Match the prefix before the first colon (case-insensitive):

| Prefix | Category |
|--------|----------|
| `feat` | Added |
| `feature` | Added |
| `add` | Added |
| `fix` | Fixed |
| `bugfix` | Fixed |
| `hotfix` | Fixed |
| `refactor` | Changed |
| `change` | Changed |
| `update` | Changed |
| `improve` | Changed |
| `perf` | Changed |
| `style` | Changed |
| `chore` | Changed |
| `build` | Changed |
| `ci` | Changed |
| `docs` | Changed |
| `test` | Changed |
| `remove` | Removed |
| `delete` | Removed |
| `deprecate` | Removed |
| `revert` | Changed |
| `breaking` | Changed |

### Fallback: Keyword Heuristics
If no conventional commit prefix is detected, scan the commit message body for keywords:

- **Added**: message contains "add", "new", "create", "introduce", "implement", "support"
- **Fixed**: message contains "fix", "bug", "patch", "resolve", "correct", "repair"
- **Changed**: message contains "update", "change", "modify", "refactor", "improve", "enhance", "rename", "move", "migrate", "upgrade", "adjust", "optimize"
- **Removed**: message contains "remove", "delete", "drop", "deprecate", "clean up", "strip"

If a commit matches multiple keyword categories, use the first match from the order: Added, Fixed, Removed, Changed.

If no category can be determined, place it under **Changed**.

## Step 4: Generate the CHANGELOG.md

Write the file `CHANGELOG.md` in the repository root using this exact format:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [VERSION] - YYYY-MM-DD

### Added
- Commit message here (SHORT_HASH)

### Fixed
- Commit message here (SHORT_HASH)

### Changed
- Commit message here (SHORT_HASH)

### Removed
- Commit message here (SHORT_HASH)
```

Rules for the output:
- VERSION is the determined next version or "Unreleased"
- YYYY-MM-DD is today's date
- Only include category sections that have at least one commit
- Strip the conventional commit prefix and scope from the displayed message (e.g., `feat(auth): add login` becomes `Add login`)
- Capitalize the first letter of each commit message
- Include the short hash in parentheses at the end of each line
- If a previous CHANGELOG.md exists, prepend the new version section after the header, preserving existing content
- Order sections: Added, Fixed, Changed, Removed
- Each commit appears exactly once

## Step 5: Report results

After writing the file, report:
- How many commits were processed
- How many in each category
- The output file path

Do NOT push or commit the CHANGELOG.md -- just write it and let the user decide what to do next.
