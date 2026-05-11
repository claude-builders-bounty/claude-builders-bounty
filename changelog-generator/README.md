# Auto Changelog Generator

A simple bash script that automatically generates a structured `CHANGELOG.md` from a project's git history. It categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed` based on conventional commit prefixes.

## Setup Instructions

1. **Download the Script:** Copy the `changelog.sh` file into the root of your git repository.
2. **Make it Executable:** Run the following command in your terminal:
   ```bash
   chmod +x changelog.sh
   ```
3. **Run the Generator:** Execute the script to generate your `CHANGELOG.md`:
   ```bash
   ./changelog.sh
   ```

## Example Output
```markdown
# CHANGELOG

## Unreleased (since v1.0.0)

### Added
- feat: add user authentication
- add: new login page

### Fixed
- fix: resolve memory leak in worker
- bug: typo in documentation

### Changed
- chore: update dependencies
- docs: update README.md
```
