# Generate Changelog

A Claude Code skill that generates a structured `CHANGELOG.md` from git commit history.

## Features

- **Auto-categorizes** commits into: Added / Fixed / Changed / Removed
- **Fetches commits** since the last git tag (or any custom range)
- **Outputs** a properly formatted `CHANGELOG.md`

## Usage

### Step 1 — Install
Copy the `generate-changelog/` folder into your Claude Code skills directory:

```
~/.claude/skills/
```

### Step 2 — Run
In Claude Code, type:

```
/generate-changelog
```

### Step 3 — Done
Your `CHANGELOG.md` is ready. Claude Code will display it and offer to save it.

## Options

| Flag | Description |
|------|-------------|
| `--from <tag>` | Start from a specific tag (default: last tag) |
| `--to <tag>` | End at a specific tag (default: HEAD) |
| `--repo <path>` | Path to repository (default: current directory) |
| `--output <file>` | Output file path (default: CHANGELOG.md) |

## Example

```bash
/generate-changelog --from v1.0.0 --to v1.1.0
```

## Categorization

| Prefix | Category |
|--------|----------|
| `feat`, `feat:` | Added |
| `fix`, `fix:` | Fixed |
| `chore`, `refactor`, `build`, `perf`, `ci`, `test`, `docs` | Changed |
| `BREAKING`, `remove`, `deprecate` | Removed |

## Sample Output

See [CHANGELOG.md](./CHANGELOG.md) for a real example generated from the [pinia](https://github.com/posva/pinia) repository.
