# Generate Structured CHANGELOG from Git History

## Description
This skill automatically generates a structured CHANGELOG.md (or JSON) file from a project's git commit history. It analyzes commits since the last git tag and categorizes them into 7 conventional commit categories with emoji labels.

## Usage
```bash
# Basic — Markdown to stdout
./changelog.sh

# Save to file
./changelog.sh CHANGELOG.md

# JSON output
./changelog.sh --format=json CHANGELOG.json

# Since a specific tag or date
./changelog.sh --since=v1.0.0
./changelog.sh --since=2026-01-01

# All commits (ignore tags)
./changelog.sh --all
```

## Requirements
- Git installed and available in PATH
- Current directory is a git repository
- Bash shell (Linux/macOS) or Git Bash (Windows)

## Features

### 🏷️ 7-Category Classification
Commits are automatically sorted into categories using conventional commit prefixes and keyword matching:

| Category | Prefixes / Keywords | Emoji |
|----------|-------------------|-------|
| **Features** | `feat:`, `add:`, "implement", "create" | ✨ |
| **Bug Fixes** | `fix:`, `bug:`, "resolve", "patch" | 🐛 |
| **Documentation** | `docs:`, "readme", "changelog" | 📝 |
| **Styling** | `style:`, "format", "lint" | 💄 |
| **Refactoring** | `refactor:`, `perf:`, "optimize" | ♻️ |
| **Tests** | `test:`, "spec", "coverage" | ✅ |
| **Chores** | `chore:`, `ci:`, `build:`, "merge" | 🔧 |

Unmatched commits go to an **Other** (📦) section.

### 📄 Multiple Output Formats
- **Markdown** (`--format=md`) — Human-readable CHANGELOG with emoji headers and commit hashes
- **JSON** (`--format=json`) — Machine-readable output with stats summary, ideal for dashboards and CI pipelines

### ⏰ Flexible Date/Tag Filtering
- `--since=v1.0.0` — Changes since a specific tag
- `--since=2026-01-01` — Changes since a specific date
- `--all` — Include entire commit history
- _(default)_ — Changes since the last git tag

### 🤖 GitHub Actions Integration
Drop-in workflow file included (`changelog-action.yml`). Automatically generates and commits the CHANGELOG on every push to main/master or on new tags. Supports manual trigger with format selection.

## Setup Instructions
1. Copy `changelog.sh` to your project root
2. Run `chmod +x changelog.sh`
3. Execute: `./changelog.sh CHANGELOG.md`

**Optional CI/CD**: Copy `changelog-action.yml` to `.github/workflows/changelog.yml` for automatic generation.

## Testing
Tested on real GitHub repositories with various commit styles:
- Conventional commits (`feat:`, `fix:`, `docs:`)
- Free-form commits with keyword matching
- Repositories with and without tags
- Mixed commit styles in a single repo

Sample outputs included: `sample-CHANGELOG.md` (Markdown + JSON example).

## Acceptance Criteria Met
✅ Works via `./changelog.sh` or `bash changelog.sh`  
✅ Fetches commits since last git tag  
✅ Auto-categorizes into 7 categories (feat/fix/docs/style/refactor/test/chore)  
✅ Outputs properly formatted CHANGELOG.md  
✅ JSON output format with stats summary  
✅ CLI parameters: `--format`, `--since`, `--all`  
✅ GitHub Actions workflow for CI/CD automation  
✅ Tested on real GitHub repo with sample output  
✅ README with setup instructions in 3 steps or fewer  

## Bounty Information
- **Repository**: claude-builders-bounty/claude-builders-bounty
- **Issue**: [#1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)
- **Bounty Amount**: $50
- **Powered by**: Opire
