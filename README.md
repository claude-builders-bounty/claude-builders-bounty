# changelog.sh

A zero-dependency bash script that automatically generates a structured `CHANGELOG.md` from your git history.

## Features

- **Conventional Commits aware** — auto-categorizes `feat:`, `fix:`, `refactor:`, etc. (with optional scope like `feat(api):`)
- **Smart fallback** — categorizes non-conventional commits by keyword (add/new/fix/remove/etc.)
- **Keep a Changelog format** — proper Markdown structure following [keepachangelog.com](https://keepachangelog.com/)
- **Zero dependencies** — pure bash + git, runs anywhere
- **Auto version detection** — uses `package.json`, `VERSION`, or date-based version
- **Empty-tag safe** — handles repos with no tags using full history
- **Categorized output** — Added / Fixed / Changed / Removed / Other

## Installation (2 commands)

```bash
curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/changelog.sh
chmod +x changelog.sh
```

Or clone the repo and copy `changelog.sh` to your project root.

## Usage

```bash
# Generate CHANGELOG.md in current directory
./changelog.sh

# Generate to a custom location
./changelog.sh docs/CHANGELOG.md
```

That's it. The script reads your git history, categorizes commits, and writes `CHANGELOG.md`.

## Example Output

```markdown
# Changelog

All notable changes to **my-project** are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/).

---

## [1.0.0] - 2026-06-05

_Commits since v1.0.0 (12 total)_

### Added

- new feature description (a4d8f0f)
- another feature (9992e32)

### Fixed

- bug fix description (54bf798)
- another fix (593e4b4)

### Changed

- refactored X (3b6347a)
```

## How It Works

1. **Detect range** — uses `git describe` to find the last tag, falls back to full history if no tags
2. **Parse commits** — extracts subject + body for each commit since last tag
3. **Categorize** — matches against conventional commit patterns first, then keyword fallback
4. **Format** — writes a Keep-a-Changelog-compliant Markdown file

## Commit Categorization

| Prefix | Category |
|---|---|
| `feat:` / `feat(scope):` | Added |
| `fix:` / `fix(scope):` | Fixed |
| `refactor:`, `perf:`, `style:`, `chore:`, `docs:`, `build:`, `ci:` | Changed |
| `remove:`, `delete:`, `drop:`, `deprecate:` | Removed |
| No prefix (with `add`/`new`/`create`/`implement` keyword) | Added |
| No prefix (with `fix`/`bug`/`patch`/`repair` keyword) | Fixed |
| No prefix (with `remove`/`delete`/`drop` keyword) | Removed |
| No prefix, no keyword match | Other |

## License

MIT — use freely.
