# generate-changelog

Auto-generate a structured CHANGELOG.md from git history.

## Setup (3 steps)

```bash
chmod +x generate-changelog.sh
sudo cp generate-changelog.sh /usr/local/bin/generate-changelog
```

## Usage

```bash
# Generate CHANGELOG.md from commits since last tag
generate-changelog

# Specify output file
generate-changelog --output RELEASE.md

# Use custom tag prefix
generate-changelog --tag-prefix release-
```

## How it works

- Fetches commits since the latest git tag
- Auto-categorizes commits using conventional commit prefixes:
  - `feat|add` -> Added
  - `fix|bug` -> Fixed
  - `chore|refactor|style|perf|ci|build` -> Changed
  - `remove|drop|revert` -> Removed
  - Everything else -> Other

## Sample Output

See [CHANGELOG.md](./CHANGELOG.md) for a generated example.
