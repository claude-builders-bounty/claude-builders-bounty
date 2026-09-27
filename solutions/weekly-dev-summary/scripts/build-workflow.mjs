import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(fileURLToPath(new URL('..', import.meta.url)));
const read = (name) => readFile(resolve(root, name), 'utf8');
const code = Object.fromEntries(await Promise.all([
  'build-settings', 'normalize-commits', 'normalize-issues', 'normalize-pulls',
  'compose-prompt', 'validate-response', 'format-delivery',
].map(async (name) => [name, await read(`src/${name}.js`)])));
const activityPages = await read('src/activity-pages.js');
for (const name of ['normalize-commits', 'normalize-issues', 'normalize-pulls']) {
  code[name] = `${activityPages}\n${code[name]}`;
}
const nextLink = '/<([^>]+)>;\\s*rel="next"/.exec($response.headers.link || "")?.[1]';
const paginationOptions = (pulls = false) => ({
  response: { response: { responseFormat: 'json', fullResponse: true } },
  pagination: { pagination: {
    paginationMode: 'responseContainsNextURL',
    nextURL: `={{ ${nextLink} || '' }}`,
    paginationCompleteWhen: 'other',
    completeExpression: `={{ !(${nextLink})${pulls ? ' || $response.body.some(row => Date.parse(row.updated_at) < Date.parse($("Build Settings").first().json.since))' : ''} }}`,
    limitPagesFetched: false,
    requestInterval: 1000,
  } },
});
const id = (name) => name.toLowerCase().replace(/[^a-z0-9]+/g, '-');
const node = (name, type, typeVersion, position, parameters) => ({
  id: id(name), name, type, typeVersion, position, parameters,
});
const set = (name, value) => ({
  id: id(name), name, type: 'n8n-nodes-base.set', typeVersion: 3.4, position: [420, 320],
  parameters: { mode: 'manual', duplicateItem: false, assignments: { assignments: [
    { id: 'repo', name: 'repo', type: 'string', value: 'owner/repository' },
    { id: 'language', name: 'language', type: 'string', value: 'en' },
    { id: 'destinationType', name: 'destinationType', type: 'string', value: 'discord' },
    { id: 'webhookUrl', name: 'webhookUrl', type: 'string', value: 'https://discord.com/api/webhooks/REPLACE_ME' },
    { id: 'sendDelivery', name: 'sendDelivery', type: 'boolean', value: false },
  ] } },
});

const nodes = [
  node('Weekly Schedule', 'n8n-nodes-base.scheduleTrigger', 1.2, [180, 180], {
    rule: { interval: [{ field: 'weeks', weeksInterval: 1, triggerAtDay: [5], triggerAtHour: 17 }] },
  }),
  node('Run Manually', 'n8n-nodes-base.manualTrigger', 1, [180, 460], {}),
  set('Set Options', null),
  node('Build Settings', 'n8n-nodes-base.code', 2, [640, 320], { mode: 'runOnceForAllItems', jsCode: code['build-settings'] }),
  node('Get Commits', 'n8n-nodes-base.httpRequest', 4.2, [880, 100], {
    url: '=https://api.github.com/repos/{{$json.repo}}/commits?since={{$json.since}}&until={{$json.until}}&per_page=100',
    sendHeaders: true, headerParameters: { parameters: [{ name: 'Accept', value: 'application/vnd.github+json' }, { name: 'X-GitHub-Api-Version', value: '2022-11-28' }] },
    options: paginationOptions(),
  }),
  node('Get Closed Issues', 'n8n-nodes-base.httpRequest', 4.2, [880, 280], {
    url: '=https://api.github.com/repos/{{$json.repo}}/issues?state=closed&since={{$json.since}}&per_page=100',
    sendHeaders: true, headerParameters: { parameters: [{ name: 'Accept', value: 'application/vnd.github+json' }, { name: 'X-GitHub-Api-Version', value: '2022-11-28' }] },
    options: paginationOptions(),
  }),
  node('Get Pull Requests', 'n8n-nodes-base.httpRequest', 4.2, [880, 460], {
    url: '=https://api.github.com/repos/{{$json.repo}}/pulls?state=closed&sort=updated&direction=desc&per_page=100',
    sendHeaders: true, headerParameters: { parameters: [{ name: 'Accept', value: 'application/vnd.github+json' }, { name: 'X-GitHub-Api-Version', value: '2022-11-28' }] },
    options: paginationOptions(true),
  }),
  node('Normalize Commits', 'n8n-nodes-base.code', 2, [1120, 100], { mode: 'runOnceForAllItems', jsCode: code['normalize-commits'] }),
  node('Normalize Issues', 'n8n-nodes-base.code', 2, [1120, 280], { mode: 'runOnceForAllItems', jsCode: code['normalize-issues'] }),
  node('Normalize Pull Requests', 'n8n-nodes-base.code', 2, [1120, 460], { mode: 'runOnceForAllItems', jsCode: code['normalize-pulls'] }),
  node('Join Commits and Issues', 'n8n-nodes-base.merge', 3.2, [1360, 180], { mode: 'append', numberInputs: 2 }),
  node('Join All Activity', 'n8n-nodes-base.merge', 3.2, [1540, 320], { mode: 'append', numberInputs: 2 }),
  node('Compose Summary Prompt', 'n8n-nodes-base.code', 2, [1720, 320], { mode: 'runOnceForAllItems', jsCode: code['compose-prompt'] }),
  node('Call Claude API', 'n8n-nodes-base.httpRequest', 4.2, [1940, 320], {
    method: 'POST', url: 'https://api.anthropic.com/v1/messages',
    authentication: 'predefinedCredentialType', nodeCredentialType: 'anthropicApi',
    sendHeaders: true,
    headerParameters: { parameters: [{ name: 'anthropic-version', value: '2023-06-01' }] },
    sendBody: true, contentType: 'json', specifyBody: 'json', jsonBody: '={{$json.requestBody}}',
    options: { timeout: 120000, response: { response: { responseFormat: 'json', fullResponse: true } } },
  }),
  node('Validate Claude Response', 'n8n-nodes-base.code', 2, [2160, 320], { mode: 'runOnceForAllItems', jsCode: code['validate-response'] }),
  node('Prepare Delivery', 'n8n-nodes-base.code', 2, [2380, 320], { mode: 'runOnceForAllItems', jsCode: code['format-delivery'] }),
  node('Send Delivery?', 'n8n-nodes-base.if', 2.2, [2600, 320], {
    conditions: { options: { caseSensitive: true, leftValue: '', typeValidation: 'strict', version: 2 }, conditions: [{ id: 'send-delivery', leftValue: '={{$json.sendDelivery}}', rightValue: true, operator: { type: 'boolean', operation: 'equals' } }], combinator: 'and' },
    options: {},
  }),
  node('Post to Webhook', 'n8n-nodes-base.httpRequest', 4.2, [2820, 220], {
    method: 'POST', url: '={{$json.webhookUrl}}', sendBody: true, contentType: 'json', specifyBody: 'json', jsonBody: '={{$json.body}}',
    options: { response: { response: { responseFormat: 'json' } } },
  }),
];

