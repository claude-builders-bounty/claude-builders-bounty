# Claude Code PR Reviewer Agent

Automated PR review agent that analyzes GitHub pull requests and returns structured Markdown reviews.

## Setup

```bash
pip install -r requirements.txt  # no external deps beyond stdlib
chmod +x claude-pr-reviewer.py
```

## Usage

```bash
# Basic usage
export GITHUB_TOKEN=ghp_xxxx
python claude-pr-reviewer.py --pr https://github.com/owner/repo/pull/123

# Or pass token directly
python claude-pr-reviewer.py --pr https://github.com/owner/repo/pull/123 --token ghp_xxxx
```

## Output Format

- **Summary** — 2-3 sentence overview of changes
- **Identified Risks** — security issues, missing tests, dependency changes, large PRs
- **Improvement Suggestions** — code quality, tracker comments
- **Confidence Score** — Low / Medium / High

## Sample Outputs

### Sample 1: CHANGELOG generator (PR #3611)
```
PR changes 1 file(s) (+74/-0). No significant risks detected.
Confidence: Medium
```

### Sample 2: CLAUDE.md template (PR #3619)
```
PR changes 2 file(s) (+195/-0).
Found 1 tracker comment (TODO/FIXME) — consider linking to an issue.
Confidence: Medium
```

## Detection Rules

- Hardcoded secrets (API keys, tokens, AWS keys, private keys, passwords)
- Missing test files for source changes
- Large PRs (>500 line changes)
- Dependency manifest changes without lockfile updates
- TODO/FIXME/HACK comments without issue links

## Requirements

- Python 3.9+
- GitHub Fine-Grained PAT with `pull_requests:read` scope
- No external dependencies (stdlib only)
