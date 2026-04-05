# Skill: Generate Structured Changelog
# Description: Automatically generates a structured CHANGELOG.md from git history using Claude Code.

# PREREQUISITES
# 1. `git` installed in the repository
# 2. `claude` (Anthropic Claude Code CLI) installed and authenticated

# USAGE
# To use this skill, the user or agent must run:
# bash ./generate-changelog.sh

# The script finds the last git tag, grabs all commit messages since then,
# and asks Claude to format them into Added/Fixed/Changed/Removed categories, saving the result to CHANGELOG_NEW.md.
