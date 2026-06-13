# PR Review Agent

> A Claude Code sub-agent / CLI tool for automated GitHub PR review with structured Markdown output.

**Bounty:** $150 — Issue #4 from `claude-builders-bounty/claude-builders-bounty`

---

## Features

- 🔍 **Fetch any GitHub PR** — provide a URL, get a structured review
- 📝 **Structured Markdown output** — Overview, Good parts, Concerns, Suggestions, Confidence score
- 📊 **Automated static analysis** — detects code smells, large diffs, missing tests, hardcoded secrets, and more
- 🔗 **GitHub Action ready** — drop-in workflow file for automatic PR comments
- 🤖 **Claude Code compatible** — can be used as a sub-agent or integrated via SKILL.md
- 🎯 **Confidence scoring** — Low / Medium / High based on diff complexity and findings

## Quick Start

### Prerequisites

- Python 3.10+
- GitHub personal access token (classic) with `repo` scope

### 1. Clone / Download

```bash
git clone <this-repo>
cd claude-builders-bounty/pr-review-agent
```

### 2. Set your GitHub token

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
```

### 3. Run a review

```bash
# Using the Python script directly
python3 claude-review.py --pr https://github.com/numpy/numpy/pull/31622

# Using the bash wrapper
./claude-review.sh --pr https://github.com/numpy/numpy/pull/31622

# JSON output
python3 claude-review.py --pr https://github.com/numpy/numpy/pull/31622 --format json
```

## CLI Usage

```
python claude-review.py --pr https://github.com/owner/repo/pull/123
python claude-review.py --pr 123 --owner owner --repo repo
python claude-review.py --pr https://github.com/owner/repo/pull/123 --format json
```

### Options

| Option | Description |
|--------|-------------|
| `--pr URL` | Full GitHub PR URL |
| `--owner OWNER` | Repository owner (if not using `--pr`) |
| `--repo REPO` | Repository name (if not using `--pr`) |
| `--pr-number N` | PR number (if not using `--pr`) |
| `--token TOKEN` | GitHub token (default: `$GITHUB_TOKEN`) |
| `--format FMT` | Output format: `markdown` (default) or `json` |

### Token Resolution Order

1. `--token` CLI argument
2. `GITHUB_TOKEN` or `GH_TOKEN` environment variable
3. `~/.agent/credentials/github.env`
4. `~/.github/token`

## Sample Output

> See [`samples/`](./samples/) for full examples tested against real GitHub PRs.

```markdown
# PR Review: [numpy/numpy#31622](https://github.com/numpy/numpy/pull/31622)

**Title:** fix: correct 'paramters' typo in LAPACK source comments
**Author:** @Rohan5commit  •  **State:** `open`  •  **Commits:** 1

> 📊 **+2**  **–2**  across **2** files

## 📋 Overview

Fixes a misspelling in LAPACK source comments: 'paramters' → 'parameters'.

### Files Changed

| File | Status | + | – | Lang |
|------|--------|---|---|------|
| `numpy/linalg/lapack_lite/f2c_d_lapack.c` | ✏️ modified | 1 | 1 | C |
| `numpy/linalg/lapack_lite/f2c_s_lapack.c` | ✏️ modified | 1 | 1 | C |

## ✅ Good Parts

1. Small, focused PR with only 2 files changed — easy to review.
2. No code-smell patterns detected in the diff.
3. Single-language PR (C) — consistent with repo conventions.

## ⚠️ Concerns

*No significant concerns detected.*

## 💡 Suggestions

1. No automated suggestions — PR looks clean from a structural standpoint.

---

**Confidence Score:** 🟢 **High**
```

## GitHub Action

Add the workflow to your repository:

```yaml
# .github/workflows/review.yml
name: PR Review Agent

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Run PR review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python claude-review.py \
            --pr "https://github.com/${{ github.repository }}/pull/${{ github.event.pull_request.number }}" \
            --format markdown
```

See [`.github/workflows/review.yml`](./.github/workflows/review.yml) for the full workflow with automatic comment posting.

## Project Structure

```
pr-review-agent/
├── claude-review.py          # Main Python script (no external dependencies)
├── claude-review.sh           # Bash wrapper script
├── README.md                  # This file
├── SKILL.md                   # Claude Code integration skill
├── .github/workflows/
│   └── review.yml             # GitHub Action workflow
└── samples/
    ├── review-pr-31620.md     # Sample: NumPy linspace bug fix
    └── review-pr-31622.md     # Sample: NumPy typo fix
```

## What It Checks

The automated analysis scans for:

- **Code smells**: `print()` calls, bare `except:`, `TODO`/`FIXME`, `eval()`/`exec()`, wildcard imports
- **Security**: Hardcoded secrets/keys (with string-assignment detection to avoid C struct false positives)
- **PR structure**: Missing description, single commit with many files, too many commits
- **File issues**: Very large diffs, config/secret file changes, temporary files
- **Test coverage**: Detects missing test files for code changes
- **Cross-language**: Flags PRs that span many languages

## Integration with Claude Code

The `SKILL.md` file provides a Claude Code skill definition. When placed in your
Claude Code project's skills directory, you can invoke reviews by saying:

> "Review PR https://github.com/owner/repo/pull/123"

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Review completed, no concerns |
| `1` | Error (token, network, parsing) |
| `2` | Review completed, concerns found |

## License

MIT — part of the [claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty) project.
