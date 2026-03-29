# Structured CHANGELOG Generator

A Claude Code skill / bash script that automatically generates a structured `CHANGELOG.md` from your project's git history.

## 🚀 Install (3 steps)

1. **Copy the script** into your project root:
   ```bash
   cp changelog.sh /path/to/your/project/
   ```

2. **Make it executable:**
   ```bash
   chmod +x changelog.sh
   ```

3. **Run it:**
   ```bash
   bash changelog.sh
   ```

That's it! Your `CHANGELOG.md` is generated.

## How It Works

The script reads git commits since the last tag and automatically categorizes them:

| Category | Detected Patterns |
|----------|------------------|
| **Added** | `feat:`, `add`, `create`, `implement`, `new`, `introduce` |
| **Fixed** | `fix:`, `bugfix:`, `resolve`, `patch` |
| **Changed** | `refactor:`, `update`, `change`, `improve`, `chore:`, `docs:` |
| **Removed** | `remove`, `delete`, `drop`, `deprecate` |

## Options

```bash
bash changelog.sh                    # Default: outputs CHANGELOG.md
bash changelog.sh my-changelog.md    # Custom output file
```

## Sample Output

See [SAMPLE_CHANGELOG.md](./SAMPLE_CHANGELOG.md) for a real example generated from this repository.

## Requirements

- **bash** ≥ 4.0 (standard on Linux/macOS, available via Git Bash on Windows)
- **git** (must be run inside a git repository)

## Claude Code Integration

Add the `SKILL.md` to your project. When you tell Claude Code `/generate-changelog`, it will execute the script and show you the results.

## License

MIT
