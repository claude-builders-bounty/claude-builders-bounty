# CHANGELOG Generator — Claude Code Skill

Generates a structured `CHANGELOG.md` from git history. Auto-categorizes commits into **Added**, **Fixed**, **Changed**, and **Removed**.

## Installation

```bash
# 1. Copy the script to your project
cp changelog.py ~/my-project/

# 2. Generate your changelog
python changelog.py --repo . --output CHANGELOG.md
```

## Usage

```bash
python changelog.py                      # current dir → CHANGELOG.md
python changelog.py --repo ../my-app     # different repo
python changelog.py --output HISTORY.md  # custom output file
```

## How it categorizes

| Prefix | Category |
|--------|----------|
| `add`, `feat`, `feature`, `new`, `implement`, `create` | **Added** |
| `fix`, `bug`, `hotfix`, `patch`, `correct`, `repair` | **Fixed** |
| (everything else that doesn't match above) | **Changed** |
| `remove`, `delete`, `drop`, `deprecat`, `cleanup` | **Removed** |

## Sample Output

See [`SAMPLE_CHANGELOG.md`](./SAMPLE_CHANGELOG.md) — a generated changelog of 374 commits from the RustChain repo.
