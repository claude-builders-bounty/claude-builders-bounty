# Changelog Generator

Auto-generate structured CHANGELOGs from git history. Categorizes commits into Added/Fixed/Changed/Removed sections.

## Setup

1. Copy `changelog.sh` to your project root
2. `chmod +x changelog.sh`
3. Run `./changelog.sh`

## Usage

```bash
./changelog.sh                          # Since last tag
./changelog.sh --since v1.0.0           # Since specific tag
./changelog.sh --output docs/CHANGES.md # Custom output path
```

## Sample Output

See [sample-output.md](./sample-output.md) for a real-world example generated from this repository.

## How It Works

- Fetches commits since the last git tag (or all commits if no tags exist)
- Categorizes by commit message prefix: `feat`/`add` → Added, `fix` → Fixed, `refactor`/`update` → Changed, `remove`/`delete` → Removed
- Falls back to keyword matching anywhere in the message
- Outputs Keep a Changelog formatted markdown

## Stack

Pure bash — no dependencies beyond git.
