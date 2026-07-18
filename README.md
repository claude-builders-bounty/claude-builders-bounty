# Claude Builders Bounty Board

Community bounties for Claude Code skills, hooks, and templates.

## generate-changelog (PR solution for #1)

Structured `CHANGELOG.md` from git history since the last tag.

### Setup (3 steps)

1. Copy `changelog.sh` (and optional `skills/generate-changelog/`) into your project or PATH
2. `chmod +x changelog.sh`
3. `./changelog.sh` → writes `CHANGELOG.md`

Claude Code: install the skill folder and run `/generate-changelog`.

### Sample output
- `samples/CHANGELOG.sample.md` — this repo
- `samples/CHANGELOG.wallbreaker.md` — real multi-commit project (252 commits categorized)

### Files
| Path | Purpose |
|------|---------|
| `changelog.sh` | Main generator |
| `gen-changelog` | Thin wrapper |
| `skills/generate-changelog/SKILL.md` | Claude Code skill |
| `CHANGELOG_TOOL_README.md` | Standalone docs |

---

Original board README content lives in issues; bounties are tracked as GitHub issues.
