---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a project's git history, categorized into Added/Fixed/Changed/Removed. Use this whenever the user asks to generate, update, or create a changelog, release notes, or a summary of recent commits, or invokes /generate-changelog directly.
---

# Generate Changelog

Generates a `CHANGELOG.md` from git commit history since the last tag (or a specified range), sorted into `Added`, `Fixed`, `Changed`, and `Removed` sections.

## When to use this

Trigger this skill when the user asks to:
- Generate or update a `CHANGELOG.md`
- Summarize commits since the last release/tag
- Prepare release notes from git history

## How to run it

1. Confirm you're inside a git repository with at least one tag (`git tag` to check). If there are no tags, the script will fall back to the entire history — warn the user this may be noisy.
2. Run the bundled script from the repo root:

```bash
bash scripts/changelog.sh
```

Optional arguments:
```bash
bash scripts/changelog.sh <from-tag>            # commits since a specific tag, to HEAD
bash scripts/changelog.sh <from-tag> <to-ref>   # commits between two tags/refs
```

3. The script writes (or prepends to) `CHANGELOG.md` in the current directory.

## Categorization logic

- **Primary**: Conventional Commit prefixes — `feat`/`add` → Added, `fix`/`bugfix` → Fixed, `refactor`/`chore`/`perf`/`style`/`build`/`ci` → Changed, `remove`/`revert`/`drop` → Removed.
- **Fallback**: for commits with no conventional prefix, keyword-match the full message (e.g. "fixed the login bug" → Fixed) and default anything unmatched to Changed.

## After running

Show the user the generated `CHANGELOG.md` section, and ask if any commits were miscategorized before they commit it — keyword matching on non-conventional commit messages is a best-effort heuristic, not guaranteed to be perfect. If the user wants tighter accuracy going forward, suggest adopting Conventional Commits for future commit messages.
