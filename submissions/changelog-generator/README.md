# changelog.sh — CHANGELOG Generator

**Bounty #1** — $50 | [claude-builders-bounty/claude-builders-bounty#1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)

Auto-generates a structured `CHANGELOG.md` from git commit history. Zero dependencies — pure bash.

## Setup (3 steps)

**1. Download the script**
```bash
curl -O https://raw.githubusercontent.com/guidou2013-bot/claude-builders-bounty/main/submissions/changelog-generator/changelog.sh
chmod +x changelog.sh
```

**2. Run it in any git repo**
```bash
bash changelog.sh
```

**3. Commit the result**
```bash
git add CHANGELOG.md
git commit -m "docs: generate changelog"
```

## Usage

```bash
# Generate changelog from latest tag to HEAD (default)
bash changelog.sh

# Specify output file
bash changelog.sh --output CHANGES.md

# Generate from a specific tag
bash changelog.sh --since v1.2.0

# Preview without writing
bash changelog.sh --dry-run
```

## How It Works

1. **Finds your latest git tag** via `git describe --tags`
2. **Collects commits** since that tag with `git log TAG..HEAD`
3. **Auto-categorizes** each commit into:
   - **Added** — `feat:`, `add:`, keywords: add/implement/introduce
   - **Fixed** — `fix:`, `bug:`, keywords: fix/resolve/patch
   - **Changed** — `refactor:`, `chore:`, `perf:`, `update:`
   - **Removed** — `remove:`, `delete:`, `deprecate:`
4. **Formats** as Keep a Changelog Markdown with commit links (if GitHub remote detected)
5. **Prepends** to existing `CHANGELOG.md` or creates a new one

## Categorization Logic

Supports [Conventional Commits](https://www.conventionalcommits.org/):

| Commit prefix | Category |
|---------------|----------|
| `feat:`, `add:`, `new:` | Added |
| `fix:`, `bug:`, `hotfix:` | Fixed |
| `refactor:`, `chore:`, `perf:`, `update:` | Changed |
| `remove:`, `delete:`, `deprecate:` | Removed |
| anything else | Changed (fallback) |

Also works without conventional commits — scans message for keywords.

## Sample Output

See [sample_output.md](./sample_output.md) for a real example generated from this repo.

## Requirements

- bash 4+
- git
- No external dependencies

## License

MIT
