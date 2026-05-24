# Generate Changelog

## Description
Generates a structured `CHANGELOG.md` from a project's git history. Fetches commits since the last git tag and auto-categorizes them into: **Added**, **Fixed**, **Changed**, **Removed**.

## Usage

### Command
```
/generate-changelog
```

### Manual Execution
```bash
bash changelog.sh [OUTPUT_FILE]
```

- `OUTPUT_FILE` defaults to `CHANGELOG.md` in the repository root.
- Works in any git repository with conventional or keyword-based commits.

## How It Works

1. **Detects the latest git tag** in the current branch.
2. **Collects all commits** since that tag (or full history if no tags exist).
3. **Categorizes each commit** using:
   - Conventional commit prefixes (`feat:`, `fix:`, `refactor:`, `chore:`, `remove:`, etc.)
   - Keyword-based fallback (`add`, `fix`, `update`, `delete`, etc.)
4. **Outputs a formatted `CHANGELOG.md`** with sections for each category.

## Output Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Since v1.0.0] — 2025-01-15

### Added
- Add user authentication (`a1b2c3d`) [2025-01-14]

### Fixed
- Fix null pointer in login flow (`e4f5g6h`) [2025-01-13]

### Changed
- refactor: improve API response time (`i7j8k9l`) [2025-01-12]
```

## Setup (3 steps)

1. Copy `changelog.sh` into your repository root.
2. Make it executable: `chmod +x changelog.sh`
3. Run it: `bash changelog.sh`

## Requirements

- `git` installed and available in `$PATH`
- Must be run inside a git repository
- No external dependencies (pure bash)
