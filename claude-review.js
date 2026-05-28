#!/usr/bin/env node

const fs = require("fs");
const https = require("https");
const path = require("path");

const VERSION = "1.0.0";
const USER_AGENT = `claude-pr-review-agent/${VERSION}`;

function printHelp() {
  console.log(`Claude PR Review Agent

Usage:
  node claude-review.js --pr https://github.com/owner/repo/pull/123

Options:
  --pr <url>          GitHub pull request URL to review
  --token <token>    GitHub token. Defaults to GITHUB_TOKEN
  --output <file>    Write Markdown review to a file instead of stdout
  --diff-file <file> Analyze a local unified diff for offline testing
  --help             Show this help message
`);
}

function parseArgs(argv) {
  const args = {};

  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];

    if (arg === "--help" || arg === "-h") {
      args.help = true;
      continue;
    }

    if (!arg.startsWith("--")) {
      throw new Error(`Unexpected argument: ${arg}`);
    }

    const key = arg.slice(2);
    const value = argv[i + 1];
    if (!value || value.startsWith("--")) {
      throw new Error(`Missing value for --${key}`);
    }

    args[key] = value;
    i += 1;
  }

  return args;
}

function parsePullRequestUrl(input) {
  let parsed;

  try {
    parsed = new URL(input);
  } catch (error) {
    throw new Error(`Invalid pull request URL: ${input}`);
  }

  if (parsed.hostname !== "github.com") {
    throw new Error("Only github.com pull request URLs are supported");
  }

  const parts = parsed.pathname.split("/").filter(Boolean);
  if (parts.length !== 4 || parts[2] !== "pull" || !/^\d+$/.test(parts[3])) {
    throw new Error("Expected PR URL format: https://github.com/owner/repo/pull/123");
  }

  return {
    owner: parts[0],
    repo: parts[1],
    number: Number(parts[3]),
    htmlUrl: `https://github.com/${parts[0]}/${parts[1]}/pull/${parts[3]}`,
  };
}

function githubRequest(pathname, token) {
  const options = {
    hostname: "api.github.com",
    path: pathname,
    method: "GET",
    headers: {
      Accept: "application/vnd.github+json",
      "User-Agent": USER_AGENT,
      "X-GitHub-Api-Version": "2022-11-28",
    },
  };

  if (token) {
    options.headers.Authorization = `Bearer ${token}`;
  }

  return new Promise((resolve, reject) => {
    const request = https.request(options, (response) => {
      let body = "";

      response.setEncoding("utf8");
      response.on("data", (chunk) => {
        body += chunk;
      });

      response.on("end", () => {
        if (response.statusCode < 200 || response.statusCode >= 300) {
          reject(new Error(`GitHub API request failed (${response.statusCode}): ${body}`));
          return;
        }

        try {
          resolve(JSON.parse(body));
        } catch (error) {
          reject(new Error(`Failed to parse GitHub API response: ${error.message}`));
        }
      });
    });

    request.on("error", reject);
    request.end();
  });
}

async function fetchAllFiles(owner, repo, number, token) {
  const files = [];
  let page = 1;

  while (true) {
    const encodedOwner = encodeURIComponent(owner);
    const encodedRepo = encodeURIComponent(repo);
    const pageFiles = await githubRequest(
      `/repos/${encodedOwner}/${encodedRepo}/pulls/${number}/files?per_page=100&page=${page}`,
      token,
    );

    files.push(...pageFiles);

    if (pageFiles.length < 100) {
      return files;
    }

    page += 1;
  }
}

function parseLocalDiff(diffText) {
  const files = [];
  const sections = diffText.split(/^diff --git /m).filter(Boolean);

  for (const section of sections) {
    const lines = section.split("\n");
    const header = lines[0] || "";
    const match = header.match(/^a\/(.+?) b\/(.+)$/);
    const filename = match ? match[2] : "unknown";
    const patch = lines.slice(1).join("\n");
    const additions = lines.filter((line) => line.startsWith("+") && !line.startsWith("+++")).length;
    const deletions = lines.filter((line) => line.startsWith("-") && !line.startsWith("---")).length;

    files.push({
      filename,
      status: "modified",
      additions,
      deletions,
      changes: additions + deletions,
      patch,
    });
  }

  return files;
}

function normalizePatch(file) {
  return [file.filename || "", file.patch || ""].join("\n");
}

function extensionOf(filename) {
  const ext = path.extname(filename).toLowerCase();
  return ext || "(none)";
}

function hasPathSegment(filename, patterns) {
  return patterns.some((pattern) => pattern.test(filename));
}

