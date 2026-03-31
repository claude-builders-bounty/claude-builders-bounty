# changelog.sh — Auto-generate a structured CHANGELOG.md

A zero-dependency bash script (and companion Claude Code `SKILL.md`) that generates
a properly formatted `CHANGELOG.md` from your git history, categorised into
**Added / Fixed / Changed / Removed**.

---

## Setup (3 steps or fewer)

```bash
# Step 1 — copy the script to your project root
cp changelog.sh /path/to/your/project/

# Step 2 — make it executable
chmod +x changelog.sh

# Step 3 — run it
bash changelog.sh
```

That's it. No `npm install`, no `pip install`, no config files.

---

## Usage

```bash
# Generate CHANGELOG.md (appends a new section at the top)
bash changelog.sh

# Preview — print to stdout, don't write any file
bash changelog.sh --dry-run

# Start from a specific tag
bash changelog.sh --since v1.0.0

# Label the new section with a version
bash changelog.sh --version v1.1.0

# Both options combined
bash changelog.sh --since v1.0.0 --version v1.1.0

# Write to a different file
bash changelog.sh --output CHANGES.md
```

---

## How categorisation works

Commits are matched against their subject line:

| Keyword match | Section |
|---|---|
| `feat:` / `add` / `new` / `introduce` / `implement` | **Added** |
| `fix:` / `bug` / `patch` / `hotfix` / `resolve` | **Fixed** |
| `refactor:` / `change` / `update` / `bump` / `perf` / `chore` | **Changed** |
| `remove` / `delete` / `drop` / `deprecate` / `revert` | **Removed** |
| Everything else | **Changed** (safe fallback) |

Conventional-commit type prefixes (`feat:`, `fix(auth):`, etc.) are automatically
stripped from the display so the output is clean human-readable prose.

---

## Sample output

```markdown
## [v1.1.0] — 2026-03-31

### Added

- add rate limiting middleware for API endpoints (`a1b2c3d`)
- introduce Prometheus /metrics endpoint (`e4f5g6h`)
- new Docker Compose healthcheck for all services (`i7j8k9l`)

### Fixed

- fix race condition in session handler (`m0n1o2p`)
- correct null pointer when config file is missing (`q3r4s5t`)

### Changed

- upgrade Go dependencies to latest minor versions (`u6v7w8x`)
- refactor database connection pooling logic (`y9z0a1b`)

### Removed

- remove deprecated /v1/legacy API endpoint (`c2d3e4f`)
```

---

## Claude Code integration (`/generate-changelog`)

Copy `SKILL.md` to `.claude/skills/changelog/SKILL.md` (or your skill path),
and use the `/generate-changelog` slash command in Claude Code. Claude will run
the script for you and offer to commit the result.

---

## Requirements

- bash 4.0+ (ships with every modern Linux/macOS)
- git

---

## License

MIT
