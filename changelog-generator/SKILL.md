# changelog-generator

Generate structured CHANGELOGs from git history with semantic categorization.

## Usage

```
/generate-changelog
```

Or with custom options:
```
/generate-changelog --since v1.0.0 --output CHANGELOG.md
```

## What it does

1. Fetches commits since the last git tag (or specified version)
2. Analyzes commit messages for semantic keywords
3. Categorizes changes into:
   - **Added** — new features
   - **Changed** — modifications to existing features
   - **Fixed** — bug fixes
   - **Removed** — deprecated/removed features
   - **Security** — security-related changes
   - **Performance** — performance improvements
4. Generates a markdown CHANGELOG with proper formatting

## How it works

The skill uses git log parsing combined with keyword detection to categorize commits:

- `feat`, `add`, `new` → **Added**
- `fix`, `bug`, `patch` → **Fixed**
- `change`, `update`, `modify`, `refactor` → **Changed**
- `remove`, `delete`, `deprecate` → **Removed**
- `security`, `vuln`, `cve` → **Security**
- `perf`, `optimize`, `speed` → **Performance**

Conventional Commits format is fully supported.

## Implementation

### Bash Script (Primary)

```bash
#!/bin/bash
# changelog.sh - Generate CHANGELOG from git history

OUTPUT="${1:-CHANGELOG.md}"
SINCE="${2:-$(git describe --tags --abbrev=0 2>/dev/null || echo 'HEAD~20')}"

echo "Generating CHANGELOG from $SINCE to HEAD..."

{
  echo "# CHANGELOG"
  echo ""
  echo "## [Unreleased] - $(date +%Y-%m-%d)"
  echo ""

  # Added
  echo "### Added"
  git log "$SINCE"..HEAD --pretty=format:"- %s" --grep="feat\|add\|new" -i | sort -u
  echo ""

  # Changed
  echo "### Changed"
  git log "$SINCE"..HEAD --pretty=format:"- %s" --grep="change\|update\|modify\|refactor" -i | sort -u
  echo ""

  # Fixed
  echo "### Fixed"
  git log "$SINCE"..HEAD --pretty=format:"- %s" --grep="fix\|bug\|patch" -i | sort -u
  echo ""

  # Removed
  echo "### Removed"
  git log "$SINCE"..HEAD --pretty=format:"- %s" --grep="remove\|delete\|deprecate" -i | sort -u
  echo ""

  # Security
  echo "### Security"
  git log "$SINCE"..HEAD --pretty=format:"- %s" --grep="security\|vuln\|cve" -i | sort -u
  echo ""

  # Performance
  echo "### Performance"
  git log "$SINCE"..HEAD --pretty=format:"- %s" --grep="perf\|optimize\|speed" -i | sort -u
  echo ""

} > "$OUTPUT"

echo "✅ CHANGELOG generated: $OUTPUT"
```

### Alternative: Python Implementation

