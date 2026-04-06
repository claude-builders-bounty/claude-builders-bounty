# CHANGELOG Generator 🚀

Automatically generate a structured `CHANGELOG.md` from your git commit history.

## Features

- ✅ Fetches commits since the last git tag
- ✅ Auto-categorizes into: **Added** / **Fixed** / **Changed** / **Removed**
- ✅ Properly formatted Markdown output
- ✅ Works with any git repository

## Setup (3 Steps)

### 1. Download the script

```bash
curl -O https://raw.githubusercontent.com/neo-sonicseeds/changelog-generator/main/changelog.sh
```

### 2. Make it executable

```bash
chmod +x changelog.sh
```

### 3. Run it

```bash
./changelog.sh
```

That's it! Your `CHANGELOG.md` will be generated in the current directory.

---

## How It Works

The script:
1. Finds the last git tag in your repository
2. Fetches all commits since that tag (or all commits if no tags exist)
3. Categorizes commits based on their prefix:
   - `add`, `feat`, `new` → **Added**
   - `fix`, `bugfix`, `patch` → **Fixed**
   - `change`, `update`, `refactor` → **Changed**
   - `remove`, `delete` → **Removed**
4. Outputs a clean, structured `CHANGELOG.md`

## Example Output

```markdown
# CHANGELOG

## [Unreleased] - 2026-04-06

_Changes since v1.0.0_

### Added
- feat: add new authentication system
- add support for dark mode

### Fixed
- fix: resolve login timeout issue
- bugfix: correct typo in error message

### Changed
- update dependencies to latest versions
- refactor: improve code structure
```

## Requirements

- Git repository
- Bash shell
- Git tags (optional, but recommended)

## License

MIT

---

**Built with ❤️ by [Neo](https://github.com/neo-sonicseeds) @ SonicSeeds**