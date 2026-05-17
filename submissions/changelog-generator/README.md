# CHANGELOG Generator for Claude Code

A Claude Code skill + Python script that generates a structured `CHANGELOG.md` from your project's git history.

## Setup (3 steps)

1. **Copy files into your project** — place `changelog.py` and `SKILL.md` in your project root
2. **Load the skill** — in Claude Code: `/skill load changelog-generator` (or use `-s changelog-generator` on launch)
3. **Generate** — run `/generate-changelog` in Claude Code, or `python changelog.py` in your terminal

That's it — your `CHANGELOG.md` is generated automatically.

## Features

- ✅ Auto-detects the last git tag
- ✅ Parses conventional commits (`feat:`, `fix:`, `refactor:`, etc.)
- ✅ Categorizes into `✨ Added` / `🔄 Changed` / `🐛 Fixed` / `🗑️ Removed`
- ✅ Includes commit hashes with GitHub links
- ✅ Supports custom repo path, output file, and tag range
- ✅ Works standalone (no Claude Code required)

## Options

```bash
python changelog.py                           # Current directory → CHANGELOG.md
python changelog.py --repo ../other-project   # Another repo
python changelog.py --output docs/CHANGES.md  # Custom output path
python changelog.py --from-tag v0.5.0         # Start from a specific tag
```

## Sample output

See [`sample-output.md`](./sample-output.md) for a real example generated from an open-source project.
