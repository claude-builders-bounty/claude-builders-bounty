# CHANGELOG Generator Skill

## Description
Generates a structured CHANGELOG.md from git history since the last tag.

## Usage
\\ash
python changelog.py [repo_path] [output_file]
# Defaults: current directory, CHANGELOG.md
\
## Categories
- **Added**: feat, new, implement, add
- **Fixed**: fix, bug, repair, cleanup, refactor  
- **Changed**: update, modify, rename, replace
- **Removed**: remove, delete, drop, deprecate

## Claude Code Integration
Add to your project: \lias changelog='python ~/.claude/skills/changelog/changelog.py .'