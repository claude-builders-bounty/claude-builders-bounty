# changelog.sh

Generate a structured `CHANGELOG.md` from your git history — automatically categorized into **Added**, **Fixed**, **Changed**, and **Removed**.

## Setup (3 steps)

```bash
# 1. Download the script
curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/changelog.sh

# 2. Make it executable
chmod +x changelog.sh

# 3. Run it inside any git repo
./changelog.sh
```

## Usage

```bash
# Generate CHANGELOG.md from commits since last git tag
./changelog.sh

# Preview without writing (dry-run)
./changelog.sh --dry-run

# Start from a specific tag
./changelog.sh --since v2.0.0

# Custom output file
./changelog.sh --output RELEASE_NOTES.md
```

## How It Works

1. Finds the **latest git tag** and scans all commits since then
2. Parses each commit message using **conventional commit prefixes** (`feat:`, `fix:`, `chore:`, etc.)
3. Falls back to **keyword heuristics** for non-conventional commits (detects `bug`, `add`, `remove`, etc.)
4. Outputs a formatted `CHANGELOG.md` with a stats footer

## Sample Output

See [SAMPLE.md](SAMPLE.md) for a real-world example generated from [Express.js](https://github.com/expressjs/express).

## Requirements

- `bash` 4+
- `git`
- Any Unix-like system (Linux, macOS, WSL)

## License

MIT — see [LICENSE](LICENSE)
