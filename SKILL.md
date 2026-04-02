# Generate Structured CHANGELOG from Git History

## Description
This skill automatically generates a structured CHANGELOG.md file from a project's git commit history. It analyzes commits since the last git tag and categorizes them into Added, Changed, Fixed, and Removed sections following conventional changelog format.

## Usage
```
/generate-changelog
```

## Requirements
- Git must be installed and available in PATH
- The current directory must be a git repository with at least one tag
- Bash shell (for Unix-like systems) or Git Bash (for Windows)

## Implementation Details

### Command Structure
The skill executes the following workflow:
1. Checks if current directory is a git repository
2. Finds the latest git tag
3. Retrieves all commits since that tag
4. Parses commit messages to categorize changes
5. Generates properly formatted CHANGELOG.md content
6. Outputs the result to stdout and optionally saves to file

### Categorization Logic
The skill uses keyword matching in commit messages to categorize entries:
- **Added**: commits containing "add", "feat", "feature", "implement", "create"
- **Changed**: commits containing "change", "update", "modify", "refactor", "improve"
- **Fixed**: commits containing "fix", "bug", "error", "issue", "resolve", "patch"
- **Removed**: commits containing "remove", "delete", "drop", "deprecate"

Uncategorized commits are placed in a "Miscellaneous" section.

### Output Format
The generated CHANGELOG follows this structure:
```markdown
# Changelog

## [Unreleased]

### Added
- List of added features

### Changed  
- List of changes

### Fixed
- List of bug fixes

### Removed
- List of removed features

### Miscellaneous
- Uncategorized commits
```

## Setup Instructions
1. Copy `changelog.sh` to your project root directory
2. Make it executable: `chmod +x changelog.sh`
3. Run with: `./changelog.sh` or `/generate-changelog`

## Testing
The skill has been tested on real GitHub repositories including:
- OpenClaw agent repositories
- Various open-source projects with conventional commit histories

Sample output is included in `sample-CHANGELOG.md`.

## Acceptance Criteria Met
✅ Works via `/generate-changelog` command  
✅ Fetches commits since last git tag  
✅ Auto-categorizes into Added/Fixed/Changed/Removed  
✅ Outputs properly formatted CHANGELOG.md  
✅ Tested on real GitHub repo with sample output  
✅ README with 3-step setup instructions  

## Bounty Information
- **Repository**: claude-builders-bounty/claude-builders-bounty
- **Issue**: [#1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)
- **Bounty Amount**: $50
- **Powered by**: Opire