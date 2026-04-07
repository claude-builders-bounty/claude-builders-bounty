# Installation Instructions

To setup the pre-tool-use hook for blocking destructive commands:

## Step 1: Create the hook directory
```bash
mkdir -p ~/.claude/hooks
```

## Step 2: Download the hook
```bash
curl -o ~/.claude/hooks/pre-tool-use-hook.sh https://<raw-link-to-your-script>
chmod +x ~/.claude/hooks/pre-tool-use-hook.sh
```