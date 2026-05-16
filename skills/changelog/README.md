# changelog.sh

Generate a structured CHANGELOG.md from git history using Conventional Commits.

## Setup (3 steps)

```bash
# 1. Download the script
curl -o changelog.sh https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/skills/changelog/changelog.sh

# 2. Make it executable
chmod +x changelog.sh

# 3. Run it
bash changelog.sh
```

## Usage

```bash
# Basic usage - generates CHANGELOG.md from last tag to HEAD
bash changelog.sh

# Specify version
bash changelog.sh -v 1.2.0

# Custom output file
bash changelog.sh -o HISTORY.md

# Generate between specific tags
bash changelog.sh -f v1.0.0 -t v1.1.0

# Append to existing changelog
bash changelog.sh -v 1.3.0 --append
```

## Options

| Option | Description |
|--------|-------------|
| `-o, --output FILE` | Output file (default: CHANGELOG.md) |
| `-f, --from TAG` | Start from this tag (default: auto-detect) |
| `-t, --to REF` | End at this ref (default: HEAD) |
| `-v, --version VER` | Version for this release (default: Unreleased) |
| `-a, --append` | Append to existing CHANGELOG |
| `-h, --help` | Show help message |

## How It Works

1. **Reads commits** from the last git tag to HEAD (or custom range)
2. **Parses Conventional Commits** (feat, fix, docs, refactor, etc.)
3. **Auto-categorizes** into standard Keep a Changelog sections:
   - ⚠️ Breaking Changes
   - 🔒 Security
   - ✨ Added
   - 🔄 Changed
   - 🐛 Fixed
   - 🗑️ Removed
   - 📚 Documentation
   - 📦 Other
4. **Generates Markdown** with commit links to GitHub

## Conventional Commit Mapping

| Commit Type | Category |
|-------------|----------|
| `feat:`, `add:`, `new:` | ✨ Added |
| `fix:`, `bugfix:`, `hotfix:` | 🐛 Fixed |
| `refactor:`, `perf:`, `style:` | 🔄 Changed |
| `remove:`, `delete:`, `deprecate:` | 🗑️ Removed |
| `docs:`, `doc:` | 📚 Documentation |
| `security:`, `sec:` | 🔒 Security |
| `breaking:`, `break:` | ⚠️ Breaking |
| `test:`, `build:`, `ci:`, `chore:` | 📦 Other |

Non-conventional commits are categorized by keywords (add, fix, remove, update, etc.)

## Example Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2024-01-15

### ✨ Added

- Add user authentication system ([`a1b2c3d`](https://github.com/org/repo/commit/a1b2c3d))
- Implement dark mode toggle ([`e4f5g6h`](https://github.com/org/repo/commit/e4f5g6h))

### 🐛 Fixed

- Fix memory leak in cache handler ([`i7j8k9l`](https://github.com/org/repo/commit/i7j8k9l))

### 🔄 Changed

- Refactor database connection pooling ([`m0n1o2p`](https://github.com/org/repo/commit/m0n1o2p))
```

## Requirements

- Bash 4.0+ (for associative arrays)
- Git

## License

MIT
