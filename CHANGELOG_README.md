# generate-changelog.sh

Generate structured CHANGELOG.md from git history with a single command.

## Install

```bash
cp generate-changelog.sh /your/project/
chmod +x generate-changelog.sh
```

## Usage

```bash
bash generate-changelog.sh          # since last tag
bash generate-changelog.sh v1.0.0   # from specific tag
```

## Output categories

- **Added** — feat, add, new, introduce, implement
- **Fixed** — fix, bug, patch, resolve
- **Changed** — refactor, change, update, improve, perf
- **Removed** — remove, drop, delete, deprecate
