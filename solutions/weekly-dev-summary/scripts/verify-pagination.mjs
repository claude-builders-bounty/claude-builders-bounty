import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { mkdtemp, readFile, writeFile, mkdir, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(fileURLToPath(new URL('..', import.meta.url)));
const n8n = process.env.N8N_BIN;
if (!n8n) throw new Error('Set N8N_BIN to the installed n8n CLI executable');
const sandbox = await mkdtemp(resolve(tmpdir(), 'n8n-pagination-'));
const inRange = new Date(Date.now() - 4 * 86400000).toISOString();
const outside = new Date(Date.now() - 14 * 86400000).toISOString();
const requests = { commits: 0, issues: 0, pulls: 0 };
let apiScenario = 'success';
const apiRequests = [];
const commit = (i) => ({ sha: `sha${i}`, commit: { author: { date: inRange }, committer: { date: inRange }, message: `Commit ${i}` } });
const issue = (i) => ({ number: i, title: `Issue ${i}`, state: 'closed', closed_at: inRange });
const pull = (i) => ({ number: i, title: `PR ${i}`, merged_at: inRange, updated_at: inRange });
const data = {
  commits: [...Array.from({ length: 135 }, (_, i) => commit(i)), { ...commit(999), commit: { author: { date: outside } } }],
  issues: [...Array.from({ length: 135 }, (_, i) => issue(i)), ...Array.from({ length: 20 }, (_, i) => ({ ...issue(1000 + i), pull_request: {} })), ...Array.from({ length: 10 }, (_, i) => ({ ...issue(2000 + i), closed_at: outside }))],
  pulls: [...Array.from({ length: 135 }, (_, i) => pull(i)), ...Array.from({ length: 10 }, (_, i) => ({ ...pull(1000 + i), merged_at: null })), { ...pull(2000), merged_at: outside, updated_at: outside }],
};
let base;
const server = createServer((request, response) => {
  const url = new URL(request.url, base);
  if (url.pathname === '/v1/messages') {
    let body = '';
    request.on('data', (chunk) => { body += chunk; });
    request.on('end', () => {
      const payload = JSON.parse(body);
      const facts = JSON.parse(payload.messages[0].content.split('\n\n').at(-1));
      apiRequests.push({ scenario: apiScenario, method: request.method, version: request.headers['anthropic-version'], payload, facts });
      const error = apiScenario === 'error';
      const result = error
        ? { type: 'error', error: { type: 'rate_limit_error', message: 'Synthetic rate limit' } }
        : { id: 'msg_synthetic', type: 'message', role: 'assistant', model: payload.model,
          content: apiScenario === 'empty' ? [] : [{ type: 'text', text: 'Synthetic weekly summary.' }, { type: 'text', text: '135 commits, 135 closed issues, 135 merged PRs. Highlights are a sample.' }],
          stop_reason: apiScenario === 'truncated' ? 'max_tokens' : 'end_turn', usage: { input_tokens: 100, output_tokens: 35 } };
      response.writeHead(error ? 429 : 200, { 'content-type': 'application/json' }).end(JSON.stringify(result));
    });
    return;
  }
  const kind = url.pathname.split('/').pop();
  if (!(kind in data)) { response.writeHead(404).end(); return; }
  requests[kind] += 1;
  const page = Number(url.searchParams.get('page') || 1);
  const rows = data[kind].slice((page - 1) * 100, page * 100);
  const headers = { 'content-type': 'application/json' };
  if (page === 1 || kind === 'pulls') {
    headers.link = `<${base}/${kind}?page=${page + 1}>; rel="next"`;
  }
  response.writeHead(200, headers).end(JSON.stringify(rows));
});
await new Promise((done) => server.listen(0, '127.0.0.1', done));
base = `http://127.0.0.1:${server.address().port}`;
const env = {
  ...process.env,
  N8N_USER_FOLDER: sandbox,
  N8N_ENCRYPTION_KEY: 'local-synthetic-pagination-verification-only',
  N8N_DIAGNOSTICS_ENABLED: 'false',
  N8N_VERSION_NOTIFICATIONS_ENABLED: 'false',
  N8N_COMMUNITY_PACKAGES_ENABLED: 'false',
  NODES_EXCLUDE: '["n8n-nodes-base.localFileTrigger","n8n-nodes-base.executeCommand"]',
  N8N_RUNNERS_ENABLED: 'false',
};
async function run(args, allowFailure = false) {
  return new Promise((done, reject) => {
    const child = spawn(n8n, args, { env, stdio: ['ignore', 'pipe', 'pipe'] });
    let stdout = '', stderr = '';
    child.stdout.on('data', (chunk) => { stdout += chunk; });
    child.stderr.on('data', (chunk) => { stderr += chunk; });
    child.on('error', reject);
    child.on('exit', (code) => (code === 0 || allowFailure) ? done({ stdout, stderr, code }) : reject(new Error(`n8n ${args[0]} exited ${code}: ${stderr}\n${stdout}`)));
  });
}
try {
  const workflow = JSON.parse(await readFile(resolve(root, 'workflow.json'), 'utf8'));
  for (const [name, kind] of [['Get Commits', 'commits'], ['Get Closed Issues', 'issues'], ['Get Pull Requests', 'pulls']]) {
    workflow.nodes.find((node) => node.name === name).parameters.url = `${base}/${kind}?page=1`;
  }
  // Keep the actual Messages HTTP mapping and parser. Only replace the URL
  // and remove authentication for the local fixture; no API key is needed.
  const api = workflow.nodes.find((node) => node.name === 'Call Claude API');
  api.parameters.url = `${base}/v1/messages`;
  api.parameters.authentication = 'none';
  delete api.parameters.nodeCredentialType;
  const fixture = resolve(sandbox, 'workflow.json');
  await writeFile(fixture, JSON.stringify(workflow));
  await run(['import:workflow', `--input=${fixture}`]);
  const { stdout: output } = await run(['execute', `--id=${workflow.id}`, '--rawOutput']);
  const begin = output.search(/^\{/m);
  if (begin < 0) throw new Error(`No execution result: ${output.slice(-2000)}`);
  const execution = JSON.parse(output.slice(begin));
  assert.equal(execution.finished, true);
  const prompt = execution.data.resultData.runData['Compose Summary Prompt'][0].data.main[0][0].json;
  assert.deepEqual(prompt.counts, { commits: 135, closedIssues: 135, mergedPullRequests: 135 });
  assert.deepEqual(requests, { commits: 2, issues: 2, pulls: 2 });
  for (const coverage of Object.values(prompt.coverage)) assert.equal(coverage.complete, true);
  for (const highlights of Object.values(prompt.highlights)) assert.deepEqual(highlights, { shown: 20, omitted: 115 });
  const runData = execution.data.resultData.runData;
  const delivery = runData['Prepare Delivery'][0].data.main[0][0].json;
  assert.equal(delivery.summary, 'Synthetic weekly summary.\n\n135 commits, 135 closed issues, 135 merged PRs. Highlights are a sample.');
  assert.equal(delivery.sendDelivery, false);
  assert.ok(!runData['Post to Webhook']);
  assert.equal(apiRequests[0].method, 'POST');
  assert.equal(apiRequests[0].version, '2023-06-01');
  assert.equal(apiRequests[0].payload.model, 'claude-sonnet-4-6');
  assert.equal(apiRequests[0].payload.max_tokens, 1024);
  assert.deepEqual(apiRequests[0].facts.counts, prompt.counts);
  const apiChecks = { success: 'POST body/header mapping and multiple text-block extraction passed; delivery disabled' };
  for (const [scenario, expectedError] of [['error', /429|rate limit|Too Many Requests/i], ['empty', /empty summary/], ['truncated', /did not complete the summary/]]) {
    apiScenario = scenario;
    const result = await run(['execute', `--id=${workflow.id}`, '--rawOutput'], true);
    assert.notEqual(result.code, 0);
    assert.match(result.stdout + result.stderr, expectedError);
    apiChecks[scenario] = 'Workflow stopped before delivery';
  }
  assert.equal(apiRequests.length, 4);
  const receipt = {
    checkedAt: new Date().toISOString(),
    environment: 'real isolated n8n CLI; synthetic loopback GitHub responses',
    provider: 'real n8n Messages HTTP node against a synthetic loopback endpoint; no inference or real credentials',
    delivery: 'disabled; no external webhook',
    counts: prompt.counts, coverage: prompt.coverage, highlights: prompt.highlights,
    requestsPerRun: Object.fromEntries(Object.entries(requests).map(([kind, count]) => [kind, count / 4])),
    apiChecks,
    assertions: '135 weekly entries per category; complete Link pagination; old/unmerged/PR-as-issue exclusions; PR weekly-cutoff stops before page 3',
  };
  await mkdir(resolve(root, 'evidence'), { recursive: true });
  await writeFile(resolve(root, 'evidence/pagination-verification.json'), `${JSON.stringify(receipt, null, 2)}\n`);
  console.log(JSON.stringify(receipt, null, 2));
} finally {
  await new Promise((done) => server.close(done));
  await rm(sandbox, { recursive: true, force: true });
}