const connections = {
  'Weekly Schedule': { main: [[{ node: 'Set Options', type: 'main', index: 0 }]] },
  'Run Manually': { main: [[{ node: 'Set Options', type: 'main', index: 0 }]] },
  'Set Options': { main: [[{ node: 'Build Settings', type: 'main', index: 0 }]] },
  'Build Settings': { main: [[
    { node: 'Get Commits', type: 'main', index: 0 },
    { node: 'Get Closed Issues', type: 'main', index: 0 },
    { node: 'Get Pull Requests', type: 'main', index: 0 },
  ]] },
  'Get Commits': { main: [[{ node: 'Normalize Commits', type: 'main', index: 0 }]] },
  'Get Closed Issues': { main: [[{ node: 'Normalize Issues', type: 'main', index: 0 }]] },
  'Get Pull Requests': { main: [[{ node: 'Normalize Pull Requests', type: 'main', index: 0 }]] },
  'Normalize Commits': { main: [[{ node: 'Join Commits and Issues', type: 'main', index: 0 }]] },
  'Normalize Issues': { main: [[{ node: 'Join Commits and Issues', type: 'main', index: 1 }]] },
  'Join Commits and Issues': { main: [[{ node: 'Join All Activity', type: 'main', index: 0 }]] },
  'Normalize Pull Requests': { main: [[{ node: 'Join All Activity', type: 'main', index: 1 }]] },
  'Join All Activity': { main: [[{ node: 'Compose Summary Prompt', type: 'main', index: 0 }]] },
  'Compose Summary Prompt': { main: [[{ node: 'Call Claude API', type: 'main', index: 0 }]] },
  'Call Claude API': { main: [[{ node: 'Validate Claude Response', type: 'main', index: 0 }]] },
  'Validate Claude Response': { main: [[{ node: 'Prepare Delivery', type: 'main', index: 0 }]] },
  'Prepare Delivery': { main: [[{ node: 'Send Delivery?', type: 'main', index: 0 }]] },
  'Send Delivery?': { main: [[{ node: 'Post to Webhook', type: 'main', index: 0 }], []] },
};

const workflow = {
  id: 'bounty5weeklydev01',
  name: 'Weekly GitHub Development Summary',
  nodes,
  connections,
  settings: { executionOrder: 'v1', timezone: 'UTC' },
  pinData: {},
  active: false,
};
const target = resolve(root, 'workflow.json');
await mkdir(root, { recursive: true });
await writeFile(target, `${JSON.stringify(workflow, null, 2)}\n`);
console.log(`Wrote ${target}`);
