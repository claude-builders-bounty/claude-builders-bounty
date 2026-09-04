# Structured CHANGELOG Generator Skill

A lightweight, zero-dependency git changelog generator available as both a native Claude Code `SKILL.md`, a cross-platform Python script, and a pure Bash script.

---

## Acceptance Criteria Met

- [x] **Works via `/generate-changelog` command or `bash changelog.sh` (or `python changelog.py`)**
- [x] **Fetches commits since the last git tag** (auto-detects tag, falls back to initial commit)
- [x] **Auto-categorizes into**: `Added` / `Fixed` / `Changed` / `Removed`
- [x] **Outputs a properly formatted `CHANGELOG.md`**
- [x] **Tested on a real GitHub repo** (`CHANGELOG.sample.md` included)
- [x] **README with setup instructions in 3 steps or fewer**

---

## Quick Setup (3 Steps or Fewer)

### Step 1: Copy to your project or Claude directory
```bash
cp -r skills/changelog-generator/ ~/.claude/skills/
```

### Step 2: Make executable
```bash
chmod +x skills/changelog-generator/changelog.sh
```

### Step 3: Run
```bash
# Output to CHANGELOG.md
python3 skills/changelog-generator/changelog.py -o CHANGELOG.md

# Or using pure bash
bash skills/changelog-generator/changelog.sh -o CHANGELOG.md
```

---

## Category Mapping

| Category | Prefixes & Keywords |
|---|---|
| **Added** | `feat:`, `feature:`, `add:`, `new:`, `implement:` |
| **Fixed** | `fix:`, `bug:`, `hotfix:`, `patch:`, `resolve:` |
| **Changed** | `refactor:`, `perf:`, `style:`, `update:`, `chore:`, `docs:`, `build:` |
| **Removed** | `revert:`, `remove:`, `delete:`, `deprecate:`, `drop:` |

---

## CLI Options

- `--from-tag <tag>`: Explicitly define starting tag (e.g. `v1.2.0`)
- `--output, -o <file>`: Destination file (e.g. `CHANGELOG.md`)
- `--title <title>`: Release header (default: `Unreleased`)
- `--dry-run`: Output to stdout without writing to disk
