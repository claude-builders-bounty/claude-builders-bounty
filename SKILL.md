# SKILL: Pre-Tool-Use Hook — Block Destructive Commands

## Usage
Source `hooks/block-destructive.sh` before executing shell commands, or run:
```bash
bash hooks/block-destructive.sh "your command here"
```

## Blocks
- `rm -rf /`, `rm -rf ~` — System/home deletion
- `dd of=/dev/*` — Disk wiping
- `mkfs`, `fdisk` — Disk formatting
- `chmod -R 777` — Insecure permissions
- Fork bombs, download-and-execute patterns
- `DROP DATABASE`, `TRUNCATE` — Database destruction
- `git push --force` — Forced history rewrite

## Allowlist
Safe deletions: `./node_modules`, `./dist`, `./build`, `/tmp/*`
