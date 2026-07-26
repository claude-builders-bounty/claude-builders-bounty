# Destructive command hook

A Claude Code `PreToolUse` hook that blocks destructive Bash and SQL commands
before execution while allowing harmless commands that merely quote or search
for the same text.

It denies:

- recursive forced removal (`rm -rf`, split/reordered flags, and long options)
- `DROP TABLE`
- forced Git pushes (`git push --force` and `git push -f`)
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Literal destructive SQL piped from `echo` or `printf` into a supported SQL
client is also blocked. Direct SQL-client forms such as `--command=...`,
`--execute=...`, and `sqlite3 database SQL` are covered as well.

Blocked attempts are appended as JSON lines to
`~/.claude/hooks/blocked.log`. Each record includes a UTC timestamp, the
attempted command, and the project path. Claude also receives a clear denial
reason through the `PreToolUse` response.

## Install

From the repository root:

```sh
python hooks/install.py
```

Restart Claude Code after installation. The installer copies the hook to
`~/.claude/hooks/` and idempotently registers it in
`~/.claude/settings.json`.

## Test

```sh
python -m unittest discover -s tests -v
```

The hook uses only the Python standard library and fails open for malformed or
unrelated hook input.
