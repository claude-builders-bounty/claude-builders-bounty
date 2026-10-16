# Generate Changelog Skill & CLI

Automatically generates a structured, human-readable `CHANGELOG.md` from your Git commit history, categorized into **Added**, **Fixed**, **Changed**, and **Removed**, following the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) standard.

---

## ⚡ Quickstart in 3 Steps

1. **Install to your repository**:
   ```bash
   mkdir -p .claude/skills/generate-changelog
   cp -r skills/generate-changelog/* .claude/skills/generate-changelog/
   chmod +x .claude/skills/generate-changelog/changelog.sh
   ```

2. **Generate your changelog**:
   - In **Claude Code**: run `/generate-changelog`
   - In your **terminal**: run `bash .claude/skills/generate-changelog/changelog.sh`

3. **Review and commit**:
   Open `./CHANGELOG.md` to review the generated release notes!

---

## 🛠️ Command-Line Options

```bash
changelog.sh [options]
```

| Option | Description | Default |
| :--- | :--- | :--- |
| `-o, --output FILE` | Output path (use `-` for stdout preview) | `./CHANGELOG.md` |
| `-f, --force` | Overwrite existing changelog file | Disabled |
| `--since REF` | Git reference/tag to compute diff from | Latest reachable Git tag |
| `--version NAME` | Heading name for this release | `Unreleased` |
| `-C, --repo DIR` | Path to target Git repository | Current directory |
| `-h, --help` | Show usage help | - |

---

## 🏷️ Commit Categorization Rules

The generator uses a two-tier classification engine:

1. **Conventional Commits**:
   - `feat(...)` / `feat`: **Added**
   - `fix(...)` / `fix`: **Fixed**
   - `revert(...)` / `remove`: **Removed**
   - `refactor`, `perf`, `docs`, `style`, `build`, `ci`, `test`, `chore`: **Changed**
   - Breaking changes marked with `!` or `BREAKING CHANGE:` receive a bold `**BREAKING:**` prefix.

2. **Keyword Fallback**:
   - Starting with *add*, *introduce*, *create*, *implement*: **Added**
   - Starting with *fix*, *resolve*, *patch*, *correct*: **Fixed**
   - Starting with *remove*, *delete*, *drop*, *deprecate*: **Removed**
   - All other commits fall into **Changed** (nothing is silently dropped).

---

## 🚦 Exit Codes

- `0`: Success
- `1`: Runtime / I/O error
- `2`: Invalid CLI options / arguments
- `3`: Destination file already exists (use `--force` to overwrite)
- `4`: Not a Git repository or reference not found
- `5`: No commits found in range
