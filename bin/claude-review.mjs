#!/usr/bin/env node

const args = process.argv.slice(2);

function usage() {
  return `Usage: claude-review --pr https://github.com/owner/repo/pull/123

Options:
  --pr <url>       GitHub pull request URL to review.
  --diff-file <p>  Read a local diff instead of fetching from GitHub.
  --help          Show this help.
`;
}

function argValue(name) {
  const index = args.indexOf(name);
  if (index === -1) return "";
  return args[index + 1] || "";
}

function parsePrUrl(value) {
  const match = String(value || "").match(/^https:\/\/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)(?:[/?#].*)?$/i);
  if (!match) return null;
  return { owner: match[1], repo: match[2], number: match[3], url: `https://github.com/${match[1]}/${match[2]}/pull/${match[3]}` };
}

async function fetchText(url) {
  const res = await fetch(url, {
    headers: { "User-Agent": "claude-review-agent/1.0" },
  });
  if (!res.ok) throw new Error(`Failed to fetch ${url}: ${res.status}`);
  return res.text();
}

async function fetchPrDiff(pr) {
  const apiUrl = `https://api.github.com/repos/${pr.owner}/${pr.repo}/pulls/${pr.number}`;
  try {
    const res = await fetch(apiUrl, {
      headers: {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review-agent/1.0",
      },
    });
    if (!res.ok) throw new Error(`GitHub API returned ${res.status}`);
    return res.text();
  } catch {
    return fetchText(`${pr.url}.diff`);
  }
}

async function readLocal(filePath) {
  const fs = await import("node:fs/promises");
  return fs.readFile(filePath, "utf8");
}

function changedFiles(diff) {
  return [...String(diff || "").matchAll(/^diff --git a\/(.+?) b\/(.+)$/gm)]
    .map((match) => match[2])
    .filter(Boolean);
}

function countMatches(diff, pattern) {
  return (String(diff || "").match(pattern) || []).length;
}

function additions(diff) {
  return countMatches(diff, /^\+(?!\+\+)/gm);
}

function deletions(diff) {
  return countMatches(diff, /^-(?!--)/gm);
}

function hasVerificationFiles(files) {
  return files.some((file) =>
    /(^|\/)(__tests__|tests?|testRunner|fixtures?|samples?|baselines?)(\/|$)/i.test(file) ||
    /\.(test|spec)\.[cm]?[jt]sx?$/i.test(file) ||
    /\.(snap|fixture|baseline)$/i.test(file)
  );
}

function riskItems(diff, files) {
  const risks = [];
  const text = String(diff || "");
  if (/\b(eval|new Function|dangerouslySetInnerHTML|innerHTML\s*=)\b/i.test(text)) {
    risks.push("Potential code execution or unsafe HTML handling appears in the diff; verify inputs are trusted or sanitized.");
  }
  if (/\b(password|secret|token|api[_-]?key)\b/i.test(text)) {
    risks.push("Secret-like terms appear in the diff; confirm no credentials or sensitive values are committed.");
  }
  if (/\bDROP TABLE|DELETE FROM|TRUNCATE\b/i.test(text)) {
    risks.push("Destructive database operation appears in the diff; verify it is guarded and covered by migration rollback guidance.");
  }
  if (files.some((file) => /\.(yml|yaml|json|toml|ini|env)$/i.test(file)) && files.length > 3) {
    risks.push("Multiple configuration files changed; verify environment-specific behavior and deployment defaults.");
  }
  if (additions(diff) > 250 && !hasVerificationFiles(files)) {
    risks.push("Large code change without obvious test files; add or reference focused verification.");
  }
  return risks;
}

function suggestionItems(diff, files) {
  const suggestions = [];
  if (!hasVerificationFiles(files)) {
    suggestions.push("Include a focused test, fixture, or manual verification note for the changed behavior.");
  }
  if (files.some((file) => /\.(md|mdx)$/i.test(file)) && files.length === 1) {
    suggestions.push("For documentation-only changes, verify links, commands, and version names against the current project state.");
  }
  if (/\bTODO\b/i.test(diff)) {
    suggestions.push("Resolve or explain new TODOs before merging.");
  }
  return suggestions;
}

function confidence(diff, files, risks) {
  if (!diff.trim() || files.length === 0) return "Low";
  if (files.length <= 3 && additions(diff) + deletions(diff) < 120 && risks.length === 0) return "High";
  if (risks.length > 2 || additions(diff) + deletions(diff) > 400) return "Low";
  return "Medium";
}

function reviewMarkdown({ pr, diff }) {
  const files = changedFiles(diff);
  const risks = riskItems(diff, files);
  const suggestions = suggestionItems(diff, files);
  const added = additions(diff);
  const removed = deletions(diff);
  const fileList = files.slice(0, 6).join(", ") || "no files detected";
  const summary = [
    `Reviewed ${pr?.url || "the provided diff"} across ${files.length} changed file${files.length === 1 ? "" : "s"}.`,
    `The patch changes ${fileList} with approximately ${added} additions and ${removed} deletions.`,
    risks.length ? "The main review focus is behavioral risk and verification coverage." : "No immediate high-risk pattern is visible from the diff alone.",
  ].join(" ");

  return `## Summary

${summary}

## Identified Risks

${risks.length ? risks.map((item) => `- ${item}`).join("\n") : "- None identified from the diff."}

## Improvement Suggestions

${suggestions.length ? suggestions.map((item) => `- ${item}`).join("\n") : "- None."}

## Confidence

${confidence(diff, files, risks)}
`;
}

async function main() {
  if (args.includes("--help")) {
    console.log(usage());
    return;
  }

  const diffFile = argValue("--diff-file");
  const prUrl = argValue("--pr");
  const pr = parsePrUrl(prUrl);
  if (!diffFile && !pr) throw new Error("Provide --pr with a GitHub pull request URL or --diff-file with a local diff.");

  const diff = diffFile
    ? await readLocal(diffFile)
    : await fetchPrDiff(pr);

  process.stdout.write(reviewMarkdown({ pr, diff }));
}

main().catch((error) => {
  console.error(`claude-review: ${error.message}`);
  process.exit(1);
});
