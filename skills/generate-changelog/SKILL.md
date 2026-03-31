---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history. Use when the user says "generate changelog", "create CHANGELOG.md", "what changed since last release", "summarize commits", or runs /generate-changelog. Fetches commits since last tag, auto-categorizes into Added/Fixed/Changed/Removed using conventional commits. Outputs formatted CHANGELOG.md ready to commit.
---

# Generate Changelog

Automatically generates a structured `CHANGELOG.md` from your project's git history.

## Output Contract

**Produces:**
- `CHANGELOG.md` — versioned section with Added / Fixed / Changed / Removed categories, commit hashes, and date
- OR stdout preview (with `--dry-run`)

**Does NOT produce:** a git tag, a GitHub release, or any network calls — purely local git history.

**Handoff:** the generated `CHANGELOG.md` is ready to `git add` and commit as part of a release.

## Instructions

### Step 1 — Verify we're in a git repo
```bash
git rev-parse --git-dir
```
If not a git repo → explain to user and stop.

### Step 2 — Run the script
```bash
bash {baseDir}/changelog.sh
```

Common options:
```bash
bash {baseDir}/changelog.sh --dry-run           # preview only, no file written
bash {baseDir}/changelog.sh --since v1.2.0      # start from a specific tag
bash {baseDir}/changelog.sh --version v2.0.0    # set the version label
```

### Step 3 — Show result to user
Read the updated `CHANGELOG.md` and show the new section. Ask if they want to commit it:
```bash
git add CHANGELOG.md && git commit -m "chore: update CHANGELOG for [version]"
```

## Categorization rules

| Category | Conventional prefix | Keyword fallback |
|---|---|---|
| **Added** | `feat`, `add` | add, new, creat, introduc, implement |
| **Fixed** | `fix`, `bug` | fix, bug, patch, correct, resolv |
| **Changed** | `refactor`, `perf`, `chore`, `ci`, `style`, `docs`, `test` | (default bucket) |
| **Removed** | `revert`, `remove`, `delete`, `drop` | remov, delet, drop, deprecat |

## Edge cases

- **No tags yet** → uses entire commit history from first commit
- **No commits since last tag** → reports "nothing to generate", exits cleanly
- **Merge commits** → automatically excluded (`--no-merges`)
- **Existing CHANGELOG.md** → new section prepended after the `# Changelog` heading
- **No package.json/Cargo.toml** → version label defaults to `Unreleased`

## Rules
1. Always run `--dry-run` first if the user wants to preview before writing
2. Never modify any file other than `CHANGELOG.md`
3. If `--since` tag doesn't exist → tell the user and list available tags: `git tag --sort=-version:refname | head -10`
