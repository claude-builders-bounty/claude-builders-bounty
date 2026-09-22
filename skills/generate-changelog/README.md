# Generate Changelog Skill (`SKILL.md`) 📝

A Claude Code skill and standalone CLI tool that generates Keep-a-Changelog compliant `CHANGELOG.md` files from git history.

## Features
- **Git-aware**: Automatically discovers commits since the latest git tag.
- **Categorization**: Sorts commits into `Added`, `Fixed`, `Changed`, and `Removed` using Conventional Commits.
- **Non-destructive**: Prepends new releases while preserving existing changelog history.
- **Author & Hash linking**: Formats commits with short SHAs and author tags.

---

## Setup in 3 Steps

### Step 1: Install the Skill or Scripts
Copy the skill into your project or Claude Code skills directory:
```bash
mkdir -p .claude/skills/generate-changelog
cp -r skills/generate-changelog/* .claude/skills/generate-changelog/
```

### Step 2: Run the Command
Generate a changelog for your current release:
```bash
# Using the bash script
bash .claude/skills/generate-changelog/scripts/changelog.sh v1.0.0

# Or using Python directly
python .claude/skills/generate-changelog/scripts/generate-changelog.py --version v1.0.0
```

### Step 3: Review & Commit
Inspect the updated `CHANGELOG.md` and commit it:
```bash
git add CHANGELOG.md && git commit -m "docs: update CHANGELOG for v1.0.0"
```
