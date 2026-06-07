#!/usr/bin/env node

import { readFile } from "node:fs/promises";

const files = [
  "samples/react-32781.md",
  "samples/node-58362.md",
];

const requiredPatterns = [
  /^## Summary of changes$/m,
  /^## Identified risks$/m,
  /^## Improvement suggestions$/m,
  /^## Confidence score: (Low|Medium|High)$/m,
];

for (const file of files) {
  const text = await readFile(file, "utf8");
  for (const pattern of requiredPatterns) {
    if (!pattern.test(text)) {
      throw new Error(`${file} is missing ${pattern}`);
    }
  }
}

console.log(`verified ${files.length} sample reviews`);
