# Generate Changelog

Generate a structured `CHANGELOG.md` from git history since the last tag. If the repository has no tags, the script falls back to the full commit history and notes that in the output.

## Setup and Usage

```bash
chmod +x changelog.sh generate-changelog/changelog.sh
bash changelog.sh
cat CHANGELOG.md
```

## What It Does

- Finds the latest git tag with `git describe --tags --abbrev=0`
- Reads commits from `<latest-tag>..HEAD`, or from full history when no tag exists
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`
- Writes a formatted `CHANGELOG.md`

## Options

```bash
bash changelog.sh --repo /path/to/repo --output /tmp/CHANGELOG.md
bash changelog.sh --stdout
```

## Test

```bash
python generate-changelog/test_generate_changelog.py
```

## Sample Output

See `samples/CHANGELOG.sample.md`, generated from this repository's real git history.
