# SKILL.md - Generate Changelog

Generate a structured CHANGELOG.md from git history.

## When to Use

Use this skill when you need to:
- Create or update a project's CHANGELOG
- Generate release notes from recent commits
- Document changes for a new version

## Commands

### Generate CHANGELOG

```bash
/generate-changelog [output_file]
```

Generates a CHANGELOG.md file from git commits since the last tag.

**Arguments:**
- `output_file` - Optional. Defaults to `CHANGELOG.md`

**Example:**
```bash
/generate-changelog
/generate-changelog RELEASE_NOTES.md
```

## How It Works

1. Detects the last git tag (or uses all commits if no tags exist)
2. Categorizes commits into sections:
   - 🚀 Added (feat, add, implement, new)
   - 🐛 Fixed (fix, bug, repair, resolve)
   - 🔧 Changed (change, update, refactor, improve)
   - 🗑️ Removed (remove, delete, drop)
   - 📚 Documentation (doc, readme)
   - 🧪 Tests (test, spec, coverage)
   - 🔒 Security (security, vuln, auth)
3. Links PR numbers to GitHub PR pages
4. Outputs a properly formatted Markdown file

## Requirements

- Git repository with at least one commit
- `git` command available in PATH
- For PR links: remote origin set to GitHub URL

## Installation

1. Copy `generate-changelog.sh` to your project root
2. Make it executable: `chmod +x generate-changelog.sh`
3. Optionally add to PATH or create alias

```bash
# Add to .bashrc or .zshrc
alias generate-changelog='/path/to/generate-changelog.sh'
```
