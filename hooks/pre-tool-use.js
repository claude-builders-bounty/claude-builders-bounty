#!/usr/bin/env node
/**
 * Claude Code pre-tool-use hook: blocks destructive bash commands
 * 
 * Installed via: claude code hooks add preToolUse hooks/pre-tool-use.js
 *
 * Blocks:
 *   - rm -rf (recursive force delete)
 *   - DROP TABLE / DROP DATABASE (SQL destruction)
 *   - git push --force / git push -f (force push)
 *   - TRUNCATE TABLE (SQL truncation)
 *   - DELETE FROM without WHERE clause (mass deletion)
 *
 * Logs all blocked attempts to ~/.claude/hooks/blocked.log
 */

const fs = require('fs');
const path = require('path');

const LOG_FILE = path.join(process.env.HOME || '/root', '.claude', 'hooks', 'blocked.log');
const HOOKS_DIR = path.join(process.env.HOME || '/root', '.claude', 'hooks');

// Destructive patterns to block
const BLOCKED_PATTERNS = [
  {
    pattern: /^rm\s+-rf\s+/,
    reason: 'Recursive force delete — destroys data permanently',
    example: 'rm -rf /tmp/test'
  },
  {
    pattern: /git\s+push\s+--force/,
    reason: 'Force push — overwrites remote history, can lose commits',
    example: 'git push --force origin main'
  },
  {
    pattern: /git\s+push\s+-f\b/,
    reason: 'Force push shorthand — same danger as --force',
    example: 'git push -f'
  },
  {
    pattern: /^DROP\s+TABLE/i,
    reason: 'SQL DROP TABLE — removes entire table from database',
    example: 'DROP TABLE users'
  },
  {
    pattern: /^DROP\s+DATABASE/i,
    reason: 'SQL DROP DATABASE — removes entire database',
    example: 'DROP DATABASE production'
  },
  {
    pattern: /^TRUNCATE\s+TABLE/i,
    reason: 'SQL TRUNCATE — removes all rows from table',
    example: 'TRUNCATE TABLE sessions'
  },
  {
    // DELETE FROM without WHERE clause
    pattern: /^DELETE\s+FROM\s+\w+\s*;?\s*$/i,
    reason: 'DELETE FROM without WHERE clause — removes ALL rows',
    example: 'DELETE FROM users'
  }
];

function log_blocked(command, reason, projectPath) {
  const timestamp = new Date().toISOString();
  const logEntry = `[${timestamp}] BLOCKED | tool=Bash | project=${projectPath} | reason=${reason} | command=${command}\n`;
  
  try {
    // Ensure log directory exists
    if (!fs.existsSync(HOOKS_DIR)) {
      fs.mkdirSync(HOOKS_DIR, { recursive: true });
    }
    fs.appendFileSync(LOG_FILE, logEntry);
  } catch (err) {
    console.error(`[pre-tool-use hook] Warning: could not write to log: ${err.message}`);
  }
}

function is_destructive(command) {
  const trimmed = command.trim();
  
  for (const { pattern } of BLOCKED_PATTERNS) {
    if (pattern.test(trimmed)) {
      return true;
    }
  }
  return false;
}

function get_reason(command) {
  const trimmed = command.trim();
  
  for (const { pattern, reason } of BLOCKED_PATTERNS) {
    if (pattern.test(trimmed)) {
      return reason;
    }
  }
  return 'Unknown destructive command';
}

function main() {
  try {
    // Read JSON input from stdin
    let input = '';
    process.stdin.on('data', chunk => { input += chunk; });
    
    process.stdin.on('end', () => {
      try {
        const data = JSON.parse(input);
        
        // Only check Bash tool
        if (data.tool !== 'Bash') {
          process.stdout.write(JSON.stringify({ allow: true }));
          return;
        }
        
        const command = data.args?.command || '';
        const projectPath = data.args?.cwd || process.cwd();
        
        if (is_destructive(command)) {
          const reason = get_reason(command);
          log_blocked(command, reason, projectPath);
          
          // Block the command with a clear message
          const blockMessage = `
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⛔ COMMAND BLOCKED — DESTRUCTIVE OPERATION ⛔
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This command was blocked because it performs a destructive operation:

  Command: ${command}

  Reason:  ${reason}

This block was triggered by the pre-tool-use destructive-command hook.
If you need to run this command, you can:
  1. Ask the user to confirm they want to proceed
  2. Run the command directly in a terminal (bypassing Claude Code)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
`;
          process.stdout.write(JSON.stringify({ 
            allow: false, 
            reason: blockMessage
          }));
        } else {
          // Allow non-destructive commands
          process.stdout.write(JSON.stringify({ allow: true }));
        }
      } catch (err) {
        // If parsing fails, allow the command (fail open)
        console.error(`[pre-tool-use hook] Parse error: ${err.message}`);
        process.stdout.write(JSON.stringify({ allow: true }));
      }
    });
  } catch (err) {
    console.error(`[pre-tool-use hook] Error: ${err.message}`);
    process.stdout.write(JSON.stringify({ allow: true }));
  }
}

main();
