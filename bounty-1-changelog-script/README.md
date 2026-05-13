# changelog.sh — Generate a Structured CHANGELOG from Git History

A bash script that automatically generates a formatted `CHANGELOG.md` from git history.

## Quick Start

```bash
bash changelog.sh /path/to/your/project
```

## Features

- Fetches commits since the last git tag
- Auto-categorizes into: **Added**, **Fixed**, **Changed**, **Removed**
- Outputs a properly formatted `CHANGELOG.md`
- Falls back to all commits if no tags exist
- Ignores merge commits for cleaner output

## Sample Output

See `sample-changelog.md` for a real example generated from this repository.
