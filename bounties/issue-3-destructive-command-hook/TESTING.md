# Testing

Command run from `bounties/issue-3-destructive-command-hook`:

```bash
python3 -m unittest discover -s tests
```

Result:

```text
.....
----------------------------------------------------------------------
Ran 5 tests

OK
```

Coverage included:

- Safe Bash commands pass without output or blocking.
- `rm -rf`, `rm -fr`, and `sudo rm -Rf` are blocked.
- `git push --force`, `git push -f`, and `git push --force-with-lease` are blocked.
- `DROP TABLE`, `TRUNCATE`, and `DELETE FROM` without `WHERE` are blocked.
- Blocked commands exit with code `2` and append to `~/.claude/hooks/blocked.log`.
