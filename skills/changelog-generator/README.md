# Git Changelog Generator Skill for Claude Code 📝

An automated, convention-aware changelog generator that inspects git history, categorizes commits into standard [Keep a Changelog](https://keepachangelog.com/) sections (`Added`, `Fixed`, `Changed`, `Removed`), and outputs or updates `CHANGELOG.md`.

---

## 🚀 Features
- **Deterministic Conventional Mapping**: Categorizes `feat`/`add` → `Added`, `fix`/`patch` → `Fixed`, `refactor`/`chore`/`docs`/`perf` → `Changed`, and `remove`/`deprecate` → `Removed`.
- **Automatic Tag Discovery**: Fetches commits since the latest git tag automatically or accepts custom baseline references (`--since <tag>`).
- **Idempotent Header Preservation**: Safely prepends new release sections to existing `CHANGELOG.md` files without overwriting prior release history.
- **Multi-Interface**: Usable as a Claude Code Skill (`/generate-changelog`), standalone CLI script (`generate_changelog.py`), or bash runner (`changelog.sh`).

---

## 🛠️ Quick Setup (3 Steps)

### Step 1: Install / Copy Files
Add `generate_changelog.py` and `SKILL.md` to your repository:
```bash
cp generate_changelog.py /path/to/your/repo/
```

### Step 2: Run Generator
Generate changelog for your upcoming release:
```bash
# Via Python CLI
python3 generate_changelog.py --version "v1.0.0"

# Or via Bash wrapper
bash changelog.sh --version "v1.0.0"
```

### Step 3: Verify Output
Check your newly generated or updated `CHANGELOG.md`:
```bash
cat CHANGELOG.md
```

---

## 💻 CLI Options

| Flag | Default | Description |
|---|---|---|
| `--version` | `Unreleased` | Release version header (e.g. `1.2.0`, `v2.0.0`) |
| `--since` | Latest git tag | Base commit/tag reference to collect commits from |
| `--output` | `CHANGELOG.md` | Target changelog markdown file path |
| `--stdout` | `false` | Stream changelog markdown directly to terminal |

---

## 🧪 Running Tests
```bash
python3 -m unittest test_changelog.py
```
