/* Offline structural and logic checks for the exported n8n workflow. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const wf = JSON.parse(fs.readFileSync(path.join(__dirname, 'workflow.json'), 'utf8'));
const nodes = new Map(wf.nodes.map(node => [node.name, node]));
assert.equal(nodes.size, 8);
for (const node of wf.nodes) {
  assert.equal(Array.isArray(node.position), true, node.name + ': position must be XY pair');
  assert.equal(node.position.length, 2, node.name + ': position must have two entries');
  for (const coordinate of node.position) assert.equal(Number.isFinite(coordinate), true);
}
assert.equal(wf.settings.timezone, 'Asia/Jakarta');
assert.equal(wf.active, false);
assert.equal(nodes.get('Weekly Schedule').parameters.rule.interval[0].field, 'weeks');
assert.deepEqual(nodes.get('Weekly Schedule').parameters.rule.interval[0].triggerAtDay, [5]);
for (const name of ['Fetch Commits', 'Fetch Closed Issues', 'Fetch Closed PRs']) {
  assert.equal(nodes.get(name).executeOnce, true, name + ': prevent API fan-out');
  assert.equal(nodes.get(name).alwaysOutputData, true, name + ': allow no activity');
  assert.equal(nodes.get(name).parameters.method, 'GET');
}
for (let i = 0; i < wf.nodes.length - 1; i++) {
  const name = wf.nodes[i].name;
  assert.equal(wf.connections[name].main[0][0].node, wf.nodes[i + 1].name);
}
for (const node of wf.nodes) {
  const text = JSON.stringify(node.parameters);
  assert.doesNotMatch(text, /sk-ant-[A-Za-z0-9_-]{12}/);
  assert.doesNotMatch(text, /https:\/\/discord\.com\/api\/webhooks\/\d+\//);
}
assert.match(nodes.get('Claude Weekly Summary').parameters.jsonBody, /claude-sonnet-4-20250514/);
assert.match(nodes.get('Claude Weekly Summary').parameters.headerParameters.parameters[1].value, /ANTHROPIC_API_KEY/);
assert.match(nodes.get('Discord Weekly Report').parameters.url, /DISCORD_WEBHOOK_URL/);
const code = nodes.get('Build Prompt').parameters.jsCode;
new vm.Script('(function(){' + code + '\n})()');

function mockDate(daysAgo) {
  return new Date(Date.now() - daysAgo * 86400000).toISOString();
}
const json = input => ({json: input});
const data = {
  'Setup': [json({owner:'acme',repo:'engine',language:'FR',since:mockDate(7),until:mockDate(-0.001)})],
  'Fetch Commits': [json({sha:'abcdef1234567890',commit:{message:'Fix: input handling\nBody',committer:{date:mockDate(1)}},html_url:'https://github.com/acme/engine/commit/abcdef'})],
  'Fetch Closed Issues': [
    json({number:14,title:'Fix docs',closed_at:mockDate(2),html_url:'https://github.com/acme/engine/issues/14'}),
    json({number:15,title:'Not closed',closed_at:null}),
    json({number:16,title:'PR issue must be excluded',pull_request:{url:'test'},closed_at:mockDate(2)}),
  ],
  'Fetch Closed PRs': [
    json({number:77,title:'Improve SDK',merged_at:mockDate(3),html_url:'https://github.com/acme/engine/pull/77'}),
    json({number:78,title:'Closed without merge',merged_at:null}),
  ],
};
function run(overrides = {}) {
  const source = {...data,...overrides};
  const dollar = name => ({
    first: () => source[name][0],
    all: () => source[name],
  });
  return vm.runInNewContext('(function(){' + code + '\n})()', {
    $: dollar, Date, JSON, String, Number, Object, Array, Error,
  })[0].json;
}
const output = run();
assert.equal(output.repository,'acme/engine');
assert.equal(output.totals.commits,1);
assert.equal(output.totals.closedIssues,1);
assert.equal(output.totals.mergedPRs,1);
assert.match(output.prompt,/French/);
assert.match(output.prompt,/PRs/);
assert.equal(output.resultsMayBeIncomplete,false);

const empty = run({
  'Fetch Commits': [json({})],
  'Fetch Closed Issues': [json({})],
  'Fetch Closed PRs': [json({})],
});
assert.equal(empty.totals.commits,0);
assert.equal(empty.totals.closedIssues,0);
assert.equal(empty.totals.mergedPRs,0);
const hundred = Array.from({length:100}, (_, i)=>json({number:i+1,title:'Closed',closed_at:mockDate(1)}));
const limit = run({'Fetch Closed Issues':hundred});
assert.equal(limit.resultsMayBeIncomplete,true);
assert.match(limit.prompt,/100 results/);

console.log('PASS: n8n JSON schema, safe secrets, API fan-out, zero-activity, counts, PR dedup, limit warnings');
