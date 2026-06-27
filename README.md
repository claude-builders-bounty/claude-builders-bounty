# CHANGELOG Generator Skill

Auto-generate a structured `CHANGELOG.md` from your project's git history.
Works in **3 steps** or fewer.

---

## Setup (3 Steps)

### 1. Place the files

```
your-project/
├── .claude/
│   └── skills/
│       └── generate-changelog/
│           └── SKILL.md      ← copy from this repo
├── changelog.sh              ← copy from this repo
└── README.md
```

### 2. (Claude Code users only) Make the skill discoverable

```bash
cp -r .claude/skills/generate-changelog ~/.claude/skills/
```

### 3. Generate your changelog

```bash
# Standalone (no Claude Code needed)
bash changelog.sh

# Or inside Claude Code
/generate-changelog
```

That's it — `CHANGELOG.md` appears in your project root.

---

## Usage

```bash
# Default: write CHANGELOG.md
bash changelog.sh

# Print to stdout (dry-run)
bash changelog.sh --stdout

# Specify a custom tag range
bash changelog.sh --from v1.0.0 --to HEAD~5

# Show help
bash changelog.sh --help
```

## Sample Output

Running against a sample repo with conventional commits:

```markdown
# Changelog

## [v0.1.1] - 2026-06-27

### Added
- Add helper utilities module ([21886fe](#/commit/21886fe))
- Add main entry point ([1e3a62a](#/commit/1e3a62a))

### Fixed
- Correct output format ([c230c51](#/commit/c230c51))

### Changed
- Add test dependency ([01f8865](#/commit/01f8865))

### Removed
- Drop unused utils module ([07fcd2d](#/commit/07fcd2d))

---
_5 change(s) since v0.1.0_
```

*(Your actual output will vary based on your project's commit history.)*

---

## How It Works

1. Finds the **most recent git tag** reachable from `HEAD`
2. Gathers all **non-merge commits** since that tag
3. **Categorises** each commit using:
   - Conventional Commit prefixes (`feat:` → Added, `fix:` → Fixed, …)
   - Keyword fallback (`add`, `fix`, `remove`, …)
4. Outputs a well-formatted Markdown file with commit links

---

## Requirements

- **git** 2.x+
- **bash** 4.x+ (or compatible)
