#!/usr/bin/env node
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));

const setConfigCode = String.raw`// Edit these workflow variables before switching dryRun to false.
const config = {
  repo: "claude-builders-bounty/claude-builders-bounty",
  language: "EN",
  destinationChannel: "discord-dev-summary",
  discordWebhookUrl: "",
  githubToken: "",
  anthropicApiKey: "",
  dryRun: true
};

const now = new Date();
const until = now.toISOString();
const since = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString();

const repo = config.repo.trim();
const [repoOwner, repoName] = repo.split("/");

if (!repoOwner || !repoName) {
  throw new Error("repo must use owner/repo format.");
}

const language = (config.language.toUpperCase() === "FR") ? "FR" : "EN";

return [{
  json: {
    repo,
    repoOwner,
    repoName,
    since,
    until,
    language,
    dryRun: Boolean(config.dryRun),
    destinationChannel: config.destinationChannel,
    discordWebhookUrl: config.discordWebhookUrl,
    githubToken: config.githubToken,
    anthropicApiKey: config.anthropicApiKey
  }
}];`;

const aggregateActivityCode = String.raw`const config = $("Set Config").first().json;

function responseBody(nodeName) {
  return $items(nodeName).flatMap((item) => {
    const json = item.json;
    if (Array.isArray(json.body)) return json.body;
    if (Array.isArray(json.data)) return json.data;
    if (Array.isArray(json)) return json;
    return [];
  });
}

function inWindow(value) {
  if (!value) return false;
  const time = new Date(value).getTime();
  return time >= new Date(config.since).getTime() && time <= new Date(config.until).getTime();
}

const commits = responseBody("GitHub - Commits").map((commit) => ({
  sha: commit.sha,
  message: commit.commit?.message?.split("\n")[0] || "",
  author: commit.commit?.author?.name || commit.author?.login || "unknown",
  date: commit.commit?.author?.date || commit.commit?.committer?.date,
  url: commit.html_url
}));

const closedIssues = responseBody("GitHub - Closed Issues")
  .filter((issue) => !issue.pull_request && inWindow(issue.closed_at))
  .map((issue) => ({
    number: issue.number,
    title: issue.title,
    closedAt: issue.closed_at,
    author: issue.user?.login || "unknown",
    url: issue.html_url
  }));

const mergedPullRequests = responseBody("GitHub - Merged PRs")
  .filter((pr) => pr.merged_at && inWindow(pr.merged_at))
  .map((pr) => ({
    number: pr.number,
    title: pr.title,
    mergedAt: pr.merged_at,
    author: pr.user?.login || "unknown",
    url: pr.html_url
  }));

const activity = {
  commits,
  closedIssues,
  mergedPullRequests,
  metrics: {
    commitCount: commits.length,
    closedIssueCount: closedIssues.length,
    mergedPullRequestCount: mergedPullRequests.length
  }
};

return [{
  json: {
    ...config,
    activity
  }
}];`;

const buildClaudeRequestCode = String.raw`const data = $input.first().json;
const languageName = data.language === "FR" ? "French" : "English";

const prompt = [
  "Repository: " + data.repo,
  "Window: " + data.since + " to " + data.until,
  "Language: " + languageName,
  "",
  "Activity JSON:",
  JSON.stringify(data.activity, null, 2),
  "",
  "Write a weekly narrative development summary for humans.",
  "Mention the week's main themes, notable shipped work, operational risks, and next-week follow-ups.",
  "Keep it concise, useful, and non-hypey."
].join("\n");

return [{
  json: {
    ...data,
    claudeRequest: {
      model: "claude-sonnet-4-20250514",
      max_tokens: 1200,
      system: "You write concise weekly engineering summaries from GitHub activity. Return Markdown only.",
      messages: [
        {
          role: "user",
          content: prompt
        }
      ]
    }
  }
}];`;

const formatDiscordPayloadCode = String.raw`const data = $("Build Claude Request").first().json;
const response = $input.first().json;
const body = response.body || response;

let summary;
if (data.dryRun) {
  summary = [
    "## Weekly dev summary (dry run)",
    "",
    "**Repository:** " + data.repo,
    "**Window:** " + data.since.slice(0, 10) + " to " + data.until.slice(0, 10),
    "",
    "- Commits: " + data.activity.metrics.commitCount,
    "- Closed issues: " + data.activity.metrics.closedIssueCount,
    "- Merged PRs: " + data.activity.metrics.mergedPullRequestCount,
    "",
    "Production mode sends the same activity payload to Claude using claude-sonnet-4-20250514."
  ].join("\n");
} else {
  summary = body.content?.find((part) => part.type === "text")?.text || body.content?.[0]?.text;
  if (!summary) {
    throw new Error("Claude API response did not contain a text summary.");
  }
}

const content = [
  "**Weekly dev summary for " + data.repo + "**",
  "",
  summary
].join("\n").slice(0, 1900);

return [{
  json: {
    ...data,
    summary,
    discordPayload: {
      content,
      allowed_mentions: {
        parse: []
      }
    }
  }
}];`;

