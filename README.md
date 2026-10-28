# PR Review Agent

A Claude Code agent that analyzes GitHub PR diffs and generates structured markdown review comments.

## Setup & Usage

### Option 1: CLI Usage
```bash
# Make executable
chmod +x claude-review

# Review a PR
./claude-review --pr https://github.com/owner/repo/pull/123
```

### Option 2: GitHub Action
Use the workflow in `.github/workflows/pr-review.yml` to automatically review PRs.

## Output Format
The agent generates structured reviews with:
- **Summary of changes** (2-3 sentences)
- **Identified risks** (list)
- **Improvement suggestions** (list)
- **Confidence score**: Low / Medium / High

## Sample Outputs
See `samples/` directory for example reviews on real PRs.
