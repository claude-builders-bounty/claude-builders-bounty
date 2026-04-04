# Generate Structured CHANGELOG from Git History

## Description
This PR implements a comprehensive bash script that automatically generates a structured CHANGELOG.md from a project's git history, as requested in issue #1.

## What's New in This Update

### 📄 Multi-Format Output
- **Markdown** (`--format=md`) — Human-readable with emoji headers and commit hash references
- **JSON** (`--format=json`) — Machine-readable with per-category arrays and summary statistics

### 🏷️ 7-Category Classification (up from 4)
| Category | Emoji | Conventional Commit Prefix |
|----------|-------|---------------------------|
| Features | ✨ | `feat:` |
| Bug Fixes | 🐛 | `fix:` |
| Documentation | 📝 | `docs:` |
| Styling | 💄 | `style:` |
| Refactoring | ♻️ | `refactor:`, `perf:` |
| Tests | ✅ | `test:` |
| Chores | 🔧 | `chore:`, `ci:`, `build:` |

### ⏰ Flexible Filtering
- `--since=v1.0.0` — Only commits since a specific tag
- `--since=2026-01-01` — Only commits since a specific date
- `--all` — Include full commit history

### 🤖 GitHub Actions Integration
Included `changelog-action.yml` — a drop-in workflow that:
- Runs on every push to main/master
- Triggers on new version tags (`v*`)
- Supports manual dispatch with format selection
- Auto-commits the generated CHANGELOG

## Files
| File | Description |
|------|-------------|
| `changelog.sh` | Main script — 7-category classifier with MD/JSON output |
| `changelog-action.yml` | GitHub Actions workflow for CI/CD automation |
| `SKILL.md` | Full documentation with usage, features, and setup |
| `sample-CHANGELOG.md` | Sample output in both Markdown and JSON formats |
| `README.md` | Bounty task description |
| `PR-TEMPLATE.md` | This file |

## Acceptance Criteria Met
✅ Works via `bash changelog.sh` command  
✅ Fetches commits since the last git tag  
✅ Auto-categorizes into 7 categories (exceeds the 4 requested)  
✅ Outputs properly formatted CHANGELOG.md  
✅ **NEW**: JSON output format with summary stats  
✅ **NEW**: CLI parameters (`--format`, `--since`, `--all`)  
✅ **NEW**: GitHub Actions CI/CD workflow  
✅ Tested on real GitHub repo (sample output included)  
✅ README with setup instructions in 3 steps or fewer  

## How to Test
```bash
# Clone any git repository
git clone https://github.com/any/repo && cd repo

# Copy changelog.sh and make executable
chmod +x changelog.sh

# Generate Markdown
./changelog.sh CHANGELOG.md

# Generate JSON
./changelog.sh --format=json CHANGELOG.json

# Filter by date
./changelog.sh --since=2026-01-01
```

## Why This Solution

Compared to alternatives:
- **Pure bash** — zero dependencies, runs anywhere with git
- **7 categories** — covers all conventional commit types
- **Dual format** — Markdown for humans, JSON for automation
- **CI-ready** — drop-in GitHub Actions workflow included
- **Flexible filtering** — by tag, date, or all history

Fixes #1
