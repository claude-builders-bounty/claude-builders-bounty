# changelog.py

Generate a structured `CHANGELOG.md` from git history using conventional commits.

## Setup

1. **Save the script** — copy `changelog.py` into your project root.
2. **Tag your releases** — `git tag v1.0.0` (the script picks the latest tag automatically).
3. **Run it** — `python changelog.py`

That is it.

```bash
# Options
python changelog.py -o RELEASES.md          # custom output file
python changelog.py -t v0.9.0               # start from a specific tag
python changelog.py --stdout                # print to stdout only
```

## How it works

The script collects every commit since the last `git tag`, categorises them by [Conventional Commits](https://www.conventionalcommits.org/) prefix, and writes a clean markdown changelog.

| Prefix | Section |
|--------|---------|
| `feat:` | Added |
| `fix:` | Fixed |
| `refactor:` / `perf:` | Changed |
| `docs:` | Documentation |
| `style:` | Styling |
| `test:` | Testing |
| `build:` / `ci:` | Build |
| `remove:` / `deprecate:` / `revert:` | Removed |
| `chore:` | Maintenance |
| *(anything else)* | Uncategorised |

## Sample output

See [CHANGELOG.sample.md](CHANGELOG.sample.md) for a real generated example.

## Requirements

- Python 3.8+
- `git` CLI available on your PATH
