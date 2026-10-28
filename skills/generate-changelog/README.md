# 📜 Generate Changelog Skill & Tool

> Automatically generates structured, Keep-a-Changelog compliant `CHANGELOG.md` from git commit history since the latest release tag.
>
> Solves **Bounty #1** ($50 USD) for [claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty).

---

## ⚡ 3-Step Quickstart

### Step 1: Clone Repository
```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty
```

### Step 2: Run Changelog Generator
Run via bash script, Python CLI, or native Claude Code skill:
```bash
# Option A: Bash script
bash skills/generate-changelog/changelog.sh -o CHANGELOG.md

# Option B: Python CLI
python3 skills/generate-changelog/generate_changelog.py --version v1.2.0 -o CHANGELOG.md

# Option C: In Claude Code
/generate-changelog
```

### Step 3: Inspect Generated CHANGELOG.md
A structured changelog is generated following [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) standard, automatically categorized into `Added`, `Fixed`, `Changed`, `Removed`, and `Maintenance`.

---

## 🛠️ CLI Options

```bash
bash changelog.sh [OPTIONS]
```

| Flag | Description | Default |
|---|---|---|
| `--output`, `-o` | File path to write changelog | Stdout |
| `--version` | Custom version string in release header | `Unreleased` |
| `--since` | Git tag or commit hash to start from | Latest reachable tag |
| `--until` | End git commit reference | `HEAD` |
| `--repo` | Target git repository path | Current working directory |

---

## 📋 Categorization Mapping

| Conventional Commit Prefix | Keep a Changelog Category |
|---|---|
| `feat:`, `add:`, `new:` | **Added** |
| `fix:`, `bug:`, `patch:` | **Fixed** |
| `refactor:`, `perf:`, `change:`, `update:`, `style:` | **Changed** |
| `remove:`, `deprecate:`, `delete:` | **Removed** |
| `chore:`, `docs:`, `ci:`, `test:`, `build:` | **Maintenance** |

---

## 🧪 Real-World Verification

Tested against the live git history of [claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty):
- Sample output available in [`examples/SAMPLE_CHANGELOG.md`](examples/SAMPLE_CHANGELOG.md).

---

## 📄 License
MIT License.
