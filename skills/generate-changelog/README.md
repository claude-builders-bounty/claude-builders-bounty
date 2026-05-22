# Generate Changelog

Generate a structured `CHANGELOG.md` from your project's git history.

## Setup

```bash
cd your-project
python3 skills/generate-changelog/changelog.py
```

## Usage

```bash
# Basic — generates CHANGELOG.md from last tag
python3 changelog.py

# With version
python3 changelog.py --version v1.2.0

# Custom output
python3 changelog.py -o RELEASE_NOTES.md

# With commit links
python3 changelog.py -r https://github.com/user/repo

# Since specific tag
python3 changelog.py --since v1.0.0
```

## What it does

- Fetches commits since the latest git tag (or all commits if no tags)
- Auto-categorizes into: **Added** / **Changed** / **Fixed** / **Removed** / **Security** / **Docs**
- Outputs a properly formatted `CHANGELOG.md`

## Sample Output

See [CHANGELOG-sample.md](CHANGELOG-sample.md) for a real-world example.
