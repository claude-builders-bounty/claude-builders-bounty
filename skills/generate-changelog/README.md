# 📋 Generate Changelog from Git History

A bash script that auto-generates a structured `CHANGELOG.md` from your
project's git history. Works as a standalone script **or** as a Claude Code
skill via `/generate-changelog`.

## Setup (3 steps)

**1. Download**
```bash
curl -O https://raw.githubusercontent.com/<your>/<repo>/main/changelog.sh
chmod +x changelog.sh
```

**2. Run**
```bash
bash changelog.sh
# → generates CHANGELOG.md
```

**3. Review**
```bash
cat CHANGELOG.md
```

## Usage

```bash
bash changelog.sh                    # CHANGELOG.md
bash changelog.sh --output RELEASE.md
bash changelog.sh --since v1.0.0     # start from a specific tag
```

## Output

Commits are auto-categorised from conventional-commit prefixes:

| Prefixes                    | Section      |
|-----------------------------|--------------|
| `feat:`, `add:`, `new:`     | ✨ Added     |
| `fix:`, `bugfix:`, `hotfix:`| 🐛 Fixed     |
| `refactor:`, `perf:`, `chore:`, `ci:`, `docs:`, `style:`, `test:` | 🔧 Changed |
| `remove:`, `deprecate:`, `revert:` | 🗑️ Removed |

Non-standard commits land in a 🔹 Other section.

## Claude Code Skill

Copy the `SKILL.md` file into your project. Then inside Claude Code:

> `/generate-changelog`

The skill invokes the script and shows you the result.
