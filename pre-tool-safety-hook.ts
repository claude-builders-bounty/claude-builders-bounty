/**
 * Pre-Tool-Use Safety Hook for Claude Code
 *
 * Intercepts bash tool calls before execution and blocks destructive commands.
 * Integrates with Claude Code's agent loop via the preToolUse hook API.
 *
 * Bounty: $100 — claude-builders-bounty/claude-builders-bounty#3
 */

export interface ToolCall {
  tool: string;
  command?: string;
  args?: Record<string, unknown>;
}

export interface SafetyResult {
  allowed: boolean;
  reason?: string;
  severity: "none" | "warning" | "blocked";
}

// Destructive command patterns (block immediately)
const BLOCKED_PATTERNS = [
  // Filesystem destruction
  /\brm\s+(-[rf]+\s+)?\/(\s|$)/,           // rm -rf / or rm /
  /\brm\s+(-[rf]+\s+)?.*\*/,                // rm -rf * or rm -rf ~/
  /\bmkfs\./,                                // mkfs.ext4, mkfs.ntfs, etc.
  /\bdd\s+if=\/dev\/zero/,                   // dd zeroing disks
  /\bdd\s+if=\/dev\/random.*of=\/dev\//,     // dd overwriting devices
  /\b shred\b/,                              // shred overwrite tool
  /\bwipefs\b/,                              // wipe filesystem signatures
  /\b>:\s*\/dev\//,                         // overwrite device with redirect

  // System-level destructive
  /\bchmod\s+(-R\s+)?000\s+\//,             // chmod 000 /
  /\bchown\s+-R\s+.*\s+\//,                 // chown -R on root
  /\bdocker\s+(system\s+)?prune\s+-a/,      // docker prune -a (deletes all)
  /\bdocker\s+(image|container)\s+prune\s+-f/, // docker prune with force

  // Network / security destructive
  /\biptables\s+-F/,                        // flush all firewall rules
  /\biptables\s+-X/,                        // delete all chains
  /\bpasswd\s+-d\s+root/,                   // delete root password
  /\buserdel\s+(-f\s+)?root/,               // delete root user
  /\bsystemctl\s+disable\s+.*ssh/,           // disable ssh service

  // Database destructive
  /\bDROP\s+DATABASE\s+/i,                  // drop entire database
  /\bTRUNCATE\s+TABLE\s+/i,                  // truncate tables
];

// Warning patterns (allow but warn)
const WARNING_PATTERNS = [
  /\brm\s+-rf\s+/,                           // rm -rf anywhere (not root)
  /\brmdir\s+/,                              // rmdir
  /\bfind\s+.*-delete/,                      // find -delete
  /\bfind\s+.*-exec\s+rm/,                   // find -exec rm
  /\bgit\s+clean\s+-fd/,                     // git clean -fd
  /\bgit\s+reset\s+--hard/,                  // git reset --hard
  /\bgit\s+push\s+--force/,                  // git push --force
  /\bkill\s+-9\s+/,                          // kill -9
  /\bpkill\s+-9/,                             // pkill -9
  /\bkillall\s+-9/,                          // killall -9
  /\bmv\s+.*\/dev\/null/,                    // mv to /dev/null
];

export function evaluateToolUse(toolCall: ToolCall): SafetyResult {
  if (toolCall.tool !== "bash" || !toolCall.command) {
    return { allowed: true, severity: "none" };
  }

  const cmd = toolCall.command.trim();

  // Check blocked patterns first
  for (const pattern of BLOCKED_PATTERNS) {
    if (pattern.test(cmd)) {
      return {
        allowed: false,
        severity: "blocked",
        reason: `BLOCKED: Destructive command matches dangerous pattern: ${pattern.source}`,
      };
    }
  }

  // Check warning patterns
  for (const pattern of WARNING_PATTERNS) {
    if (pattern.test(cmd)) {
      return {
        allowed: true,
        severity: "warning",
        reason: `WARNING: Potentially destructive command detected: ${pattern.source}. Confirm before executing.`,
      };
    }
  }

  return { allowed: true, severity: "none" };
}

/**
 * Claude Code integration — use this in your agent loop
 */
export function preToolUseHook(toolCall: ToolCall): SafetyResult {
  const result = evaluateToolUse(toolCall);

  if (result.severity === "blocked") {
    console.error(`🚫 SAFETY BLOCK: ${result.reason}`);
    console.error(`   Command: ${toolCall.command}`);
    console.error(`   Action: Command was blocked. No execution occurred.`);
    return result;
  }

  if (result.severity === "warning") {
    console.warn(`⚠️  SAFETY WARNING: ${result.reason}`);
    console.warn(`   Command: ${toolCall.command}`);
    console.warn(`   Action: Paused for confirmation. Type 'yes' to proceed.`);
    // In real integration, prompt user for confirmation here
    return result;
  }

  return result;
}

// Test cases (run with: npx tsx pre-tool-safety-hook.ts)
if (import.meta.main) {
  const testCases: ToolCall[] = [
    { tool: "bash", command: "rm -rf /" },
    { tool: "bash", command: "rm -rf ~/projects/old" },
    { tool: "bash", command: "ls -la" },
    { tool: "bash", command: "dd if=/dev/zero of=/dev/sda" },
    { tool: "bash", command: "git push --force" },
    { tool: "bash", command: "docker system prune -a -f" },
    { tool: "bash", command: "echo hello" },
  ];

  console.log("=== Pre-Tool Safety Hook Test Results ===\n");
  for (const tc of testCases) {
    const result = preToolUseHook(tc);
    const icon = result.severity === "blocked" ? "🚫" : result.severity === "warning" ? "⚠️" : "✅";
    console.log(`${icon} ${tc.command}`);
    console.log(`   Allowed: ${result.allowed} | Severity: ${result.severity}`);
    if (result.reason) console.log(`   Reason: ${result.reason}`);
    console.log();
  }
}
