# Changelog generator

Produces CHANGELOG.md from commits after the newest git tag. The tagged commit is excluded. Subject prefixes map to sections: feat and add to Added, fix to Fixed, refactor, change, chore, and perf to Changed, remove and revert to Removed. Any other subject goes under Other.

## Setup

```
bash changelog.sh /path/to/repo
```

That writes CHANGELOG.md in the target repo and prints the range used, for example `v0.1.0..HEAD`.

## Sample output

From a repository tagged v0.1.0, with five commits after the tag:

```
# Changelog

Generated since v0.1.0.

## Added

- feat: add export button (2dfb4d5)
- feat: temp file (f7ecfb8)

## Fixed

- fix: crash when export is empty (3a016c9)

## Changed

- refactor: rename export handler (e58197e)

## Removed

- remove: drop unused temp file (4f901a9)
```

The initial commit that carries the tag is not listed.
