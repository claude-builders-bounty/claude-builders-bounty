# Pre-Tool-Use Security Hook

## Install
```bash
mkdir -p ~/.claude/hooks && ln -sf "$PWD/pre-tool-use.sh" ~/.claude/hooks/
```

## Blocks
- rm -rf /, rm -rf ~ (destructive deletion)
- DROP TABLE, DROP DATABASE (database destruction)
- git push --force (force push)
- Fork bombs, chmod -R 000, mkfs, eval
- All blocked attempts logged to blocked.log

## Allows
Normal commands pass through: npm install, git push, rm file.txt, mkdir
