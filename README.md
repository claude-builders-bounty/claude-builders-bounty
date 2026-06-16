# CHANGELOG Generator

Generate a structured `CHANGELOG.md` from your project's git history in 3 commands.

## Quick Start

```bash
# 1. Make executable
chmod +x changelog.sh

# 2. Run in your git repo
bash changelog.sh

# 3. Done — open CHANGELOG.md
```

## Usage

```bash
bash changelog.sh [options]
```

| Option | Default | Description |
|---|---|---|
| `--output FILE` | `CHANGELOG.md` | Output file path |
| `--from-tag TAG` | Previous tag | Start version for changelog |
| `--to-tag TAG` | Latest tag | End version for changelog |
| `--exclude-categories TYPES` | — | Comma-separated categories to skip (e.g., `Other,Documentation`) |
| `--help` | — | Show usage |

## How It Works

1. Reads git tags to determine version range
2. Parses commit history using conventional commit format
3. Auto-categorizes into: **Added**, **Fixed**, **Changed**, **Deprecated**, **Removed**, **Security**, **Documentation**, **Other**
4. Outputs a `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format

## Example Output

```markdown
# Changelog

## [v1.2.0] — 2026-06-15

### Added
- User invitation via email links (a1b2c3d)
- Export dashboard to CSV (e4f5g6h)

### Fixed
- Pagination resets on filter change (i7j8k9l)
- Stripe webhook retry handling (m0n1o2p)
```

## Requirements

- Git repository with [conventional commits](https://www.conventionalcommits.org/)
- Bash 4+
