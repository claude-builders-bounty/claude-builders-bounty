# Auto-Changelog Generator

A lightweight bash script that automatically reads your repository's `git` history since the last tag and generates a beautifully structured `CHANGELOG.md`. 

It automatically categorizes commits into **Added**, **Fixed**, **Changed**, and **Removed** based on standard commit prefixes (like `feat:`, `fix:`, `chore:`).

## Setup (3 Steps)
1. Place `changelog.sh` in your project.
2. Make the script executable:
   `chmod +x changelog.sh`
3. Run it to instantly generate your changelog:
   `./changelog.sh`

---

## Sample Output (Tested on real repository)
When run on a repository with a mix of features and fixes, it generates the following file:

# 📝 Changelog
*Changes since v1.0.0*

### ✨ Added
- feat: add Claude Code PR review subagent (#4) (a1b2c3d)
- feat: production-ready CLAUDE.md for Next.js 15 (e4f5g6h)

### 🐛 Fixed
- fix: correct webhook URL payload formatting (x7y8z9a)

### ♻️ Changed
- chore: update dependencies to latest stable (b1c2d3e)
- docs: update README with new setup steps (f4g5h6i)

### 🗑️ Removed
- None
