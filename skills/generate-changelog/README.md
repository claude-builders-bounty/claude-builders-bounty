# Generate Changelog

Generates a structured `CHANGELOG.md` from git history — categorized into Added / Fixed / Changed / Removed.

Two modes:
- **Claude Code skill** (`SKILL.md`) — Claude reads every commit message and categorizes using judgment, not keyword matching. Handles typos, non-conventional commits, and ambiguous messages that regex misclassifies.
- **Bash fallback** (`changelog.sh`) — zero-dependency script for CI or repos without Claude Code.

See [`sample/CHANGELOG.md`](sample/CHANGELOG.md) for output format.

## Setup (3 steps)

**1. Install the skill**
```bash
mkdir -p .claude/skills
cp SKILL.md .claude/skills/generate-changelog.md
```

**2. Run inside Claude Code**
```
/generate-changelog
```
Or with options: `/generate-changelog --since v1.0.0 --preview`

**3. (Fallback) Run the bash script**
```bash
bash changelog.sh              # writes CHANGELOG.md
bash changelog.sh --preview    # prints to stdout only
bash changelog.sh --since v1.0.0 --output RELEASE.md
```

## Options

| Flag | Description |
|---|---|
| `--since <ref>` | Start from this tag or SHA (default: last git tag) |
| `--output <file>` | Write to this file (default: `CHANGELOG.md`) |
| `--version <label>` | Override the version label |
| `--preview` | Print to stdout, do not write to disk |

## Why the skill beats regex

Most commit messages don't follow conventional commits perfectly:
- `"bump dependency"` → Changed (not a prefix-based match)
- `"sidebar now collapsible"` → Added (Claude infers it's a new capability)
- `"oops, wrong field name"` → Fixed (Claude reads context, not prefix)

The bash fallback handles standard prefixes (`feat:`, `fix:`, etc.) for CI environments.
