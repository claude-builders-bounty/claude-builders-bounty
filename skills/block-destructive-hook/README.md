# Block Destructive Commands — Claude Code Hook

A `PreToolUse` hook that denies dangerous Bash commands before Claude Code runs them.
It only returns a permission decision for a blocked command. Safe commands return no
hook decision, so Claude Code's normal permission flow remains in control.

## Claude Code registration

From this directory, run the installer once:

```bash
./install.sh
```

It copies the hook and its tokenizer to `~/.claude/hooks/`, then merges one
`Bash` `PreToolUse` entry into `~/.claude/settings.json` without replacing
unrelated settings. The installed hook uses its adjacent tokenizer, so the
absolute path remains valid from every project.

Manual registration is also supported: copy both `block-destructive.sh` and
`command_parser.py` to a stable absolute directory, make them executable, and
add this to `~/.claude/settings.json` (merge it; do not replace unrelated
configuration):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/Users/YOU/.claude/hooks/block-destructive.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

Use the real absolute path for `command`. The `matcher` limits this hook to the
Bash tool. Claude Code sends a JSON request on stdin, including `tool_name`,
`tool_input.command`, and `cwd`. A blocked request returns the official
`hookSpecificOutput` `PreToolUse` response with `permissionDecision: "deny"`.
For safe/non-Bash requests this hook emits no decision (neutral exit), rather
than explicitly returning `allow` and bypassing Claude Code permissions.

## Blocked patterns

The classifier tokenizes command boundaries, shell quoting, wrappers, and options;
it does not search arbitrary text for dangerous substrings. It recursively inspects
executing shell payloads in `$(...)`, backticks, `<(...)`/`>(...)` process
substitutions (including nested ones), shell `-c`/`sh -c`, `eval`, `find -exec`,
and here-strings/heredocs (`<<<`, `<<EOF`) fed to a shell, while leaving
single-quoted documentation and echo/printf examples neutral. It also decodes
ANSI-C quoted words (`$'...'`) and expands brace expressions (`{a,b}`,
`{1..5}`) the same way bash would, before checking targets. It blocks:

- Filesystem destruction: every `rm -rf`/`rm -fr` invocation (as required by
  the bounty contract), plus root, normalized parent traversal, glob-root,
  parent/current/home directories, sensitive system subtrees, and `./build`
  even when only one destructive flag is present — including targets hidden
  behind `$'...'` escapes or `{...}` brace expansion
- `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, and `DELETE FROM` without `WHERE`,
  including multiline SQL, SQL comments, and fused short flags
  (`psql -c"DELETE FROM t"`, `mysql -e"DROP TABLE t"`, `sqlcmd -Q "..."`)
- `git push --force`, `git push -f`, `git push --force-with-lease` (including
  `git -C repo push ...`), and `git reset --hard`
- `shutdown` and `halt` as command words, plus the existing download-to-shell
  and disk-wipe patterns
- Destructive payloads behind `nice`, `xargs`, `timeout`, `nohup`, and `exec`
  wrappers, including their own attached/fused flags (`nice -n19`, `xargs -n1`)

Because the acceptance contract names the `rm -rf` pattern itself,
`rm -rf build` is denied too. Non-recursive ordinary removal and quoted
documentation such as `echo 'rm -rf /'` and `printf 'git push --force'`
remain neutral. If the classifier itself fails, the hook fails closed rather
than treating an analysis error as permission. Blocked attempts are logged to
`~/.claude/hooks/blocked.log`; the `project` value comes from the request's JSON
`cwd`.

## Testing

Run both test suites from the repository root:

```bash
bash tests/test_block_destructive.sh
bash skills/block-destructive-hook/tests/test_block_destructive.sh
```

The first is a fast smoke test of the classifier's acceptance-critical paths.
The second invokes the script with the same JSON-over-stdin protocol Claude
Code uses and is the full regression suite: denial and neutral safe-command
behavior, quoted echo/documentation, `git -C` force pushes, force-with-lease,
normalized paths, multiline/commented SQL, fused SQL client flags, benign
halt text, attached/fused wrapper flags (`nice`, `xargs`), ANSI-C quoted
(`$'...'`) targets, brace expansion, here-strings and heredocs, nested process
substitutions, and JSON `cwd` logging. The installer is intentionally small
and only merges its own hook entry.
