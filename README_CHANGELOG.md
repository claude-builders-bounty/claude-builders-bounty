# CHANGELOG Generator

This repo includes a lightweight script that generates a structured `CHANGELOG.md`
from commit history since the latest git tag.

## Setup (3 steps)

1. `git clone <your-repo-url>`
2. `cd <your-repo>`
3. `bash changelog.sh`

## Usage

Default:

```bash
bash changelog.sh
```

Custom repo/output:

```bash
bash changelog.sh --repo /path/to/repo --output CHANGELOG.md
```

## Category Rules

- `Added`: commits starting with `feat:`, `add:`, `new:`
- `Fixed`: commits starting with `fix:` or containing `bug`, `hotfix`, `patch`
- `Changed`: `refactor:`, `perf:`, `style:`, `docs:`, `chore:`, `ci:`, `build:`, and uncategorized commits
- `Removed`: `remove:`, `delete:`, or messages containing `removed`, `deprecated`, `drop`

## Sample Outputs (tested on real GitHub repos)

- `samples/claude-builders-bounty-CHANGELOG.md` (this repository)
- `samples/requests-CHANGELOG.md` (https://github.com/psf/requests)
