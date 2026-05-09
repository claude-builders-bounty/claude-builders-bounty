#!/usr/bin/env node

/**
 * Security Pre-Hook for Bash Commands
 * Analyzes bash commands for dangerous or destructive patterns before execution.
 */

// Patterns that indicate highly destructive or dangerous behavior
const DANGEROUS_PATTERNS = [
    {
        id: 'recursive_delete_root',
        regex: /rm\s+-r[fv]?\s+(?:\/|\/\*|~|~\/\*|\$HOME|\$HOME\/\*)/i,
        message: 'Attempted to recursively delete root or home directory.'
    },
    {
        id: 'curl_pipe_bash',
        regex: /(?:curl|wget).*\|\s*(?:bash|sh|zsh)/i,
        message: 'Attempted to download and pipe a remote script directly to a shell.'
    },
    {
        id: 'disk_format_wipe',
        regex: /(?:mkfs|dd\s+if=\/dev\/zero|dd\s+if=\/dev\/urandom|fdisk\s|mkswap)/i,
        message: 'Attempted to format or wipe a disk partition.'
    },
    {
        id: 'modify_shadow_passwd',
        regex: /(?:>>?>?|chmod|chown|rm|vi|nano)\s+\/etc\/(?:shadow|passwd|sudoers)/i,
        message: 'Attempted to modify critical system authentication files.'
    },
    {
        id: 'ssh_key_extraction',
        regex: /(?:cat|cp|mv|curl|wget).*~\/\.ssh\/(?:id_rsa|id_ed25519|id_ecdsa)(?!\.pub)/i,
        message: 'Attempted to access or exfiltrate private SSH keys.'
    },
    {
        id: 'fork_bomb',
        regex: /:\(\)\{\s*:\|:&\s*\};:/i,
        message: 'Attempted to execute a fork bomb.'
    },
    {
        id: 'dev_tcp_reverse_shell',
        regex: /\/dev\/tcp\/\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,5}/i,
        message: 'Attempted to open a reverse shell or raw TCP connection.'
    },
    {
        id: 'chmod_777_root',
        regex: /chmod\s+(?:-R\s+)?777\s+\//i,
        message: 'Attempted to make the root directory globally writable.'
    }
];

function analyzeCommand(command) {
    if (!command || typeof command !== 'string') {
        return { isSafe: true, command, violations: [] };
    }

    const violations = [];

    for (const pattern of DANGEROUS_PATTERNS) {
        if (pattern.regex.test(command)) {
            violations.push({
                id: pattern.id,
                message: pattern.message
            });
        }
    }

    return {
        isSafe: violations.length === 0,
        command,
        violations
    };
}

// If run as a CLI tool
if (require.main === module) {
    const args = process.argv.slice(2);
    
    if (args.length === 0 || args[0] === '--help') {
        console.log(`
Usage:
  node index.js "your bash command"

Example:
  node index.js "ls -la"
  node index.js "rm -rf /"
        `);
        process.exit(0);
    }

    const command = args[0];
    const result = analyzeCommand(command);

    if (result.isSafe) {
        console.log(JSON.stringify({ status: 'allowed', command: result.command }, null, 2));
        process.exit(0);
    } else {
        console.error(JSON.stringify({ 
            status: 'blocked', 
            command: result.command,
            reasons: result.violations.map(v => v.message)
        }, null, 2));
        
        // Exit with 1 to indicate failure (halts automated execution)
        process.exit(1);
    }
}

module.exports = { analyzeCommand, DANGEROUS_PATTERNS };
