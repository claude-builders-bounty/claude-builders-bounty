const preparedMessage = $("Prepare Slack Message").first().json;

return [
  {
    json: {
      status: "delivered",
      destination: "slack",
      repository: preparedMessage.repository,
      periodStart: preparedMessage.periodStart,
      periodEnd: preparedMessage.periodEnd,
      language: preparedMessage.language,
      commitCount: preparedMessage.commitCount,
      closedIssueCount: preparedMessage.closedIssueCount,
      mergedPullRequestCount: preparedMessage.mergedPullRequestCount,
      slackChannel: preparedMessage.slackChannel,
      summary: preparedMessage.summary,
      deliveredAt: new Date().toISOString(),
    },
  },
];
