# Skill: Generate Changelog

Generate a structured `CHANGELOG.md` from git commit history following the [Keep a Changelog](https://keepachangelog.com/) format. Commits are auto-categorized into Added / Fixed / Changed / Removed based on conventional commit prefixes.

## Usage

```
/generate-changelog
```

Optional arguments (pass as natural language):
- `--since <tag>` — use a specific git tag as the baseline (default: latest tag)
- `--output <file>` — write to a custom file (default: `CHANGELOG.md`)
- `--version <label>` — label for the unreleased block (default: `Unreleased`)

## Implementation

When this skill is invoked, follow these steps:

### 1. Detect the baseline tag

Run:
```bash
git describe --tags --abbrev=0 2>/dev/null
```
If a tag is found, use it as `LAST_TAG`. If no tags exist, use the entire commit history (i.e., no `..HEAD` range filter).

### 2. Collect commits since the last tag

```bash
# With a tag
git log ${LAST_TAG}..HEAD --pretty=format:"%H|%s|%b" --no-merges

# Without any tag (full history)
git log --pretty=format:"%H|%s|%b" --no-merges
```

Each line contains: `<hash>|<subject>|<body>`

### 3. Categorize each commit

Apply these prefix rules to the commit **subject** (case-insensitive):

| Prefix(es)                              | Category    |
|-----------------------------------------|-------------|
| `feat:`, `add:`, `feature:`             | **Added**   |
| `fix:`, `bug:`, `bugfix:`               | **Fixed**   |
| `change:`, `refactor:`, `chore:`, `perf:`, `style:`, `docs:`, `test:`, `ci:`, `build:` | **Changed** |
| `remove:`, `delete:`, `deprecate:`, `revert:` | **Removed** |
| *(anything else)*                       | **Changed** |

Strip the prefix from the display text. If the subject contains a `(#NNN)` reference, preserve it.

### 4. Build the CHANGELOG block

Format the output as:

```markdown
# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- <commit message> (<short hash>)

### Fixed
- <commit message> (<short hash>)

### Changed
- <commit message> (<short hash>)

### Removed
- <commit message> (<short hash>)
```

Omit any section that has no entries.

### 5. Write the file

- If `CHANGELOG.md` already exists, **prepend** the new block after the `# Changelog` header, before any existing content.
- If it does not exist, create it fresh.

### 6. Confirm

Print a summary: how many commits were processed, how many per category, and the output file path.

## Notes

- Skip merge commits (`--no-merges`).
- If the working directory is not a git repo, output a clear error and stop.
- The script version (`changelog.sh`) implements the same logic and can be used as a reference or run directly without an AI agent.
