---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag, auto-categorizing commits into Added / Fixed / Changed / Removed.
allowed_tools: ["Bash", "Read", "Write", "Edit"]
---

# generate-changelog

Generate a `CHANGELOG.md` for the current repository from commits since the most recent git tag, auto-categorized using conventional commit prefixes.

## When to use

The user runs `/generate-changelog` or otherwise asks to "generate a changelog," "build release notes," or "summarize the commits since the last tag."

## Behavior

1. **Determine the commit range.** Run `git describe --tags --abbrev=0` to find the most recent tag. If no tag exists, fall back to the root commit (`git rev-list --max-parents=0 HEAD | tail -n 1`). The range is `<last-tag>..HEAD`.

2. **Read commits.** Run:
   ```bash
   git log <last-tag>..HEAD --pretty=format:"%h%x09%s"
   ```
   Each line is `<short-sha><TAB><subject>`.

3. **Categorize each commit** by the leading conventional-commit prefix in the subject (case-insensitive, allowing optional `(scope)` between prefix and colon):

   | Prefix(es) | Category |
   |---|---|
   | `feat`, `feature` | **Added** |
   | `fix`, `bugfix`, `hotfix` | **Fixed** |
   | `perf`, `refactor`, `style`, `docs`, `ci`, `build`, `chore`, `test` | **Changed** |
   | `revert`, `remove`, `delete`, `deprecate` | **Removed** |
   | _no recognizable prefix_ | **Changed** |

   The `BREAKING CHANGE:` footer (anywhere in body) and a `!` after the prefix (e.g. `feat!:`) both promote the commit; note them in the output with a `**BREAKING:**` lead.

4. **Determine the version header.**
   - If the user supplied a version (e.g. `/generate-changelog 1.4.0`), use that.
   - Else if the working tree has unreleased commits, use `## [Unreleased] — <today's date YYYY-MM-DD>`.
   - Else exit with a message: "No commits since last tag (`<tag>`). Nothing to write."

5. **Render `CHANGELOG.md`.** If a `CHANGELOG.md` already exists, prepend the new section above the previous content. If not, create a new file beginning with the standard Keep-a-Changelog header (see template below). Skip empty categories.

6. **Confirm output.** Print to the user:
   - The commit range used
   - The category counts (e.g. "Added: 4, Fixed: 2, Changed: 7, Removed: 0")
   - The path to the written file

## Output template

```markdown
# Changelog

All notable changes to this project will be documented in this file.
The format is based on Keep a Changelog (keepachangelog.com) and this project
adheres to Semantic Versioning (semver.org).

## [<version-or-Unreleased>] — <YYYY-MM-DD>

### Added
- <subject> (`<sha>`)

### Fixed
- <subject> (`<sha>`)

### Changed
- <subject> (`<sha>`)

### Removed
- <subject> (`<sha>`)
```

## Edge cases

- **No commits in range:** print the "nothing to write" message and exit cleanly. Do not modify any file.
- **Repo has no tags:** range is root-commit..HEAD; the version header is `[Unreleased]`.
- **Merge commits:** include them only if their subject starts with a recognized prefix; skip otherwise (default `--pretty=format` already excludes the merge-commit chatter, so usually nothing to do).
- **Subject contains backticks or pipes:** escape with backslash so the markdown table / list still renders.

## Anti-patterns (do not do)

- Do not call any LLM to "summarize" commits. The point is deterministic auto-categorization from prefixes; LLM rewrites change wording across runs and break diff review.
- Do not rewrite history or modify existing CHANGELOG sections — only prepend the new release block.
- Do not assume the working tree is clean; this skill is read-only against git, write-only against `CHANGELOG.md`.
