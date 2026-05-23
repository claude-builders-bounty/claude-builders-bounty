# changelog-gen

A Claude Code skill + standalone bash script that generates a structured `CHANGELOG.md` from git history.

## Setup (3 steps)

```bash
# 1. Make it executable
chmod +x changelog.sh

# 2. Run in any git repo
./changelog.sh

# 3. Optional: since a specific tag
./changelog.sh v1.0.0 docs/CHANGELOG.md
```

## Features

- Fetches commits since the last git tag (or last 100 commits)
- Auto-categorizes into **Added** / **Fixed** / **Changed** / **Removed**
- Outputs a Keppchangelog-compatible `CHANGELOG.md`
- Zero dependencies — pure bash
- Works on Linux, macOS, and WSL

## Categorization Logic

| Prefix          | Category |
|-----------------|----------|
| `add`, `feat`, `feature`, `new`, `implement`, `create`, `introduce`, `support` | **Added** |
| `fix`, `bug`, `patch`, `resolve`, `hotfix`, `correct` | **Fixed** |
| `remove`, `drop`, `delete`, `deprecate`, `retire` | **Removed** |
| Everything else | **Changed** |

## Claude Code Usage

Add as a custom skill:

```
/skill changelog.sh — generate CHANGELOG.md from git history
```

Or use directly:

```
/generate-changelog → runs changelog.sh and outputs structured changelog
```

## Sample Output

See [EXAMPLE.md](EXAMPLE.md) for a real-world generated changelog.

## License

MIT
