# Generate Changelog

A dead-simple bash script that auto-generates a structured `CHANGELOG.md` from your git history.

## Setup

1. Copy `changelog.sh` into your project root.
2. Make it executable: `chmod +x changelog.sh`
3. Run it: `bash changelog.sh`

Done ✅ — `CHANGELOG.md` appears in your repo root.

## How it works

- Detects the latest git tag and grabs all commits since then.
- Categorizes commits into **Added**, **Fixed**, **Changed**, **Removed** based on conventional commit prefixes (`feat`, `fix`, `chore`, `refactor`, etc.).
- Outputs a clean, standard `CHANGELOG.md`.

## Sample Output

See `CHANGELOG.md` in this repo for a real-world example generated from the [anxovatomica/smartlights](https://github.com/anxovatomica/smartlights) project.
