# Skill: Generate Structured CHANGELOG

Automatically generates a beautiful, categorized `CHANGELOG.md` from your git history.

## Setup in 3 Steps
1. **Copy the script**: Place `scripts/generate_changelog.py` in your project.
2. **Install dependencies**: Ensure you have Python 3 installed (no external libs required).
3. **Run it**:
   ```bash
   python3 generate_changelog.py --tag v1.0.0
   ```

## Features
- **Auto-categorization**: Automatically groups commits into Added, Fixed, Breaking Changes, etc.
- **Conventional Commits**: Fully supports conventional commit prefixes (feat, fix, docs, etc.).
- **Breaking Changes**: Identifies breaking changes using `!` or `BREAKING CHANGE` keyword.
- **GitHub Links**: Automatically links commit hashes to their GitHub URLs if the remote origin is set.
- **Custom Tags**: Specify the new version tag for the header.

## Sample Output
See `sample_CHANGELOG.md` in this directory.
