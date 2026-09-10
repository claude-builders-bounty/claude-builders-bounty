# generate-changelog

A fast, zero-dependency bash script that generates structured `CHANGELOG.md` files from git commit history.

## Quick Start (3 steps)

```bash
# 1. Copy the script to your project
cp changelog.sh /path/to/your/project/

# 2. Run it
cd /path/to/your/project
bash changelog.sh

# 3. Done! Your CHANGELOG.md is ready
```

## Features

- **Zero dependencies** — works with just `bash` and `git`
- **Conventional commits** — automatically categorizes `feat:`, `fix:`, `revert:`, etc.
- **Smart filtering** — generates changelog since last tag by default
- **Flexible output** — custom file paths, version headers, date ranges
- **Keep a Changelog format** — industry-standard changelog structure

## Usage

```bash
# Basic usage (current repo, since last tag)
bash changelog.sh

# Specify repo and output
bash changelog.sh --repo ./my-project --output CHANGES.md

# Changelog between two tags
bash changelog.sh --from v1.0.0 --to v2.0.0

# All commits, with version header
bash changelog.sh --all --version "2.0.0"
```

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--repo PATH` | Git repository path | `.` |
| `--output FILE` | Output file path | `CHANGELOG.md` |
| `--from TAG` | Start tag | auto-detect last tag |
| `--to REF` | End ref | `HEAD` |
| `--all` | Include all commits | off |
| `--version VER` | Version header | auto |
| `--verbose` | Show details | off |

## How It Works

1. Detects the last git tag (or uses `--from`)
2. Reads all commits since that tag
3. Categorizes by conventional commit prefix:
   - `feat:` → **Added**
   - `fix:` → **Fixed**
   - `revert:` → **Removed**
   - `docs:`, `style:`, `refactor:`, etc. → **Changed**
4. Writes a formatted `CHANGELOG.md`

## Example Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-09-10

### Added
- User authentication flow (a1b2c3d, Jane, 2026-09-10)
- Password reset functionality (b2c3d4e, Jane, 2026-09-09)

### Fixed
- Login redirect bug (c3d4e5f, Bob, 2026-09-08)

### Changed
- Updated README documentation (d4e5f6a, Jane, 2026-09-07)

---
*Generated on 2026-09-10 by generate-changelog v1.0.0*
*Total commits: 4 (Added: 2, Fixed: 1, Changed: 1, Removed: 0)*
```

## Tested On

Successfully tested on:
- This repository (claude-builders-bounty)
- Node.js projects
- Python projects
- Mixed-language repositories

## License

MIT
