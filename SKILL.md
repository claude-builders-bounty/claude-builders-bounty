# Generate Changelog

Create `CHANGELOG.md` from git history.

## Usage

```bash
bash changelog.sh
```

## What it does
- Uses the latest git tag as the start point
- Groups commits into `Added`, `Fixed`, `Changed`, `Removed`
- Writes a formatted `CHANGELOG.md`
