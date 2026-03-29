# Generate Structured CHANGELOG from Git History

Automatically generate a categorized `CHANGELOG.md` from your project's git history.

## Setup (3 steps)

1. **Download:** Copy `changelog.sh` to your project root
2. **Make executable:** `chmod +x changelog.sh`
3. **Run:** `./changelog.sh`

## Usage

```bash
# Generate changelog since last tag
./changelog.sh

# Generate since a specific tag
./changelog.sh --since v1.2.0

# Custom output file
./changelog.sh --output CHANGES.md
```

## How It Works

- Fetches all commits since the last git tag (or all commits if no tags)
- Auto-categorizes based on conventional commit prefixes and keywords:
  - **Added**: `feat`, `add`, `new`, `create`, `implement`
  - **Fixed**: `fix`, `bug`, `patch`, `resolve`
  - **Changed**: `refactor`, `update`, `change`, `improve`, `enhance`
  - **Removed**: `remove`, `delete`, `drop`, `deprecate`
- Outputs a properly formatted CHANGELOG.md following [Keep a Changelog](https://keepachangelog.com/) format
