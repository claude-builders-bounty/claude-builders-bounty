# changelog

Generate a structured `CHANGELOG.md` from git history.

## Usage
```bash
bash changelog.sh
```

Options: `--tag v1.0.0` (start from specific tag), `--output CHANGELOG.md` (custom output path)

## How it works
- Fetches commits since the last git tag
- Auto-categorizes: **Added** / **Fixed** / **Changed** / **Removed**
- Uses conventional commit prefixes
- Outputs clean markdown

## Requirements
- git installed and available in PATH