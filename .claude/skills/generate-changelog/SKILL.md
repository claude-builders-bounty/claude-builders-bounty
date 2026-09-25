---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag. Use when the user asks to "generate a changelog", "update CHANGELOG.md", or runs "/generate-changelog".
---

# Generate Changelog

Generates a structured `CHANGELOG.md` entry from git commit history, categorizing
commits into `Added`, `Fixed`, `Changed`, and `Removed` sections.

## When to use this skill

- The user runs `/generate-changelog`
- The user asks to create or update a project changelog from git history

## How it works

1. Finds the most recent git tag (or falls back to the full history if no tag exists).
2. Collects every commit made since that tag on the current branch.
3. Categorizes each commit by its subject line prefix:
   - `feat`, `add` → **Added**
   - `fix`, `bug` → **Fixed**
   - `refactor`, `change`, `update`, `perf`, `style` → **Changed**
   - `remove`, `delete`, `revert` → **Removed**
   - anything else → **Changed** (default bucket)
4. Writes (or prepends) a new dated section to `CHANGELOG.md` at the repository root.

## Usage

Run the bundled script from the repository root:

```bash
bash .claude/skills/generate-changelog/changelog.sh
```

Optional arguments:

```bash
# Generate against a specific range instead of "since last tag"
bash .claude/skills/generate-changelog/changelog.sh v1.0.0..HEAD

# Write to a custom output file
bash .claude/skills/generate-changelog/changelog.sh "" CHANGES.md
```

## Steps for the agent

1. Confirm the current directory is a git repository (`git rev-parse --is-inside-work-tree`).
2. Run `bash .claude/skills/generate-changelog/changelog.sh` (pass a range/output path if the
   user specified one).
3. Show the user the generated/updated section of `CHANGELOG.md` and confirm the categorization
   looks correct — commits with non-conventional messages fall into `Changed` by default and may
   need manual re-categorization.
4. Do not commit the change automatically; let the user review and commit `CHANGELOG.md` themselves.
