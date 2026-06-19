#!/usr/bin/env node
/**
 * Tests for Claude Sonnet 4 narrative summary nodes (Build Claude Prompt, Claude API, Format Summary).
 */
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { buildFormatSummaryPayload } from './lib/delivery.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const workflow = JSON.parse(readFileSync(join(__dirname, '..', 'weekly-dev-summary.json'), 'utf8'));

const failures = [];
function assert(condition, message) {
  if (!condition) failures.push(message);
}

const weekStart = new Date('2026-06-08T00:00:00Z');
const weekEnd = new Date('2026-06-15T23:59:59Z');

const sampleConfig = {
  owner: 'acme',
  repo: 'widget',
  repoFullName: 'acme/widget',
  language: 'EN',
  weekStart: weekStart.toISOString(),
  weekEnd: weekEnd.toISOString(),
  deliveryChannel: 'discord',
  emailFrom: 'n8n@localhost',
  emailTo: '',
};

const sampleRecords = {
  'Fetch Commits': {
    records: [{
      sha: 'abc1234',
      commit: {
        message: 'feat: ship cache layer',
        author: { date: '2026-06-10T12:00:00Z', name: 'dev' },
      },
      author: { login: 'dev' },
    }],
  },
  'Fetch Closed Issues': {
    records: [{
      number: 12,
      title: 'Fix login timeout',
      closed_at: '2026-06-11T12:00:00Z',
    }],
  },
  'Fetch Merged PRs': {
    records: [{
      number: 34,
      title: 'Add metrics dashboard',
      merged_at: '2026-06-12T12:00:00Z',
      user: { login: 'dev' },
    }],
  },
};

function runBuildPrompt(language = 'EN') {
  const buildPrompt = workflow.nodes.find((n) => n.name === 'Build Claude Prompt');
  const buildCode = buildPrompt?.parameters?.jsCode || '';
  const config = { ...sampleConfig, language };
  const sandbox = {
    $: (name) => ({
      first: () => {
        if (name === 'Load Config') return { json: config };
        const item = sampleRecords[name];
        if (!item) throw new Error(`Missing output from ${name}`);
        return { json: item };
      },
    }),
    console,
  };
  vm.createContext(sandbox);
  const wrapped = `(async () => {\n${buildCode}\n})()`;
  return vm.runInContext(wrapped, sandbox);
}

const buildPrompt = workflow.nodes.find((n) => n.name === 'Build Claude Prompt');
const buildCode = buildPrompt?.parameters?.jsCode || '';
assert(buildPrompt?.parameters?.mode === 'runOnceForAllItems', 'Claude summary: Build Claude Prompt runs once after merge');
assert(buildCode.includes('claude-sonnet-4-20250514'), 'Claude summary: prompt builder targets Claude Sonnet 4 model');
assert(
  buildCode.includes('You summarize GitHub development activity'),
  'Claude summary: system prompt requests accurate narrative summary',
);

try {
  const enResult = await runBuildPrompt('EN');
  const request = enResult?.[0]?.json?.claudeRequest;
  assert(request?.model === 'claude-sonnet-4-20250514', 'Claude summary: EN request uses claude-sonnet-4-20250514');
  assert(
    request?.system?.includes('You summarize GitHub development activity'),
    'Claude summary: EN system prompt guides narrative generation',
  );
  assert(
    request?.messages?.[0]?.content?.includes('feat: ship cache layer'),
    'Claude summary: activity JSON includes commit messages',
  );
  assert(
    request?.messages?.[0]?.content?.includes('Fix login timeout'),
    'Claude summary: activity JSON includes closed issues',
  );
  assert(enResult[0].json.stats.commits === 1, 'Claude summary: stats count commits for narrative context');
} catch (error) {
  failures.push(`Claude summary EN build failed: ${error.message}`);
}

try {
  const frResult = await runBuildPrompt('FR');
  const frRequest = frResult?.[0]?.json?.claudeRequest;
  assert(frRequest?.system?.includes('résumez l'), 'Claude summary: FR system prompt is localized');
  assert(frRequest?.messages?.[0]?.content?.includes('Rédigez un résumé'), 'Claude summary: FR user instructions are localized');
} catch (error) {
  failures.push(`Claude summary FR build failed: ${error.message}`);
}

const claudeNode = workflow.nodes.find((n) => n.name === 'Claude API');
assert(claudeNode?.parameters?.url === 'https://api.anthropic.com/v1/messages', 'Claude summary: Claude API posts to Anthropic messages endpoint');
assert(
  claudeNode?.parameters?.headerParameters?.parameters?.some(
    (h) => h.name === 'x-api-key' && h.value?.includes('$env.ANTHROPIC_API_KEY'),
  ),
  'Claude summary: Claude API reads ANTHROPIC_API_KEY from $env only',
);
assert(claudeNode?.parameters?.jsonBody?.includes('claudeRequest'), 'Claude summary: Claude API serializes Build Claude Prompt payload');
assert(claudeNode?.onError === 'continueRegularOutput', 'Claude summary: Claude API continues on transient failures');

const narrative = buildFormatSummaryPayload({
  config: {
    repoFullName: 'acme/widget',
    weekStart: weekStart.toISOString(),
    weekEnd: weekEnd.toISOString(),
  },
  stats: { commits: 3, issues: 2, prs: 1, contributors: 2 },
  claudeContent: [{ text: 'Shipped widget v2 with improved caching and observability.' }],
});
assert(
  narrative.summary.includes('Shipped widget v2'),
  'Claude summary: Format Summary path preserves Claude narrative text',
);
assert(narrative.markdown.includes('3 commits'), 'Claude summary: markdown output includes contributor stats line');

const formatNode = workflow.nodes.find((n) => n.name === 'Format Summary');
const formatCode = formatNode?.parameters?.jsCode || '';
const formatSandbox = {
  $: (name) => ({
    first: () => ({
      json: {
        config: sampleConfig,
        stats: { commits: 1, issues: 1, prs: 1, contributors: 1 },
        claudeRequest: { model: 'claude-sonnet-4-20250514' },
      },
    }),
  }),
  $json: { content: [{ text: 'Weekly narrative: caching layer and dashboard shipped.' }] },
  console,
};
vm.createContext(formatSandbox);
try {
  const formatResult = await vm.runInContext(`(async () => {\n${formatCode}\n})()`, formatSandbox);
  const row = formatResult?.[0]?.json;
  assert(row?.summary?.includes('Weekly narrative'), 'Claude summary: Format Summary node extracts Claude narrative');
  assert(row?.markdown?.includes('Weekly Dev Summary'), 'Claude summary: Format Summary builds markdown delivery payload');
} catch (error) {
  failures.push(`Claude summary Format Summary vm failed: ${error.message}`);
}

if (failures.length) {
  console.error('FAILED Claude Sonnet 4 summary tests:\n- ' + failures.join('\n- '));
  process.exit(1);
}

console.log('OK: Claude Sonnet 4 summary tests passed.');
