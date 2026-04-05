# Automated Changelog Generator (Issue #1)

This solution provides a robust Bash script and a Claude Code `SKILL.md` to automatically generate a structured `CHANGELOG.md` from a project's git history, fulfilling the requirements for Bounty #1.

## Features
- **Dependency Checks:** Ensures `claude` and `git` are installed before running.
- **Tag Detection:** Automatically finds the last git tag and fetches commits since that tag. If no tags exist, it fetches recent commits.
- **Safe Interpolation:** Commit messages are passed safely via a temporary file, avoiding arbitrary bash variable expansion (e.g., if a commit message contains `$PATH`).
- **Token Limits:** Limits the fetch to the last 500 commits to prevent overwhelming the LLM context window.

## Usage

### Option 1: Direct Bash Script
Simply execute the script in your git repository:
```bash
bash ./generate-changelog.sh
```
It will analyze the commits and output a cleanly formatted `CHANGELOG_NEW.md` using the Anthropic Claude CLI.

### Option 2: Claude Code Skill
If you are using Claude Code, the provided `SKILL.md` acts as a custom skill definition. Place it in your project's `.claude/skills/` directory (or wherever you manage skills) so Claude knows how to invoke the changelog generation.

## Requirements
- `git`
- [Anthropic Claude CLI](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview) (`npm install -g @anthropic-ai/claude-cli`)
