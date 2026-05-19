const config = {
  githubOwner: "claude-builders-bounty",
  githubRepo: "claude-builders-bounty",
  summaryLanguage: "EN",
  lookbackDays: 7,
  anthropicApiKey: "REPLACE_ME_ANTHROPIC_API_KEY",
  slackWebhookUrl: "https://hooks.slack.com/services/REPLACE_ME",
  slackChannel: "",
};

function requireConfigured(value, name) {
  if (!value || String(value).includes("REPLACE_ME")) {
    throw new Error(`${name} must be configured before running the workflow.`);
  }
}

if (!["EN", "FR"].includes(config.summaryLanguage)) {
  throw new Error("summaryLanguage must be EN or FR.");
}

if (!Number.isFinite(config.lookbackDays) || config.lookbackDays < 1 || config.lookbackDays > 31) {
  throw new Error("lookbackDays must be a number from 1 to 31.");
}

requireConfigured(config.githubOwner, "githubOwner");
requireConfigured(config.githubRepo, "githubRepo");
requireConfigured(config.anthropicApiKey, "anthropicApiKey");
requireConfigured(config.slackWebhookUrl, "slackWebhookUrl");

return [{ json: config }];
