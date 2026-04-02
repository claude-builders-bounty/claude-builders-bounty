# /generate-changelog

Generate a structured CHANGELOG.md from git commit history, auto-categorized by change type.

## When to use

Use `/generate-changelog` when the user wants to:
- Generate a changelog from recent git commits
- Create release notes from git history
- Categorize commits into Added/Fixed/Changed/Removed sections
- Prepare a CHANGELOG.md following Keep a Changelog format

## Instructions

Run the changelog generator script. The script is located at `bounties/changelog/changelog.sh` relative to the workspace root.

### Basic usage (full changelog to file)

```bash
bash bounties/changelog/changelog.sh
```

### Print to stdout instead of writing a file

```bash
bash bounties/changelog/changelog.sh --stdout
```

### Prepend a new release to an existing CHANGELOG.md

```bash
bash bounties/changelog/changelog.sh --prepend
```

### Specify a custom range

```bash
bash bounties/changelog/changelog.sh --from v1.0.0 --to v1.1.0
```

### Specify a version label

```bash
bash bounties/changelog/changelog.sh --version v2.0.0
```

### All options

| Flag | Description |
|---|---|
| `-o, --output FILE` | Output file (default: `CHANGELOG.md`) |
| `-f, --from REF` | Start ref — tag or commit (default: last tag) |
| `-t, --to REF` | End ref (default: `HEAD`) |
| `-r, --repo DIR` | Repository path (default: `.`) |
| `-v, --version VER` | Version label (default: auto-detect) |
| `--stdout` | Print to stdout |
| `--prepend` | Prepend to existing CHANGELOG |
| `-h, --help` | Show help |

### How categorization works

The script uses a two-tier classification strategy:

1. **Conventional Commits** (highest priority): Recognizes prefixes like `feat:`, `fix:`, `refactor:`, `remove:`, `security:`, etc.
2. **Keyword heuristics** (fallback): Scans commit subjects for action words like "add", "fix", "update", "remove", "delete", etc.
3. **Default**: Unclassified commits go into the "Changed" bucket.

### Output format

The output follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) with sections:
- **Added** — new features
- **Fixed** — bug fixes
- **Changed** — refactors, updates, improvements
- **Removed** — deleted features or code
- **Security** — vulnerability fixes
- **Deprecated** — soon-to-be-removed features

Each entry includes a short commit hash for traceability.

### After running

1. Review the generated `CHANGELOG.md` for accuracy
2. Edit any miscategorized entries if needed
3. Commit the changelog: `git add CHANGELOG.md && git commit -m "docs: update changelog"`
