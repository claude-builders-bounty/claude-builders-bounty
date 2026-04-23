# Changelog Generator

**Automatically generate a structured CHANGELOG.md from git commit history.**

## Installation

### Option 1: Bash Script (Standalone)

```bash
# 1. Copy the script to your project
curl -O https://raw.githubusercontent.com/mjthinkkits/claude-builders-bounty/bounty-1-changelog-generator/changelog.sh

# 2. Make it executable
chmod +x changelog.sh

# 3. Run it
bash changelog.sh
```

### Option 2: Claude Code Skill

```bash
# 1. Copy skill to Claude's skills directory
mkdir -p ~/.claude/skills/generate-changelog
curl -o ~/.claude/skills/generate-changelog/SKILL.md https://raw.githubusercontent.com/mjthinkkits/claude-builders-bounty/bounty-1-changelog-generator/SKILL-generate-changelog.md

# 2. Copy the script
curl -o ~/.claude/skills/generate-changelog/changelog.sh https://raw.githubusercontent.com/mjthinkkits/claude-builders-bounty/bounty-1-changelog-generator/changelog.sh
chmod +x ~/.claude/skills/generate-changelog/changelog.sh

# 3. Use in Claude Code
/generate-changelog
```

## How It Works

1. **Finds last git tag** - Uses `git describe --tags` to get the latest version
2. **Fetches commits** - Gets all commits since that tag with `git log`
3. **Auto-categorizes** - Parses commit messages and groups them:
   - **Added**: `feat:`, `add:`, "Add ..."
   - **Fixed**: `fix:`, `bug:`, "Fix ..."
   - **Changed**: `refactor:`, `update:`, `chore:`, "Change ...", "Update ..."
   - **Removed**: `remove:`, `delete:`, "Remove ...", "Delete ..."
4. **Generates CHANGELOG.md** - Outputs in [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format
5. **Preserves history** - Appends new entries to the top, keeps existing content

## Example

### Input (Git commits since last tag)

```
feat: add user authentication with Clerk
fix: hydration mismatch on dashboard page
refactor: auth middleware for edge runtime
Add mobile responsive menu
Fix menu not closing on mobile
Update Next.js to 15.1.2
Remove deprecated API routes
```

### Output (CHANGELOG.md)

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased] - 2026-04-23

### Added

- user authentication with Clerk
- mobile responsive menu

### Fixed

- hydration mismatch on dashboard page
- menu not closing on mobile

### Changed

- auth middleware for edge runtime
- Next.js to 15.1.2

### Removed

- deprecated API routes
```

## Real-World Test

Tested on this repository (`claude-builders-bounty`):

```bash
$ bash changelog.sh
✓ CHANGELOG.md generated successfully!

Summary:
  Added: 5
  Fixed: 2
  Changed: 3
  Removed: 1
```

See the generated `CHANGELOG-SAMPLE.md` in this PR for the actual output.

## Best Practices

### Conventional Commits

For best auto-categorization, use conventional commit format:

```bash
git commit -m "feat: add user dashboard"
git commit -m "fix: resolve memory leak"
git commit -m "refactor: simplify auth logic"
git commit -m "remove: deprecated endpoints"
```

### Action Verb Commits

Or start with action verbs (also works):

```bash
git commit -m "Add user dashboard"
git commit -m "Fix memory leak"
git commit -m "Update dependencies"
git commit -m "Remove old API routes"
```

### Update Version Number

After generating the changelog, update `[Unreleased]` to your version:

```diff
- ## [Unreleased] - 2026-04-23
+ ## [1.2.0] - 2026-04-23
```

Then create a git tag:

```bash
git tag v1.2.0
git push --tags
```

## Requirements

- Git repository with at least one commit
- Bash 4.0+ (macOS/Linux)
- Git 2.0+

## License

MIT - Use freely in your projects
