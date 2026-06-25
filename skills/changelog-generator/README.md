# Changelog Generator

Generate a structured `CHANGELOG.md` from your project's git history.

## Quick Setup (3 steps)

1. Download `changelog.sh` into your project root
2. Make it executable: `chmod +x changelog.sh`
3. Run: `./changelog.sh`

That's it. A `CHANGELOG.md` is generated from commits since the last git tag.

## Usage

```bash
# Default: commits since last tag → CHANGELOG.md
./changelog.sh

# Specific range
./changelog.sh v1.0.0..v1.2.0

# Custom output
./changelog.sh --output releases/v1.2.md

# JSON format instead of markdown
./changelog.sh --format json

# Help
./changelog.sh --help
```

## How It Works

- Fetches commits in the given range (or since last tag)
- Auto-categorizes into **Added** / **Fixed** / **Changed** / **Removed** using Conventional Commits patterns
- Skips merge commits and dependency bumps
- Outputs a clean, properly formatted `CHANGELOG.md`

## Supported Patterns

| Prefix | Category |
|--------|----------|
| `feat`, `add`, `new` | Added 🆕 |
| `fix`, `bug`, `patch` | Fixed 🐛 |
| `refactor`, `improve`, `update`, `change` | Changed 🔄 |
| `remove`, `drop`, `delete`, `deprecate` | Removed 🗑️ |

Everything else goes in **Other** 📝.

## Requirements

- Bash 4+ (Linux, macOS, WSL, Git Bash on Windows)
- A git repository with at least one commit

## Sample Output

```markdown
## Unreleased

### 🆕 Added

- feat(auth): add OAuth2 login support
- add dark mode toggle

### 🐛 Fixed

- fix(ci): resolve flaky test on Node 18
- bug: fix memory leak in cache module

### 🔄 Changed

- refactor(core): simplify event dispatcher
- update dependencies to latest versions

### 🗑️ Removed

- drop Node 14 support
```
