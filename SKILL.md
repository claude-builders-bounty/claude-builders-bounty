# Generate Changelog

## Description
Generates a structured `CHANGELOG.md` from the project's git history. The skill fetches commits since the last git tag, auto-categorizes them into `Added`, `Fixed`, `Changed`, and `Removed` sections, and outputs a properly formatted markdown file.

## Usage
- **Command**: `/generate-changelog`
- **Alternative**: Run `bash changelog.sh` in the terminal

## Options
- `--output, -o`: Specify output file (default: CHANGELOG.md)
- `--since, -s`: Specify a git tag to start from (default: last tag)

## Examples