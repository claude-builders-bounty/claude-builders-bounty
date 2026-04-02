# 📋 Changelog Generator

> Generate a structured, categorized `CHANGELOG.md` from your git history — in one command.

Follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format. Auto-categorizes commits into **Added**, **Fixed**, **Changed**, **Removed**, **Security**, and **Deprecated** sections using conventional commit prefixes and keyword heuristics.

## Setup (3 steps)

### 1. Copy the script into your project

```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/bounties/changelog/changelog.sh \
  -o changelog.sh && chmod +x changelog.sh
```

Or simply copy `changelog.sh` to your repo root.

### 2. Generate your changelog

```bash
bash changelog.sh
```

That's it — `CHANGELOG.md` is written to your project root.

### 3. (Optional) Add to CI or as a git hook

```yaml
# .github/workflows/changelog.yml
name: Update Changelog
on:
  push:
    tags: ['v*']
jobs:
  changelog:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # full history needed for tags
      - run: bash changelog.sh --prepend --version ${{ github.ref_name }}
      - uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "docs: update changelog for ${{ github.ref_name }}"
```

## How it works

```
git log ──▶ categorize ──▶ CHANGELOG.md
             │
             ├─ feat: / add / implement    → ✅ Added
             ├─ fix: / bugfix / resolve     → 🐛 Fixed
             ├─ refactor: / update / improve→ 🔄 Changed
             ├─ remove: / delete / drop     → 🗑️ Removed
             ├─ security: / CVE / vuln      → 🔒 Security
             └─ (everything else)           → 🔄 Changed
```

**Two-tier classification:**

1. **Conventional Commits** — `feat:`, `fix:`, `refactor:`, `remove:`, `security:`, `docs:`, `chore:`, `perf:`, `ci:`, `test:`, `build:`, `revert:`
2. **Keyword heuristics** — scans subject for action words (`add`, `fix`, `update`, `delete`, etc.)
3. **Default** — uncategorized commits land in "Changed"

## Usage

```bash
# Basic — commits since last tag → CHANGELOG.md
bash changelog.sh

# Custom output file
bash changelog.sh -o RELEASES.md

# Specific range
bash changelog.sh --from v1.0.0 --to v2.0.0

# Set version label manually
bash changelog.sh --version v3.0.0

# Print to terminal (don't write file)
bash changelog.sh --stdout

# Append new release to existing CHANGELOG
bash changelog.sh --prepend

# Different repo
bash changelog.sh --repo /path/to/other/project
```

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `-o, --output` | Output file path | `CHANGELOG.md` |
| `-f, --from` | Start ref (tag/commit) | Latest tag |
| `-t, --to` | End ref | `HEAD` |
| `-r, --repo` | Repository path | `.` |
| `-v, --version` | Release version label | Auto-detect |
| `--stdout` | Print to stdout | Off |
| `--prepend` | Prepend to existing file | Off |
| `-h, --help` | Show help | — |

## Edge cases handled

- **No tags** — uses full repo history from root commit
- **HEAD is a tag** — uses range from previous tag to that tag
- **Single tag only** — range from root to that tag
- **No commits in range** — exits cleanly with a message
- **Non-conventional commits** — falls back to keyword heuristics
- **Breaking changes** (`feat!:`) — flagged with **BREAKING** label
- **Scoped commits** (`feat(auth):`) — scope is parsed, description extracted

## Claude Code integration

Copy `SKILL.md` to your `.claude/skills/` directory to enable the `/generate-changelog` slash command in Claude Code.

## Sample output

See [sample-output.md](sample-output.md) for a realistic example.

## License

MIT
