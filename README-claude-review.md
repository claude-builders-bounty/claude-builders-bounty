# claude-review — PR-Review-Agent

> Strukturierte PR-Reviews generiert von Claude Code.  
> Bounty: claude-builders-bounty Issue #4 ($150)

---

## 🚀 Installation (2 Schritte)

### Schritt 1: Speichern
Speichere `claude-review.py` in deinem Projekt-Root.

### Schritt 2: API-Key setzen
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```
Hole den Key unter https://console.anthropic.com

---

## 🎯 Nutzung

### Einfache Review
```bash
python claude-review.py --pr https://github.com/envoyproxy/envoy/pull/33079
```

### In Datei speichern
```bash
python claude-review.py --pr https://github.com/envoyproxy/envoy/pull/33079 --output review.md
```

### Anderes Claude-Modell verwenden
```bash
python claude-review.py --pr owner/repo#123 --model claude-opus-4-20250514
```

---

## 📋 Output-Format

```
## 📋 Summary
2–3 Sätze zum PR-Zweck.

## ⚠️ Risks
- Potenzielles Risiko 1
- Potenzielles Risiko 2

## 💡 Suggestions
- Verbesserungsvorschlag 1
- Verbesserungsvorschlag 2

## 🎯 Confidence
Confidence Score: Low / Medium / High
Begründung in 1 Satz.
```

---

## 🔧 Voraussetzungen

- Python 3.8+
- `pip install requests`
- `ANTHROPIC_API_KEY` in der Umgebung

---

## 📝 Beispiel

```bash
$ python claude-review.py --pr https://github.com/envoyproxy/envoy/pull/33079

🔄 Prüfe PR: envoyproxy/envoy #33079
Hole Diff … Diff: 12.834 Zeichen, +241 additions, -187 deletions
Sende an Claude …

## 📋 Summary
This PR updates header casing documentation in the HTTP/1 connection manager, clarifying expected behavior for incoming and outgoing header casing rules.

## ⚠️ Risks
- Potentially breaking existing proxies that rely on case-insensitive header handling

## 💡 Suggestions
- Add a test case with mixed-case headers
- Update changelog with the doc update

## 🎯 Confidence
Confidence Score: High
Changes are documentation-only and affect no runtime behavior.
```

---

## 📄 Lizenz

MIT
