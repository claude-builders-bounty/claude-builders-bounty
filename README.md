# changelog.sh — Git History CHANGELOG Generator

A zero-dependency bash script that generates a structured `CHANGELOG.md` from git history.

## Installation

```bash
curl -sLO https://raw.githubusercontent.com/Andyyook/claude-builders-bounty/main/changelog.sh
chmod +x changelog.sh
```

## Usage

```bash
./changelog.sh              # Generate CHANGELOG.md
./changelog.sh --stdout     # Print to stdout
./changelog.sh --tag=v1.0.0 # From a specific tag
```

## How It Works

- Fetches commits since the last git tag (or full history if no tags)
- Auto-categorizes into: 🚀 Added / 🐛 Fixed / 🔄 Changed / 🗑️ Removed
- Uses Conventional Commit prefixes (`feat:`, `fix:`, `chore:`, etc.)
- Outputs a proper Markdown changelog with version and date
