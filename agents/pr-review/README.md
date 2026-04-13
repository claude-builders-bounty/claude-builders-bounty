# Claude Code PR Review Agent

Automatically reviews GitHub PRs and posts structured comments.

## Usage

### CLI
```bash
python pr-review-agent.py --pr https://github.com/owner/repo/pull/123
```

### GitHub Action
```yaml
uses: your-repo/.github/workflows/pr-review.yml@main
```

## Features

✅ Analyzes PR diffs  
✅ Generates structured Markdown reviews  
✅ Posts as GitHub PR comments  
✅ Includes confidence score  

## Files

- `pr-review-agent.py` - CLI tool
- `.github/workflows/pr-review.yml` - GitHub Action
- `README.md` - This file