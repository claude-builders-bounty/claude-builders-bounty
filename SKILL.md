# /generate-changelog — Generate structured CHANGELOG.md from git history

Generates a categorized changelog from a project's git history.

## Usage

```
/generate-changelog              # current directory, default output
/generate-changelog --output CHANGES.md
/generate-changelog --since v1.0.0
/generate-changelog --repo /path/to/project
```

## Categorization Rules

| Prefix | Section |
|--------|---------|
| feat:, add:, new:, create:, implement | Added |
| fix:, bugfix:, hotfix:, patch:, correct: | Fixed |
| change:, update:, refactor:, improve:, migrate: | Changed |
| remove:, delete:, drop:, deprecate: | Removed |
| security:, sec:, vuln: | Security |

## Output

Produces `CHANGELOG.md` with categorized entries and commit links.
