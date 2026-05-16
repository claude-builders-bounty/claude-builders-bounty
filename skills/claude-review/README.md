# claude-review 🔍

**An AI-powered PR review analysis tool for GitHub.**

`claude-review` fetches a GitHub Pull Request, analyzes the diff for risks (secrets, debug code, large changes, new dependencies), and produces a structured Markdown review report.

---

## Installation

### Via pip (recommended)

```bash
pip install claude-review
```

### From source

```bash
git clone https://github.com/claude-builders-bounty/claude-review.git
cd claude-review
pip install .
```

### Requirements

- Python 3.8+
- `requests` (auto-installed via pip)

---

## Usage

### Basic usage

```bash
# Review a pull request, output to terminal
claude-review --pr https://github.com/owner/repo/pull/123

# Write output to a file
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

### Authentication

A GitHub token is required. Set it via environment variable or enter when prompted:

```bash
export GITHUB_TOKEN="ghp_..."
# or
export GH_TOKEN="ghp_..."

claude-review --pr https://github.com/owner/repo/pull/123
```

> Create a token at https://github.com/settings/tokens with `repo` or `public_repo` scope.

### GitHub Actions

Add `.github/workflows/claude-review.yml` to your repository (see the `.github/workflows/` directory in this repo) to auto-review every new PR.

---

## Features

| Feature | Description |
|---|---|
| **Diff parsing** | Splits unified diffs per file with +/- counts |
| **File type detection** | Identifies Python, JS, Go, Rust, Java, and 30+ other types |
| **Secrets detection** | Flags hardcoded API keys, passwords, tokens, private keys, AWS keys |
| **Debug code detection** | Finds console.log, print(), TODOs, FIXMEs, breakpoints |
| **Dependency tracking** | Detects new dependencies in package.json, requirements.txt, Cargo.toml, go.mod, and more |
| **Confidence scoring** | High / Medium / Low based on risk severity and count |
| **Structured Markdown** | Summary, per-file analysis, risks, suggestions |

---

## Output Example

```markdown
# PR Review: Fixed #18387 -- Added `force_insert` support

- **Files changed:** 4
- **Additions:** +89  **Deletions:** –12

## Summary
This PR introduces changes across 4 files (+89/–12 lines).
Notable findings: 1 potential risk(s).

## File-by-File Analysis
### `django/db/models/fields/related_descriptors.py`
- **Type:** Python
- **Stats:** +47/–4

**Findings:**
- 🟡 **Debug code:** print() debug statement

## Risks Found
### 🟡 Debug Code / TODOs
- `related_descriptors.py` — print() debug statement

## Suggestions
- Remove or resolve debug statements / TODOs before merging.

## Confidence: **Medium**
```

---

## Project Structure

```
claude-review/
├── claude-review              # CLI entry point
├── setup.py                   # pip install config
├── README.md                  # this file
├── examples/
│   ├── django-review.md       # sample review (django/django#18387)
│   └── requests-review.md     # sample review (psf/requests#6802)
└── .github/workflows/
    └── claude-review.yml      # GitHub Actions workflow
```

---

## License

MIT