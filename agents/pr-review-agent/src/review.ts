/**
 * Prompt construction and output parsing for the review sub-agent.
 *
 * The system prompt instructs Claude to emit a strict, parseable
 * Markdown structure so the formatter can render it consistently
 * regardless of the model version.
 */

import type { PullRequest } from "./fetch-pr.js";

export interface Review {
  summary: string;
  risks: string[];
  improvements: string[];
  confidence: "Low" | "Medium" | "High";
  source: { kind: "mock" | "claude"; model?: string };
  context: {
    prTitle: string;
    prUrl: string;
    diffLines: number;
  };
}

const SYSTEM_PROMPT = `You are a senior software engineer reviewing a pull request. Produce a structured Markdown review with EXACTLY four top-level sections in this order:

## Summary
Two or three sentences describing what the change does and why.

## Risks
A bulleted list of concrete risks introduced by this change. Each bullet should be one sentence, start with a verb, and reference a specific file or function. If there are no risks, write "- None identified."

## Improvements
A bulleted list of suggested improvements. Same format as Risks. Suggestions should be actionable, not stylistic preferences.

## Confidence
A single line: \`Low\`, \`Medium\`, or \`High\`, followed by a one-sentence justification.

Rules:
- Do not propose changes outside the diff's scope. No "while you're here" suggestions.
- Be specific. "Consider extracting this into a helper" is not useful; "Extract the rate-limit reset calculation in api/users.ts:42 so it can be unit tested" is.
- Do not invent issues. If the diff is small and clean, the Risks and Improvements sections can be empty.
- Output ONLY the four sections, in order, with no preamble or epilogue.`;

export function buildReviewPrompt(context: PullRequest): {
  system: string;
  user: string;
} {
  const diffSnippet =
    context.diff.length > 50_000
      ? context.diff.slice(0, 50_000) + "\n\n[diff truncated at 50,000 characters]"
      : context.diff;

  const user = [
    `Title: ${context.title}`,
    `Author: ${context.author}`,
    `Base: ${context.baseRef}  Head: ${context.headRef}`,
    `URL: ${context.url}`,
    context.body ? `\nPR description:\n${context.body}\n` : "",
    `\nDiff:\n\`\`\`diff\n${diffSnippet}\n\`\`\``,
  ]
    .filter(Boolean)
    .join("\n");

  return { system: SYSTEM_PROMPT, user };
}

export function parseReviewOutput(text: string, context: PullRequest): Review {
  const sections = splitSections(text);

  const summary = (sections.summary ?? "").trim();
  const risks = parseList(sections.risks ?? "");
  const improvements = parseList(sections.improvements ?? "");
  const confidence = parseConfidence(sections.confidence ?? "");

  return {
    summary: summary || "(no summary provided)",
    risks,
    improvements,
    confidence,
    source: { kind: "claude" },
    context: {
      prTitle: context.title,
      prUrl: context.url,
      diffLines: context.diff.split("\n").length,
    },
  };
}

function splitSections(text: string): Record<string, string> {
  const out: Record<string, string> = {};
  const re = /^##\s+(\w[\w\s]*?)\s*$/gm;
  const matches: RegExpExecArray[] = [];
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) matches.push(m);
  for (let i = 0; i < matches.length; i++) {
    const name = matches[i][1].trim().toLowerCase();
    const start = matches[i].index! + matches[i][0].length;
    const end = i + 1 < matches.length ? matches[i + 1].index! : text.length;
    out[name] = text.slice(start, end);
  }
  return out;
}

function parseList(block: string): string[] {
  const items: string[] = [];
  for (const raw of block.split("\n")) {
    const line = raw.trim();
    if (line.startsWith("- ") || line.startsWith("* ")) {
      items.push(line.slice(2).trim());
    } else if (line && !line.startsWith("#")) {
      // Treat a non-empty line that's not a heading as a single-item paragraph.
      items.push(line);
    }
  }
  // Collapse "None identified" / "None." into an empty list.
  if (
    items.length === 1 &&
    /^none(\s+identified)?\.?$/i.test(items[0].replace(/\.$/, ""))
  ) {
    return [];
  }
  return items;
}

function parseConfidence(block: string): "Low" | "Medium" | "High" {
  const m = block.match(/\b(Low|Medium|High)\b/i);
  if (!m) return "Low";
  const value = m[1][0].toUpperCase() + m[1].slice(1).toLowerCase();
  if (value === "Low" || value === "Medium" || value === "High") {
    return value;
  }
  return "Low";
}
