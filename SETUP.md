# 📋 generate-changelog.sh — Setup & Usage

Erzeugt eine strukturierte `CHANGELOG.md` aus Git-Commit-History — **in unter 3 Schritten**.

---

## 🚀 Installation (3 Schritte)

### Schritt 1: Speichern
Speichere das Skript als `generate-changelog.sh` in deinem Projekt-Root.

### Schritt 2: Ausführbar machen
```bash
chmod +x generate-changelog.sh
```

### Schritt 3: Ausführen
```bash
./generate-changelog.sh
```

Fertig! Die Datei `CHANGELOG.md` wird im aktuellen Ordner erstellt.

---

## 🎯 Nutzung

### Standard
```bash
./generate-changelog.sh
```
→ Alle Commits seit dem letzten Git-Tag bis HEAD.

### Mit eigenem Bereich
```bash
./generate-changelog.sh v1.0.0 HEAD
```
→ Alle Commits zwischen `v1.0.0` und `HEAD`.

### In Datei-Umgebungsvariable
```bash
OUTPUT_FILE=docs/CHANGELOG.md ./generate-changelog.sh
```

---

## ⚙️ Funktionsweise

1. **Commit-Sammlung:** Holt alle Commits im gewünschten Bereich via `git log`
2. **Kategorisierung:** Klassifiziert jede Commit-Message nach [Conventional Commits](https://www.conventionalcommits.org/):
   - `Added` — `feat`, `add`, `new`, `implement`
   - `Fixed` — `fix`, `hotfix`, `bugfix`, `resolv`
   - `Changed` — `chore`, `refactor`, `perf`, `improve`, `update`
   - `Removed` — `remove`, `delet`, `drop`, `deprecat`
   - `Docs` — `doc`, `docs`, `document`, `comment`
   - `Tests` — `test`, `tests`, `spec`, `assert`
   - `Build` — `build`, `compile`, `bundle`, `deps`
   - `CI` — `ci`, `cd`, `pipeline`, `workflow`, `lint`, `format`
3. **Formatierung:** Schreibt eine saubere Markdown-Datei mit Kategorien und Commit-Hashes

---

## 📦 Voraussetzungen

- **Bash** 4.0+
- **Git** 2.0+
- Keine weiteren Abhängigkeiten

---

## 📝 Testen

Nutze das [`envoyproxy/envoy`](https://github.com/envoyproxy/envoy) Repo zum Ausprobieren:

```bash
git clone https://github.com/envoyproxy/envoy.git
cd envoy
./generate-changelog.sh
# → erzeugt CHANGELOG.md mit den letzten Commits
```

---

## ✍️ Lizenz

MIT – siehe Haupt-Repo.