const executionSummaryCode = String.raw`const data = $("Format Discord Payload").first().json;
const response = $input.first().json;

return [{
  json: {
    ok: true,
    dryRun: data.dryRun,
    repo: data.repo,
    language: data.language,
    destinationChannel: data.destinationChannel,
    delivery: data.dryRun ? "Postman Echo dry run" : "Discord webhook",
    deliveryStatusCode: response.statusCode || 200,
    metrics: data.activity.metrics,
    summaryPreview: data.summary.slice(0, 500)
  }
}];`;

const jsonResponseOptions = (timeout) => ({
  response: {
    response: {
      responseFormat: "json",
      fullResponse: true
    }
  },
  timeout
});

const paginatedJsonResponseOptions = (timeout, maxRequests = 10) => ({
  ...jsonResponseOptions(timeout),
  pagination: {
    pagination: {
      paginationMode: "updateAParameterInEachRequest",
      parameters: {
        parameters: [
          {
            type: "qs",
            name: "page",
            value: "={{ $pageCount + 1 }}"
          }
        ]
      },
      paginationCompleteWhen: "other",
      completeExpression: "={{ Array.isArray($response.body) && $response.body.length < 100 }}",
      limitPagesFetched: true,
      maxRequests,
      requestInterval: 250
    }
  }
});

const githubHeadersJson =
  "={{ JSON.stringify({ Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', ...($('Set Config').first().json.githubToken ? { Authorization: 'Bearer ' + $('Set Config').first().json.githubToken } : {}) }) }}";

