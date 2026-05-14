# Destructive Hook Sample Output

Command:

```bash
rm -rf dist
```

Hook response:

```json
{
  "decision": "block",
  "reason": "Blocked dangerous bash command pattern: rm -rf. Refusing to run destructive filesystem deletion."
}
```

Blocked log line shape:

```text
2026-05-14T05:05:00Z\t/root/example-project\trm -rf dist\trm -rf
```
