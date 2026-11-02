.PHONY: test

test:
	python3 -I -c "import json,re; d=json.load(open('n8n-weekly-dev-summary/weekly-dev-summary.json')); n=d['nodes']; names=[x['name'] for x in n]; ids=[x['id'] for x in n]; assert len(set(names))==len(names), 'duplicate node names'; assert len(set(ids))==len(ids), 'duplicate node ids'; c=d['connections']; assert all(k in names for k in c), 'unknown connection source'; assert all(t['node'] in names for v in c.values() for o in v.get('main',[]) for t in o), 'unknown connection target'; s=json.dumps(d); assert not re.search(r'sk-ant-|hooks\.slack\.com/services/|discord\.com/api/webhooks/', s), 'secret or webhook url found'; assert 'claude-sonnet-4-20250514' in s, 'model missing'; assert '0 17 * * 5' in s, 'cron missing'; print('workflow ok:', len(n), 'nodes')"
