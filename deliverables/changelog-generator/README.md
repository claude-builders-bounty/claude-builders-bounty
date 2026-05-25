# Changelog Generator

3 steps:

1. `chmod +x changelog.sh`
2. `./changelog.sh /path/to/repo`
3. open `CHANGELOG.md`

That's it. Uses the last git tag as the baseline and buckets commits into `Added`, `Fixed`, `Changed`, `Removed`.

Tested on `work-vscode-icons` (`v2.18.0..HEAD`).
