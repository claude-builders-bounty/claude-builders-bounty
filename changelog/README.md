# Changelog Generator

Generate a structured `CHANGELOG.md` from git history — categorized into **Added**, **Fixed**, **Changed**, and **Removed** — in seconds.

## Setup

**Step 1 — Copy the files to your project root:**
```bash
cp changelog.py changelog.sh /path/to/your-project/
```

**Step 2 — Run it:**
```bash
bash changelog.sh
```

That's it. A `CHANGELOG.md` will appear in the current directory.

---

## Usage via Claude Code (skill)

Add `SKILL.md` to your project so Claude can invoke it:

```bash
cp SKILL.md /path/to/your-project/
```

Then use the command inside a Claude Code session:
```
/generate-changelog
```

---

## How it works

1. Detects the latest git tag via `git describe --tags --abbrev=0`.
2. Reads commits from that tag to `HEAD` (or all commits if no tag exists).
3. Categorizes each commit using:
   - Conventional commit prefixes (`feat:`, `fix:`, `refactor:` …).
   - Keyword heuristics as fallback.
4. Writes `CHANGELOG.md` in the current directory.

## Category rules

| Category  | Detected keywords / prefixes                              |
|-----------|----------------------------------------------------------|
| Added     | `feat`, `add`, `new`, `create`, `implement`, `support`   |
| Fixed     | `fix`, `bug`, `resolve`, `close`, `patch`, `hotfix`      |
| Removed   | `remove`, `delete`, `deprecate`, `drop`, `clean`         |
| Changed   | everything else (refactor, chore, docs, perf, ci …)      |

---

## Sample output

```markdown
# Changelog (since tag v1.0.0)

## Added
- feat: implement dark mode support (bc6c8b2)

## Fixed
- fix: fix crash when uploading large files (1eb8364)

## Changed
- chore: update dependencies to latest versions (432135e)
- refactor: clean up database connection logic (649a5f1)

## Removed
- remove: delete legacy API endpoints (3fc1b2c)
```

---

## Requirements

- Python 3.6+ (no external dependencies)
- git
