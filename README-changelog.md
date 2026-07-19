# Git Changelog Generator

A simple, zero-dependency bash script to generate a structured `CHANGELOG.md` based on your Git commit history since the last tag. It automatically categorizes commits into Added, Fixed, Changed, and Removed based on conventional commit prefixes (e.g., `feat:`, `fix:`, `remove:`).

## Setup Instructions

1. **Download the script**: Save `changelog.sh` into your repository root.
2. **Make it executable**: Run `chmod +x changelog.sh` in your terminal.
3. **Generate**: Run `./changelog.sh` to automatically parse history and create `CHANGELOG.md`.