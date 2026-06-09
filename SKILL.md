---
name: generate-changelog
description: >
  Automatically generate a structured CHANGELOG.md from git history.
  Categorizes commits by conventional-commit prefix into Added / Fixed / Changed / Removed.
---

# Generate Changelog

Generate a structured `CHANGELOG.md` from the project's git history.

## Usage

Run the changelog generator:

```bash
bash changelog.sh
```

Or print to stdout without writing a file:

```bash
bash changelog.sh --stdout
```

## Options

| Flag | Description |
|------|-------------|
| `--stdout` | Print to stdout instead of writing CHANGELOG.md |
| `--tag TAG` | Generate changes since a specific git tag |
| `--output FILE` | Write to a custom file path |
| `-h, --help` | Show usage information |

## How It Works

1. Finds the last git tag (or uses `--tag` if provided)
2. Collects all commits since that tag
3. Categorizes each commit by conventional-commit prefix:
   - `feat:` / `feature:` → **Added**
   - `fix:` → **Fixed**
   - `refactor:` / `perf:` / `style:` / `docs:` / `test:` / `build:` / `ci:` / `chore:` → **Changed**
   - `revert:` / `remove:` / `delete:` / `drop:` / `breaking:` → **Removed**
   - (no prefix) → **Changed**
4. Outputs a formatted CHANGELOG.md

## Example Output

```markdown
# Changelog

All notable changes since v1.2.0 will be documented in this file.

### Added

- feat(auth): add OAuth2 login support
- feat(api): add batch endpoint for bulk operations

### Fixed

- fix(ui): resolve button alignment on mobile
- fix(db): handle connection timeout gracefully

### Changed

- refactor(core): simplify middleware pipeline
- docs: update API reference

### Removed

- remove(deprecated): drop legacy v1 endpoints
```