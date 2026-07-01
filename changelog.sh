#!/bin/bash
# Generate CHANGELOG.md from git history
# Usage: ./changelog.sh [--tag <tag>] [--output <file>]

set -euo pipefail

OUTPUT_FILE="CHANGELOG.md"
CUSTOM_TAG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --tag) CUSTOM_TAG="$2"; shift 2 ;;
        --output) OUTPUT_FILE="$2"; shift 2 ;;
        *) echo "Usage: $0 [--tag <tag>] [--output <file>]"; exit 1 ;;
    esac
done

# Determine tag range
if [ -n "$CUSTOM_TAG" ]; then
    TAG="$CUSTOM_TAG"
elif git describe --tags --abbrev=0 2>/dev/null; then
    TAG=""
    TAG=$(git describe --tags --abbrev=0)
else
    TAG=""
fi

if [ -z "$TAG" ]; then
    RANGE="HEAD"
else
    RANGE="${TAG}..HEAD"
fi

VERSION="${TAG:-unreleased}"
DATE=$(date '+%Y-%m-%d')

# Delegate to python script
python3 -c "
import subprocess, re, os, sys

tag = '$TAG'
version = '$VERSION'
date_str = '$DATE'
output = '$OUTPUT_FILE'
tag_str = f'{tag}..HEAD' if tag else 'HEAD'

# Get commits
result = subprocess.run(
    ['git', 'log', tag_str, '--pretty=format:%s|||%h|||%an', '--no-merges'],
    capture_output=True, text=True
)
lines = [l for l in result.stdout.strip().split(chr(10)) if l]

# Get repo URL
remote = subprocess.run(['git', 'remote', 'get-url', 'origin'], capture_output=True, text=True).stdout.strip()
m = re.search(r'github[^/]+[/:]([^/]+)/([^/.]+)', remote)
base_url = f'https://github.com/{m.group(1)}/{m.group(2)}' if m else ''

# Categorise
cats = {'Added': [], 'Fixed': [], 'Changed': [], 'Removed': []}

for line in lines:
    parts = line.split('|||', 2)
    if len(parts) < 2:
        continue
    msg = parts[0].strip()
    h = parts[1].strip()
    entry = f'- {msg} ([{h}]({base_url}/commit/{h}))' if base_url else f'- {msg} ({h})'

    low = msg.lower()
    if re.match(r'^(feat|feature|add|new|implement|introduce)', low):
        cats['Added'].append(entry)
    elif re.match(r'^(fix|bug|hotfix|patch|correct|resolve)', low):
        cats['Fixed'].append(entry)
    elif re.match(r'^(remove|delete|drop|deprecate)', low):
        cats['Removed'].append(entry)
    else:
        cats['Changed'].append(entry)

# Write output
out_path = os.path.join(os.getcwd(), output)
with open(out_path, 'w') as f:
    f.write(f'# Changelog\n\n')
    f.write(f'## [{version}] - {date_str}\n\n')
    
    for heading in ['Added', 'Fixed', 'Changed', 'Removed']:
        items = cats[heading]
        if items:
            f.write(f'### {heading}\n')
            for item in items:
                f.write(f'{item}\n')
            f.write('\n')

print(f'Written {len(lines)} entries to {output}')
" 2>&1