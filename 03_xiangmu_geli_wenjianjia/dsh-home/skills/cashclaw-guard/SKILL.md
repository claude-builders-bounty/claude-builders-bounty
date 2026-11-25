---
name: cashclaw-guard
description: Runtime guard with cost cap, recursion kill, tool firewall.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [cashclaw, guard, runtime-protection, cost-cap, recursion-kill, tool-firewall]
    related_skills: [cashclaw-core]
    requires_toolsets: [terminal, web, file]
---

# CashClaw Guard - Runtime Protection

## When to Use
- Need to enforce hard runtime cost caps per task/call/day
- Need to prevent infinite recursion loops
- Need to restrict tool usage to allowed set
- Need rate limiting on tool calls
- Need webhook alerts on violations

---

## Guard Policy (YAML)

```yaml
version: 1
limits:
  cost_usd_per_day: 50
  cost_usd_per_call: 5
  max_tokens_per_call: 50000
  max_recursion_depth: 10
tools:
  denylist: []
  rate_limits:
    web_search: { max_per_minute: 20 }
    browser_exec: { max_per_minute: 10 }
    delegate_task: { max_per_minute: 5 }
webhook:
  feishu:
    enabled: true
    on: [budget_exceeded, recursion_killed, tool_denied, mission_failed]
    chat_id: "oc_2c2df597014d50f6874aa1ab78b05eb9"
```

---

## Guard Components

### 1. Cost Tracker
- Tracks token usage and USD cost per call/session/day
- Hard cap at `cost_usd_per_call` (default $5) and `cost_usd_per_day` (default $50)
- Aggregates across all LLM calls in a session
- Throws `BudgetExceeded` exception when limit hit

### 2. Recursion Detector
- Fingerprints each call (prompt + context hash)
- Sliding window counter (default 60s window)
- Throws `RecursionKilled` when same fingerprint exceeds `max_recursion_depth` (default 10) in window
- Ring buffer for last N events (default 1000)

### 3. Tool Firewall
- Allowlist: `web_search`, `browser_exec`, `terminal`, `read_file`, `write_file`, `patch`, `search_files`, `vision_analyze`, `delegate_task`, `skill_view`, `skill_manage`, `web_extract`
- Denylist: `shell`, `exec`, `eval`, `rm` (configured in policy)
- Rate limits per tool (configurable in policy)
- Throws `ToolDenied` on violation

### 4. Webhook Alerts
- Channels: Feishu, Telegram, Slack, Discord, generic HTTP
- Events: `budget_exceeded`, `recursion_killed`, `tool_denied`, `mission_failed`, `token_exhausted`
- Auto-sends on violation with context

---

## CLI Commands

```bash
# Initialize guard policy
cashclaw guard init

# Check status
cashclaw guard status

# Test guard (dry-run 8 scenarios)
cashclaw guard test

# Kill running agent
cashclaw guard kill <agent_id>

# View recent guard events
cashclaw guard logs

# Hot-reload YAML policy without restart
cashclaw guard reload
```

---

## Programmatic Usage

```javascript
import { guard } from 'cashclaw/guard';

const safeChat = guard.llm({
  maxCostUsd: 5,
  maxRecursion: 10,
  agentId: 'support-bot',
})(async (prompt) => {
  return await openai.chat.completions.create({
    model: 'gpt-5.5',
    messages: [{ role: 'user', content: prompt }],
  });
});

await safeChat('summarize this ticket');
// Throws BudgetExceeded if call would push over cap
// Throws RecursionKilled if fingerprint repeats 5x in 60s
```

---

## Integration with Hermes RuntimeGuard

The Hermes `RuntimeGuard` class implements equivalent protection in Python:

```python
class RuntimeGuard:
    MAX_EXECUTION_TIME = 300          # 5 min per task
    MAX_RECURSION_DEPTH = 10          # max recursion depth
    MAX_TOOL_CALLS_PER_TASK = 50      # max tool calls per task
    TOOL_WHITELIST = {
        "web_search", "browser_exec", "terminal", "read_file", "write_file",
        "patch", "search_files", "vision_analyze", "delegate_task",
        "skill_view", "skill_manage", "web_extract"
    }
    TOOL_BLACKLIST = set()
    
    def check_tool(self, tool: str) -> bool:
        if tool in self.TOOL_BLACKLIST: return False
        if self.tool_call_count >= 50: return False
        return tool in self.TOOL_WHITELIST
    
    def on_tool_call(self, tool: str):
        self.tool_call_count += 1
    
    def check_timeout(self) -> bool:
        if self.start_time and (time.time() - self.start_time) > 300:
            return False
        return True
```

---

## Guard Policy File
Location: `~/.cashclaw/guard-policy.yaml`

```yaml
version: 1
limits:
  cost_usd_per_day: 50
  cost_usd_per_call: 5
  max_tokens_per_call: 50000
  max_recursion_depth: 10
tools:
  denylist: []
  rate_limits:
    web_search: { max_per_minute: 20 }
    browser_exec: { max_per_minute: 10 }
    delegate_task: { max_per_minute: 5 }
webhook:
  feishu:
    enabled: true
    on: [budget_exceeded, recursion_killed, tool_denied, mission_failed]
    chat_id: "oc_2c2df597014d50f6874aa1ab78b05eb9"
```

---

## Guard CLI Commands

```bash
cashclaw guard init       # Write default policy
cashclaw guard status     # Active policy + last 10 events
cashclaw guard test       # Dry-run 8 scenarios
cashclaw guard kill <id>  # Signal kill for running agent
cashclaw guard logs       # In-process event ring buffer
cashclaw guard reload     # Hot-reload YAML without restart
```

---

## Integration with Hermes
- Hermes `RuntimeGuard` class provides equivalent protection in Python
- Feishu webhook alerts on violations
- Integrated into `PlatformHandler.execute_task()` for every task

*蒸馏自 CashClaw v1.7.0 cashclaw-guard 源码，适配 Hermes RuntimeGuard。*