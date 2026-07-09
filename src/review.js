const { spawnSync } = require("node:child_process");

const REQUIRED_HEADINGS = [
  "## Summary of changes",
  "## Identified risks",
  "## Improvement suggestions",
  "## Confidence score",
];

function truncate(text, maxLength) {
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, maxLength)}\n\n[diff truncated at ${maxLength} characters]`;
}

function buildClaudePrompt(pr) {
  return `You are a senior code reviewer. Review this GitHub pull request diff and return only Markdown with exactly these sections:

## Summary of changes
Write 2-3 concise sentences.

## Identified risks
Use bullet points. Include behavioral, testing, security, migration, and maintainability risks when relevant.

## Improvement suggestions
Use bullet points. Make suggestions concrete and actionable.

## Confidence score
One of: Low, Medium, High. Add one short reason.

Pull request:
- URL: ${pr.htmlUrl}
- Title: ${pr.title}
- Author: ${pr.author}
- Base: ${pr.baseRef}
- Head: ${pr.headRef}
- Changed files: ${pr.changedFiles}
- Additions: ${pr.additions}
- Deletions: ${pr.deletions}

Files:
${pr.files
  .map(
    (file) =>
      `- ${file.filename} (${file.status}, +${file.additions}/-${file.deletions})`,
  )
  .join("\n")}

Diff:
${truncate(pr.diff, 60000)}
`;
}

function runClaudeReview(prompt) {
  const command = process.env.CLAUDE_REVIEW_COMMAND || "claude";
  const configuredArgs = process.env.CLAUDE_REVIEW_ARGS || "-p";
  const args = configuredArgs.split(/\s+/).filter(Boolean);
  const result = spawnSync(command, [...args, prompt], {
    encoding: "utf8",
    maxBuffer: 1024 * 1024 * 8,
    timeout: 120000,
    windowsHide: true,
  });

  if (result.error) {
    return { ok: false, error: result.error.message };
  }
  if (result.status !== 0) {
    return {
      ok: false,
      error: result.stderr || `Claude command exited with ${result.status}`,
    };
  }

  const markdown = (result.stdout || "").trim();
  if (!REQUIRED_HEADINGS.every((heading) => markdown.includes(heading))) {
    return {
      ok: false,
      error: "Claude output did not include the required Markdown headings",
    };
  }

  return { ok: true, markdown };
}

function extension(filename) {
  const match = filename.match(/\.([^.]+)$/);
  return match ? match[1].toLowerCase() : "";
}

function topChangedFiles(files) {
  return [...files]
    .sort((left, right) => right.changes - left.changes)
    .slice(0, 3)
    .map((file) => `${file.filename} (+${file.additions}/-${file.deletions})`);
}

function hasTests(files) {
  return files.some((file) =>
    /(^|\/)(__tests__|test|tests|spec)(\/|$)|(\.|-)(test|spec)\./i.test(
      file.filename,
    ),
  );
}

function createHeuristicReview(pr) {
  const files = pr.files || [];
  const names = files.map((file) => file.filename);
  const topFiles = topChangedFiles(files);
  const touchedExtensions = [...new Set(names.map(extension).filter(Boolean))]
    .slice(0, 6)
    .join(", ");

  const risks = [];
  if (!hasTests(files)) {
    risks.push(
      "No dedicated test files were changed, so regressions may not be caught automatically.",
    );
  }
  if (pr.changedFiles > 10 || pr.additions + pr.deletions > 600) {
    risks.push(
      "The diff is broad enough that unrelated behavior changes could be hidden in review.",
    );
  }
  if (names.some((name) => /package-lock|pnpm-lock|yarn.lock|requirements|poetry.lock/i.test(name))) {
    risks.push(
      "Dependency or lockfile changes can alter install behavior and should be checked in a clean environment.",
    );
  }
  if (names.some((name) => /\.ya?ml$|\.json$|\.toml$|\.ini$|\.env/i.test(name))) {
    risks.push(
      "Configuration changes may affect CI, deployment, or local setup outside the touched code path.",
    );
  }
  if (names.some((name) => /auth|token|secret|permission|security|crypto/i.test(name))) {
    risks.push(
      "Security-sensitive paths appear to be touched; verify authorization and secret-handling assumptions.",
    );
  }
  if (risks.length === 0) {
    risks.push(
      "The main risk is semantic correctness: the diff should be exercised against the user-facing scenario it changes.",
    );
  }

  const suggestions = [];
  suggestions.push("Run the focused test suite for the changed area before merging.");
  if (!hasTests(files)) {
    suggestions.push(
      "Add at least one regression test or documented manual verification for the changed behavior.",
    );
  }
  if (topFiles.length) {
    suggestions.push(`Review the largest touched files carefully: ${topFiles.join("; ")}.`);
  }
  if (names.some((name) => /README|docs?\//i.test(name))) {
    suggestions.push(
      "Check that documentation examples match the final CLI/API behavior exactly.",
    );
  }
  suggestions.push("Confirm CI passes from a clean checkout, not only from a warm local workspace.");

  let confidence = "Medium";
  let confidenceReason = "The diff metadata is available, but the review is based on static analysis.";
  if (hasTests(files) && pr.changedFiles <= 5 && pr.additions + pr.deletions <= 300) {
    confidence = "High";
    confidenceReason = "The change is small and includes test coverage.";
  } else if (!pr.diff || pr.diff.includes("[diff truncated")) {
    confidence = "Low";
    confidenceReason = "The diff was missing or truncated, limiting review depth.";
  } else if (!hasTests(files) && pr.additions + pr.deletions > 600) {
    confidence = "Low";
    confidenceReason = "The change is broad and lacks visible test coverage.";
  }

  return `## Summary of changes
This PR changes ${pr.changedFiles} file(s) with ${pr.additions} additions and ${pr.deletions} deletions. The largest touched areas are ${topFiles.length ? topFiles.join("; ") : "not available from the GitHub file list"}. ${touchedExtensions ? `The diff primarily involves these file types: ${touchedExtensions}.` : "No dominant file type was detected from the file list."}

## Identified risks
${risks.map((risk) => `- ${risk}`).join("\n")}

## Improvement suggestions
${suggestions.map((suggestion) => `- ${suggestion}`).join("\n")}

## Confidence score
${confidence} - ${confidenceReason}
`;
}

module.exports = {
  REQUIRED_HEADINGS,
  buildClaudePrompt,
  createHeuristicReview,
  runClaudeReview,
};
