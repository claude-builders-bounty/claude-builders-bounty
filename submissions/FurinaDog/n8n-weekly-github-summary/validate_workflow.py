"""Static checks for the exported n8n workflow."""

import json
from pathlib import Path


workflow_path = Path(__file__).with_name('workflow.json')
workflow = json.loads(workflow_path.read_text(encoding='utf-8'))
nodes = workflow['nodes']
names = {node['name'] for node in nodes}
required = {
    'Weekly trigger',
    'Prepare configuration',
    'Fetch GitHub activity',
    'Build Claude prompt',
    'Generate narrative with Claude',
    'Format Discord message',
    'Deliver to Discord',
}
missing = required - names
assert not missing, f'missing nodes: {sorted(missing)}'

trigger = next(node for node in nodes if node['name'] == 'Weekly trigger')
interval = trigger['parameters']['rule']['interval'][0]
assert interval['field'] == 'weeks'
assert interval['triggerAtDay'] == ['5'], 'trigger must run on Friday'
assert interval['triggerAtHour'] == 17 and interval['triggerAtMinute'] == 0

for node_name in ('Fetch GitHub activity', 'Generate narrative with Claude', 'Deliver to Discord'):
    node = next(node for node in nodes if node['name'] == node_name)
    assert node['type'] == 'n8n-nodes-base.httpRequest'

assert workflow['connections']['Format Discord message']['main'][0][0]['node'] == 'Deliver to Discord'

serialized = json.dumps(workflow)
assert 'claude-sonnet-4-20250514' in serialized
assert 'api.github.com/graphql' in serialized
assert 'DISCORD_WEBHOOK_URL' in serialized
assert 'GITHUB_TOKEN' in serialized
assert 'ANTHROPIC_API_KEY' in serialized
for secret in ('sk-ant-', 'ghp_', 'https://discord.com/api/webhooks/'):
    assert secret not in serialized, f'literal secret detected: {secret}'

print(f'OK: validated {len(nodes)} nodes and {len(workflow["connections"])} connections')
