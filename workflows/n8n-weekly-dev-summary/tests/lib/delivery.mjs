/**
 * Delivery payload helpers mirrored by Format Summary and webhook nodes.
 * Tests import this module so Discord/Slack/email regressions catch workflow drift.
 */

export const DELIVERY_CHANNELS = ['discord', 'slack', 'email'];

/**
 * Build channel-specific payloads from Claude output (mirrors Format Summary node).
 */
export function buildFormatSummaryPayload({ config, stats, claudeContent = [], apiError = '' }) {
  const statsLine = `${stats.commits} commits · ${stats.issues} issues closed · ${stats.prs} PRs merged · ${stats.contributors} contributors`;
  const summary = apiError
    ? `Claude API unavailable (${apiError}). Stats for the week: ${statsLine}.`
    : (claudeContent.map((part) => part.text || '').join('\n').trim() || 'No summary generated.');

  const title = `Weekly Dev Summary — ${config.repoFullName}`;
  const period = `${config.weekStart.slice(0, 10)} → ${config.weekEnd.slice(0, 10)}`;
  const escapeHtml = (value) => String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');

  return {
    config,
    title,
    period,
    statsLine,
    summary,
    markdown: `# ${title}\n*${period}*\n\n> ${statsLine}\n\n${summary}`,
    discordBody: {
      content: `**${title}**\n*${period}*\n${statsLine}\n\n${summary.slice(0, 1800)}`,
    },
    slackBody: {
      blocks: [
        { type: 'header', text: { type: 'plain_text', text: title } },
        { type: 'section', text: { type: 'mrkdwn', text: `*${period}*\n${statsLine}` } },
        { type: 'section', text: { type: 'mrkdwn', text: summary.slice(0, 2800) } },
      ],
    },
    emailSubject: `${title} (${period})`,
    emailText: `${title}\n${period}\n${statsLine}\n\n${summary}`,
    emailHtml: `<h1>${escapeHtml(title)}</h1><p><em>${escapeHtml(period)}</em></p><p>${escapeHtml(statsLine)}</p><pre style="white-space:pre-wrap;font-family:inherit">${escapeHtml(summary)}</pre>`,
  };
}

/**
 * POST JSON body to a Discord or Slack incoming webhook.
 */
export async function postJsonWebhook(url, body, { fetchFn = fetch } = {}) {
  const trimmed = (url || '').trim();
  if (!trimmed) {
    throw new Error('Webhook URL is required.');
  }

  const res = await fetchFn(trimmed, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    throw new Error(`Webhook POST failed: ${res.status} ${res.statusText || ''}`.trim());
  }

  return res;
}

/**
 * Resolve delivery channel from explicit setting or first configured destination.
 */
export function resolveDeliveryChannel({
  deliveryChannel = '',
  discordWebhookUrl = '',
  slackWebhookUrl = '',
  emailTo = '',
} = {}) {
  let channel = (deliveryChannel || '').trim().toLowerCase();
  if (!channel) {
    if ((discordWebhookUrl || '').trim()) channel = 'discord';
    else if ((slackWebhookUrl || '').trim()) channel = 'slack';
    else if ((emailTo || '').trim()) channel = 'email';
  }

  if (!DELIVERY_CHANNELS.includes(channel)) {
    throw new Error('Set DELIVERY_CHANNEL to discord, slack, or email (and the matching destination variable).');
  }
  if (channel === 'discord' && !(discordWebhookUrl || '').trim()) {
    throw new Error('DELIVERY_CHANNEL=discord requires DISCORD_WEBHOOK_URL.');
  }
  if (channel === 'slack' && !(slackWebhookUrl || '').trim()) {
    throw new Error('DELIVERY_CHANNEL=slack requires SLACK_WEBHOOK_URL.');
  }
  if (channel === 'email' && !(emailTo || '').trim()) {
    throw new Error('DELIVERY_CHANNEL=email requires SUMMARY_EMAIL_TO.');
  }
  if (channel === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test((emailTo || '').trim())) {
    throw new Error('SUMMARY_EMAIL_TO must be a valid email address.');
  }
  const emailFromRaw = (process.env.SUMMARY_EMAIL_FROM || '').trim();
  if (channel === 'email' && emailFromRaw && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailFromRaw)) {
    throw new Error('SUMMARY_EMAIL_FROM must be a valid email address.');
  }

  return channel;
}
