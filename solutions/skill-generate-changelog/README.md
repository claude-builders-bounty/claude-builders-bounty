# changelog.sh — structured `CHANGELOG.md` from git history

A tiny, dependency-free generator that turns your project's git history into a
properly formatted `CHANGELOG.md`, auto-categorized into **Added / Fixed /
Changed / Removed**.

Built for the $50 Claude Builders Bounty:
[*SKILL: Generate a structured CHANGELOG from git history*](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1).

---

## Setup (3 steps)

1. **Add the script to your repo**
   ```bash
   cp changelog.sh /path/to/your/repo/
   ```
   *(or copy `SKILL.md` into `.claude/skills/generate-changelog/` to use it as a
   Claude Code skill — see below)*
2. **Make it executable**
   ```bash
   chmod +x /path/to/your/repo/changelog.sh
   ```
3. **Run it from inside the repo**
   ```bash
   ./changelog.sh
   ```

Done — `CHANGELOG.md` is written to the repo root, covering every commit **since
the last git tag**.

---

## Usage

```bash
bash changelog.sh                    # since the most recent tag (default)
bash changelog.sh v1.0.0             # from a specific tag
bash changelog.sh v1.0.0..HEAD       # from an explicit range
CHANGELOG_FILE=docs/CHANGES.md bash changelog.sh   # custom output path
```

### How commits are categorized

Matching is case-insensitive on the **prefix of the commit subject**:

| Commit prefix                                   | Section    |
|-------------------------------------------------|------------|
| `feat`, `add`, `new`, `implement`               | **Added**  |
| `fix`, `bug`, `patch`, `hotfix`, `repair`       | **Fixed**  |
| `remove`, `drop`, `delete`, `deprecate`         | **Removed**|
| anything else (`chore`, `docs`, `refactor`, …)  | **Changed**|

Unknown subjects fall back to **Changed** — commits are never silently dropped.
Merge commits are skipped.

### Example output

See [`SAMPLE-CHANGELOG-minimal.md`](SAMPLE-CHANGELOG-minimal.md) (a real repo,
12 commits since its last tag) and [`SAMPLE-CHANGELOG.md`](SAMPLE-CHANGELOG.md)
(the real repo `sindresorhus/got`, all four categories).

### Using it as a Claude Code skill (`/generate-changelog`)

`SKILL.md` in this folder is a drop-in [Claude Code
skill](https://docs.claude.com/en/docs/claude-code/skills). Install it with:

```bash
mkdir -p .claude/skills/generate-changelog
cp SKILL.md changelog.sh .claude/skills/generate-changelog/
```

Then invoke it in Claude Code with the **`/generate-changelog`** command (or just
ask *"generate a changelog"*). The skill shells out to the same `changelog.sh`.

---

## Requirements

- `bash` 4+ and `git`. No other dependencies.

## License

MIT.
