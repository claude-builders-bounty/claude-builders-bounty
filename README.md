# Changelog generator (Claude Builders bounty)

Bash script + Claude Code skill that builds a Keep-a-Changelog document from commits **since the last git tag**, grouped into **Added / Fixed / Changed / Removed**.

## Install / run (3 steps)

```bash
chmod +x changelog.sh
./changelog.sh
./changelog.sh > CHANGELOG.md
```

Optional: copy `.claude/skills/changelog/` into a repo’s `.claude/skills/` so Claude Code can invoke the skill.

## Sample

See `CHANGELOG.sample.md` for output against a tiny tagged demo history.
