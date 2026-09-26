# CHANGELOG Generator — `changelog.py` / `changelog.sh` / `changelog.ps1`

Generate a structured `CHANGELOG.md` from git history in 3 steps:

1. **Run it** — in your repo: `python changelog.py` (any OS), `bash changelog.sh` (Linux/macOS), or `powershell -File changelog.ps1` (Windows).
2. **Open it** — a new `CHANGELOG.md` appears with commits since the last tag, grouped into `Added` / `Fixed` / `Changed` / `Removed`.
3. **Ship it** — review, commit, and include it in your release.

No tags yet? It uses the full history. Need a custom path? `python changelog.py /path/to/repo out.md`.

## Example output

See [`examples/sample-CHANGELOG.md`](examples/sample-CHANGELOG.md).