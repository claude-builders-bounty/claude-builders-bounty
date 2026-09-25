# CLAUDE.md template

Opinionated rules for a new Next.js 15 App Router app that stores data in a local SQLite file. The template is meant to be copied as CLAUDE.md without editing the rules.

## Use

```
cp CLAUDE.md /path/to/new-next-app/CLAUDE.md
```

## Check

```
python3 check_template.py /path/to/new-next-app
```

The check fails if a path named in CLAUDE.md is missing from that app. It does not claim an assistant has read the file.
