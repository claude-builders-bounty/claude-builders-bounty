# Changelog Generator

A bash script that automatically generates a structured `CHANGELOG.md` from a project's git history.

## Features

- ✅ Works via `./changelog.sh` — zero dependencies beyond `git` and `bash`
- ✅ Fetches commits since the last git tag (or all commits if no tags exist)
- ✅ Auto-categorizes into: `Added` / `Fixed` / `Changed` / `Removed` / `Documentation`
- ✅ Supports conventional commit prefixes (`feat:`, `fix:`, `docs:`, `refactor:`, etc.)
- ✅ Falls back to keyword matching for non-conventional messages
- ✅ Outputs a properly formatted `CHANGELOG.md`
- ✅ Custom output path with `--output` flag
- ✅ Works on any git repo with `--repo` flag

## Setup

1. Copy `changelog.sh` to your project root
2. Make it executable: `chmod +x changelog.sh`

## Usage

```bash
# Generate CHANGELOG.md in current directory
./changelog.sh

# Specify output file
./changelog.sh --output docs/CHANGELOG.md

# Generate for another repo
./changelog.sh --repo /path/to/project

# Combine options
./changelog.sh --repo /path/to/project --output /path/to/CHANGELOG.md
```

## How It Works

1. Detects the last git tag (or uses the initial commit if no tags exist)
2. Iterates through commits grouped by tag
3. Categorizes each commit message using conventional commit prefixes
4. Falls back to keyword matching for plain English messages
5. Outputs a clean, structured Markdown file

## Sample Output

See [SAMPLE.md](SAMPLE.md) for a generated example.
