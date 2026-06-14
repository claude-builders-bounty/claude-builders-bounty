# changelog.sh — Structured CHANGELOG from git history

Generate a categorized `CHANGELOG.md` from your project's git history. Commits are sorted into **Added ✨**, **Fixed 🐛**, **Changed 🔧**, and **Removed 🗑️** based on conventional commit prefixes and keyword heuristics.

## Setup (3 steps)

```bash
# 1. Download
curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/changelog.sh

# 2. Make executable
chmod +x changelog.sh

# 3. Generate your changelog
bash changelog.sh
```

## Usage

| Command | Description |
|---------|-------------|
| `bash changelog.sh` | Generate `CHANGELOG.md` in current directory |
| `bash changelog.sh --output FILE.md` | Write to a custom path |
| `bash changelog.sh --repo /path` | Run in a different repository |
| `bash changelog.sh --help` | Show help |

## How it works

1. Finds the **last git tag** and collects all commits since then (or from the beginning if no tags exist)
2. Classifies each commit by **conventional commit prefix** (`feat:`, `fix:`, `remove:`, `chore:`, etc.)
3. Falls back to **keyword heuristics** for non-standard messages (containing "add", "fix", "remove", etc.)
4. Outputs a clean **CHANGELOG.md** with emoji-categorized sections and a commit count summary

## Sample output

See [SAMPLE.md](./SAMPLE.md) — output generated from the [Hermes Agent](https://github.com/NousResearch/hermes-agent) repository (~125 commits since last tag).

## Requirements

- **Git** — any modern version
- **Bash** 4.0+ (macOS: `brew install bash` if on older versions)
