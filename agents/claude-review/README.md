# PR Review Claude Code Agent

## Usage
```bash
export GITHUB_TOKEN=your_token
python claude-review.py --pr https://github.com/owner/repo/pull/123
```

## What it checks
- Hardcoded secrets
- Debug code
- Silent exception catching
- SQL injection risks
- TODO/FIXME leftovers
- Dangerous function calls
