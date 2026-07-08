# changelog.sh

Generate a structured \`CHANGELOG.md\` from git history.

## Usage

```bash
# In your project directory
bash changelog.sh

# From anywhere
bash changelog.sh --repo /path/to/project

# From a specific tag
bash changelog.sh --since v1.0.0
```

Commits are auto-categorized:
- \`feat:\` / \`add:\` → Added
- \`fix:\` → Fixed
- \`refactor:\` / \`update:\` → Changed
- \`remove:\` / \`deprecate:\` → Removed

Requires Bash 4+ and Git.
