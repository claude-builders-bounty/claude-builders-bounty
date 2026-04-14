# Changelog Generator

A simple bash script that automatically generates a structured `CHANGELOG.md` from a project's git history since the last tag.

## How to use (in 3 steps or fewer)

1. Make the script executable:
   ```bash
   chmod +x changelog.sh
   ```
2. Run the script inside any git repository:
   ```bash
   ./changelog.sh
   ```
3. Open the newly generated `CHANGELOG.md` file to see your categorized commits (`Added`, `Fixed`, `Changed`, `Removed`).

## Sample Output
Running this script will output a `CHANGELOG.md` file formatted like this:
```markdown
# Changelog

## Unreleased

### Added
- new login feature
- setup instructions

### Fixed
- typo in readme
```
