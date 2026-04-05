# generate-changelog

Generate a categorized `CHANGELOG.md` from your git history. Commits are auto-sorted into **Added / Fixed / Changed / Removed** based on conventional commit prefixes.

## Setup

1. Copy `changelog.sh` into your repo
2. Run `bash changelog.sh`
3. Check the generated `CHANGELOG.md`

## How it works

- Fetches commits since the last git tag (or all commits if no tags exist)
- Categorizes by commit prefix: `feat:` → Added, `fix:` → Fixed, `chore:/refactor:` → Changed, `remove:/delete:` → Removed
- Unrecognized prefixes go under Changed
- Outputs a [Keep a Changelog](https://keepachangelog.com/) formatted file

## Usage

```bash
bash changelog.sh              # writes CHANGELOG.md
bash changelog.sh output.md   # writes to custom file
```

## Example

See [sample-CHANGELOG.md](sample-CHANGELOG.md) for real output.
