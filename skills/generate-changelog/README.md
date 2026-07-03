# generate-changelog

Generate a structured `CHANGELOG.md` from your project's git history using conventional commits.

## Setup (3 steps)

1. **Copy the skill to your project:**
   ```bash
   cp -r skills/generate-changelog /path/to/your/project/skills/generate-changelog
   ```

2. **Make the script executable:**
   ```bash
   chmod +x skills/generate-changelog/changelog.sh
   ```

3. **Run it:**
   ```bash
   bash skills/generate-changelog/changelog.sh
   ```

## Usage

```bash
# Generate full changelog since last tag
bash skills/generate-changelog/changelog.sh

# Generate changelog between versions
bash skills/generate-changelog/changelog.sh --tag v1.0.0 --version "1.1.0"

# Generate changelog for last 10 commits
bash skills/generate-changelog/changelog.sh --since HEAD~10

# Custom output file
bash skills/generate-changelog/changelog.sh --output docs/CHANGELOG.md
```

## Requirements

- **Git** — your project must be a git repository
- **Bash 4+** — typically pre-installed on macOS/Linux

## Sample Output

```markdown
# Changelog

## [v1.0.0] — 2025-06-15

### ✨ Added
- User authentication system ([abc1234](https://github.com/user/repo/commit/abc1234))
- Dashboard analytics widget ([def5678](https://github.com/user/repo/commit/def5678))

### 🐛 Fixed
- Crash on empty search results ([ghi9012](https://github.com/user/repo/commit/ghi9012))
- Memory leak in WebSocket handler ([jkl3456](https://github.com/user/repo/commit/jkl3456))

### 🔄 Changed
- Upgraded to Next.js 15 ([mno7890](https://github.com/user/repo/commit/mno7890))
- Refactored API routes for consistency ([pqr1234](https://github.com/user/repo/commit/pqr1234))
```

## Conventional Commits Supported

| Prefix | Category | Emoji |
|--------|----------|-------|
| `feat:` | Added | ✨ |
| `fix:` | Fixed | 🐛 |
| `docs:` | Documentation | 📖 |
| `perf:` | Performance | ⚡ |
| `refactor:` / `chore:` / `style:` / `revert:` | Changed | 🔄 |
| `remove:` / `deprecate:` / `delete:` | Removed | 🗑 |
| `test:` | Testing | 🧪 |
| `build:` / `ci:` | Dependencies & Build | 📦 |
| `!` or `BREAKING CHANGE` | Breaking Changes | ⚠ |