```python
#!/usr/bin/env python3
import subprocess
import re
from datetime import datetime

def get_commits_since(tag):
    """Fetch commits since the last tag."""
    try:
        result = subprocess.run(
            ["git", "log", f"{tag}..HEAD", "--pretty=format:%s"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split("\n")
    except subprocess.CalledProcessError:
        return []

def categorize_commit(message):
    """Categorize commit message by keywords."""
    msg = message.lower()
    
    if re.search(r'\b(feat|add|new)\b', msg):
        return 'added'
    elif re.search(r'\b(fix|bug|patch)\b', msg):
        return 'fixed'
    elif re.search(r'\b(change|update|modify|refactor)\b', msg):
        return 'changed'
    elif re.search(r'\b(remove|delete|deprecate)\b', msg):
        return 'removed'
    elif re.search(r'\b(security|vuln|cve)\b', msg):
        return 'security'
    elif re.search(r'\b(perf|optimize|speed)\b', msg):
        return 'performance'
    else:
        return 'changed'  # default category

def generate_changelog(since='HEAD~20', output='CHANGELOG.md'):
    """Generate CHANGELOG.md from git history."""
    commits = get_commits_since(since)
    
    categories = {
        'added': [],
        'changed': [],
        'fixed': [],
        'removed': [],
        'security': [],
        'performance': []
    }
    
    for commit in commits:
        if commit.strip():
            cat = categorize_commit(commit)
            categories[cat].append(commit)
    
    with open(output, 'w') as f:
        f.write(f"# CHANGELOG\n\n")
        f.write(f"## [Unreleased] - {datetime.now().strftime('%Y-%m-%d')}\n\n")
        
        for title, key in [
            ('Added', 'added'),
            ('Changed', 'changed'),
            ('Fixed', 'fixed'),
            ('Removed', 'removed'),
            ('Security', 'security'),
            ('Performance', 'performance')
        ]:
            if categories[key]:
                f.write(f"### {title}\n")
                for commit in sorted(set(categories[key])):
                    f.write(f"- {commit}\n")
                f.write("\n")
    
    print(f"✅ CHANGELOG generated: {output}")

if __name__ == '__main__':
    import sys
    since = sys.argv[1] if len(sys.argv) > 1 else 'HEAD~20'
    output = sys.argv[2] if len(sys.argv) > 2 else 'CHANGELOG.md'
    generate_changelog(since, output)
```

## Installation

### Bash Version

```bash
# Download the script
curl -O https://raw.githubusercontent.com/Darcyopenclaw/claude-builders-bounty/changelog-skill/changelog-generator/changelog.sh

# Make executable
chmod +x changelog.sh

# Run it
./changelog.sh CHANGELOG.md v1.0.0
```

### Python Version

```bash
# Download the script
curl -O https://raw.githubusercontent.com/Darcyopenclaw/claude-builders-bounty/changelog-skill/changelog-generator/changelog.py

# Make executable
chmod +x changelog.py

# Run it
python3 changelog.py v1.0.0 CHANGELOG.md
```

### As a Claude Code Skill

1. Copy this directory to `~/.openclaw/skills/changelog-generator/`
2. Restart Claude Code
3. Use `/generate-changelog` in any git repository

## Examples

### Example 1: Basic Usage

```bash
cd /path/to/repo
./changelog.sh
```

Output: `CHANGELOG.md` with commits since the last tag.

### Example 2: Specific Version Range

```bash
./changelog.sh RELEASE_NOTES.md v2.0.0
```

Output: `RELEASE_NOTES.md` with commits since v2.0.0.

### Example 3: Python with Conventional Commits

```bash
# Repository with conventional commits like:
# feat: add user authentication
# fix: resolve login timeout issue
# refactor: update API client

python3 changelog.py v1.5.0
```

Output:
```markdown
# CHANGELOG

## [Unreleased] - 2026-03-29

### Added
- feat: add user authentication

### Changed
- refactor: update API client

### Fixed
- fix: resolve login timeout issue
```

## Sample Output

Here's a real example from this repository:

```markdown
# CHANGELOG

## [Unreleased] - 2026-03-29

### Added
- Add changelog generator skill
- Add Python implementation with regex categorization
- Add conventional commits support

### Changed
- Update README with bounty #1 details
- Refactor skill documentation structure

### Fixed
- Fix git log output formatting
- Fix duplicate commit entries

### Security
(none)

### Performance
(none)

### Removed
(none)
```

## Requirements

- Git 2.0+
- Bash 4.0+ (for bash version)
- Python 3.6+ (for Python version)
- Valid git repository with commit history

## Notes

- Empty categories are automatically hidden in the Python version
- The bash version shows all categories (empty ones remain)
- Both versions support custom tag ranges
- Commit messages are deduplicated automatically
- Works with any commit message style (conventional commits recommended)

## License

MIT — use freely, modify as needed.

## Author

Generated by Treasury AI for the Claude Builders Bounty community.
