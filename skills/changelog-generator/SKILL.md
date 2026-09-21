---
name: changelog-generator
description: "Generate a structured CHANGELOG.md from git history by extracting conventional commits, grouping into Added/Fixed/Changed/Removed, and formatting with semantic versioning headers."
---

# Changelog Generator

## Purpose

Generate a clean, readable `CHANGELOG.md` from a Git repository's commit history using conventional commit parsing. Useful for release notes, project documentation, and automated changelog generation in CI/CD pipelines.

## Workflow

1. **Read repository state.**
   - Run `git log --oneline --no-merges` to get recent commit history.
   - Identify the latest reachable tag automatically; if none exists, use the full history.
   - **Done when:** you have a list of commits with hashes, dates, and messages.

2. **Parse conventional commits.**
   - Extract commit type prefix: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `style`, `perf`.
   - Parse scope if present: `feat(auth): add login flow` → type=`feat`, scope=`auth`.
   - Extract description after the colon.
   - **Done when:** each commit is classified into a category with its description.

3. **Group by type.**
   - Group commits under their type header while preserving Git's newest-first log order.
   - Emit the literal contract sections in order: `Added`, `Fixed`, `Changed`, `Removed`.
   - **Done when:** commits are organized into categorized sections.

4. **Format the changelog.**
   - Write a `CHANGELOG.md` with:
     - Title: `# Changelog`
     - Version header: `## [Unreleased]` or `## [vX.Y.Z] - YYYY-MM-DD` if a tag exists.
     - Type sections: `### Added`, `### Fixed`, `### Changed`, and `### Removed`.
     - Each entry: `- <description> (<short-hash>)`
   - Include an `[Unreleased]` section at top if no tag found.
   - **Done when:** the file follows standard Keep a Changelog format.

5. **Verify output.**
   - Read back the generated `CHANGELOG.md`.
   - Confirm it contains at least one entry per commit type found.
   - Check that all commit hashes referenced exist in the repo.
   - **Done when:** the changelog is complete, formatted correctly, and references valid commits.

## Notes

- Non-conventional commits are retained under `### Changed` so every post-tag commit remains visible.
- Preserve author attribution if requested: include `(Author Name)` after the hash.
- The Bash user command writes `CHANGELOG.md` deterministically for the current post-tag history.
