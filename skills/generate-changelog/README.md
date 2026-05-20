# generate-changelog

A Claude Code skill that produces a properly formatted `CHANGELOG.md` section from your git history, with commits auto-categorized into **Added / Fixed / Changed / Removed** per the Keep-a-Changelog spec.

Ships with two interfaces:

1. **`SKILL.md`** — a Claude Code skill, invoked via `/generate-changelog` (or any natural-language phrasing like "update the changelog").
2. **`changelog.sh`** — a standalone bash script for CI pipelines and git hooks (no Claude required).

## Setup (3 steps)

### 1. Install the skill

```bash
mkdir -p ~/.claude/skills && cp -r skills/generate-changelog ~/.claude/skills/
```

### 2. (Optional) Make the bash fallback executable

```bash
chmod +x ~/.claude/skills/generate-changelog/changelog.sh
```

### 3. Use it

In Claude Code:

```
/generate-changelog
```

Or from a shell, in any git repo:

```bash
~/.claude/skills/generate-changelog/changelog.sh v1.3.0 > NEW_SECTION.md
```

## How commits are classified

| Commit prefix | Section |
|---------------|---------|
| `feat:`, `feature:`, `add:` | **Added** |
| `fix:`, `bug:`, `bugfix:`, `hotfix:` | **Fixed** |
| `refactor:`, `chore:`, `style:`, `perf:`, `docs:`, `ci:`, `build:`, `test:` | **Changed** |
| `revert:`, `remove:`, `deprecate:` | **Removed** |
| anything else | **Changed** (default) |

Conventional-commit scopes (`feat(api): …`) are recognized. Merge commits are skipped. Commits whose body contains `BREAKING CHANGE:` are flagged with a `**BREAKING:**` prefix in the rendered output.

## Sample output

See [`sample-output.md`](./sample-output.md) — a real `CHANGELOG.md` entry generated from the `cli/cli` (GitHub CLI) repository between tags `v2.62.0` and `v2.63.0`.

## What's in this directory

```
skills/generate-changelog/
├── SKILL.md          # Claude Code skill definition
├── changelog.sh      # standalone bash fallback (no Claude required)
├── README.md         # this file
└── sample-output.md  # example output from a real repo
```

## Why two interfaces?

The `SKILL.md` is interactive — Claude prompts you for the new version, shows you the diff before writing, and handles the edge case of "this is the first release". The `changelog.sh` is meant for automation — drop it into a release script or a `prepare-release` git hook and pipe the output wherever you need it.

Both share the same classification rules, so output stays consistent whether you trigger the skill manually or run the bash version in CI.
