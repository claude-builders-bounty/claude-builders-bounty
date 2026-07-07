# Git Changelog Generator

A simple tool to generate a beautiful, structured `CHANGELOG.md` from git commits.

## 🚀 Setup & Usage (3 steps)

1. **Save `changelog.sh`** to the root of your git repository.
2. **Make it executable**:
   ```bash
   chmod +x changelog.sh
   ```
3. **Run it**:
   ```bash
   bash changelog.sh
   ```

## Output Format
The script will analyze commits since the last tag (falling back to all commits if no tags are present) and group them into:
- **Added**: Features, additions, and new code.
- **Fixed**: Bug fixes and error resolutions.
- **Removed**: Code deletions and cleanups.
- **Changed**: Refactorings, updates, and maintenance.
