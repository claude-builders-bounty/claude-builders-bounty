# changelog.sh — Generate a structured CHANGELOG from git

Automatically generate a `CHANGELOG.md` from your git history, categorized by commit type.

## Setup

```bash
# 1. Copy the script to your project root
cp changelog.sh /your/project/

# 2. Make it executable
chmod +x changelog.sh
```

## Run

```bash
bash changelog.sh
```

That's it. The script auto-detects your last git tag and generates `CHANGELOG.md`.

---

## How it works

| Commit prefix | Category |
|---|---|
| `feat:`, `add:`, `new:`, `implement:` | **Added** |
| `fix:`, `bug:`, `patch:`, `hotfix:` | **Fixed** |
| `refactor:`, `perf:`, `update:`, `chore:` | **Changed** |
| `remove:`, `delete:`, `drop:`, `revert:` | **Removed** |
| Everything else | **Other** |

Follows [Conventional Commits](https://www.conventionalcommits.org/) convention.

## Options

| Flag | Default | Description |
|---|---|---|
| `--since <tag\|commit>` | last git tag | Override baseline |
| `--version <x.y.z>` | from `package.json` / `Cargo.toml` / date | Override version |
| `--output <file>` | `CHANGELOG.md` | Output file |

## Sample output

See [`SAMPLE_OUTPUT.md`](./SAMPLE_OUTPUT.md) for a real example.

## Requirements

- `git` (any version)
- `bash` 4+ (macOS: `brew install bash` if needed)
- Optional: `node` (for `package.json` version detection)
