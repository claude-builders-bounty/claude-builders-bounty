# Git Changelog Generator

Auto-generate `CHANGELOG.md` from git history with conventional commit support.

## Setup (3 Steps)

1. **Download the script:**
   ```bash
   curl -o changelog.sh https://raw.githubusercontent.com/your-repo/changelog.sh
   chmod +x changelog.sh
   ```

2. **Install in your project:**
   ```bash
   ./changelog.sh
   ```

3. **View the output:**
   ```bash
   cat CHANGELOG.md
   ```

## Usage

```bash
# Generate using default output (CHANGELOG.md)
./changelog.sh

# Custom output file
OUTPUT_FILE=MY_CHANGELOG.md ./changelog.sh
```

## How It Works

- Fetches commits since the last git tag
- Auto-categorizes using conventional commit prefixes:
  - `feat:`, `feature:`, `add:`, `added:` → **Added**
  - `fix:`, `bugfix:`, `bug:`, `hotfix:` → **Fixed**  
  - `remove:`, `removed:`, `delete:`, `deleted:` → **Removed**
  - Everything else → **Changed**
- Outputs structured Markdown with date header

## Requirements

- Bash 4.0+
- Git

## License

MIT