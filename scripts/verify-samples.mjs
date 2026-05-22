#!/usr/bin/env node
import { readFileSync } from "node:fs";

const requiredSections = [
  "## Summary",
  "## Identified Risks",
  "## Improvement Suggestions",
  "## Confidence",
];

const samples = [
  "samples/cli-11534-review.md",
  "samples/cli-13482-review.md",
];

for (const sample of samples) {
  const markdown = readFileSync(sample, "utf8");
  for (const section of requiredSections) {
    if (!markdown.includes(section)) {
      throw new Error(sample + " is missing " + section);
    }
  }
  if (!/## Confidence\r?\n(?:Low|Medium|High)\b/.test(markdown)) {
    throw new Error(sample + " is missing a Low/Medium/High confidence score");
  }
}

console.log("Verified " + samples.length + " structured PR review sample outputs.");
