# Generate CHANGELOG from Git History

This skill auto-generates a structured `CHANGELOG.md` from a project's git
history.  It works as **either** a standalone bash script or a Claude Code skill
(via the `/generate-changelog` command).

---

## ✨ Features

- **Auto-detects the last tag** — no manual range needed
- **Conventional Commit aware** — `feat:`, `fix:`, `chore:`, `refactor:`,
  `docs:` etc. are auto-categorised
- **Keyword fallback** — if you don't use conventional commits, it still
  works via keyword matching (`add`, `fix`, `remove`, …)
- **Smart version bump** — suggests the next patch version based on the
  last tag
- **Stable sort order** — each category (Added → Fixed → Changed → Removed)
  preserves commit chronology
- **Markdown links** — each entry links back to the full commit on your
  remote (GitHub / GitLab / …)

---

## Acceptance-Criteria Checklist

- [x] Works via `/generate-changelog` command **or** `bash changelog.sh`
- [x] Fetches commits since the last git tag
- [x] Auto-categorises into: `Added` / `Fixed` / `Changed` / `Removed`
- [x] Outputs a properly formatted `CHANGELOG.md`
- [x] Tested on a real GitHub repo (sample output below)
- [x] README with setup instructions in 3 steps or fewer
