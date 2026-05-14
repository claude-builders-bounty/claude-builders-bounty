# CHANGELOG Generator

A bash script that automatically generates a structured `CHANGELOG.md` from a repository's git history.

## Setup (2 steps)

```bash
# 1. Clone this repo or copy changelog.sh
git clone <this-repo>

# 2. Make it executable
chmod +x changelog.sh
```

## Usage

```bash
# Generate CHANGELOG.md in the current repo
bash changelog.sh

# Or specify a repo path
bash changelog.sh /path/to/your/project
```

## Features

- Fetches commits since the last git tag
- Auto-categorizes into **Added** / **Fixed** / **Changed** / **Removed**
  - `feat:` → Added
  - `fix:` → Fixed
  - `remove:` / `deprecate:` → Removed
  - Breaking changes (`!`) auto-detected
  - Everything else → Changed
- Outputs a properly formatted `CHANGELOG.md`
- No external dependencies — pure bash + git
