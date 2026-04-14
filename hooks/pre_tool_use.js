/**
 * Claude Code pre-tool-use hook: blocks destructive bash/SQL commands.
 * Place in ~/.claude/hooks/pre_tool_use.js
 * Claude Code auto-discovers hooks in ~/.claude/hooks/
 */
'use strict';

const fs = require('fs');
const path = require('path');

const LOG_FILE = path.join(process.env.HOME, '.claude', 'hooks', 'blocked.log');

const BLOCK_PATTERNS = [
  { pattern: /rm\s+-rf\s+\./,                      reason: "recursive rm on current dir" },
  { pattern: /DROP\s+TABLE/i,                       reason: "DROP TABLE — data destruction" },
  { pattern: /TRUNCATE\s+TABLE/i,                   reason: "TRUNCATE TABLE — full wipe" },
  { pattern: /DELETE\s+FROM\s+\w+\s*;?\s*$/i,        reason: "DELETE without WHERE — full table wipe" },
  { pattern: /git\s+push\s+--force/i,              reason: "git push --force — history rewrite" },
  { pattern: /git\s+push\s+-f/i,                   reason: "git push -f — history rewrite" },
  { pattern: /DROP\s+DATABASE/i,                   reason: "DROP DATABASE" },
];

function logBlocked(toolName, command, reason, cwd) {
  const ts = new Date().toISOString();
  const entry = `[${ts}] BLOCKED tool=${toolName} reason=${reason}\n  command=${JSON.stringify(command)}\n  cwd=${cwd}\n\n`;
  try {
    const dir = path.dirname(LOG_FILE);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.appendFileSync(LOG_FILE, entry);
  } catch (_) {}
}

function checkBlock(command, toolName, cwd) {
  for (const { pattern, reason } of BLOCK_PATTERNS) {
    if (pattern.test(command)) {
      logBlocked(toolName, command, reason, cwd);
      return {
        decision: "block",
        reason: `DESTRUCTIVE_COMMAND: ${reason}`,
        metadata: {
          original_command: command,
          suggestion: "Remove the destructive flag or add --dry-run before proceeding."
        }
      };
    }
  }
  return null;
}

/**
 * Claude Code hook interface.
 * @param {{ toolName: string, toolInput: any, result: any, context: any }} input
 */
module.exports = function preToolUseHook({ toolName, toolInput, result, context }) {
  if (!["Bash", "BashTool", "bash", "Shell"].includes(toolName)) {
    return { decision: "allow" };
  }
  const command = typeof toolInput === 'string' ? toolInput : (toolInput.command || '');
  const cwd = (context && context.cwd) || process.cwd();
  const block = checkBlock(command, toolName, cwd);
  return block || { decision: "allow" };
};
