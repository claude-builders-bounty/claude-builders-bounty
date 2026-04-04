# 📋 git-changelog-skill

Auto-generate a structured `CHANGELOG.md` from your git history — categorized into **Added**, **Fixed**, **Changed**, and **Removed** — in one command.

Works as a **bash script** (`changelog.sh`) or as a **Claude Code skill** (`/generate-changelog`).

---

## Setup (3 steps)

**1. Copy `changelog.sh` to your project root**
```bash
curl -O https://raw.githubusercontent.com/<YOUR_USERNAME>/git-changelog-skill/main/changelog.sh
```

**2. Make it executable**
```bash
chmod +x changelog.sh
```

**3. Run it**
```bash
bash changelog.sh
```

That's it — `CHANGELOG.md` is generated in your project root. ✅

---

## Claude Code Usage

Copy `SKILL.md` into your project's `.claude/skills/` directory, then in Claude Code run:

```
/generate-changelog
```

---

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--since <tag>` | Start from a specific tag | last git tag |
| `--output <file>` | Output file path | `CHANGELOG.md` |
| `--version <label>` | Version label for new section | `Unreleased` |

**Examples:**
```bash
# Use last tag automatically
bash changelog.sh

# Override tag range
bash changelog.sh --since v1.0.0

# Tag a release version
bash changelog.sh --version 2.1.0 --since v2.0.0
```

---

## How Categorization Works

Commits are matched by prefix or keyword — first match wins:

| Category  | Matched prefixes / keywords |
|-----------|-----------------------------|
| ✨ Added   | `feat`, `add`, `new`, `create`, `introduce`, `implement` |
| 🐛 Fixed   | `fix`, `bug`, `patch`, `resolve`, `hotfix`, `correct`, `revert` |
| 🔧 Changed | `refactor`, `update`, `change`, `improve`, `upgrade`, `bump`, `chore`, `style`, `perf`, `docs` |
| 🗑️ Removed | `remove`, `delete`, `drop`, `deprecate` |

Conventional commit prefixes (`feat(scope): message`) are stripped for clean output.

---

## Sample Output

See [`CHANGELOG.md`](./CHANGELOG.md) for a real example generated from this repo.