# Claude PR Reviewer Agent

Automated PR review agent that produces structured Markdown analysis.

## Installation (2 Commands)

```bash
# 1. Download the script
curl -o claude_review.py https://raw.githubusercontent.com/.../claude_review.py
chmod +x claude_review.py

# 2. Install gh CLI (if not already installed)
brew install gh  # macOS
sudo apt-get install gh  # Ubuntu/Debian
```

## Usage

### CLI Mode
```bash
# Review a PR
./claude_review.py --pr https://github.com/owner/repo/pull/123

# Save to file
./claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
```

### GitHub Action Mode
```yaml
# Add to .github/workflows/pr-review.yml
uses: ./workflows/pr-review.yml
```

See `pr-review.yml` for the workflow definition.

## Output Format

```markdown
## PR Review Summary

### Summary
This PR adds 151 lines and across 2 files.

### Identified Risks
- No significant risks identified

### Improvement Suggestions
- Code looks good to merge

### Confidence Score: **Medium**

> Files: 2 | Additions: 151 | Deletions: 0
```

## Confidence Scoring

| Level | Criteria |
|-------|----------|
| High | ≤50 lines, no risks |
| Medium | 51-300 lines or minor risks |
| Low | >300 lines or high-risk patterns |

## Requirements

- Python 3.8+
- GitHub CLI (`gh`) authenticated
- Access to target repository