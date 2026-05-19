# 📝 CHANGELOG Generator

Automatically generate a structured `CHANGELOG.md` from git history since the last tag.

## ⚡ Quick Start (3 steps)

```bash
# 1. Clone this repo (or just grab changelog.sh)
curl -O https://raw.githubusercontent.com/2569658930/claude-builders-bounty/main/changelog.sh

# 2. Make it executable
chmod +x changelog.sh

# 3. Run it in any git repo
bash changelog.sh
```

## 🎯 How It Works

- Finds the latest git tag via `git describe --tags`
- Collects all non-merge commits since that tag
- Auto-categorizes into **Added / Fixed / Changed / Removed**
- Outputs a clean `CHANGELOG.md`

## 📂 Files

| File | Description |
|------|-------------|
| `changelog.sh` | Bash script (zero dependencies beyond git) |
| `SKILL.md` | Claude Code skill for `/generate-changelog` |
| `SAMPLE_CHANGELOG.md` | Sample output from yt-dlp repo |

## 🔧 Options

```bash
bash changelog.sh --output docs/CHANGELOG.md   # Custom output path
bash changelog.sh --tag v2.0.0                 # Start from a specific tag
```

## 📋 Sample Output

See [SAMPLE_CHANGELOG.md](SAMPLE_CHANGELOG.md) — generated from the yt-dlp repository.
