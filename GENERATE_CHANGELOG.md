# Generate Changelog Skill

This submission adds a Claude Code slash command and a Bash script for bounty #1.

## Install

Copy the command into a Claude-enabled repository and keep changelog.sh at the repository root:

    mkdir -p .claude/commands
    cp path/to/generate-changelog.md .claude/commands/generate-changelog.md
    cp path/to/changelog.sh ./changelog.sh
    chmod +x ./changelog.sh

## Usage

Run either:

    /generate-changelog

or:

    bash changelog.sh

The script writes CHANGELOG.md. Pass a custom output path as the first argument:

    bash changelog.sh RELEASE_NOTES.md

## Behavior

- Fetches commits since the latest Git tag.
- Falls back to all commits if no tag exists.
- Groups entries into Features, Fixes, Documentation, Tests, Maintenance, and Other using conventional commit prefixes when available.
- Includes subject, short hash, commit date, and author for each entry.

## Validation

    bash changelog.sh /tmp/CHANGELOG.md
    node scripts/verify-changelog-output.mjs /tmp/CHANGELOG.md
