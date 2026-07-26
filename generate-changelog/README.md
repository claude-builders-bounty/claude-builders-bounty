# Generate Changelog

Bash tool (and Claude/Grok skill) that builds a structured `CHANGELOG.md` from git history since the last tag, categorized into **Added** / **Fixed** / **Changed** / **Removed**.

## Setup (3 steps)

1. **Get the script** — clone this repo (or copy the `generate-changelog/` folder).
2. **Run it** on any git repo:
   ```bash
   bash generate-changelog/changelog.sh CHANGELOG.md /path/to/your/repo
   ```
3. **Open** the generated `CHANGELOG.md` (or install `SKILL.md` under your agent skills and run `/generate-changelog`).

## Usage

```bash
bash changelog.sh                  # → ./CHANGELOG.md for cwd
bash changelog.sh OUT.md /my/repo  # custom output + repo path
```

## Requirements

- `bash` 4+, `git`, standard Unix tools (`date`, `tr`)

## Sample

See `sample-CHANGELOG.md` for output produced against a real public repository during verification.
