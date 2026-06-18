# 📋 Auto CHANGELOG Generator

Generate a structured `CHANGELOG.md` from your git history in one command.

## Setup (3 steps)

1. **Download the script**
   ```bash
   curl -O https://raw.githubusercontent.com/fanjuxin9630/openclaw-workspace/master/changelog/generate_changelog.sh
   chmod +x generate_changelog.sh
   ```

2. **Run it in your project**
   ```bash
   ./generate_changelog.sh
   ```

3. **Commit the result**
   ```bash
   git add CHANGELOG.md && git commit -m "docs: add CHANGELOG"
   ```

## Usage

```bash
./generate_changelog.sh [output_file] [repo_path]
```

### Examples

```bash
# Basic usage (generates CHANGELOG.md in current directory)
./generate_changelog.sh

# Custom output file
./generate_changelog.sh docs/HISTORY.md

# Specify a different repo
./generate_changelog.sh CHANGELOG.md ../my-other-project
```

## Python version

```bash
python3 generate_changelog.py [output_file] [repo_path]
```

## Features

- ✅ Fetches commits since the last git tag (or all commits if no tags)
- ✅ Auto-categorizes into: Added / Fixed / Changed / Removed
- ✅ Recognizes conventional commits (`feat:`, `fix:`, `chore:`, etc.)
- ✅ Recognizes semantic prefixes (`Add`, `Fix`, `Update`, `Remove`, etc.)
- ✅ Outputs a properly formatted CHANGELOG.md
- ✅ Includes commit hashes with GitHub links
- ✅ Works anywhere (Bash or Python)

## Output example

```markdown
# Changelog

## [Unreleased]

### ✨ Added
- Implement user authentication. ([a1b2c3d](https://github.com/user/repo/commit/a1b2c3d))

### 🐛 Fixed
- Resolve login page crash on mobile. ([e4f5g6h](https://github.com/user/repo/commit/e4f5g6h))

### 🔄 Changed
- Update dependencies to latest versions. ([i7j8k9l](https://github.com/user/repo/commit/i7j8k9l))
```

## Compatibility

- **Bash** — Works on Linux, macOS, WSL, CI/CD pipelines
- **Python 3** — Works anywhere Python 3 is installed

---

_Claude Builders Bounty #1 · $50_
