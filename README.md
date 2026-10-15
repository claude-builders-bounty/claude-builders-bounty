# Git Changelog Generator Skill

A lightweight, zero-dependency bash tool and Claude Code skill to automatically generate structured `CHANGELOG.md` files from git history.

## 🚀 3-Step Setup

1. **Make the script executable**:
   ```bash
   chmod +x changelog.sh
   ```

2. **Run the changelog generator**:
   ```bash
   ./changelog.sh
   ```
   *(Or via Claude Code skill command: `/generate-changelog`)*

3. **Verify generated `CHANGELOG.md`**:
   Review the auto-categorized entries grouped under `Added`, `Fixed`, `Changed`, and `Removed`.

## ⚙️ Advanced Flags

```bash
# Generate changelog for a specific release tag range
./changelog.sh --from v1.0.0 --to v1.1.0 --output CHANGELOG.md

# Preview output in console without writing to file
./changelog.sh --stdout
```

## 🧪 Testing & Verification
Tested against real git repositories with multiple commit types (Conventional Commits, merge commits, and standard messages). See [examples/sample-output.md](examples/sample-output.md) for sample generated output.
