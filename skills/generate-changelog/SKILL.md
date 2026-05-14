# /generate-changelog — Git History Changelog Generator

Automatically generates `CHANGELOG.md` from git history since the last tag.

## Usage
```
/generate-changelog
```

Or via bash:
```bash
bash changelog.sh
```

## Behavior
1. Finds the most recent git tag
2. Collects all commits since that tag
3. Auto-categorizes commits into: Added, Fixed, Changed, Removed
4. Outputs formatted `CHANGELOG.md` in Keep a Changelog format
5. Previews the result before saving

## Categorization Rules
| Pattern | Category |
|---------|----------|
| `feat:` `add:` `new:` `Added` | Added |
| `fix:` `bug:` `patch:` `resolve` `close` | Fixed |
| `refactor:` `update:` `tweak:` `perf:` `style:` | Changed |
| `remove:` `delete:` `drop:` `deprecate:` | Removed |
