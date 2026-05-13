/**
 * Claude Code Pre-Tool-Use Hook: Destructive Command Guard
 * Bounty #3 ($100)
 */
import * as fs from "fs";
import * as path from "path";
import * as readline from "readline";

const HOOKS_DIR = path.join(process.env.HOME || "~", ".claude", "hooks");
const LOG_FILE = path.join(HOOKS_DIR, "blocked.log");

const DANGEROUS: RegExp[] = [
  /rm\s+-rf/i, /dd\s+if=/i, /mkfs(?:\.[a-z]+)?\s/i,
  /:\s*\(\s*\)\s*\{/, /chmod\s+-R\s+777/i,
  />\s*\/dev\/sd[a-z]/i, /\bshutdown\b/i, /\breboot\b/i,
  /\bhalt\b/i, /\bpoweroff\b/i, /\bformat\b/i,
  /\bfdisk\b/i, /\bparted\b/i, /\bmv\s+\/\*/i,
  /\bDROP\s+TABLE\b/i, /\bTRUNCATE\b/i,
  /\bDELETE\s+FROM\b(?!.*WHERE)/i, /git\s+push\s+--force/i,
];

function isDangerous(cmd: string): boolean {
  return DANGEROUS.some((p) => p.test(cmd));
}

function log(entry: string): void {
  const ts = new Date().toISOString();
  try {
    if (!fs.existsSync(HOOKS_DIR)) fs.mkdirSync(HOOKS_DIR, { recursive: true });
    fs.appendFileSync(LOG_FILE, `[${ts}] ${entry} | ${process.cwd()}\n`, "utf-8");
  } catch {}
}

async function prompt(msg: string): Promise<boolean> {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise((resolve) => {
    rl.question(`${msg} (y/N): `, (ans) => { rl.close(); resolve(ans.toLowerCase() === "y"); });
  });
}

export async function preToolUse(event: any): Promise<any> {
  if (event.tool_name !== "bash" && event.tool_name !== "zsh") return {};
  const cmd = event.input?.command as string;
  if (!cmd || !isDangerous(cmd)) return {};

  console.warn(`\nDESTRUCTIVE COMMAND BLOCKED\nCommand: ${cmd}\n`);
  log(`BLOCKED: ${cmd}`);

  const ok = await prompt("Execute anyway?");
  if (ok) { log(`OVERRIDDEN: ${cmd}`); return {}; }

  return { abort: true, error: `Command blocked: ${cmd}` };
}
