# `/generate-changelog`

Generate `CHANGELOG.md` from git history.

## Use

```bash
./changelog.sh /path/to/repo
```

## Rules

- use the latest git tag as the lower bound
- group commits into `Added`, `Fixed`, `Changed`, `Removed`
- output Keep a Changelog style markdown

## Output

- write `CHANGELOG.md`
- include commit short hashes
