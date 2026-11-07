# Changelog Generator

A simple tool to generate a structured `CHANGELOG.md` from git history.

## Setup Instructions

1. Ensure you have `python3` and `git` installed on your machine.
2. Clone this repository and make the script executable: `chmod +x changelog.sh`
3. Run `./changelog.sh` in your git repository to generate `CHANGELOG.md`.

## Features
- Fetches commits since the last git tag (or all commits if no tags exist).
- Auto-categorizes into `Added`, `Fixed`, `Changed`, and `Removed`.
- Outputs a properly formatted Markdown file.
