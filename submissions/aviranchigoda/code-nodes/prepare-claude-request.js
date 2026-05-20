function nodeJson(nodeName) {
  const items = $(nodeName).all();

  if (items.length === 0) {
    return null;
  }

  if (items.length === 1) {
    return items[0].json;
  }

  return items.map((item) => item.json);
}

function asArray(value) {
  if (Array.isArray(value)) {
    return value;
  }

  if (value && Array.isArray(value.body)) {
    return value.body;
  }

  if (value && Array.isArray(value.items)) {
    return value.items;
  }

  if (value && value.body && Array.isArray(value.body.items)) {
    return value.body.items;
  }

  if (value && typeof value === "object" && Object.keys(value).every((key) => /^\d+$/.test(key))) {
    return Object.keys(value)
      .sort((a, b) => Number(a) - Number(b))
      .map((key) => value[key]);
  }

  return [];
}

const config = $("Build GitHub API URLs").first().json;
const commits = asArray(nodeJson("GitHub Commits"));
const closedIssues = asArray(nodeJson("GitHub Closed Issues"));
const mergedPullRequests = asArray(nodeJson("GitHub Merged Pull Requests"));

const activity = {
  repository: config.repository,
  period: {
    start: config.periodStart,
    end: config.periodEnd,
  },
  commits: commits.map((commit) => ({
    sha: commit.sha,
    title: commit.commit?.message?.split("\n")[0] || "",
    author: commit.commit?.author?.name || commit.author?.login || "unknown",
    date: commit.commit?.author?.date || commit.commit?.committer?.date || "",
    url: commit.html_url,
  })),
  closedIssues: closedIssues.map((issue) => ({
    number: issue.number,
    title: issue.title,
    author: issue.user?.login || "unknown",
    closedAt: issue.closed_at,
    url: issue.html_url,
  })),
  mergedPullRequests: mergedPullRequests.map((pullRequest) => ({
    number: pullRequest.number,
    title: pullRequest.title,
    author: pullRequest.user?.login || "unknown",
    mergedAt: pullRequest.closed_at,
    url: pullRequest.html_url,
  })),
};

const outputLanguage = config.summaryLanguage === "FR" ? "French" : "English";
const prompt = [
  `Write a weekly engineering narrative summary in ${outputLanguage}.`,
  `Repository: ${config.repository}`,
  `Period: ${config.periodStartDate} through ${config.periodEndDate}`,
  "",
  "Use this structure:",
  "1. Headline",
  "2. What changed",
  "3. Notable issues closed",
  "4. Merged pull requests",
  "5. Suggested follow-ups",
  "",
  "Keep it concise, useful for a development team, and cite issue or PR numbers when present.",
  "",
  "GitHub activity JSON:",
  JSON.stringify(activity, null, 2),
].join("\n");

return [
  {
    json: {
      ...config,
      commitCount: activity.commits.length,
      closedIssueCount: activity.closedIssues.length,
      mergedPullRequestCount: activity.mergedPullRequests.length,
      activity,
      claudeBody: {
        model: "claude-sonnet-4-20250514",
        max_tokens: 1200,
        system: "You write clear weekly software development updates from GitHub activity data.",
        messages: [
          {
            role: "user",
            content: prompt,
          },
        ],
      },
    },
  },
];
