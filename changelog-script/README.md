# Changelog Generator Script

This is a simple bash script that automatically generates a structured `CHANGELOG.md` from a project's git history since the last tag.

## Installation & Setup

1. Copy the script to your project root:
   ```bash
   cp changelog.sh /path/to/your/project/
   ```
2. Make it executable:
   ```bash
   chmod +x changelog.sh
   ```
3. Run the script:
   ```bash
   ./changelog.sh
   ```

The script will read your commit history and output a categorized `CHANGELOG.md` file!