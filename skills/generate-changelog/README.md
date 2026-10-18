# generate-changelog skill

Generates a structured `CHANGELOG.md` from git history.

## Setup (3 steps)

1. Copy `changelog.sh` to your project root.
2. `chmod +x changelog.sh`
3. Run `bash changelog.sh` (optionally pass an output file path).

## Requirements
- git, bash

## Output
Categorizes commits since the last tag into Added / Fixed / Changed / Removed / Other.