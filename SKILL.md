# Skill: Generate Structured CHANGELOG

## Description
This skill enables the generation of a structured `CHANGELOG.md` file from git history. It parses commit messages and groups them into logical categories (Features, Fixes, Documentation, etc.) based on conventional commit prefixes.

## Context
Use this skill when a project needs to summarize changes since the last release or when preparing a new version.

## Usage
- Command: `/generate-changelog`
- Execution: Runs `python3 generate_changelog.py` in the repository root.

## Technical Details
- Language: Python 3
- Requirements: `git` must be installed and the directory must be a git repository.
- Logic:
    1. Finds the most recent git tag.
    2. Retrieves all commits from that tag to `HEAD`.
    3. Categorizes commits using regex patterns on the subject line.
    4. Formats and writes the results to `CHANGELOG.md`.
