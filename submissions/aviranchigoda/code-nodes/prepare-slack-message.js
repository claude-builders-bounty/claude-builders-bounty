const config = $("Prepare Claude Request").first().json;
const claudeResponse = $("Claude Summary").first().json;

const summary = (claudeResponse.content || [])
  .filter((part) => part.type === "text")
  .map((part) => part.text)
  .join("\n")
  .trim();

if (!summary) {
  throw new Error("Claude API returned no text summary.");
}

const slackPayload = {
  text: summary,
  mrkdwn: true,
};

if (config.slackChannel) {
  slackPayload.channel = config.slackChannel;
}

return [
  {
    json: {
      repository: config.repository,
      periodStart: config.periodStart,
      periodEnd: config.periodEnd,
      language: config.summaryLanguage,
      commitCount: config.commitCount,
      closedIssueCount: config.closedIssueCount,
      mergedPullRequestCount: config.mergedPullRequestCount,
      slackWebhookUrl: config.slackWebhookUrl,
      slackChannel: config.slackChannel || "webhook default",
      slackPayload,
      summary,
      generatedAt: new Date().toISOString(),
    },
  },
];
