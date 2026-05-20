const preparedMessage = $("Prepare Slack Message").first().json;
const slackResponse = $("Send Slack Summary").first().json;
const slackStatusCode = Number(slackResponse.statusCode ?? slackResponse.status ?? 0);
const slackResponseBody = String(slackResponse.body ?? slackResponse.data ?? "").trim();

if (!Number.isInteger(slackStatusCode) || slackStatusCode < 200 || slackStatusCode >= 300) {
  throw new Error(`Slack webhook returned unexpected status code: ${slackStatusCode || "missing"}.`);
}

if (slackResponseBody && slackResponseBody !== "ok") {
  throw new Error(`Slack webhook returned unexpected body: ${slackResponseBody}.`);
}

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
      slackStatusCode,
      slackResponseBody: slackResponseBody || "empty",
      summary: preparedMessage.summary,
      deliveredAt: new Date().toISOString(),
    },
  },
];
