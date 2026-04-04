# SKILL.md — Generate CHANGELOG from git history

Generate a structured `CHANGELOG.md` from your project's git history with one command.

## Usage

```bash
# Generate for unreleased changes since last tag
bash changelog.sh

# Generate with a specific version label
bash changelog.sh v2.0.0

# Generate between two specific tags
bash changelog.sh v2.0.0 v1.9.0
```

## Output

Produces a `CHANGELOG.md` with commits auto-categorized into:

- **Added** — `feat`, `add`, `new`, `implement` prefixes
- **Fixed** — `fix`, `bug`, `patch`, `hotfix`, `resolve` prefixes  
- **Changed** — `refactor`, `perf`, `update`, `change`, `improve`, `bump`, `upgrade`, `style`, `chore` prefixes
- **Removed** — `remove`, `delete`, `drop`, `deprecate` prefixes
- **Other** — everything else

Supports conventional commits (`feat(scope): message` → categorized correctly).

If a `CHANGELOG.md` already exists, the new section is prepended; previous history is preserved.

## Setup

3 steps:

1. Copy `changelog.sh` to your repo root
2. `chmod +x changelog.sh`
3. Run `bash changelog.sh v1.0.0`

No dependencies beyond `git` and `bash`.
