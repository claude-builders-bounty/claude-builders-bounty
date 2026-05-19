---
name: generate-changelog
description: Automatically generates a structured CHANGELOG.md from git history. Use when you want to summarize changes since the last tag or for a new release.
---

# Generate Changelog

This skill generates a `CHANGELOG.md` file based on the project's git history. It categorizes commits into **Added**, **Fixed**, **Changed**, and **Removed** based on conventional commit prefixes.

## Commands

### /generate-changelog

Generates the `CHANGELOG.md` file.

**Usage:**

- `/generate-changelog`: Generates changes under an `[Unreleased]` section.
- `/generate-changelog --tag v1.0.0`: Generates changes for the specified version tag.

## How it Works

1. Identifies the latest git tag using `git describe`.
2. Fetches all commit messages from the latest tag to `HEAD`.
3. Categorizes commits:
   - `Added`: Commits starting with `feat:`, `add:`, `added:`
   - `Fixed`: Commits starting with `fix:`, `fixed:`, `bugfix:`
   - `Removed`: Commits starting with `removed:`, `remove:`, `delete:`
   - `Changed`: All other commits (refactor, docs, chore, etc.)
4. Formats the output into a clean, Markdown-based `CHANGELOG.md`.

## Implementation Detail

The skill executes a Python script (`scripts/generate_changelog.py`) which handles the logic of interacting with git and formatting the markdown.
