#!/usr/bin/env node
/**
 * changelog.js - Generate a structured CHANGELOG.md from git history.
 *
 * Usage:
 *   node changelog.js              # writes CHANGELOG.md in cwd
 *   node changelog.js <output.md>  # writes to custom path
 *
 * Reads commits since the latest git tag, categorizes them by conventional
 * commit prefix, and writes a formatted CHANGELOG.md.
 *
 * Requirements: Node.js 18+ (global fetch not needed - uses child_process/git).
 * No npm dependencies.
 */

import { execSync } from "node:child_process";
import { writeFileSync } from "node:fs";

const OUT = process.argv[2] || "CHANGELOG.md";

function git(args) {
  return execSync(args, { encoding: "utf8", stdio: ["pipe", "pipe", "pipe"] }).trim();
}

function runGit(args) {
  try {
    return git(args);
  } catch {
    return "";
  }
}

// Find the latest tag, or use the root commit if none exists
const prevTag = runGit("git describe --tags --abbrev=0") || "";
const range = prevTag ? `${prevTag}..HEAD` : runGit("git rev-list --max-parents=0 HEAD");

// Collect commits since the previous tag (oldest first)
let raw = "";
try {
  raw = execSync(`git log --reverse --pretty="format:%s%x01%an" ${range}`, {
    encoding: "utf8",
  }).trim();
} catch {
  raw = "";
}

const commits = raw.split("\n").filter((line) => line.trim());

// Category buckets
const added = [];
const fixed = [];
const changed = [];
const removed = [];

for (const line of commits) {
  const sepIdx = line.indexOf("\u0001");
  const msg = sepIdx >= 0 ? line.slice(0, sepIdx) : line;
  const author = sepIdx >= 0 ? line.slice(sepIdx + 1) : "unknown";
  const lower = msg.toLowerCase();

  const item = `- ${msg} (@${author})`;

  if (lower.startsWith("feat:")) {
    added.push(item);
  } else if (lower.startsWith("fix:")) {
    fixed.push(item);
  } else if (
    lower.startsWith("docs:") ||
    lower.startsWith("style:") ||
    lower.startsWith("refactor:") ||
    lower.startsWith("perf:") ||
    lower.startsWith("build:") ||
    lower.startsWith("ci:") ||
    lower.startsWith("chore:")
  ) {
    changed.push(item);
  } else if (lower.startsWith("test:")) {
    fixed.push(item);
  } else if (lower.startsWith("remove:") || lower.startsWith("delete:") || lower.startsWith("drop:")) {
    removed.push(item);
  } else {
    changed.push(item);
  }
}

// Build output
const lines = [];
lines.push("# Changelog");
lines.push("");
lines.push("## [Unreleased]");
lines.push("");

if (added.length) {
  lines.push("### Added");
  lines.push(...added);
  lines.push("");
}
if (fixed.length) {
  lines.push("### Fixed");
  lines.push(...fixed);
  lines.push("");
}
if (changed.length) {
  lines.push("### Changed");
  lines.push(...changed);
  lines.push("");
}
if (removed.length) {
  lines.push("### Removed");
  lines.push(...removed);
  lines.push("");
}

writeFileSync(OUT, lines.join("\n") + "\n");

console.log(`CHANGELOG written to ${OUT}`);
console.log(`Commits processed: ${commits.length}`);
console.log(`Added: ${added.length}, Fixed: ${fixed.length}, Changed: ${changed.length}, Removed: ${removed.length}`);
