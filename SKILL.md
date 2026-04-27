# /generate-changelog — Auto-Generate CHANGELOG from Git History

Generate a structured `CHANGELOG.md` from your project's git history with automatic commit categorization.

## Usage

```
./generate-changelog.sh [output-file] [repo-path]
```

Defaults: `./generate-changelog.sh CHANGELOG.md .`

## Features

- ✅ Fetches commits since the last git tag
- ✅ Auto-categorizes into: `Added` / `Fixed` / `Changed` / `Removed`
- ✅ Outputs properly formatted `CHANGELOG.md`
- ✅ Includes all previous tags with dates
- ✅ Fallback keyword matching for non-conventional commits
- ✅ Zero dependencies — pure bash + git

## Requirements

- `git` (any version)
- `bash` 4+

## Examples

```bash
# In your project root
./generate-changelog.sh

# Custom output
./generate-changelog.sh docs/release-notes.md

# From another directory
./generate-changelog.sh ../my-project/CHANGELOG.md ../my-project/
```