function addRisk(risks, level, title, details, files) {
  const key = `${level}:${title}:${details}`;
  const existing = risks.byKey.get(key);
  if (existing) {
    for (const file of files || []) {
      if (!existing.files.includes(file)) {
        existing.files.push(file);
      }
    }
    return;
  }

  const risk = { level, title, details, files: files || [] };
  risks.byKey.set(key, risk);
  risks.items.push(risk);
}

function analyzeFiles(files, pr) {
  const risks = { items: [], byKey: new Map() };
  const suggestions = new Set();
  const changedFiles = files.length;
  const additions = files.reduce((total, file) => total + (file.additions || 0), 0);
  const deletions = files.reduce((total, file) => total + (file.deletions || 0), 0);
  const totalChanges = additions + deletions;
  const extensions = new Map();

  for (const file of files) {
    const filename = file.filename || "unknown";
    const patch = normalizePatch(file);
    extensions.set(extensionOf(filename), (extensions.get(extensionOf(filename)) || 0) + 1);

    if (
      hasPathSegment(filename, [
        /(^|\/)(auth|authentication|authorization|security|crypto|secrets?)(\/|\.|$)/i,
        /(^|\/)(login|session|oauth|jwt|password|permissions?)(\/|\.|$)/i,
      ])
    ) {
      addRisk(
        risks,
        "High",
        "Authentication or security-sensitive code changed",
        "Review authorization boundaries, secret handling, and failure paths carefully.",
        [filename],
      );
      suggestions.add("Ask for explicit security-focused review on authentication, authorization, and secret-handling changes.");
    }

    if (/\beval\s*\(/.test(patch) || /\bnew\s+Function\s*\(/.test(patch)) {
      addRisk(
        risks,
        "High",
        "Dynamic code execution detected",
        "`eval()` or `new Function()` can execute attacker-controlled input if not tightly constrained.",
        [filename],
      );
      suggestions.add("Replace dynamic code execution with a parser, lookup table, or constrained interpreter.");
    }

    if (/\binnerHTML\s*=/.test(patch) || /\bdangerouslySetInnerHTML\b/.test(patch)) {
      addRisk(
        risks,
        "High",
        "HTML injection surface detected",
        "Direct HTML assignment can introduce XSS when any value is user-controlled.",
        [filename],
      );
      suggestions.add("Use safe DOM APIs, templating escapes, or a reviewed sanitizer for inserted HTML.");
    }

    if (
      hasPathSegment(filename, [
        /(^|\/)(migrations?|db|database|schema)(\/|\.|$)/i,
        /\.(sql)$/i,
      ])
    ) {
      addRisk(
        risks,
        "Medium",
        "Database or migration file changed",
        "Schema and data migrations need rollback, ordering, and production data compatibility checks.",
        [filename],
      );
      suggestions.add("Document migration order, rollback behavior, and any expected data backfill impact.");
    }

    if (
      hasPathSegment(filename, [
        /(^|\/)(\.github|config|configs?|settings)(\/|\.|$)/i,
        /(^|\/)(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|Dockerfile|docker-compose\.ya?ml)$/i,
        /\.(env|ya?ml|toml|ini|conf|config|properties)$/i,
      ])
    ) {
      addRisk(
        risks,
        "Medium",
        "Configuration or automation file changed",
        "Config updates can alter deployment, dependency, or CI behavior outside the touched code path.",
        [filename],
      );
      suggestions.add("Confirm configuration changes in an environment close to production before merge.");
    }

    if ((file.changes || 0) >= 300) {
      addRisk(
        risks,
        "Low",
        "Large file-level change",
        `${filename} has ${file.changes} changed lines, which can hide unrelated edits.`,
        [filename],
      );
      suggestions.add("Split unrelated large file changes or call out generated files in the PR description.");
    }

    if (/\bconsole\.(log|debug|trace)\s*\(/.test(patch)) {
      addRisk(
        risks,
        "Low",
        "Debug logging present",
        "Console logging may leak noisy or sensitive runtime details if it ships to production.",
        [filename],
      );
      suggestions.add("Remove temporary debug logging or gate it behind an appropriate logger level.");
    }

    if (/\b(TODO|FIXME)\b/i.test(patch)) {
      addRisk(
        risks,
        "Low",
        "TODO or FIXME marker present",
        "Follow-up markers should be tracked before the change is merged.",
        [filename],
      );
      suggestions.add("Convert TODO/FIXME comments into tracked issues or complete them before merge.");
    }
  }

  if (changedFiles >= 20 || totalChanges >= 1000) {
    addRisk(
      risks,
      "Medium",
      "Large pull request",
      `This PR touches ${changedFiles} files with ${totalChanges} changed lines.`,
      [],
    );
    suggestions.add("Consider splitting this PR by concern so each review has a smaller blast radius.");
  }

  if (suggestions.size === 0) {
    suggestions.add("Add or update tests that exercise the changed behavior before merge.");
    suggestions.add("Confirm the PR description explains the user-visible behavior and verification steps.");
  }

  return {
    pr,
    stats: { changedFiles, additions, deletions, totalChanges, extensions },
    risks: risks.items,
    suggestions: Array.from(suggestions),
  };
}

function riskScore(level) {
  if (level === "High") return 3;
  if (level === "Medium") return 2;
  return 1;
}

function confidenceFor(analysis) {
  const patchesAvailable = analysis.stats.changedFiles === 0
    ? 0
    : analysis.pr.filesWithPatch / analysis.stats.changedFiles;

  if (patchesAvailable < 0.6 || analysis.stats.totalChanges > 2500) {
    return "Low";
  }

  if (analysis.stats.totalChanges > 1000 || analysis.risks.some((risk) => risk.level === "High")) {
    return "Medium";
  }

  return "High";
}

function pluralize(count, singular, plural = `${singular}s`) {
  return count === 1 ? singular : plural;
}

function renderSummary(analysis) {
  const { pr, stats } = analysis;
  const topExtensions = Array.from(stats.extensions.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([extension, count]) => `${count} ${extension}`)
    .join(", ");

  const title = pr.title ? ` titled "${pr.title}"` : "";
  const scope = topExtensions ? ` The most common touched file types are ${topExtensions}.` : "";

  return `This review covers PR #${pr.number || "unknown"}${title}, which changes ${stats.changedFiles} ${pluralize(stats.changedFiles, "file")} with ${stats.additions} additions and ${stats.deletions} deletions.${scope} The analysis is heuristic and should be paired with human review for domain-specific correctness.`;
}

function renderRisks(risks) {
  const levels = ["High", "Medium", "Low"];
  const lines = [];

  for (const level of levels) {
    const matching = risks.filter((risk) => risk.level === level).sort((a, b) => a.title.localeCompare(b.title));
    lines.push(`### ${level}`);

    if (matching.length === 0) {
      lines.push("- None detected.");
      lines.push("");
      continue;
    }

    for (const risk of matching) {
      const fileList = risk.files && risk.files.length > 0 ? ` Files: ${risk.files.map((file) => `\`${file}\``).join(", ")}.` : "";
      lines.push(`- **${risk.title}:** ${risk.details}${fileList}`);
    }

    lines.push("");
  }

  return lines.join("\n").trimEnd();
}

function renderMarkdown(analysis) {
  const sortedRisks = analysis.risks.slice().sort((a, b) => riskScore(b.level) - riskScore(a.level));
  const confidence = confidenceFor(analysis);

  return `## Claude PR Review

### Summary
${renderSummary(analysis)}

### Identified Risks
${renderRisks(sortedRisks)}

### Improvement Suggestions
${analysis.suggestions.map((suggestion) => `- ${suggestion}`).join("\n")}

### Confidence Score
${confidence}
`;
}

async function loadPullRequest(args) {
  if (args["diff-file"]) {
    const diffPath = path.resolve(args["diff-file"]);
    const diffText = fs.readFileSync(diffPath, "utf8");
    const files = parseLocalDiff(diffText);
    return {
      pr: {
        number: "local",
        title: `Local diff: ${path.basename(diffPath)}`,
        htmlUrl: diffPath,
        filesWithPatch: files.filter((file) => file.patch).length,
      },
      files,
    };
  }

  if (!args.pr) {
    throw new Error("Missing required --pr option");
  }

  const parsed = parsePullRequestUrl(args.pr);
  const token = args.token || process.env.GITHUB_TOKEN || "";
  const encodedOwner = encodeURIComponent(parsed.owner);
  const encodedRepo = encodeURIComponent(parsed.repo);
  const [pullRequest, files] = await Promise.all([
    githubRequest(`/repos/${encodedOwner}/${encodedRepo}/pulls/${parsed.number}`, token),
    fetchAllFiles(parsed.owner, parsed.repo, parsed.number, token),
  ]);

  return {
    pr: {
      number: parsed.number,
      title: pullRequest.title,
      htmlUrl: parsed.htmlUrl,
      filesWithPatch: files.filter((file) => file.patch).length,
    },
    files,
  };
}

async function main() {
  const args = parseArgs(process.argv);

  if (args.help) {
    printHelp();
    return;
  }

  const { pr, files } = await loadPullRequest(args);
  const analysis = analyzeFiles(files, pr);
  const markdown = renderMarkdown(analysis);

  if (args.output) {
    fs.writeFileSync(path.resolve(args.output), markdown, "utf8");
    return;
  }

  process.stdout.write(markdown);
}

main().catch((error) => {
  console.error(`Error: ${error.message}`);
  process.exitCode = 1;
});
