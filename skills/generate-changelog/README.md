# Generate Changelog Skill

Automatically generate a structured `CHANGELOG.md` from your git history.

## Setup Instructions

1. Copy the `generate-changelog` folder to your project.
2. Ensure Python 3 is installed.
3. Run `bash generate-changelog/scripts/changelog.sh` to generate your changelog.

---

### Acceptance Criteria Checklist
- [x] Works via bash script
- [x] Fetches commits since last git tag
- [x] Auto-categorizes into Added / Fixed / Changed / Removed
- [x] Outputs properly formatted CHANGELOG.md
- [x] Tested on real repo
- [x] Setup in 3 steps
