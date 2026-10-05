import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const workflow = JSON.parse(readFileSync(new URL('./weekly-dev-summary.json', import.meta.url)));
const nodes = Object.fromEntries(workflow.nodes.map(node => [node.name, node]));
const cfg = { githubRepo: 'fixture/example', language: 'EN', since: '2026-09-28T00:00:00.000Z', until: '2026-10-05T00:00:00.000Z' };
const execute = (name, values, config = cfg) => new Function('$input', '$', nodes[name].parameters.jsCode)(
  { first: () => ({ json: values[0] }), all: () => values.map(json => ({ json })) },
  () => ({ first: () => ({ json: config }) }),
);
const page = (commits = [], issues = [], prs = [], more = false) => ({ data: {
  repository: { defaultBranchRef: { target: { history: { nodes: commits, pageInfo: { hasNextPage: more } } } } },
  closedIssues: { nodes: issues, issueCount: issues.length, pageInfo: { hasNextPage: false } },
  mergedPullRequests: { nodes: prs, issueCount: prs.length, pageInfo: { hasNextPage: false } },
} });
const commit = (id, date) => ({ oid: id.repeat(40), messageHeadline: `Commit ${id}`, committedDate: date, author: { name: 'Fixture' }, url: 'https://example.test' });

test('repository and language are validated before any request', () => {
  assert.throws(() => execute('Build 7-Day Window', [{ githubRepo: 'fixture/example is:private', language: 'EN' }]), /owner\/repo/);
  assert.throws(() => execute('Build 7-Day Window', [{ githubRepo: 'fixture/example', language: 'DE' }]), /EN or FR/);
  const result = execute('Build 7-Day Window', [{ githubRepo: 'fixture/example', language: 'fr' }])[0].json;
  assert.equal(result.language, 'FR');
  assert.equal(Date.parse(result.until) - Date.parse(result.since), 7 * 24 * 60 * 60 * 1000);
});

test('all pages are deduplicated and bounded by both ends of the week', () => {
  const first = commit('a', cfg.since), last = commit('b', cfg.until);
  const old = commit('c', '2026-09-27T23:59:59Z'), future = commit('d', '2026-10-05T00:00:01Z');
  const result = execute('Build Claude Prompt', [page([first, old], [], [], true), page([first, last, future])])[0].json;
  assert.equal(result.activity.commits.length, 2);
  assert.match(result.prompt, /- aaaaaaaa: Commit a — Fixture\n- bbbbbbbb: Commit b/);
  assert.ok(!result.prompt.includes('\\n-'));
});

test('GraphQL errors and inaccessible repositories fail before generation', () => {
  assert.throws(() => execute('Build Claude Prompt', [{ errors: [{ message: 'Rate limited' }] }]), /Rate limited/);
  assert.throws(() => execute('Build Claude Prompt', [{ data: { repository: null } }]), /not found/);
});

test('search limits or incomplete pagination never produce inaccurate counts', () => {
  const capped = page(); capped.data.closedIssues.issueCount = 1001;
  assert.throws(() => execute('Build Claude Prompt', [capped]), /1000-result/);
  assert.throws(() => execute('Build Claude Prompt', [page([], [], [], true)]), /pagination did not complete/);
});

test('an empty week and French output remain explicit', () => {
  const result = execute('Build Claude Prompt', [page()], { ...cfg, language: 'FR' })[0].json;
  assert.match(result.prompt, /français/);
  assert.match(result.prompt, /Commits \(0\):\n- None/);
  assert.equal(result.activity.mergedPullRequests.length, 0);
});

test('pagination preserves exhausted collections while advancing the others', () => {
  const expression = nodes['Fetch GitHub Weekly Activity'].parameters.options.pagination.pagination.parameters.parameters[0].value;
  const update = new Function('$request', '$response', `return (${expression.slice(3, -2)});`);
  const previous = { skipCommits: false, skipIssues: false, skipPrs: true, prCursor: '1' };
  const next = update({ body: { variables: previous } }, { body: { data: {
    repository: { defaultBranchRef: { target: { history: { pageInfo: { endCursor: '135', hasNextPage: false } } } } },
    closedIssues: { pageInfo: { endCursor: '200', hasNextPage: true } },
  } } });
  assert.equal(next.skipCommits, true);
  assert.equal(next.skipIssues, false);
  assert.equal(next.skipPrs, true);
  assert.equal(next.issueCursor, '200');
  assert.equal(next.prCursor, '1');
});

test('all text blocks are joined and Slack receives real line breaks', () => {
  const result = execute('Extract Narrative', [{ stop_reason: 'end_turn', content: [
    { type: 'text', text: 'First' }, { type: 'thinking', thinking: 'omitted' }, { type: 'text', text: 'Second' },
  ] }], { ...cfg, activity: { commits: [], closedIssues: [], mergedPullRequests: [] } })[0].json;
  assert.equal(result.summary, 'First\nSecond');
  assert.equal(result.slackText, '*Weekly dev summary — fixture/example*\nFirst\nSecond');
});

test('empty or truncated model output is rejected before delivery', () => {
  assert.throws(() => execute('Extract Narrative', [{ content: [] }]), /no text summary/);
  assert.throws(() => execute('Extract Narrative', [{ stop_reason: 'max_tokens', content: [{ type: 'text', text: 'Partial' }] }]), /truncated/);
});
