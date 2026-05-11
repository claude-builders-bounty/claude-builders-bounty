# generate-changelog

Generate a structured `CHANGELOG.md` from any project's git history. Auto-categorizes commits into **Added** / **Fixed** / **Changed** / **Removed** sections.

## Install (3 steps)

1. Copy the script to your project:
   ```bash
   cp skills/changelog/changelog.sh /your/project/changelog.sh
   ```

2. Run it:
   ```bash
   bash changelog.sh
   ```

3. Review the generated `CHANGELOG.md`.

Or use it as a Claude Code skill by copying `SKILL.md` to your project's `.claude/skills/` directory.

## Usage

```bash
# Generate changelog since the last git tag
bash changelog.sh

# Generate changelog since a specific tag
bash changelog.sh --since v2.0.0

# Output to a custom file
bash changelog.sh --output RELEASES.md
```

## How categorization works

The script recognizes both **conventional commit** prefixes and **natural language**:

| Category | Matched prefixes |
|----------|-----------------|
| **Added** | `feat:`, `add`, `new`, `implement` |
| **Fixed** | `fix:`, `bugfix`, `hotfix`, `patch`, `resolve` |
| **Changed** | `refactor:`, `update`, `change`, `improve`, `enhance`, `perf:`, `chore:`, `ci:`, `docs:`, `style:`, `build:` |
| **Removed** | `remove`, `delete`, `deprecate`, `revert` |
| **Other** | Everything else |

## Sample output

See [sample-output.md](sample-output.md) for a real example generated from this repository.

## Requirements

- bash 4+
- git
