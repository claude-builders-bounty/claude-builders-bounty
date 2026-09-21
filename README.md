# CHANGELOG Generator for Claude Code

Generate structured CHANGELOG.md from git history automatically.

## Install (2 commands)
\\ash
git clone https://github.com/Zhiyilang074811/claude-builders-bounty.git
python claude-bounty-work/changelog.py
\
## Usage
\\ash
# From repo root (generates CHANGELOG.md in current dir)
python changelog.py

# From another repo
python changelog.py /path/to/repo

# Custom output
python changelog.py /path/to/repo RELEASE.md
\
## How it works
- Fetches commits since the last git tag
- Categorizes commits: Added / Fixed / Changed / Removed
- Outputs a clean markdown CHANGELOG

## Categories
| Category | Keywords |
|----------|----------|
| Added | add, feat, new, implement |
| Fixed | fix, bug, repair |
| Changed | change, update, modify, rename |
| Removed | remove, delete, drop |
