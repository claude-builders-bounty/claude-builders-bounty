---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag. Use when the user asks to generate, update, or create a changelog.
---

# Generate CHANGELOG

Produce or update `CHANGELOG.md` from commits since the last git tag.

## Steps

1. Run the bundled script (preferred) or the inline flow below.

```bash
bash "${CLAUDE_PLUGIN_ROOT:-.}/scripts/changelog.sh"
```

If the script is unavailable:

1. Detect the latest tag: `git describe --tags --abbrev=0 2>/dev/null` (fallback: first commit).
2. Collect commits: `git log <tag>..HEAD --pretty=format:%s%n%b---`
3. Categorize each subject by conventional-commit / keyword heuristics:
   - **Added** — `feat`, `add`, `new`
   - **Fixed** — `fix`, `bug`, `patch`
   - **Removed** — `remove`, `delete`, `drop`, `deprecate`
   - **Changed** — everything else (`refactor`, `chore`, `docs`, `perf`, …)
4. Write `CHANGELOG.md` with Keep-a-Changelog structure: `## [Unreleased]` → category `###` sections, bullet list of subjects (skip merge noise).
5. Show a short summary to the user (counts per section, range tag..HEAD).

## Output format

```markdown
# Changelog

## [Unreleased] — <short-sha> (<date>)

### Added
- …

### Fixed
- …

### Changed
- …

### Removed
- …
```

## Constraints

- Do not invent commits.
- Do not rewrite history.
- Prefer updating the existing `CHANGELOG.md` Unreleased section if present.
