# Sample Output

## Test repo

A temporary git repo created locally with these commits:

```
init: project setup
feat: add login page
fix: correct off-by-one
chore: update dependencies
remove: drop unused helpers
```

## Commit range

`first-commit..HEAD` (no tags present, 4 commits)

## Generate command

```bash
python3 skills/changelog-generator/changelog.py
```

## Result

```markdown
# Changelog

## Added
- feat: add login page

## Fixed
- fix: correct off-by-one

## Changed
- chore: update dependencies

## Removed
- remove: drop unused helpers
```
