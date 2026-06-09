# Git Changelog Generator

A lightweight, zero-dependency bash script to automatically generate structured, markdown-formatted `CHANGELOG.md` files from your Git commit history. 

It fetches all commits since the last Git tag (or all commits if no tags exist), groups them by action (`Added`, `Changed`, `Fixed`, `Removed`), and links commits directly to their GitHub pages.

## Setup & Usage (3 steps or fewer)

1. **Download the script** to your repository root:
   ```bash
   curl -o changelog.sh https://raw.githubusercontent.com/sosal123tyu1/claude-builders-bounty/main/changelog.sh
   ```

2. **Make it executable**:
   ```bash
   chmod +x changelog.sh
   ```

3. **Run the generator**:
   ```bash
   ./changelog.sh
   ```

---

*Powered by [sosal123tyu1](https://github.com/sosal123tyu1)*
