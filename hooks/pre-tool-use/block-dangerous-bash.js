#!/usr/bin/env node

import {appendFileSync, mkdirSync} from 'node:fs';
import {dirname, join} from 'node:path';
import {fileURLToPath} from 'node:url';

const HOME = process.env.HOME || process.env.USERPROFILE || '';
const DEFAULT_LOG_PATH = HOME ? join(HOME, '.claude', 'hooks', 'blocked.log') : 'blocked.log';

const BLOCKERS = [
  {
    name: 'rm -rf',
    reason: 'Recursive forced deletion can permanently remove project files.',
    matches: (command) => /(^|[;&|()\s])rm\s+(?:-[^\s]*r[^\s]*f|-\S*f\S*r\S*)\b/i.test(command),
  },
  {
    name: 'DROP TABLE',
    reason: 'Dropping tables destroys database schema and data.',
    matches: (command) => /\bdrop\s+table\b/i.test(command),
  },
  {
    name: 'git push --force',
    reason: 'Force pushing can rewrite shared branch history.',
    matches: (command) => /\bgit\s+push\b[^\n;|&]*\s--force(?:\b|=)/i.test(command),
  },
  {
    name: 'TRUNCATE',
    reason: 'TRUNCATE can erase all rows from a table.',
    matches: (command) => /\btruncate\b/i.test(command),
  },
  {
    name: 'DELETE FROM without WHERE',
    reason: 'DELETE FROM without a WHERE clause can erase every row in a table.',
    matches: hasUnsafeDeleteFrom,
  },
];

export function getCommandFromHookInput(input) {
  const parsed = typeof input === 'string' ? JSON.parse(input || '{}') : input || {};
  const toolInput = parsed.tool_input || parsed.toolInput || parsed.input || {};

  if (parsed.tool_name && parsed.tool_name !== 'Bash') {
    return '';
  }

  return String(toolInput.command || parsed.command || '');
}

export function findBlockedPattern(command) {
  return BLOCKERS.find((blocker) => blocker.matches(command)) || null;
}

export function buildBlockResponse(blocker, command) {
  return {
    decision: 'block',
    reason: `Blocked dangerous bash command: ${blocker.name}. ${blocker.reason}`,
    command,
  };
}

export function logBlockedAttempt({command, blocker, cwd = process.cwd(), logPath = DEFAULT_LOG_PATH}) {
  mkdirSync(dirname(logPath), {recursive: true});
  const record = {
    timestamp: new Date().toISOString(),
    pattern: blocker.name,
    command,
    project_path: cwd,
  };
  appendFileSync(logPath, `${JSON.stringify(record)}\n`, 'utf8');
}

function hasUnsafeDeleteFrom(command) {
  const statements = command.split(';');
  return statements.some((statement) => {
    const normalized = statement.replace(/\s+/g, ' ').trim();
    if (!/\bdelete\s+from\b/i.test(normalized)) {
      return false;
    }

    return !/\bwhere\b/i.test(normalized);
  });
}

async function readStdin() {
  let input = '';
  for await (const chunk of process.stdin) {
    input += chunk;
  }
  return input;
}

async function main() {
  let command = '';

  try {
    command = getCommandFromHookInput(await readStdin());
  } catch (error) {
    console.error(`Claude hook could not parse input: ${error.message}`);
    process.exit(0);
  }

  if (!command) {
    process.exit(0);
  }

  const blocker = findBlockedPattern(command);
  if (!blocker) {
    process.exit(0);
  }

  logBlockedAttempt({command, blocker});
  console.log(JSON.stringify(buildBlockResponse(blocker, command)));
  process.exit(2);
}

const executedPath = process.argv[1] ? fileURLToPath(import.meta.url) === process.argv[1] : false;
if (executedPath) {
  main();
}
