# Installation

## Project configuration

Keep `block_destructive_bash.py` at the project root, copy `settings.json` to
`.claude/settings.json`, and make the script executable:

```sh
mkdir -p .claude && cp settings.json .claude/settings.json && chmod +x block_destructive_bash.py
```

## User-wide configuration

Install the script in the global hooks directory:

```sh
mkdir -p ~/.claude/hooks && cp block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py && chmod +x ~/.claude/hooks/block_destructive_bash.py
```

Then merge `global-settings.json` into `~/.claude/settings.json`. The hook
creates `~/.claude/hooks/blocked.log` on the first blocked attempt.
