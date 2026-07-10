# CHANGELOG Generator

Auto-generates a structured `CHANGELOG.md` from git history.

## Setup (3 steps)

1. Clone this repo
2. Run: `bash changelog.sh /path/to/your/repo`
3. Find your `CHANGELOG.md` in the current directory

## How It Works

- Finds all commits since the last git tag
- Auto-categorizes into: Added / Fixed / Changed / Removed
- Outputs a properly formatted `CHANGELOG.md`

## Example

```bash
$ bash changelog.sh ../my-project
Generated CHANGELOG.md with changes categorized
```
