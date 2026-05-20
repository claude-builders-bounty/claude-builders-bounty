# Changelog Generator

> 📦 A zero-dependency bash script + Claude Code skill that auto-generates
> structured `CHANGELOG.md` from git history.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
![Shell](https://img.shields.io/badge/shell-bash-blue)

## ✨ Features

- 🔍 **Auto-detects** git tags and generates changelog since the last one
- 🏷️ **Smart categorisation** — conventional commits + keyword heuristics:
  `Added` / `Fixed` / `Changed` / `Removed` / `Deprecated` / `Security`
- 📝 **Clean Markdown** output with project name, date, and summary
- 🎨 **Coloured terminal output** for quick visual feedback
- ⚡ **No dependencies** — pure bash, runs anywhere git is installed

## 🚀 Quick Start (3 steps)

```bash
# 1. Make executable
chmod +x changelog.sh

# 2. Run inside any git repo
./changelog.sh

# 3. View the output
cat CHANGELOG.md
```

## 📖 Usage

| Command | Description |
|---------|-------------|
| `./changelog.sh` | Commits since last tag → `CHANGELOG.md` |
| `./changelog.sh --all` | Full repo history |
| `./changelog.sh --range=v1.0.0..v2.0.0` | Custom revision range |
| `./changelog.sh --output=RELEASE_NOTES.md` | Custom output file |
| `./changelog.sh --no-unreleased` | Skip "Unreleased" section |

## 🎯 Claude Code Integration

Copy `SKILL.md` to your project's `.claude/skills/` directory, then use:

```
/generate-changelog
```

## 🧪 Tested On

- ✅ Git 2.40+ (Windows / macOS / Linux)
- ✅ Real repositories with 50–500+ commits
- ✅ Projects with and without git tags
- ✅ Conventional commit and free-form commit styles

## 📂 Files

```
changelog-generator/
├── changelog.sh          # main bash script
├── SKILL.md              # Claude Code skill definition
├── CHANGELOG.sample.md   # example output
└── README.md             # this file
```

## 📄 License

MIT — see the repository LICENSE file.
