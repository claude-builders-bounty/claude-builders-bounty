#!/usr/bin/env node
/**
 * Integration tests for workflow components: token gate, GitHub fetch, activity merge.
 */
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import {
  collectRecords,
  fetchGitHubPages,
  validateGitHubToken,
} from './lib/github-collect.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const workflow = JSON.parse(readFileSync(join(__dirname, '..', 'weekly-dev-summary.json'), 'utf8'));

const failures = [];
function assert(condition, message) {
  if (!condition) failures.push(message);
}

function mockResponse(status, body) {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: String(status),
    json: async () => body,
  };
}

async function mockGitHubApi(url) {
  if (url.includes('/commits')) {
    return mockResponse(200, [
      { sha: 'abc', commit: { message: 'feat: add widget', author: { date: '2026-06-10T12:00:00Z' } } },
    ]);
  }
  if (url.includes('/search/issues')) {
    return mockResponse(200, { items: [{ number: 3, title: 'Merged PR', merged_at: '2026-06-12T12:00:00Z' }] });
  }
  if (url.includes('/issues')) {
    return mockResponse(200, [
      { number: 1, title: 'Bug', closed_at: '2026-06-11T12:00:00Z' },
      { number: 2, title: 'PR', closed_at: '2026-06-11T12:00:00Z', pull_request: {} },
    ]);
  }
  if (/\/repos\/[^/]+\/[^/?]+$/.test(url.split('?')[0])) {
    return mockResponse(200, { full_name: 'o/r' });
  }
  return mockResponse(404, { message: 'Not Found', documentation_url: 'https://docs.github.com' });
}

const repoName = await validateGitHubToken('integration-token', { repo: 'o/r', fetchFn: mockGitHubApi });
assert(repoName === 'o/r', 'integration: validateGitHubToken accepts mocked GitHub repo access');

const commits = await fetchGitHubPages(
  'https://api.github.com/repos/o/r/commits',
  'integration-token',
  { since: '2026-06-01' },
  { fetchFn: mockGitHubApi },
);
const issues = await fetchGitHubPages(
  'https://api.github.com/repos/o/r/issues',
  'integration-token',
  { state: 'closed' },
  { fetchFn: mockGitHubApi },
);
const merged = await fetchGitHubPages(
  'https://api.github.com/search/issues',
  'integration-token',
  { q: 'repo:o/r is:pr is:merged' },
  { fetchFn: mockGitHubApi },
);

const weekStart = new Date('2026-06-08T00:00:00Z');
const weekEnd = new Date('2026-06-15T23:59:59Z');
const inWeek = (iso) => {
  if (!iso) return false;
  const d = new Date(iso);
  return d >= weekStart && d <= weekEnd;
};

const activity = {
  commits: collectRecords([{ json: { records: commits } }]).filter((c) =>
    inWeek(c.commit?.author?.date || c.commit?.committer?.date),
  ),
  closedIssues: collectRecords([{ json: { records: issues } }]).filter(
    (i) => inWeek(i.closed_at) && !i.pull_request,
  ),
  mergedPullRequests: collectRecords([{ json: { records: merged } }]).filter((p) => inWeek(p.merged_at)),
};

assert(activity.commits.length === 1, 'integration: commits flow through collectRecords + week filter');
assert(activity.closedIssues.length === 1, 'integration: closed issues exclude pull requests');
assert(activity.mergedPullRequests.length === 1, 'integration: merged PR search results merge into activity');

const buildPrompt = workflow.nodes.find((n) => n.name === 'Build Claude Prompt');
const buildCode = buildPrompt?.parameters?.jsCode || '';
const sandbox = {
  $: (name) => ({
    first: () => ({
      json: {
        owner: 'o',
        repo: 'r',
        repoFullName: 'o/r',
        language: 'EN',
        weekStart: weekStart.toISOString(),
        weekEnd: weekEnd.toISOString(),
        deliveryChannel: 'discord',
        emailFrom: 'n8n@localhost',
        emailTo: '',
      },
    }),
  }),
  console,
};
vm.createContext(sandbox);
try {
  const wrapped = `(async () => {\n${buildCode}\n})()`;
  const result = await vm.runInContext(wrapped, sandbox);
  assert(Array.isArray(result) && result[0]?.json?.claudeRequest, 'integration: Build Claude Prompt emits claudeRequest');
  assert(result[0].json.claudeRequest.model === 'claude-sonnet-4-20250514', 'integration: Claude model matches bounty requirement');
  assert(result[0].json.claudeRequest.messages?.length >= 1, 'integration: Claude request includes user messages');
} catch (error) {
  failures.push(`Build Claude Prompt integration failed: ${error.message}`);
}

const loadConfig = workflow.nodes.find((n) => n.name === 'Load Config');
const loadCode = loadConfig?.parameters?.jsCode || '';
assert(loadCode.includes('validateGitHubToken'), 'integration: Load Config validates token before GitHub fetches');
assert(loadCode.includes('api.github.com/repos/'), 'integration: Load Config validates token against target repo');

const claudeNode = workflow.nodes.find((n) => n.name === 'Claude API');
assert(claudeNode?.parameters?.url === 'https://api.anthropic.com/v1/messages', 'integration: Claude API targets Anthropic messages endpoint');

const routeNode = workflow.nodes.find((n) => n.name === 'Route Delivery');
assert(routeNode?.parameters?.rules?.values?.length === 3, 'integration: Route Delivery exposes discord, slack, and email branches');

if (failures.length) {
  console.error('FAILED workflow integration tests:\n- ' + failures.join('\n- '));
  process.exit(1);
}

console.log('OK: workflow integration tests passed.');
