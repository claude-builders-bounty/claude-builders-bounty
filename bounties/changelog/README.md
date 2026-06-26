# CHANGELOG Generator

A bash script that generates `CHANGELOG.md` from git history.

## Setup

```bash
# 1. Copy to your project
cp changelog.sh /path/to/your/project/

# 2. Make executable
chmod +x changelog.sh

# 3. Run
bash changelog.sh
```

## How it works

Reads commits since the last git tag via `git describe`, categorizes by conventional commit prefix (`feat`, `fix`, `refactor`/`perf`/`style`, `remove`/`chore`), and writes a clean `CHANGELOG.md`.

## Sample output

See [sample/CHANGELOG.md](sample/CHANGELOG.md) for an example generated against this repository.
