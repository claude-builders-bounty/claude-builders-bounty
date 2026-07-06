# 📜 generate-changelog

> **Bounty:** [#1 — $50](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)
> **Auto-generate a structured `CHANGELOG.md` from git history**

## Quick Start

```bash
# 1. Download the script
curl -O https://raw.githubusercontent.com/dev-nana27/claude-builders-bounty/agent/nana27/changelog-generator/changelog.sh

# 2. Make it executable
chmod +x changelog.sh

# 3. Run it in your project
./changelog.sh
```

## Usage

```bash
# Generate CHANGELOG.md from last tag to HEAD
./changelog.sh

# Print to stdout instead of writing a file
./changelog.sh --stdout

# Use a specific tag as the base
./changelog.sh --tag v1.0.0

# Use a date range instead of tags
./changelog.sh --since 2026-01-01
```

## Categorisation Rules

The script automatically categorises commits using Conventional Commits prefixes:

| Prefix | Section |
|--------|---------|
| `feat!:` or `BREAKING CHANGE` | 💥 Breaking Changes |
| `feat:`, `add:`, `new:` | 🚀 Added |
| `fix:`, `bugfix:`, `hotfix:` | 🐛 Fixed |
| `refactor:`, `perf:`, `update:` | 🔄 Changed |
| `remove:`, `deprecate:` | 🗑️ Removed |
| `docs:`, `readme:` | 📚 Documentation |
| `security:` | 🔒 Security |
| `test:`, `ci:`, `chore:` | ⚙️ Internal |

## Output Format

```markdown
# Changelog

## [v2.1.0] — 2026-07-06

_12 changes since last release_

## 🚀 Added
- Add payment webhook handler  (a1b2c3d)
- Implement user onboarding flow  (e4f5g6h)

## 🐛 Fixed
- Fix race condition in queue processor  (i7j8k9l)
```

## Requirements

- **Git** (any project with git history)
- **Bash** 4+ (for associative arrays)

Works on Linux, macOS, and WSL.
