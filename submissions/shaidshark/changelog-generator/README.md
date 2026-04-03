# CHANGELOG Generator

Generates a structured CHANGELOG.md from git commit history using conventional commits.

## Usage

```bash
# Generate from all commits
python changelog.py

# Between two tags
python changelog.py --from v1.0.0 --to v2.0.0

# Save to file
python changelog.py --from v1.0.0 -o CHANGELOG.md
```

## Conventional Commit Support

| Type | Category |
|------|----------|
| `feat` | Features |
| `fix` | Bug Fixes |
| `docs` | Documentation |
| `refactor` | Refactoring |
| `perf` | Performance |
| `test` | Tests |
| `ci` | CI/CD |
| `chore` | Chores |

Commits with `BREAKING CHANGE:` in body or `!` after type are listed separately.

## Output Format

```markdown
# Changelog

## v2.0.0 (2026-04-03)

### BREAKING CHANGES
- **api**: Removed deprecated endpoints (a1b2c3d)

### Features
- Add user dashboard (e4f5g6h)

### Bug Fixes
- Fix login redirect loop (i7j8k9l)
```
