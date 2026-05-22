# Auto Changelog Generator

Generate a structured `CHANGELOG.md` from your git history.

## Setup

### 1. Clone this repo

```bash
git clone https://github.com/your-org/claude-builders-bounty.git
cd claude-builders-bounty
```

### 2. Run the script

```bash
chmod +x changelog.sh
./changelog.sh [optional tag]
```

- Without arguments: categorizes all commits
- With a tag: categorizes commits since that tag

### 3. Output

Writes `CHANGELOG.md` in the current directory with sections:

- **Added** — commits starting with `feat`, `add`, `new`, `implement`
- **Fixed** — commits starting with `fix`, `bug`, `patch`, `correct`
- **Changed** — everything else
- **Removed** — commits starting with `remove`, `delete`, `drop`, `cleanup`

## Requirements

- Bash 4+
- Git repository with commits

## Example

```bash
./changelog.sh v1.0.0
cat CHANGELOG.md
```

You’ll get a formatted markdown changelog ready to commit.
