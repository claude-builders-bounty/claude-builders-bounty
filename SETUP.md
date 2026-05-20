# changelog.sh — Quick Setup

## 3-Step Setup

```bash
# 1. Make it executable
chmod +x changelog.sh

# 2. Run it in any git repo
bash changelog.sh

# 3. Your CHANGELOG.md is ready!
cat CHANGELOG.md
```

## Usage

```bash
# Since a specific tag
bash changelog.sh --since v1.2.0

# Custom output path
bash changelog.sh --output docs/CHANGELOG.md
```

## How It Works

- Fetches commits since the **last git tag** (or all commits if no tags)
- Auto-categorizes by [Conventional Commits](https://www.conventionalcommits.org/) prefixes:
  - `feat:` / `add:` → **Added**
  - `fix:` / `bug:` → **Fixed**
  - `remove:` / `revert:` → **Removed**
  - Everything else → **Changed**
- Skips merge commits
- Outputs a clean `CHANGELOG.md` with proper structure

See `SAMPLE_CHANGELOG.md` for example output.
