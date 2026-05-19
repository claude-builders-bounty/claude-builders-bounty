const config = $input.first().json;
const DAY_MS = 24 * 60 * 60 * 1000;

const end = new Date();
const start = new Date(end.getTime() - config.lookbackDays * DAY_MS);
const startDate = start.toISOString().slice(0, 10);
const endDate = end.toISOString().slice(0, 10);
const repository = `${config.githubOwner}/${config.githubRepo}`;

function githubUrl(path, params) {
  const query = Object.entries(params)
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
    .join("&");
  return `https://api.github.com${path}?${query}`;
}

return [
  {
    json: {
      ...config,
      repository,
      periodStart: start.toISOString(),
      periodEnd: end.toISOString(),
      periodStartDate: startDate,
      periodEndDate: endDate,
      commitsUrl: githubUrl(`/repos/${repository}/commits`, {
        since: start.toISOString(),
        until: end.toISOString(),
        per_page: 100,
      }),
      closedIssuesUrl: githubUrl("/search/issues", {
        q: `repo:${repository} type:issue is:closed closed:${startDate}..${endDate}`,
        per_page: 50,
      }),
      mergedPullRequestsUrl: githubUrl("/search/issues", {
        q: `repo:${repository} type:pr is:merged merged:${startDate}..${endDate}`,
        per_page: 50,
      }),
    },
  },
];
