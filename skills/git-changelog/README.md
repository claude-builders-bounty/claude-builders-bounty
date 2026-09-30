# Git Changelog Generator

A zero-dependency automation skill & script to generate structured, Keep-a-Changelog compliant `CHANGELOG.md` files directly from Git commits.

## Quick Start (3 Steps)

1. **Copy into your repository**:
   ```bash
   cp -r git-changelog/ your-repo/skills/git-changelog/
2. **Run the generator**:
bash skills/git-changelog/changelog.sh
# or: python skills/git-changelog/generate_changelog.py
3. **Commit the generated CHANGELOG.md**:
git add CHANGELOG.md && git commit -m "docs: update changelog"