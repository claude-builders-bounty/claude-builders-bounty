# CHANGELOG Generator

A zero-dependency CHANGELOG generator that works as a **Claude Code skill** (`/generate-changelog`) or a **standalone bash script** (`bash changelog.sh`).

## Setup in 3 Steps

### Quick start (bash script)
```bash
# 1. Copy the script to your project
cp changelog.sh /path/to/your/project/

# 2. Make it executable
chmod +x changelog.sh

# 3. Run it
cd /path/to/your/project && bash changelog.sh
```

### Claude Code Skill
```bash
# 1. Place SKILL.md in your project
# 2. Run in Claude Code:
/generate-changelog
```

## Features

- ✅ **Conventional Commits parsing** — `feat:`, `fix:`, `refactor:`, etc.
- ✅ **Smart tag detection** — finds the most recent version tag automatically
- ✅ **7 categories** — Added, Fixed, Changed, Deprecated, Removed, Security, Documentation
- ✅ **Zero dependencies** — pure bash + git, no npm/pip
- ✅ **Beautiful output** — auto-links commits, capitalizes messages
- ✅ **Error handling** — graceful fallbacks for edge cases

## Requirements

- `bash 4+`
- `git` (any version)
