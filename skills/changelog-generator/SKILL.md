# Generate a structured CHANGELOG

## Description
This skill teaches Claude Code how to automatically generate a structured `CHANGELOG.md` file from the repository's git history using conventional commits.

## Usage
Tell Claude: `/generate-changelog` or "Generate the changelog for this repo."

## Instructions for Claude
1. Read the provided `changelog.sh` script in this directory.
2. Execute the script via the `Bash` tool: `bash path/to/changelog.sh`.
3. The script will automatically parse the git history since the last tag, categorize the commits into Added, Fixed, Changed, and Removed, and write the output to `CHANGELOG.md` in the root of the project.
4. Read the generated `CHANGELOG.md` and print a short summary to the user.
