/**
 * Heuristic fallback reviewer. Used when ANTHROPIC_API_KEY is missing
 * (--mock, or no key set) so the CLI is still useful for testing the
 * parse and format pipeline.
 *
 * The rules are deliberately conservative: only flag things a
 * human reviewer would also notice.
 */

import type { Review } from "./review.js";
import type { PullRequest } from "./fetch-pr.js";

interface DiffHit {
  file: string;
  line: string;
  number: number;
}

interface Rule {
  id: string;
  match: (diff: string) => DiffHit[];
}

const RULES: Rule[] = [
  {
    id: "console-log",
    match: (diff) =>
      linesMatching(diff, /\bconsole\.(log|debug|info|warn|error)\(/).map((hit) => {
        const call = hit.line.match(/console\.\w+/)?.[0] ?? "console call";
        const loc = `${hit.file}${hit.number ? `:${hit.number}` : ""}`;
        return { file: loc, line: `Leftover ${call} here. Remove before merge or replace with a structured logger.`, number: 0 };
      }),
  },
  {
    id: "todo-fixme",
    match: (diff) =>
      linesMatching(diff, /\b(TODO|FIXME|XXX|HACK)\b/).map((hit) => {
        const tag = hit.line.match(/\b(?:TODO|FIXME|XXX|HACK)\b/)?.[0] ?? "TODO";
        const loc = `${hit.file}${hit.number ? `:${hit.number}` : ""}`;
        return { file: loc, line: `Unresolved ${tag}. Either resolve it or link an issue.`, number: 0 };
      }),
  },
  {
    id: "as-any",
    match: (diff) =>
      linesMatching(diff, /\bas\s+any\b/).map((hit) => {
        const loc = `${hit.file}${hit.number ? `:${hit.number}` : ""}`;
        return { file: loc, line: "`as any` here. Replace with a narrower type assertion or a proper interface.", number: 0 };
      }),
  },
  {
    id: "ts-ignore",
    match: (diff) =>
      linesMatching(diff, /@ts-(ignore|expect-error)/).map((hit) => {
        const tag = hit.line.match(/@ts-\w+/)?.[0] ?? "@ts-ignore";
        const loc = `${hit.file}${hit.number ? `:${hit.number}` : ""}`;
        return { file: loc, line: `${tag} here. Add a comment explaining what's being suppressed and why.`, number: 0 };
      }),
  },
  {
    id: "eval",
    match: (diff) =>
      linesMatching(diff, /\beval\s*\(/).map((hit) => {
        const loc = `${hit.file}${hit.number ? `:${hit.number}` : ""}`;
        return { file: loc, line: "`eval()` here. Almost always a security or correctness bug; replace with a parser.", number: 0 };
      }),
  },
  {
    id: "catch-all",
    match: (diff) =>
      linesMatching(diff, /catch\s*\(\s*\w*\s*\)\s*\{\s*\}/).map((hit) => {
        const loc = `${hit.file}${hit.number ? `:${hit.number}` : ""}`;
        return { file: loc, line: "Empty catch block here. Silent failures are debugging nightmares; at minimum, log the error.", number: 0 };
      }),
  },
];

function linesMatching(diff: string, pattern: RegExp): DiffHit[] {
  const out: DiffHit[] = [];
  let currentFile: string | null = null;
  let lineNumber = 0;
  for (const raw of diff.split("\n")) {
    if (raw.startsWith("diff --git ") || raw.startsWith("+++ ")) {
      const m = raw.match(/b\/(.+)$/);
      if (m) currentFile = m[1] ?? null;
      continue;
    }
    if (raw.startsWith("@@")) {
      const m = raw.match(/\+(\d+)/);
      if (m) lineNumber = Number(m[1]);
      continue;
    }
    if (raw.startsWith("+") && !raw.startsWith("+++")) {
      lineNumber++;
      if (pattern.test(raw)) {
        out.push({ file: currentFile ?? "?", line: raw.slice(1), number: lineNumber });
      }
    }
  }
  return out;
}

export function mockReview(context: PullRequest): Review {
  const risks: string[] = [];
  for (const rule of RULES) {
    for (const hit of rule.match(context.diff)) {
      risks.push(`${hit.line} (${hit.file})`);
    }
  }

  const improvements: string[] = [
    "Verify the diff is covered by tests; the bounty requires at least 80% coverage on new code.",
    "Run the project's linter and type-checker locally before pushing; a CI failure on formatting is a wasted review round.",
  ];
  if (context.diff.length > 10_000) {
    improvements.push(
      "Consider splitting this PR into smaller, independently mergeable changes. Reviewer fatigue is real.",
    );
  }

  const diffLines = context.diff.split("\n").length;
  return {
    summary: `Mock review of "${context.title}". The diff has ${diffLines} lines across ${countFiles(context.diff)} file(s). This is a heuristic pass — for a real review, set ANTHROPIC_API_KEY and re-run.`,
    risks,
    improvements,
    confidence: "Low",
    source: { kind: "mock" },
    context: {
      prTitle: context.title,
      prUrl: context.url,
      diffLines,
    },
  };
}

function countFiles(diff: string): number {
  return diff.split("\n").filter((l) => l.startsWith("diff --git ")).length;
}
