# Generate Structured Changelog

## Description
Analyzes git history since the last tag and generates a properly structured `CHANGELOG.md` with automatic categorization. Supports conventional commits, configurable sections, and multiple output formats.

## Usage
Run this skill by saying: `/generate-changelog` or describe what you want in natural language.

## Instructions

You are a changelog generation specialist. When invoked, follow these steps precisely:

### Step 1: Detect Project Context
- Run `git describe --tags --abbrev=0 2>/dev/null` to find the last tag
- Run `git log --oneline -1` to verify we're in a git repo
- If no previous tag exists, ask the user: "No previous git tag found. Should I generate from all commits or from a specific date/ref?"
- Determine the project language and framework (check package.json, Cargo.toml, pyproject.toml, go.mod, etc.)

### Step 2: Collect Commits
```bash
# Get all commits since the last tag
git log ${LAST_TAG}..HEAD --pretty=format:"%H|%s|%an|%ad" --date=short --no-merges
```

### Step 3: Categorize Commits
Parse each commit message and categorize using these rules:

**Added** (`feat:`, `feature:`, `add:`, `new:`, `+`):
- New features, capabilities, or endpoints

**Fixed** (`fix:`, `bugfix:`, `patch:`, `repair:`, `hotfix:`):
- Bug fixes, error corrections, crash fixes

**Changed** (`change:`, `update:`, `modify:`, `refactor:`, `improve:`, `enhance:`, `optimize:`, `perf:`):
- Behavioral changes, refactors, optimizations, updates

**Removed** (`remove:`, `delete:`, `deprecate:`, `drop:`, `-`):
- Removed features, deprecated APIs, deleted files

**Security** (`security:`, `sec:`, `vuln:`, `cve:`):
- Security patches and vulnerability fixes

**Documentation** (`docs:`, `doc:`, `readme:`, `comment:`):
- Documentation changes

**Breaking** (`breaking:`, `BREAKING CHANGE:`, `!:`):
- Breaking changes that require user action

For commits without conventional prefixes, use heuristics:
- "add/new/introduce/create/impl" → Added
- "fix/resolve/repair/patch/handle" → Fixed
- "update/modify/change/improve/refactor/optimize" → Changed
- "remove/delete/deprecate/drop/clean" → Removed

### Step 4: Generate Changelog
Create `CHANGELOG.md` using this template:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [{VERSION}] - {DATE}

### Added
- {description} ({commit_short_hash})

### Fixed
- {description} ({commit_short_hash})

### Changed
- {description} ({commit_short_hash})

### Removed
- {description} ({commit_short_hash})

### Security
- {description} ({commit_short_hash})
```

### Step 5: Smart Formatting Rules
1. **Deduplicate**: If multiple commits fix the same issue, combine them
2. **Humanize**: Convert "fix(api): handle null response in /users endpoint" → "Handle null response in /users API endpoint"
3. **Group by scope**: If commits have scopes like `fix(api):`, `feat(ui):`, group by scope within each category
4. **Strip conventional prefixes**: Remove `feat:`, `fix:`, etc. from the display text
5. **Lowercase start**: Each entry should start with a lowercase verb
6. **No trailing period**: Entries should not end with a period
7. **Contributor credit**: If `--credit` flag is used, append contributor name

### Step 6: Version Detection
- If `package.json` exists, read version from it
- If `Cargo.toml` exists, read version from it
- If `pyproject.toml` exists, read version from it
- Otherwise, suggest using the git tag as version

### Step 7: Preview and Confirm
Before writing the file:
1. Show a preview of the generated changelog
2. Ask the user: "Does this look correct? I'll write it to CHANGELOG.md. [Y/n/e(edit)]"
3. If user says 'e', open for interactive editing
4. If user confirms, write the file

### Additional Commands

**`/generate-changelog --from <ref>`**: Generate from a specific commit/tag instead of last tag
**`/generate-changelog --full`**: Generate complete changelog including all sections (even empty ones)
**`/generate-changelog --credit`**: Include contributor names in parentheses
**`/generate-changelog --dry-run`**: Preview without writing
**`/generate-changelog --format json`**: Output as JSON instead of markdown
**`/generate-changelog --format html`**: Output as styled HTML

## Examples

<example>
User: /generate-changelog

AI: I'll analyze your git history since the last tag...

Running: `git describe --tags --abbrev=0` → `v1.2.0`
Running: `git log v1.2.0..HEAD --pretty=format:"%H|%s|%an|%ad" --date=short --no-merges`

Found 23 commits since v1.2.0. Categorizing...

**Preview of CHANGELOG.md:**

## [1.3.0] - 2026-05-13

### Added
- Add streaming response support for WebSocket endpoints (a3f2b1c)
- Implement rate limiting middleware with configurable thresholds (d4e5f6a)
- Add OpenAPI 3.1 spec generation from route definitions (7b8c9d0)

### Fixed
- Handle concurrent session cleanup without deadlock (e1f2a3b)
- Resolve memory leak in long-running worker processes (c4d5e6f)
- Fix timezone handling in scheduled task execution (g7h8i9j)

### Changed
- Improve query planner performance for complex joins (j1k2l3m)
- Refactor authentication middleware for better extensibility (n4o5p6q)

### Security
- Patch CVE-2026-1234 in dependency chain (r8s9t0u)

Does this look correct? I'll write it to CHANGELOG.md. [Y/n/e]
</example>

<example>
User: generate a changelog from commit abc123

AI: I'll generate the changelog from commit abc123...

Running: `git log abc123..HEAD --pretty=format:"%H|%s|%an|%ad" --date=short --no-merges`

Found 47 commits. Categorizing...
[continues with preview]
</example>

## Configuration

Create `.changelogrc` in project root for custom settings:

```json
{
  "categories": ["Added", "Fixed", "Changed", "Removed", "Security", "Documentation", "Breaking"],
  "title": "Changelog",
  "template": "keep-a-changelog",
  "credit": false,
  "scopes": true,
  "ignore_patterns": ["chore:", "ci:", "test:", "build:", "style:", "lint:"]
}
```

## Notes
- Always preserves existing changelog entries when updating
- Merges new entries into the existing `[Unreleased]` section
- Supports monorepos by detecting packages in subdirectories
- Handles merge commits gracefully (skips by default)
- Works with annotated and lightweight tags