const workflow = {
  id: "weekly-github-dev-summary-claude",
  name: "Weekly GitHub Dev Summary with Claude",
  active: false,
  nodes: [
    {
      parameters: {},
      id: "manual-trigger",
      name: "Manual Test Trigger",
      type: "n8n-nodes-base.manualTrigger",
      typeVersion: 1,
      position: [-980, 160]
    },
    {
      parameters: {
        rule: {
          interval: [
            {
              field: "weeks",
              triggerAtDay: [5],
              triggerAtHour: 17,
              triggerAtMinute: 0
            }
          ]
        }
      },
      id: "weekly-schedule",
      name: "Weekly Friday 5pm",
      type: "n8n-nodes-base.scheduleTrigger",
      typeVersion: 1.2,
      position: [-980, -20]
    },
    {
      parameters: {
        jsCode: setConfigCode
      },
      id: "set-config",
      name: "Set Config",
      type: "n8n-nodes-base.code",
      typeVersion: 2,
      position: [-720, 80]
    },
    {
      parameters: {
        url: "=https://api.github.com/repos/{{ $json.repoOwner }}/{{ $json.repoName }}/commits",
        sendQuery: true,
        queryParameters: {
          parameters: [
            { name: "since", value: "={{ $json.since }}" },
            { name: "until", value: "={{ $json.until }}" },
            { name: "per_page", value: "100" }
          ]
        },
        sendHeaders: true,
        specifyHeaders: "json",
        jsonHeaders: githubHeadersJson,
        options: paginatedJsonResponseOptions(30000)
      },
      id: "github-commits",
      name: "GitHub - Commits",
      type: "n8n-nodes-base.httpRequest",
      typeVersion: 4.2,
      executeOnce: true,
      position: [-440, 80]
    },
    {
      parameters: {
        url: "=https://api.github.com/repos/{{ $('Set Config').first().json.repoOwner }}/{{ $('Set Config').first().json.repoName }}/issues",
        sendQuery: true,
        queryParameters: {
          parameters: [
            { name: "state", value: "closed" },
            { name: "since", value: "={{ $('Set Config').first().json.since }}" },
            { name: "per_page", value: "100" }
          ]
        },
        sendHeaders: true,
        specifyHeaders: "json",
        jsonHeaders: githubHeadersJson,
        options: paginatedJsonResponseOptions(30000)
      },
      id: "github-closed-issues",
      name: "GitHub - Closed Issues",
      type: "n8n-nodes-base.httpRequest",
      typeVersion: 4.2,
      executeOnce: true,
      position: [-160, 80]
    },
    {
      parameters: {
        url: "=https://api.github.com/repos/{{ $('Set Config').first().json.repoOwner }}/{{ $('Set Config').first().json.repoName }}/pulls",
        sendQuery: true,
        queryParameters: {
          parameters: [
            { name: "state", value: "closed" },
            { name: "sort", value: "updated" },
            { name: "direction", value: "desc" },
            { name: "per_page", value: "100" }
          ]
        },
        sendHeaders: true,
        specifyHeaders: "json",
        jsonHeaders: githubHeadersJson,
        options: paginatedJsonResponseOptions(30000)
      },
      id: "github-merged-prs",
      name: "GitHub - Merged PRs",
      type: "n8n-nodes-base.httpRequest",
      typeVersion: 4.2,
      executeOnce: true,
      position: [120, 80]
    },
    {
      parameters: {
        jsCode: aggregateActivityCode
      },
      id: "aggregate-activity",
      name: "Aggregate Weekly Activity",
      type: "n8n-nodes-base.code",
      typeVersion: 2,
      position: [400, 80]
    },
    {
      parameters: {
        jsCode: buildClaudeRequestCode
      },
      id: "build-claude-request",
      name: "Build Claude Request",
      type: "n8n-nodes-base.code",
      typeVersion: 2,
      position: [680, 80]
    },
    {
      parameters: {
        method: "POST",
        url: "={{ $json.dryRun ? 'https://postman-echo.com/post' : 'https://api.anthropic.com/v1/messages' }}",
        sendHeaders: true,
        headerParameters: {
          parameters: [
            { name: "Content-Type", value: "application/json" },
            { name: "anthropic-version", value: "2023-06-01" },
            { name: "x-api-key", value: "={{ $json.anthropicApiKey }}" }
          ]
        },
        sendBody: true,
        specifyBody: "json",
        jsonBody: "={{ JSON.stringify($json.dryRun ? { dryRun: true, model: $json.claudeRequest.model, promptPreview: $json.claudeRequest.messages[0].content.slice(0, 500) } : $json.claudeRequest) }}",
        options: jsonResponseOptions(60000)
      },
      id: "call-claude-api",
      name: "Claude API - Generate Summary",
      type: "n8n-nodes-base.httpRequest",
      typeVersion: 4.2,
      position: [960, 80]
    },
    {
      parameters: {
        jsCode: formatDiscordPayloadCode
      },
      id: "format-discord-payload",
      name: "Format Discord Payload",
      type: "n8n-nodes-base.code",
      typeVersion: 2,
      position: [1240, 80]
    },
    {
      parameters: {
        method: "POST",
        url: "={{ $json.dryRun ? 'https://postman-echo.com/post' : $json.discordWebhookUrl }}",
        sendHeaders: true,
        headerParameters: {
          parameters: [
            { name: "Content-Type", value: "application/json" }
          ]
        },
        sendBody: true,
        specifyBody: "json",
        jsonBody: "={{ JSON.stringify($json.discordPayload) }}",
        options: jsonResponseOptions(30000)
      },
      id: "send-discord-webhook",
      name: "Discord Webhook - Deliver Summary",
      type: "n8n-nodes-base.httpRequest",
      typeVersion: 4.2,
      position: [1520, 80]
    },
    {
      parameters: {
        jsCode: executionSummaryCode
      },
      id: "execution-summary",
      name: "Execution Summary",
      type: "n8n-nodes-base.code",
      typeVersion: 2,
      position: [1800, 80]
    }
  ],
  connections: {
    "Manual Test Trigger": {
      main: [[{ node: "Set Config", type: "main", index: 0 }]]
    },
    "Weekly Friday 5pm": {
      main: [[{ node: "Set Config", type: "main", index: 0 }]]
    },
    "Set Config": {
      main: [[{ node: "GitHub - Commits", type: "main", index: 0 }]]
    },
    "GitHub - Commits": {
      main: [[{ node: "GitHub - Closed Issues", type: "main", index: 0 }]]
    },
    "GitHub - Closed Issues": {
      main: [[{ node: "GitHub - Merged PRs", type: "main", index: 0 }]]
    },
    "GitHub - Merged PRs": {
      main: [[{ node: "Aggregate Weekly Activity", type: "main", index: 0 }]]
    },
    "Aggregate Weekly Activity": {
      main: [[{ node: "Build Claude Request", type: "main", index: 0 }]]
    },
    "Build Claude Request": {
      main: [[{ node: "Claude API - Generate Summary", type: "main", index: 0 }]]
    },
    "Claude API - Generate Summary": {
      main: [[{ node: "Format Discord Payload", type: "main", index: 0 }]]
    },
    "Format Discord Payload": {
      main: [[{ node: "Discord Webhook - Deliver Summary", type: "main", index: 0 }]]
    },
    "Discord Webhook - Deliver Summary": {
      main: [[{ node: "Execution Summary", type: "main", index: 0 }]]
    }
  },
  settings: {
    timezone: "Africa/Johannesburg",
    executionOrder: "v1"
  },
  staticData: null,
  pinData: {},
  tags: []
};

writeFileSync(
  join(__dirname, "weekly-dev-summary.workflow.json"),
  JSON.stringify(workflow, null, 2) + "\n",
  "utf8"
);

console.log("Wrote weekly-dev-summary.workflow.json");
