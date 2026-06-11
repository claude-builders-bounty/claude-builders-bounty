import https from "node:https";

export function reviewDiff(diff, options = {}) {
  const stats = summarizeDiff(diff);
  const risks = detectRisks(diff, stats);
  const suggestions = suggestImprovements(diff, stats);
  const summary = [
    `This PR changes ${stats.filesChanged} file(s), adding ${stats.additions} line(s) and removing ${stats.deletions} line(s).`,
    describePrimaryChange(stats, options.source)
  ].join(" ");
  return {
    summary,
    risks,
    suggestions,
    confidence: confidenceFor(stats, risks)
  };
}

export function summarizeDiff(diff) {
  const lines = String(diff || "").split(/\r?\n/);
  const files = new Set();
  let additions = 0;
  let deletions = 0;
  let testsTouched = false;
  let docsTouched = false;
  let configTouched = false;
  for (const line of lines) {
    if (line.startsWith("+++ b/")) {
      const file = line.slice(6);
      files.add(file);
      testsTouched ||= /(^|\/)(test|tests|spec|__tests__)(\/|$)|\.(test|spec)\./i.test(file);
      docsTouched ||= /readme|docs?\//i.test(file);
      configTouched ||= /package\.json|tsconfig|eslint|workflow|\.ya?ml$/i.test(file);
    } else if (line.startsWith("+") && !line.startsWith("+++")) additions++;
    else if (line.startsWith("-") && !line.startsWith("---")) deletions++;
  }
  return { filesChanged: files.size, additions, deletions, testsTouched, docsTouched, configTouched };
}

export async function fetchPullRequestDiff(prUrl) {
  const url = new URL(prUrl);
  if (url.hostname !== "github.com" || !/\/pull\/\d+$/.test(url.pathname)) {
    throw new Error("Only GitHub pull request URLs are supported.");
  }
  url.pathname = `${url.pathname}.diff`;
  return fetchText(url);
}

function detectRisks(diff, stats) {
  const risks = [];
  if (stats.filesChanged > 12) risks.push("Large change surface; review file ownership and regression risk carefully.");
  if (stats.additions + stats.deletions > 600) risks.push("Large diff size may hide behavioral regressions.");
  if (/password|secret|token|api[_-]?key/i.test(diff)) risks.push("Diff mentions sensitive configuration terms; verify no secrets are introduced.");
  if (/child_process|exec\(|eval\(|dangerouslySetInnerHTML/i.test(diff)) risks.push("Potentially dangerous execution or rendering API touched.");
  if (!stats.testsTouched) risks.push("No test files appear to be changed.");
  return risks;
}

function suggestImprovements(diff, stats) {
  const suggestions = [];
  if (!stats.testsTouched) suggestions.push("Add or update focused tests that cover the changed behavior.");
  if (!stats.docsTouched && /cli|config|api|option/i.test(diff)) suggestions.push("Update README or usage docs for user-facing behavior.");
  if (stats.configTouched) suggestions.push("Double-check CI and local install behavior after configuration changes.");
  if (suggestions.length === 0) suggestions.push("Run the project test suite and include the command output in the PR.");
  return suggestions;
}

function describePrimaryChange(stats, source) {
  const areas = [];
  if (stats.testsTouched) areas.push("tests");
  if (stats.docsTouched) areas.push("documentation");
  if (stats.configTouched) areas.push("configuration");
  const areaText = areas.length ? `Primary touched area(s): ${areas.join(", ")}.` : "Primary touched area is implementation code.";
  return source ? `${areaText} Source: ${source}.` : areaText;
}

function confidenceFor(stats, risks) {
  if (stats.filesChanged === 0) return "Low";
  if (risks.length >= 3 || stats.additions + stats.deletions > 600) return "Low";
  if (risks.length === 0 && stats.testsTouched) return "High";
  return "Medium";
}

function fetchText(url, redirects = 0) {
  return new Promise((resolve, reject) => {
    https.get(url, { headers: { "user-agent": "claude-pr-review-agent" } }, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        res.resume();
        if (redirects >= 5) {
          reject(new Error("Too many redirects while fetching PR diff."));
          return;
        }
        resolve(fetchText(new URL(res.headers.location, url), redirects + 1));
        return;
      }
      if (res.statusCode < 200 || res.statusCode >= 300) {
        reject(new Error(`GitHub diff request failed: ${res.statusCode}`));
        res.resume();
        return;
      }
      let body = "";
      res.setEncoding("utf8");
      res.on("data", (chunk) => (body += chunk));
      res.on("end", () => resolve(body));
    }).on("error", reject);
  });
}
