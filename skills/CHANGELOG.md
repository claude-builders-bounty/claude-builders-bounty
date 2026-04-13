# CHANGELOG Skill

Generate a structured CHANGELOG.md from git history.

## Description

This skill auto-generates a categorized changelog from conventional commits in your git repository. Commits are grouped into Added, Fixed, Changed, and Removed sections.

## Usage

When the user asks to generate a changelog, run:

```bash
bash changelog.sh
```

This will:
1. Find all commits since the last git tag (or all commits if no tags exist)
2. Parse conventional commit prefixes (`feat:`, `fix:`, `refactor:`, etc.)
3. Categorize into Added / Fixed / Changed / Removed
4. Output a formatted `CHANGELOG.md`

## Options

- `--output FILE` — Custom output path (default: `CHANGELOG.md`)
- `--since TAG` — Start from a specific tag

## Example

```bash
bash changelog.sh
bash changelog.sh --output RELEASE-NOTES.md --since v1.0.0
```

## Commit Convention

Commits should follow the conventional commit format:

```
feat: add user authentication
fix: resolve login timeout issue
refactor: simplify database queries
```

See `README.md` for the full prefix-to-category mapping.
