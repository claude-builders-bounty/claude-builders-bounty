# changelog.sh

Generate a structured `CHANGELOG.md` from any Git repository's commit history.

## Quick Start

```bash
bash changelog.sh
```

This generates a `CHANGELOG.md` in the current directory using all commits
since the last Git tag (or since the first commit).

## Usage

| Argument     | Default          | Description                          |
|-------------|------------------|--------------------------------------|
| `--repo`    | `$(pwd)`         | Path to the target Git repository    |
| `--tag`     | Last tag / first commit | Starting ref (tag or commit hash) |
| `--output`  | `CHANGELOG.md`   | Output file path                     |

### Examples

```bash
# Generate for another repo
bash changelog.sh --repo /path/to/project --output docs/CHANGELOG.md

# Generate from a specific tag
bash changelog.sh --tag v1.0.0

# Generate from a commit hash
bash changelog.sh --tag abc1234
```

## Output Sections

Commits are auto-categorized into:

- **Added** — `add:`, `new:`, `feat:`, `introduce:`, `create:`
- **Fixed** — `fix:`, `bug:`, `hotfix:`
- **Changed** — `change:`, `refactor:`, `update:`, `improve:`
- **Removed** — `remove:`, `delete:`, `drop:`
- **Other** — everything else

## Requirements

- **Git** (any modern version)
- **Bash 3+** (available on macOS, Linux, WSL)

No external dependencies. No Python. No npm.
