# changelog-skill

> Auto-generate a structured `CHANGELOG.md` from git history — in one command.

[![Bounty $50](https://img.shields.io/badge/bounty-%2450-brightgreen)](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)

---

## Setup (3 steps)

**Step 1 — Clone or copy this skill into your project**

```bash
curl -O https://raw.githubusercontent.com/uvkwong/changelog-skill/main/changelog.sh
chmod +x changelog.sh
```

**Step 2 — Run**

```bash
bash changelog.sh
```

That's it. `CHANGELOG.md` is written to your project root.

**Step 3 — (Optional) Use as a Claude Code skill**

Copy `SKILL.md` to your project root, then type `/generate-changelog` in Claude Code.

---

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--since <tag>` | last git tag | Start from a specific tag |
| `--output <file>` | `CHANGELOG.md` | Write to a custom file path |

```bash
# Examples
bash changelog.sh --since v1.0.0
bash changelog.sh --output HISTORY.md
bash changelog.sh --since v2.1.0 --output docs/CHANGES.md
```

---

## How it categorises commits

The script reads the **subject line** of each commit and maps it to a category:

| Category | Matched prefixes (case-insensitive) |
|----------|-------------------------------------|
| ✨ Added | `feat`, `add`, `new`, `create`, `implement`, `init` |
| 🐛 Fixed | `fix`, `bug`, `patch`, `hotfix`, `resolve`, `close` |
| 🔄 Changed | `refactor`, `perf`, `style`, `docs`, `test`, `ci`, `chore`, `update`, `improve`, `bump`, `change` |
| 🗑️ Removed | `remove`, `delete`, `drop`, `clean` |
| 📦 Other | anything else |

> Works with **conventional commits** (`feat: add login`) as well as plain messages (`Add login button`).

---

## Sample output

```markdown
# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [v1.2.4] — 2026-03-31

> Changes since `v1.2.3`

### ✨ Added
- feat: add dark mode toggle (`a3f1b2c`)
- add user avatar upload (`9d8e7f6`)

### 🐛 Fixed
- fix: resolve login redirect loop (`c4d5e6f`)
- fix null pointer in cart service (`1a2b3c4`)

### 🔄 Changed
- refactor: extract auth middleware (`7890abc`)
- docs: update API reference (`def1234`)

### 🗑️ Removed
- remove deprecated v1 endpoints (`456789a`)

---

[v1.2.4]: https://github.com/example/repo/compare/v1.2.3...HEAD
```

---

## Requirements

- `git` (any version ≥ 2.x)
- `bash` (macOS, Linux, WSL, or Git Bash on Windows)

No external dependencies. No npm install. No pip install.

---

## License

MIT
