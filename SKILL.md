---
name: generate-changelog
description: Generate a structured CHANGELOG.md from the project's git history. Auto-categorizes commits into Added / Fixed / Changed / Removed sections following Keep a Changelog format.
---

# Generate Changelog Skill

This skill generates a structured `CHANGELOG.md` from your project's git history.

## Usage

Run this skill with the slash command:

```
/generate-changelog
```

Or directly via bash:

```bash
bash changelog.sh
```

## What it does

1. Finds the latest git tag in your repository
2. Collects all commits since that tag (or all commits if no tag exists)
3. Auto-categorizes each commit into:
   - **Added** — new features (`feat:`, `add:`, `implement:`, etc.)
   - **Fixed** — bug fixes (`fix:`, `bug:`, `patch:`, etc.)
   - **Changed** — refactors, updates, improvements (`refactor:`, `update:`, `chore:`, etc.)
   - **Removed** — deletions and deprecations (`remove:`, `delete:`, `deprecate:`, etc.)
4. Outputs a properly formatted `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com) conventions

## Instructions for Claude Code

When the user runs `/generate-changelog`:

1. Check if `changelog.sh` exists in the project root. If not, ask the user to add it (or copy it from this skill directory).

2. Run the script:
   ```bash
   bash changelog.sh
   ```

3. If the user wants to generate from a specific tag:
   ```bash
   bash changelog.sh --since v1.2.3
   ```

4. If the user wants a custom output file:
   ```bash
   bash changelog.sh --output MY_CHANGELOG.md
   ```

5. After generation, show a summary of what was written:
   - How many commits were categorized
   - Which sections have entries
   - Where the file was written

6. Offer to open the generated file for review.

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--since <tag>` | Generate from this tag onwards | Latest git tag |
| `--output <file>` | Write output to this file | `CHANGELOG.md` |
| `--help` | Show usage information | — |

## Example Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [Unreleased] — 2026-07-02

### Added
- feat: add user authentication module (`a1b2c3d`) — Alice

### Fixed
- fix: resolve null pointer in payment flow (`d4e5f6g`) — Bob

### Changed
- refactor: extract database layer into service (`h7i8j9k`) — Charlie
- chore: update dependencies to latest (`l0m1n2o`) — Alice

### Removed
- remove: deprecated v1 API endpoints (`p3q4r5s`) — Bob
```
