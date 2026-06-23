#!/usr/bin/env node
/**
 * Unit and integration tests for Discord, Slack, and email delivery paths.
 */
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import {
  buildFormatSummaryPayload,
  postJsonWebhook,
  resolveDeliveryChannel,
} from './lib/delivery.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const workflow = JSON.parse(readFileSync(join(__dirname, '..', 'weekly-dev-summary.json'), 'utf8'));

const failures = [];
function assert(condition, message) {
  if (!condition) failures.push(message);
}

const sampleConfig = {
  repoFullName: 'acme/widget',
  deliveryChannel: 'discord',
  weekStart: '2026-06-08T00:00:00.000Z',
  weekEnd: '2026-06-15T23:59:59.000Z',
  emailFrom: 'n8n@localhost',
  emailTo: 'team@example.com',
};

const sampleStats = { commits: 3, issues: 2, prs: 1, contributors: 2 };
const claudeContent = [{ text: 'Shipped widget v2 with improved caching.' }];

const payload = buildFormatSummaryPayload({
  config: sampleConfig,
  stats: sampleStats,
  claudeContent,
});

assert(payload.discordBody?.content?.includes('Weekly Dev Summary'), 'discord: content includes title');
assert(payload.discordBody.content.includes('Shipped widget v2'), 'discord: content includes Claude summary');
assert(payload.slackBody?.blocks?.length === 3, 'slack: payload has header + two section blocks');
assert(payload.slackBody.blocks[0].type === 'header', 'slack: first block is header');
assert(payload.emailSubject.includes('Weekly Dev Summary'), 'email: subject includes title');
assert(payload.emailText.includes('3 commits'), 'email: body includes stats line');
assert(payload.emailHtml?.includes('<h1>') && payload.emailHtml.includes('Shipped widget v2'), 'email: html includes title and summary');
assert(!payload.emailHtml.includes('<script>'), 'email: html escapes unsafe markup');

const fallback = buildFormatSummaryPayload({
  config: sampleConfig,
  stats: sampleStats,
  apiError: 'rate limit',
});
assert(fallback.summary.includes('Claude API unavailable'), 'delivery: API error falls back to stats-only summary');

assert(resolveDeliveryChannel({ deliveryChannel: 'slack', slackWebhookUrl: 'https://hooks.example/slack' }) === 'slack', 'resolve: explicit slack channel');
assert(resolveDeliveryChannel({ discordWebhookUrl: 'https://hooks.example/discord' }) === 'discord', 'resolve: infers discord from webhook URL');
assert(resolveDeliveryChannel({ emailTo: 'a@b.com' }) === 'email', 'resolve: infers email from SUMMARY_EMAIL_TO');

try {
  resolveDeliveryChannel({ deliveryChannel: 'email', emailTo: 'not-an-email' });
  assert(false, 'resolve: invalid email must throw');
} catch (error) {
  assert(error.message.includes('valid email address'), 'resolve: invalid email error is descriptive');
}

try {
  resolveDeliveryChannel({ deliveryChannel: 'discord' });
  assert(false, 'resolve: discord without webhook must throw');
} catch (error) {
  assert(error.message.includes('DISCORD_WEBHOOK_URL'), 'resolve: discord error mentions webhook');
}

const posted = [];
const mockFetch = async (url, init) => {
  posted.push({ url, body: JSON.parse(init.body) });
  return { ok: true, status: 200, statusText: 'OK' };
};

await postJsonWebhook('https://hooks.example/discord', payload.discordBody, { fetchFn: mockFetch });
assert(posted.length === 1 && posted[0].body.content, 'discord: webhook POST sends content payload');

await postJsonWebhook('https://hooks.example/slack', payload.slackBody, { fetchFn: mockFetch });
assert(posted[1].body.blocks?.length === 3, 'slack: webhook POST sends blocks payload');

try {
  await postJsonWebhook('', payload.discordBody, { fetchFn: mockFetch });
  assert(false, 'webhook: empty URL must throw');
} catch (error) {
  assert(error.message.includes('Webhook URL'), 'webhook: empty URL error is descriptive');
}

const formatNode = workflow.nodes.find((n) => n.name === 'Format Summary');
const formatCode = formatNode?.parameters?.jsCode || '';
const sandbox = {
  $: (name) => ({
    first: () => ({
      json: {
        config: sampleConfig,
        stats: sampleStats,
        claudeRequest: { model: 'claude-sonnet-4-20250514' },
      },
    }),
  }),
  $json: { content: claudeContent },
  console,
};
vm.createContext(sandbox);
try {
  const wrapped = `(async () => {\n${formatCode}\n})()`;
  const result = await vm.runInContext(wrapped, sandbox);
  const row = result?.[0]?.json;
  assert(row?.discordBody?.content && row?.slackBody?.blocks && row?.emailSubject, 'integration: Format Summary node emits all channel payloads');
  assert(row.emailText.includes('Shipped widget v2'), 'integration: Format Summary email text includes summary');
  assert(row.emailHtml?.includes('<h1>') && row.emailHtml.includes('Shipped widget v2'), 'integration: Format Summary email html includes summary');
} catch (error) {
  failures.push(`Format Summary vm integration failed: ${error.message}`);
}

const routeNode = workflow.nodes.find((n) => n.name === 'Route Delivery');
const rules = routeNode?.parameters?.rules?.values || [];
const channels = rules.map((rule) => rule.outputKey);
assert(channels.join(',') === 'discord,slack,email', 'workflow: Route Delivery branches cover discord, slack, email');

for (const [name, envVar, bodyField] of [
  ['Send Discord', '$env.DISCORD_WEBHOOK_URL', 'discordBody'],
  ['Send Slack', '$env.SLACK_WEBHOOK_URL', 'slackBody'],
]) {
  const node = workflow.nodes.find((n) => n.name === name);
  assert(node?.parameters?.method === 'POST', `${name} uses POST`);
  assert(node?.parameters?.url?.includes(envVar), `${name} reads webhook URL from ${envVar}`);
  assert(node?.parameters?.jsonBody?.includes(bodyField), `${name} serializes ${bodyField}`);
}

const sendEmail = workflow.nodes.find((n) => n.name === 'Send Email');
assert(sendEmail?.parameters?.fromEmail?.includes('emailFrom'), 'Send Email resolves sender from Load Config emailFrom');
assert(sendEmail?.parameters?.toEmail?.includes('emailTo'), 'Send Email resolves recipient from Load Config emailTo');
assert(sendEmail?.parameters?.subject?.includes('emailSubject'), 'Send Email uses formatted emailSubject');
assert(sendEmail?.parameters?.text?.includes('emailText'), 'Send Email uses formatted emailText');
assert(sendEmail?.parameters?.html?.includes('emailHtml'), 'Send Email uses formatted emailHtml');

if (failures.length) {
  console.error('FAILED delivery channel tests:\n- ' + failures.join('\n- '));
  process.exit(1);
}

console.log('OK: delivery channel tests passed (Discord, Slack, email).');
