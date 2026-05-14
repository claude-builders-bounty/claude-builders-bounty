#!/usr/bin/env python3
import json
import sys
from pathlib import Path

REQUIRED_NODES = {
    'Weekly Friday 5pm',
    'Config',
    'GitHub Commits',
    'GitHub Closed Issues',
    'GitHub Merged PRs',
    'Build Claude Prompt',
    'Claude Summary',
    'Format Discord Message',
    'Send Discord Webhook',
}

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'workflows/weekly-dev-summary-claude.json')
data = json.loads(path.read_text())
node_names = {node['name'] for node in data.get('nodes', [])}
missing = REQUIRED_NODES - node_names
if missing:
    raise SystemExit(f'missing nodes: {sorted(missing)}')
text = path.read_text()
for needle in ['claude-sonnet-4-20250514', 'GITHUB_REPO', 'DISCORD_WEBHOOK_URL', 'SUMMARY_LANGUAGE', 'GITHUB_TOKEN', 'ANTHROPIC_API_KEY']:
    if needle not in text:
        raise SystemExit(f'missing configurable value: {needle}')
if 'Friday' not in text and 'triggerAtDay' not in text:
    raise SystemExit('missing weekly schedule config')
print(f'workflow ok: {path} ({len(data["nodes"])} nodes)')
