# changelog.sh — Git-to-CHANGELOG generator

A **zero-dependency** bash script that generates a structured `CHANGELOG.md` from your project's git history — categorizing commits into **Added**, **Fixed**, **Changed**, and **Removed**.

## Usage

**Step 1:** Place `changelog.sh` in your repo root.

**Step 2:** Run it:

```bash
bash changelog.sh
```

**Step 3 (optional):** Use flags for more control:

```bash
bash changelog.sh --stdout              # Preview without writing
bash changelog.sh --tag v1.0.0          # Commits since v1.0.0
bash changelog.sh --repo /path/to/repo  # Run on another repo
bash changelog.sh --help                # Full options
```

## Output example

```markdown
# Changelog

## [Unreleased] — 2026-05-28

### Added
- feat: add user authentication flow (`a1b2c3d`)
- implement dark mode toggle (`e4f5g6h`)

### Fixed
- fix: resolve login redirect loop (`i7j8k9l`)
- bug: correct date formatting in dashboard (`m0n1o2p`)

### Changed
- refactor: optimize database queries (`q3r4s5t`)
- update dependencies to latest versions (`u6v7w8x`)

### Removed
- drop deprecated v1 API endpoints (`y9z0a1b`)
```

## Requirements

- **Git** (any version)
- **Bash** (any modern shell, including Git Bash on Windows)

No Python, Node, or npm needed.
