const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');

test('validates n8n workflow schema and node connections', () => {
  const jsonPath = path.join(__dirname, 'weekly_dev_summary.n8n.json');
  const raw = fs.readFileSync(jsonPath, 'utf8');
  const data = JSON.parse(raw);

  assert.ok(data.nodes.length >= 6);
  assert.ok(data.connections);
  assert.ok(data.nodes.some(n => n.name.includes('Cron Trigger')));
  assert.ok(data.nodes.some(n => n.name.includes('Claude API Call')));
  assert.ok(data.nodes.some(n => n.name.includes('Fetch Weekly Commits')));
});
