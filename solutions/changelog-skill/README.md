# changelog-generator

Generate a structured `CHANGELOG.md` from your git history in seconds.  
Follows the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format and auto-categorises commits by conventional-commit prefixes.

## Setup

**Step 1 — Copy the script into your project**
```bash
cp changelog.sh /your/project/
```

**Step 2 — Run it from the root of your git repository**
```bash
bash changelog.sh
```

**Step 3 — Done.** A `CHANGELOG.md` is created (or updated) in the current directory.

---

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--since <tag>` | Start from a specific git tag | latest tag |
| `--output <file>` | Write to a custom filename | `CHANGELOG.md` |
| `--version <label>` | Label for the unreleased block | `Unreleased` |

**Examples:**
```bash
# Generate changelog since v1.2.0
bash changelog.sh --since v1.2.0

# Write to a custom file
bash changelog.sh --output CHANGES.md

# Tag a release
bash changelog.sh --version 2.0.0
```

---

## Commit Message Conventions

The script maps commit prefixes to changelog categories:

| Prefix(es) | Category |
|------------|----------|
| `feat:`, `add:`, `feature:` | **Added** |
| `fix:`, `bug:`, `bugfix:` | **Fixed** |
| `change:`, `refactor:`, `chore:`, `perf:`, `style:`, `docs:`, `test:`, `ci:`, `build:` | **Changed** |
| `remove:`, `delete:`, `deprecate:`, `revert:` | **Removed** |
| *(anything else)* | **Changed** |

Scoped commits (`feat(auth): add OAuth`) are also handled — the scope is preserved in the message.

---

## Claude Code / AI Agent Usage

Copy `SKILL.md` into your Claude Code workspace (`.claude/skills/` or the project root).  
Then simply type:
```
/generate-changelog
```
The AI agent will follow the skill instructions to produce the same structured output.

---

## Requirements

- `bash` 4.0+
- `git` (must be run inside a git repository)
