# Changelog Generator Skill

## Description
Automatically generates a structured `CHANGELOG.md` file by parsing the project's Git history. It categorizes changes into Features, Bug Fixes, Documentation, and Maintenance based on Conventional Commit standards.

## Usage
Run the script from the root of any git repository:
`bash generate_changelog.sh`

## Technical Details
- **Tooling**: Bash, Git.
- **Logic**: Uses `git log` with regex filtering to group commits by prefix (feat:, fix:, etc.).
- **Output**: Markdown format.
