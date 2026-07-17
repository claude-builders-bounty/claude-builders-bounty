# changelog.sh

Generate a structured `CHANGELOG.md` from a project's git history.

## Setup (3 steps)

1. **Download** the script into your repo:
   ```bash
   curl -O https://raw.githubusercontent.com/<your-fork>/changelog.sh
   chmod +x changelog.sh
   ```
2. **Run** it from the repo root:
   ```bash
   ./changelog.sh
   ```
3. **Commit** the generated `CHANGELOG.md`.

## Usage

```bash
./changelog.sh                       # changes since last git tag
./changelog.sh --version v1.2.0      # label the section
./changelog.sh --since main          # custom starting ref
./changelog.sh --out docs/CHANGELOG.md
```

## How it works

- Reads commits in `last-tag..HEAD` (or `first-commit..HEAD` if untagged).
- Categorizes each commit into **Added / Changed / Fixed / Removed** from
  Conventional Commits prefixes (`feat:`, `fix:`, `chore:`, …) and keywords.
- Writes a formatted `CHANGELOG.md`.

Also usable as a Claude Code skill via `SKILL.md` (`/generate-changelog`).
