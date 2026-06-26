# Sample blocked log

`~/.claude/hooks/blocked.log` entries are JSON lines:

```json
{"timestamp":"2026-06-26T03:44:00.000000+00:00","project_path":"/tmp/example-project","reason":"recursive forced remove (rm -rf / rm -fr)","command":"rm -rf build/"}
{"timestamp":"2026-06-26T03:45:00.000000+00:00","project_path":"/tmp/example-project","reason":"DELETE FROM statement without a WHERE clause","command":"psql -c \"DELETE FROM users\""}
```

