#!/usr/bin/env node
/**
 * Claude Code Pre-Tool-Use Hook: Destructive Command Blocker (Node.js engine)
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

function logBlocked(command, reason, projectDir) {
  const home = os.homedir();
  const logDir = path.join(home, '.claude', 'hooks');
  try {
    fs.mkdirSync(logDir, { recursive: true });
    const logFile = path.join(logDir, 'blocked.log');
    const timestamp = new Date().toISOString();
    const entry = `[${timestamp}] BLOCKED: ${reason} | DIR: ${projectDir || process.cwd()} | CMD: ${command}\n`;
    fs.appendFileSync(logFile, entry, 'utf8');
  } catch (err) {
    process.stderr.write(`Failed to write to blocked.log: ${err.message}\n`);
  }
}

function checkCommand(command) {
  if (!command) return { allowed: true };
  const cmd = command.trim();

  // 1. Check rm -rf variants (rm -rf, rm -fr, rm -r -f, rm -f -r)
  if (/\brm\s+/i.test(cmd)) {
    const hasR = /-[a-zA-Z]*r/i.test(cmd);
    const hasF = /-[a-zA-Z]*f/i.test(cmd);
    if (hasR && hasF) {
      return { allowed: false, reason: 'Destructive recursive file deletion (rm -rf)' };
    }
  }

  // 2. Drop table / database / schema
  if (/\bDROP\s+(?:DATABASE|TABLE|SCHEMA)\b/i.test(cmd)) {
    return { allowed: false, reason: 'Database drop table/database/schema query' };
  }

  // 3. Truncate table
  if (/\bTRUNCATE\s+(?:TABLE\s+)?[a-zA-Z0-9_]+/i.test(cmd)) {
    return { allowed: false, reason: 'Database table truncate query' };
  }

  // 4. Delete from without WHERE
  if (/\bDELETE\s+FROM\b/i.test(cmd) && !/\bWHERE\b/i.test(cmd)) {
    return { allowed: false, reason: 'Unbounded DELETE FROM query without a WHERE clause' };
  }

  // 5. Git push --force or -f
  if (/\bgit\s+push\b/i.test(cmd) && /(?:--force|-f\b)/i.test(cmd)) {
    return { allowed: false, reason: 'Forced git push (--force / -f)' };
  }

  // 6. Filesystem formatting
  if (/\bmkfs(?:\.[a-zA-Z0-9]+)?\b/i.test(cmd)) {
    return { allowed: false, reason: 'Filesystem format command (mkfs)' };
  }

  // 7. Direct raw disk overwriting
  if (/\bdd\s+if=\/dev\/(?:zero|urandom|null)\s+of=\/dev\/[a-zA-Z0-9]+/i.test(cmd)) {
    return { allowed: false, reason: 'Direct raw disk overwriting (dd)' };
  }

  // 8. Fork bomb
  if (/:\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:/.test(cmd)) {
    return { allowed: false, reason: 'Fork bomb pattern' };
  }

  return { allowed: true };
}

function main() {
  let raw = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', chunk => { raw += chunk; });
  process.stdin.on('end', () => {
    if (!raw.trim()) process.exit(0);

    try {
      const data = JSON.parse(raw);
      const toolName = data.tool_name || '';
      const toolInput = data.tool_input || {};
      const projectDir = data.cwd || process.cwd();

      if (['bash', 'execute_command', 'run_command'].includes(toolName)) {
        const cmd = toolInput.command || toolInput.CommandLine || '';
        const { allowed, reason } = checkCommand(cmd);
        if (!allowed) {
          logBlocked(cmd, reason, projectDir);
          const errorMsg = `⛔ COMMAND BLOCKED BY SECURITY HOOK: ${reason}\nAttempted command: ${cmd}\nThis operation is prohibited to prevent accidental data loss or destructive git/database mutations.\n`;
          process.stderr.write(errorMsg);
          process.exit(1);
        }
      }
    } catch {
      // ignore non-JSON input
    }
    process.exit(0);
  });
}

if (require.main === module) {
  main();
}

module.exports = { checkCommand };
