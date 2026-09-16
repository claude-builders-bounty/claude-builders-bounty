# Generate Changelog Tool & Skill

Automatically generate structured `CHANGELOG.md` files from Git commit history following [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) standards.

## Features

- 🏷️ **Tag-Aware**: Automatically computes commits since the most recent Git release tag.
- 📂 **Auto-Categorization**: Groups commits by conventional commit prefixes (`feat:` → **Added**, `fix:` → **Fixed**, `refactor:`/`docs:`/`chore:` → **Changed**, `remove:` → **Removed**, `security:` → **Security**). Falls back to keyword heuristics for non-conventional messages.
- 🔄 **Safe Incremental Updates**: Prepends new versions directly under `# Changelog`, preserving past releases.
- ⚡ **Zero Dependencies**: Pure standard Python (3.8+). Only `git` is required.

## 3-Step Setup & Usage

### 1. Copy the skill into your project

Copy this `generate-changelog/` folder into your project (or into your Claude Code skills directory).

### 2. Run it

```bash
# Generate / update CHANGELOG.md for commits since the last tag
python generate_changelog.py          # or: bash changelog.sh
```

### 3. (Optional) Label a release version

```bash
python generate_changelog.py --version "v1.2.0" --tag "v1.1.0"
```

Other options: `--stdout` (preview without writing), `-o FILE` (custom output path).

## Claude Code Skill

`SKILL.md` in this folder makes the tool available as a Claude Code skill: ask Claude to "generate the changelog" or "draft release notes" and it will run the commands above automatically.

## Sample Output

See [`SAMPLE_OUTPUT.md`](./SAMPLE_OUTPUT.md) for a real run against the [cli/cli](https://github.com/cli/cli) repository (GitHub CLI) between tags `v2.88.0` and `v2.89.0`.

## Tests

```bash
python -m unittest discover -s tests   # from the repository root
```
