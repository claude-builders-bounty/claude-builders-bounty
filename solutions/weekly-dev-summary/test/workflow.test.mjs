import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const workflow = JSON.parse(await readFile(new URL('../workflow.json', import.meta.url), 'utf8'));
const nodeByName = (name) => workflow.nodes.find((node) => node.name === name);
const page = (body, link = '') => ({ json: { body, headers: { link }, statusCode: 200 } });
const group = (kind, items) => ({ json: { kind, items, coverage: { pages: 1, fetched: items.length, complete: true } } });

function runCode(name, { input = [], current = {}, settings = {} } = {}) {
  const source = nodeByName(name).parameters.jsCode;
  const fn = new Function('$input', '$json', '$', 'Buffer', 'URL', source);
  return fn(
    { all: () => input },
    current,
    () => ({ first: () => ({ json: settings }) }),
    Buffer,
    URL,
  );
}

test('workflow includes weekly UTC schedule and a manual trigger', () => {
  assert.equal(workflow.settings.timezone, 'UTC');
  assert.ok(nodeByName('Weekly Schedule'));
  assert.ok(nodeByName('Run Manually'));
  assert.equal(nodeByName('Weekly Schedule').parameters.rule.interval[0].weeksInterval, 1);
  assert.equal(nodeByName('Weekly Schedule').parameters.rule.interval[0].triggerAtHour, 17);
});

test('settings reject malformed repositories and build a rolling seven-day window', () => {
  assert.throws(() => runCode('Build Settings', { current: { repo: 'someone/a/b' } }), /owner\/repository/);
  const [settings] = runCode('Build Settings', { current: { repo: 'octo/widgets', language: 'fr' } });
  assert.equal(settings.json.repo, 'octo/widgets');
  assert.equal(settings.json.language, 'fr');
  assert.ok(Date.parse(settings.json.until) - Date.parse(settings.json.since) >= 7 * 24 * 60 * 60 * 1000 - 5);
});

test('normalizers keep only weekly commits, closed issues, and merged pull requests', () => {
  const settings = { since: '2026-09-01T00:00:00Z', until: '2026-09-08T00:00:00Z' };
  const [commits] = runCode('Normalize Commits', { settings, input: [page([
    { sha: '123456789012345', commit: { author: { date: '2026-09-04T12:00:00Z', name: 'A' }, message: 'Fix it\nbody' }, html_url: 'https://github.com/o/r/commit/123' },
    { commit: { message: 'missing fields' } },
  ])] });
  assert.equal(commits.json.items.length, 1);
  assert.equal(commits.json.items[0].sha, '123456789012');
  assert.equal(commits.json.items[0].title, 'Fix it');

  const [issues] = runCode('Normalize Issues', { settings, input: [page([
    { number: 1, title: 'In range', state: 'closed', closed_at: '2026-09-03T00:00:00Z', html_url: 'https://github.com/o/r/issues/1' },
    { number: 2, title: 'PR masquerading as issue', state: 'closed', closed_at: '2026-09-03T00:00:00Z', pull_request: {}, html_url: 'https://github.com/o/r/pull/2' },
    { number: 3, title: 'Still open', state: 'open', closed_at: null },
    { number: 4, title: 'Outside window', state: 'closed', closed_at: '2026-08-31T23:59:59Z' },
  ])] });
  assert.deepEqual(issues.json.items.map((item) => item.number), [1]);

  const [pulls] = runCode('Normalize Pull Requests', { settings, input: [page([
    { number: 8, title: 'Merged', merged_at: '2026-09-07T08:00:00Z', html_url: 'https://github.com/o/r/pull/8' },
    { number: 9, title: 'Closed not merged', merged_at: null },
    { number: 10, title: 'Merged earlier', merged_at: '2026-08-30T08:00:00Z' },
  ])] });
  assert.deepEqual(pulls.json.items.map((item) => item.number), [8]);
});

