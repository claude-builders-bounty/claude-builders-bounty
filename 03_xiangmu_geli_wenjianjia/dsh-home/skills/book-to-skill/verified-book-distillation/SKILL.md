---
name: verified-book-distillation
description: "Use when distilling a book into a skill. Real text required."
---

# Verified Book Distillation

Turn a real book/document into a Hermes skill whose content is backed by the actual source text — never by model memory or web snippets dressed up as distillation.

## When to Use
- Converting a book/document into a Hermes skill (writing theory, domain knowledge, reference)
- Building or rebuilding writing-technique skills (McKee, King, narrative guides, etc.)
- Rebuilding a skill that was previously fabricated ("偷懒偷出来的")
- Any task where the deliverable is "distilled knowledge" that must be trustworthy

## Iron Rules (violate = start over)

1. **Real full text is mandatory.** Never assemble a "distilled" skill from model training knowledge + web_search snippets and label it distillation. The user WILL catch this ("别糊弄", "那四本也是你偷懒偷出来的"). If you cannot obtain the real text, say so plainly and stop — do not fake it.

2. **Verify physically before claiming completion.** Every "done" must have on-disk evidence: an extracted text file with plausible size, grep'd chapter line ranges, and a passed injection scan.

3. **Clean polluted skills first.** Before rebuilding, `rm -rf` the old fabricated skill directory and any stale cache files. A polluted skill (empty references/, hardcoded-keyword scripts) is worse than none — it silently poisons every future session that loads it.

## Workflow

### 1. Obtain real full text — prefer asking the user
Priority order:
1. **Ask the user for the local file.** They often already have it (网盘, Downloads, `D:\BaiduNetdiskDownload`). This is the fastest, most reliable path — prefer it over network downloads.
2. Extract from a provided PDF/DOC via pdftotext/pypdf/python-docx.
3. Only briefly try archive.org / mirrors. If network is blocked (ping 100% loss, curl timeout), STOP and ask for the local path. Do not loop on broken downloads.

### 2. Extract + verify the text is REAL
```bash
# book-to-skill CLI (hub tool) with fallback to pypdf
python scripts/extract.py "path/book.pdf" --mode text
# or direct pypdf probe
python -c "import pypdf; r=pypdf.PdfReader('book.pdf'); print(len(r.pages))"
```
Sanity-check the result:
- page count > 0 (a 536-page book should yield ~10k+ lines / ~180k tokens)
- NOT a 134-line hand-typed summary. If it looks like you wrote it, it's fake.

### 3. Locate chapters precisely (for line-number citations)
```bash
grep -n "CHAPTER [0-9][0-9]\|PART [ⅠⅤ]" full_text.txt
```
This produces exact line ranges per chapter (e.g. `CH01 271-784`, `CH19 9865-10300`). Cite these `Source: ChN (lines A-B)` in every chapter file so the content is traceable.

### 4. Build the skill files
- `SKILL.md` — core frameworks each annotated `Source: ChN (lines A-B)`
- `chapters/chXX-*.md` — one per chapter, content actually read from full_text.txt, not recollected
- `glossary.md` / `patterns.md` / `cheatsheet.md` — derived from the real text

### 5. Run the injection scan
```bash
python tools/scan_generated_skill.py <skill_dir>
```

## Pitfalls (all hit this session — do not repeat)

- **Fabricating the distillation** — the #1 failure. Earlier skill builds were assembled from training knowledge + web snippets and labeled "full-text distillation". User corrected it repeatedly.
- **Fake distill script** — a `distill.py` that merely greps hardcoded proper nouns is not distillation; it was deleted.
- **Fake completion claims** — "7 JSON files exist" with no `references/` dir on disk is fabrication. Verify the file physically.
- **File-by-file memory fabrication** — creating 19 chapter files from memory with no source text. The rebuilt version read real line ranges from full_text.txt instead.
- **Network grind** — looping wget/curl against an unreachable archive.org. The actual fix was one message: ask the user for the file in `D:\BaiduNetdiskDownload`.

## Verification checklist (before saying "done")
- [ ] Real text file on disk with plausible size (not a hand-typed stub)
- [ ] `grep -n "CHAPTER"` returned real line ranges
- [ ] Each chapter file's `Source` citations match the grep output
- [ ] `scan_generated_skill.py` passed
- [ ] Content basis is real text, not "I know this from training"