---
name: generate-changelog
description: Generate a structured CHANGELOG.md (Added/Fixed/Changed/Removed) from git commits since the last tag. Use when the user asks for a changelog, release notes, or "what changed since the last release".
argument-hint: "[--version NAME] [--since REF] [--output FILE] [--force]"
allowed-tools: Bash(bash:*), Bash(git:*), Read, Edit
---

# Generate Changelog Skill

This skill automatically parses commit history, extracts changes since the last Git tag (or all history if no tags exist), categorizes entries according to Keep a Changelog standards, and outputs a clean `CHANGELOG.md`.

## Workflow for Claude Code

When invoked via `/generate-changelog`:

1. **Locate script**:
   Determine the path to `changelog.sh` in the skill directory:
   ```bash
   SCRIPT_PATH="$(dirname "${CLAUDE_SKILL_PATH:-.}")/changelog.sh"
   ```

2. **Run Generator in Preview Mode**:
   Execute the script to inspect the formatted changelog output:
   ```bash
   bash "$SCRIPT_PATH" -o - $ARGUMENTS
   ```

3. **Handle Exit Codes**:
   - `0`: Success. Review the categorized sections with the user.
   - `3`: Target file already exists. Prompt the user whether they want to overwrite with `--force`.
   - `4`: Not a Git repository or invalid Git reference. Report to the user clearly.
   - `5`: No new commits found in the range. Inform the user that the repository is up to date.

4. **Persist Changelog**:
   Once confirmed, generate the final file:
   ```bash
   bash "$SCRIPT_PATH" $ARGUMENTS
   ```
   Do not commit, tag, or push without explicit user consent.
