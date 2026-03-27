# SKILL: Generate CHANGELOG from git history

## What it does
Generates a structured `CHANGELOG.md` from your project's git history.
- Automatically fetches commits since the last git tag
- Categorizes into **Added / Fixed / Changed / Removed**
- Detects version from `package.json` or `Cargo.toml`
- Prepends to existing CHANGELOG without destroying history

## Usage

```bash
# Run directly — auto-detects last tag
bash changelog.sh

# Custom range
bash changelog.sh --since v1.2.0

# Specify version and output file
bash changelog.sh --version 2.0.0 --output RELEASES.md
```

## Trigger phrase (Claude Code)
```
/generate-changelog
```

---

## SKILL.md Instructions (for Claude Code)

When the user types `/generate-changelog`:

1. Check if `changelog.sh` exists in the project root. If not, offer to create it.
2. Run:
   ```bash
   bash changelog.sh
   ```
3. Read the generated `CHANGELOG.md` and summarize what was categorized.
4. Ask the user if they want to review or commit the file.

### Advanced options
- `--since <tag>` — override the baseline tag
- `--version <x.y.z>` — override the detected version
- `--output <file>` — write to a different file (default: `CHANGELOG.md`)
