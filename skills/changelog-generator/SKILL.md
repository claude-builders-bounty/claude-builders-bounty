---
name: generate-changelog
description: Automatically generates a structured Keep-a-Changelog CHANGELOG.md from git history since the last git tag, categorized into Added, Fixed, Changed, and Removed.
---

# Generate Structured CHANGELOG

This skill inspects git history between the most recent reachable tag and `HEAD`, parses commit messages using Conventional Commits patterns, and compiles a structured Markdown changelog.

## When to Use
- When asked to "generate a changelog", "create release notes", or "document recent changes".
- When running the `/generate-changelog` command.
- Before publishing a release tag.

## Execution Workflow

1. Run the generator script:
   ```bash
   python3 skills/changelog-generator/changelog.py --output CHANGELOG.md
   ```
   Or using pure bash:
   ```bash
   bash skills/changelog-generator/changelog.sh --output CHANGELOG.md
   ```

2. The generator auto-detects the last git tag via `git describe --tags --abbrev=0`.
   - If tags exist: extracts `last_tag..HEAD`.
   - If no tags exist: extracts full commit history up to `HEAD`.

3. Commits are categorized according to conventional prefixes:
   - `feat:`, `feature:`, `add:` → **Added**
   - `fix:`, `bug:`, `patch:` → **Fixed**
   - `refactor:`, `perf:`, `chore:`, `docs:`, `ci:` → **Changed**
   - `revert:`, `remove:`, `delete:` → **Removed**

4. The changelog prepends or updates `CHANGELOG.md` adhering to the Keep-a-Changelog standard format.
