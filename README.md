# CHANGELOG Generator — Skill for Claude Code / Bash

A bash script that automatically generates a structured `CHANGELOG.md` from your project's git history.

---

## 🚀 Setup (3 steps)

**Step 1** — Place `changelog.sh` in your project root:

```bash
curl -O https://raw.githubusercontent.com/yihangwu539-png/claude-builders-bounty/main/changelog.sh
chmod +x changelog.sh
```

**Step 2** — Make sure you have `git` installed and are inside a git repository:

```bash
git init  # or ensure .git exists
```

**Step 3** — Run it:

```bash
./changelog.sh
```

That's it! Your `CHANGELOG.md` will be generated automatically.

---

## 📖 Usage

```
./changelog.sh                  # Writes CHANGELOG.md
./changelog.sh --output=FILE    # Write to a specific file
./changelog.sh --since=v1.0.0   # Start from a specific tag
./changelog.sh --dry-run        # Print to stdout (no file write)
./changelog.sh --help           # Show full help
```

## 🧠 How it works

1. Fetches all commits since the **last git tag** (or all commits if no tags exist)
2. Auto-categorizes each commit into: **Added ✨**, **Fixed 🐛**, **Changed 🔄**, or **Removed 🗑️**
3. Uses [conventional commit](https://www.conventionalcommits.org/) prefixes and keyword heuristics for categorization
4. Outputs a well-formatted `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/) standards
5. Includes links to commits, author info, and summary statistics

## 📋 Sample output

See [`CHANGELOG_SAMPLE.md`](./CHANGELOG_SAMPLE.md) for a sample generated from this repository.

## 🔧 Requirements

- `git` installed and available on `PATH`
- A git repository with at least one commit

---

*Part of the [Claude Builders Bounty](https://github.com/claude-builders-bounty/claude-builders-bounty) program.*
