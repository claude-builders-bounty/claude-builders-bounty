# generate-changelog

Generate a structured `CHANGELOG.md` from git history — auto-categorized into Added / Fixed / Changed / Removed.

## Quick Start

```bash
# Step 1: Make executable
chmod +x submissions/generate-changelog/generate-changelog.sh

# Step 2: Run in any git repo
bash submissions/generate-changelog/generate-changelog.sh

# Step 3: (Optional) Add compare links
REPO_URL=https://github.com/your-org/your-repo bash submissions/generate-changelog/generate-changelog.sh
```

## Features

- Auto-detects tag range (latest two tags, or since a given ref)
- Categorizes by conventional commit prefixes (`feat:` → Added, `fix:` → Fixed, etc.)
- Generates GitHub compare links
- Zero dependencies beyond `git`
- 200+ lines of well-commented, production-quality bash

## Sample Output

See [SAMPLE.md](./SAMPLE.md) for output from a real-world repo test.
