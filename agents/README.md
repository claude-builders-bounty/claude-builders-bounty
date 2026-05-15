# Claude Code PR Review Agent

A CLI tool that takes a PR diff as input, analyzes it, and returns a structured Markdown review comment.

## 💰 Bounty

Created for [claude-builders-bounty #4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4) ($150 bounty).

## Installation (2 commands)

```bash
# 1. Download the agent
curl -sL https://raw.githubusercontent.com/qiuluoli/claude-builders-bounty/agent-pr-review/agents/claude_review.py -o claude-review && chmod +x claude-review

# 2. Install dependency (gh CLI - usually already installed)
# No additional dependencies needed! Uses only Python stdlib + gh CLI
```

## Usage

```bash
# Review a PR by URL
python3 claude_review.py --pr https://github.com/owner/repo/pull/123

# Review by shorthand
python3 claude_review.py --pr owner/repo/123

# Save review to file
python3 claude_review.py --pr https://github.com/owner/repo/pull/123 -o review.md

# Post review as PR comment
python3 claude_review.py --pr https://github.com/owner/repo/pull/123 --comment
```

## Structured Output Format

Every review includes:

1. **Summary of changes** (2-3 sentences)
2. **Identified risks** (list)
3. **Improvement suggestions** (list)
4. **Confidence score**: Low / Medium / High

## Risk Detection Patterns

The agent detects these code risks:

| Pattern | Risk Level |
|---------|-----------|
| eval/exec | Code injection |
| subprocess calls | Input sanitization |
| SQL string formatting | SQL injection |
| Hardcoded passwords/keys/secrets | Security leak |
| chmod 777 | Permission risk |
| Bare except | Silent error swallowing |
| TODO/FIXME | Unresolved issues |
| print statements | Should use logging |
| debug=True | Production risk |

## Confidence Score

Based on diff size:
- **High**: Small diffs (<500 chars) — thorough analysis possible
- **Medium**: Medium diffs (500-5000 chars) — most patterns covered
- **Low**: Large diffs (>5000 chars) — recommend manual review

## Sample Outputs

### Test 1: loop-monitor PR #302 (bug fix)

```
python3 claude_review.py --pr svv2014/loop-monitor/302
```

Output:
```
## 🤖 Automated PR Review

**PR**: https://github.com/svv2014/loop-monitor/pull/302
**Files changed**: 1 | **Additions**: +5 | **Deletions**: -2

### Summary
This PR (Fix silent data loss in POST /api/report #196) changes 1 file(s) (+5/-2).
No significant risks detected. Has 1 improvement suggestion(s).

### ⚠️ Identified Risks
No significant risks identified.

### 💡 Improvement Suggestions
- Code looks clean. Consider adding tests for the new functionality.

### 🎯 Confidence Score: **High**
```

### Test 2: fcms PR #670 (security fix)

```
python3 claude_review.py --pr ryanhowdy/fcms/670
```

Output:
```
## 🤖 Automated PR Review

**PR**: https://github.com/ryanhowdy/fcms/pull/670
**Files changed**: 2 | **Additions**: +8 | **Deletions**: -0

### Summary
This PR (Security: Fix Session Fixation & CSV Injection) changes 2 file(s) (+8/-0).
No significant risks detected. Has 1 improvement suggestion(s).

### ⚠️ Identified Risks
No significant risks identified.

### 💡 Improvement Suggestions
- Code looks clean. Consider adding tests for the new functionality.

### 🎯 Confidence Score: **High**
```

## GitHub Action Workflow

```yaml
name: PR Review
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install gh CLI
        run: |
          curl -fsSL https://cli.github.com/packages/githubcli-archive.key | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
          echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
          sudo apt update && sudo apt install gh -y
      - name: Run Review
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python3 agents/claude_review.py --pr ${{ github.event.pull_request.html_url }} --comment
```

## License

MIT