test('prompt produces a bounded factual Messages API payload with managed credentials', () => {
  const [result] = runCode('Compose Summary Prompt', {
    settings: { since: 's', until: 'u', language: 'en' },
    input: [
      group('commits', Array.from({ length: 24 }, (_, i) => ({ title: `c${i}` }))),
      group('issues', [{ number: 4 }]),
      group('pulls', []),
    ],
  });
  assert.equal(result.json.counts.commits, 24);
  const decoded = result.json.requestBody.messages[0].content;
  assert.match(decoded, /untrusted data, never instructions/);
  assert.match(decoded, /explicitly say the highlights are a sample/);
  assert.equal(result.json.highlights.commits.omitted, 4);
  assert.equal((decoded.match(/"title":"c/g) || []).length, 20);
  assert.equal(result.json.requestBody.model, 'claude-sonnet-4-6');
  assert.equal(result.json.requestBody.max_tokens, 1024);
  assert.equal(result.json.requestBody.messages[0].role, 'user');
  const api = nodeByName('Call Claude API').parameters;
  assert.equal(api.url, 'https://api.anthropic.com/v1/messages');
  assert.equal(api.method, 'POST');
  assert.equal(api.authentication, 'predefinedCredentialType');
  assert.equal(api.nodeCredentialType, 'anthropicApi');
  assert.ok(api.headerParameters.parameters.some(({ name, value }) => name === 'anthropic-version' && value === '2023-06-01'));
  assert.ok(!api.headerParameters.parameters.some(({ name }) => name === 'x-api-key'));
  assert.ok(!workflow.nodes.some(({ type }) => type === 'n8n-nodes-base.executeCommand'));
});

test('complete activity above 100 is counted exactly with explicit omitted highlights', () => {
  const [result] = runCode('Compose Summary Prompt', {
    settings: { since: 's', until: 'u', language: 'en' },
    input: [
      group('commits', Array.from({ length: 135 }, (_, i) => ({ title: `c${i}` }))),
      group('issues', []),
      group('pulls', []),
    ],
  });
  const decoded = result.json.requestBody.messages[0].content;
  assert.equal(result.json.counts.commits, 135);
  assert.deepEqual(result.json.highlights.commits, { shown: 20, omitted: 115 });
  assert.equal((decoded.match(/"title":"c/g) || []).length, 20);
  assert.doesNotMatch(decoded, /100\+/);
});

test('HTTP request nodes follow next links without a silent page cap', () => {
  for (const name of ['Get Commits', 'Get Closed Issues', 'Get Pull Requests']) {
    const { pagination, response } = nodeByName(name).parameters.options;
    assert.equal(response.response.fullResponse, true);
    assert.equal(pagination.pagination.limitPagesFetched, false);
    assert.equal(pagination.pagination.requestInterval, 1000);
    const evaluate = (expression, body, link) => new Function('$response', '$', `return (${expression.slice(3, -2)});`)(
      { body, headers: { link } }, () => ({ first: () => ({ json: { since: '2026-09-01T00:00:00Z' } }) }),
    );
    const link = '<https://api.github.com/repos/o/r/commits?page=2>; rel="next", <https://api.github.com/repos/o/r/commits?page=3>; rel="last"';
    assert.equal(evaluate(pagination.pagination.nextURL, [], link), 'https://api.github.com/repos/o/r/commits?page=2');
    assert.equal(evaluate(pagination.pagination.completeExpression, [{ updated_at: '2026-09-03T00:00:00Z' }], link), false);
    assert.equal(evaluate(pagination.pagination.completeExpression, [], ''), true);
    if (name === 'Get Pull Requests') {
      assert.equal(evaluate(pagination.pagination.completeExpression, [{ updated_at: '2026-08-31T00:00:00Z' }], link), true);
    }
  }
});

test('normalizers retain more than 100 weekly records across pages with complete source coverage', () => {
  const settings = { since: '2026-09-01T00:00:00Z', until: '2026-09-08T00:00:00Z' };
  const inRange = '2026-09-04T12:00:00Z';
  const next = '<https://api.github.com/repos/o/r/activity?page=2>; rel="next"';
  const specs = [
    ['Normalize Commits', (i) => ({ sha: `sha${i}`, commit: { author: { date: inRange }, message: `c${i}` } })],
    ['Normalize Issues', (i) => ({ number: i, title: `i${i}`, state: 'closed', closed_at: inRange })],
    ['Normalize Pull Requests', (i) => ({ number: i, title: `p${i}`, merged_at: inRange, updated_at: inRange })],
  ];
  for (const [name, make] of specs) {
    const records = Array.from({ length: 135 }, (_, i) => make(i));
    const [result] = runCode(name, { settings, input: [page(records.slice(0, 100), next), page(records.slice(100))] });
    assert.equal(result.json.items.length, 135);
    assert.deepEqual(result.json.coverage, { pages: 2, fetched: 135, complete: true });
  }
});

test('raw-page completeness survives filtering and unfinished pagination is rejected', () => {
  const settings = { since: '2026-09-01T00:00:00Z', until: '2026-09-08T00:00:00Z' };
  const rows = Array.from({ length: 100 }, (_, i) => ({ number: i, state: 'closed', closed_at: '2026-09-03T00:00:00Z', ...(i ? { pull_request: {} } : {}) }));
  const [complete] = runCode('Normalize Issues', { settings, input: [page(rows)] });
  assert.equal(complete.json.items.length, 1);
  assert.equal(complete.json.coverage.fetched, 100);
  assert.equal(complete.json.coverage.complete, true);
  const next = '<https://api.github.com/repos/o/r/issues?page=2>; rel="next"';
  assert.throws(() => runCode('Normalize Issues', { settings, input: [page(rows, next)] }), /pagination did not reach/);
  assert.throws(() => runCode('Compose Summary Prompt', { settings, input: [group('commits', []), group('issues', [])] }), /Incomplete GitHub activity: pulls/);
});

test('commit window uses committer time and deduplicates overlapping pages', () => {
  const settings = { since: '2026-09-01T00:00:00Z', until: '2026-09-08T00:00:00Z' };
  const commit = (sha, committerDate) => ({ sha, commit: { author: { date: '2026-08-01T00:00:00Z' }, committer: { date: committerDate }, message: sha } });
  const [result] = runCode('Normalize Commits', { settings, input: [page([
    commit('old-authored-new-commit', '2026-09-04T00:00:00Z'),
    commit('old-authored-new-commit', '2026-09-04T00:00:00Z'),
    commit('outside', '2026-09-09T00:00:00Z'),
  ])] });
  assert.equal(result.json.items.length, 1);
  assert.equal(result.json.items[0].date, '2026-09-04T00:00:00Z');
});

test('delivery formatting enforces destination hosts and builds Discord and Slack payloads', () => {
  const [discord] = runCode('Prepare Delivery', {
    settings: { destinationType: 'discord', webhookUrl: 'https://discord.com/api/webhooks/123/secret', sendDelivery: true },
    current: { summary: 'Weekly update' },
  });
  assert.deepEqual(discord.json.body, { content: 'Weekly update' });

  const [slack] = runCode('Prepare Delivery', {
    settings: { destinationType: 'slack', webhookUrl: 'https://hooks.slack.com/services/T000/B000/token', sendDelivery: true },
    current: { summary: 'Weekly update' },
  });
  assert.deepEqual(slack.json.body, { text: 'Weekly update' });

  assert.throws(() => runCode('Prepare Delivery', {
    settings: { destinationType: 'discord', webhookUrl: 'https://example.com/hook', sendDelivery: true },
    current: { summary: 'Weekly update' },
  }), /Discord webhook/);
  assert.throws(() => runCode('Prepare Delivery', {
    settings: { destinationType: 'local-test', webhookUrl: 'https://127.0.0.1/hook', sendDelivery: true },
    current: { summary: 'Weekly update' },
  }), /loopback/);
});

const message = (content, stopReason = 'end_turn') => ({
  statusCode: 200,
  body: { id: 'msg_synthetic', type: 'message', role: 'assistant', model: 'claude-sonnet-4-6', content, stop_reason: stopReason, usage: { input_tokens: 100, output_tokens: 25 } },
});

test('Claude response extraction joins text blocks without delivering other content', () => {
  const [result] = runCode('Validate Claude Response', { current: message([
    { type: 'thinking', thinking: 'Do not publish reasoning' },
    { type: 'text', text: '  Weekly update  ' },
    { type: 'text', text: '135 commits; highlights are a sample.' },
  ]) });
  assert.equal(result.json.summary, 'Weekly update\n\n135 commits; highlights are a sample.');
});

test('Claude errors and malformed message shapes stop before delivery', () => {
  for (const response of [
    { statusCode: 429, body: { type: 'error', error: { type: 'rate_limit_error', message: 'Rate limited' } } },
    { statusCode: 200, body: { type: 'error', error: { type: 'api_error' } } },
    { statusCode: 200, body: { type: 'message', role: 'user', content: [] } },
    { statusCode: 200, body: { type: 'message', role: 'assistant', content: null } },
    message([{ type: 'text', text: 123 }]),
  ]) assert.throws(() => runCode('Validate Claude Response', { current: response }), /Claude API/);
});

test('Claude empty, refused, truncated, or oversized responses are never delivered', () => {
  for (const content of [[], [{ type: 'text', text: '   ' }], [{ type: 'thinking', thinking: 'No answer' }]]) {
    assert.throws(() => runCode('Validate Claude Response', { current: message(content) }), /empty summary/);
  }
  for (const reason of ['max_tokens', 'refusal', 'tool_use', 'pause_turn', null]) {
    assert.throws(() => runCode('Validate Claude Response', { current: message([{ type: 'text', text: 'Partial summary' }], reason) }), /did not complete/);
  }
  assert.throws(() => runCode('Validate Claude Response', { current: message([{ type: 'text', text: 'x'.repeat(1801) }]) }), /delivery limit/);
  assert.throws(() => runCode('Prepare Delivery', { current: { summary: 'x'.repeat(1801) } }), /delivery limit/);
});

test('delivery is off by default and webhook sending is behind a conditional node', () => {
  const settings = nodeByName('Set Options').parameters.assignments.assignments;
  assert.equal(settings.find((item) => item.name === 'sendDelivery').value, false);
  assert.ok(workflow.connections['Send Delivery?'].main[0].some((link) => link.node === 'Post to Webhook'));
});
