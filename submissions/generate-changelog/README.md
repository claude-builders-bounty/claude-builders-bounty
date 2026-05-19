# Generate Changelog

Generate a structured `CHANGELOG.md` from git history.

## Setup

```bash
git clone <repo-url>
cd generate-changelog
```

## Usage

```bash
# Generate CHANGELOG.md in current directory
./generate-changelog.sh

# Generate to a specific file
./generate-changelog.sh CHANGELOG.md
```

## How It Works

1. Fetches commits since the last git tag
2. Auto-categorizes into:
   - **Added** — `feat`, `add`, `introduce`, `implement`, `new`
   - **Fixed** — `fix`, `bug`, `repair`, `correct`, `resolve`, `hotfix`
   - **Changed** — `change`, `update`, `modify`, `refactor`, `improve`, `enhance`, `upgrade`, `deprecate`
   - **Removed** — `remove`, `delete`, `drop`, `clean`, `cleanup`, `revert`
   - **Other** — everything else
3. Outputs a properly formatted `CHANGELOG.md`

## Requirements

- Bash 4.0+
- Git

## License

MIT
