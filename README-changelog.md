# changelog.sh

Generate a structured `CHANGELOG.md` from your git history — one command, no dependencies.

## Quick Start

1. **Download** — save `changelog.sh` in your project root
2. **Make executable** — `chmod +x changelog.sh`
3. **Run** — `./changelog.sh`

That's it. `CHANGELOG.md` appears in your current directory.

## How It Works

| Step | What happens |
|------|-------------|
| **Range** | Auto-detects commits since the last git tag (or all history if no tags) |
| **Categorise** | Groups commits by conventional-commit prefix |
| **Output** | Writes a clean `CHANGELOG.md` |

### Commit mapping

| Prefix | Section |
|--------|---------|
| `feat:`, `add` | Added |
| `fix:`, `bug` | Fixed |
| `remove` | Removed |
| everything else | Changed |
| `chore`, `docs`, `style`, `test`, `ci`, `build` | skipped |

## Examples

```bash
# Since last tag → CHANGELOG.md
./changelog.sh

# Print to terminal
./changelog.sh --stdout

# Specific range
./changelog.sh v1.0..HEAD
```

## Sample Output

```markdown
# CHANGELOG — my-project

## [v1.2.0..HEAD] — 2026-05-11

### Added
- feat: dark mode toggle (`a1b2c3d`)
- add: user profile page (`e4f5g6h`)

### Fixed
- fix: login timeout on slow networks (`i7j8k9l`)

### Changed
- refactor: simplify database pool (`m0n1o2p`)
- perf: lazy-load dashboard images (`q3r4s5t`)

### Removed
- remove: deprecated v1 API endpoints (`u6v7w8x`)
```

## CLI Reference

| Flag | Description |
|------|-------------|
| *(none)* | Writes `CHANGELOG.md` in current directory |
| `--stdout` | Prints to stdout instead |
| `<range>` | Any valid `git log` range (`v1.0..HEAD`, `main~10..main`, etc.) |

## Requirements

- **bash 4+** (for `${var,,}` lowercase expansion)
- **git** (obviously)
- No other dependencies — no npm, no pip, no Docker
