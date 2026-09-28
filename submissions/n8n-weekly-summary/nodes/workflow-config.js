// =========================================================================
// ⚙️ WORKFLOW CONFIGURATION & TIME WINDOW CALCULATION
// =========================================================================
// Easily configure repository targets, language, delivery channels, and model.

const input = $input.first()?.json || {};

const config = {
  // Target GitHub repository (owner / repo)
  githubOwner: input.githubOwner || 'claude-builders-bounty',
  githubRepo: input.githubRepo || 'claude-builders-bounty',

  // GitHub Personal Access Token (Optional: elevates rate limit from 60 to 5,000 req/hr)
  githubToken: input.githubToken || '',

  // Language for the summary narrative: 'EN' (English) or 'FR' (French)
  language: (input.language || 'EN').toUpperCase(),

  // Lookback window in days (default: 7 for a weekly summary)
  lookbackDays: Number(input.lookbackDays) || 7,

  // Claude API Model (specified in bounty issue: claude-sonnet-4-20250514)
  claudeModel: input.claudeModel || 'claude-sonnet-4-20250514',

  // Anthropic Claude API Key (sk-ant-...)
  anthropicApiKey: input.anthropicApiKey || '',

  // Delivery destination channel: 'discord', 'slack', 'both', or 'dry-run'
  deliveryChannel: (input.deliveryChannel || 'both').toLowerCase(),

  // Webhook URLs (paste your Discord / Slack incoming webhook URLs)
  discordWebhookUrl: input.discordWebhookUrl || '',
  slackWebhookUrl: input.slackWebhookUrl || '',

  // Optional email recipient
  emailRecipient: input.emailRecipient || 'dev-team@example.com'
};

// Compute dynamic 7-day lookback window in UTC
const now = new Date();
const sinceDate = new Date(now.getTime() - config.lookbackDays * 24 * 60 * 60 * 1000);
const sinceISO = sinceDate.toISOString();
const untilISO = now.toISOString();

// Format human-friendly date ranges
const dateOptions = { year: 'numeric', month: 'short', day: 'numeric', timeZone: 'UTC' };
const sinceFormatted = sinceDate.toLocaleDateString(config.language === 'FR' ? 'fr-FR' : 'en-US', dateOptions);
const untilFormatted = now.toLocaleDateString(config.language === 'FR' ? 'fr-FR' : 'en-US', dateOptions);

return [{
  json: {
    ...config,
    sinceISO,
    untilISO,
    sinceFormatted,
    untilFormatted,
    repoFullName: `${config.githubOwner}/${config.githubRepo}`
  }
}];
