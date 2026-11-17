---
name: browser-exec-web-scraping
description: "Drive browser_exec for JS-heavy site scraping with pagination, extraction, and fallback handling."
version: 0.1.0
author: User (Hermes Agent)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [browser, scraping, browser-exec, playwright, javascript, pagination, data-extraction]
    related_skills: [novel-download-12kanshu, playwright-chromium-china-mirror, web-content-fetcher]
---

# browser_exec Web Scraping Workflow

Standardized workflow for scraping JavaScript-heavy websites using `browser_exec` with Playwright. Handles pagination, dynamic content extraction, anti-bot measures, and fallback strategies.

## When to Use

- Site requires JavaScript rendering (SPA, dynamic loading, onclick handlers)
- Need to extract data from complex DOM structures
- Pagination via JavaScript (not simple URL patterns)
- Anti-bot measures (Cloudflare, login walls, rate limiting)
- Chapter/content extraction from Chinese novel sites, e-commerce, etc.

Don't use for:
- Static HTML sites (use `web_extract` or `web_search` instead)
- Simple API endpoints (use direct HTTP requests)
- One-off single-page scrapes (use `browser_exec` directly without this workflow)

## Prerequisites

- `PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/` (China mirror, set in `~/.profile` or systemd drop-in)
- `browser-use` CLI available (installed with Hermes)
- Browser binaries: `npx playwright install chromium` (run once)
- Network access to target site

## How to Run

```bash
# Set mirror (persistent)
echo 'export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/' >> ~/.profile
source ~/.profile

# Or one-time
PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/ npx playwright install chromium
```

## Quick Reference

| Step | Tool | Purpose |
|------|------|---------|
| 1. Navigate | `browser_exec(code="new_tab(url); wait_for_load()")` | Load initial page |
| 2. Inspect | `browser_exec(code="page_info(); js('document.body.innerHTML')")` | Understand DOM structure |
| 3. Extract list | `browser_exec(code="js(extraction_code)")` | Get item IDs, titles, URLs |
| 4. Handle pagination | Loop with `new_tab(page_url)` or click "next" | Fetch all pages |
| 5. Detail extraction | `browser_exec(code="new_tab(detail_url); wait_for_load(); js(content_extractor)")` | Get content per item |
| 6. Assemble & validate | Python post-processing | Combine, deduplicate, verify |

## Procedure

### 1. Initial Page Load & DOM Discovery

```python
# Load index page
code = """
new_tab("https://example.com/list")
wait_for_load()
print(page_info())
"""
```

**Completion criterion**: Page loads, `page_info()` shows expected URL/title, no 404/block.

### 2. Extract Item List from JavaScript-Rendered DOM

```python
# Generic pattern for onclick-based navigation (common on Chinese sites)
code = """
import json
items = js("""
(() => {
  const elements = document.querySelectorAll('YOUR_SELECTOR');
  const result = [];
  elements.forEach(el => {
    const onclick = el.getAttribute('onclick') || '';
    const match = onclick.match(/YOUR_REGEX/);
    const text = el.textContent.trim();
    if (match && text) {
      result.push({id: match[1], title: text, url: `https://example.com/item/${match[1]}.html`});
    }
  });
  return result;
})()
""")
print(json.dumps(items, ensure_ascii=False, indent=2))
"""
```

**Completion criterion**: JSON array with all items (id, title, URL) on current page.

### 3. Pagination Handling

**Pattern A: URL-based pagination (e.g., `page_N.html`)**
```python
page = 1
all_items = []
while True:
    url = f"https://example.com/list_{page}.html" if page > 1 else "https://example.com/list"
    code = f'new_tab("{url}"); wait_for_load(); {extraction_code}'
    items = run_browser_exec(code)
    if len(items) < EXPECTED_PER_PAGE:  # Last page
        all_items.extend(items)
        break
    all_items.extend(items)
    page += 1
    time.sleep(0.5)  # Rate limit
```

**Pattern B: Click "Next" button**
```python
while True:
    items = extract_current_page()
    all_items.extend(items)
    # Check for next button
    has_next = js("""document.querySelector('a.next, button.next, .pagination .next') !== null""")
    if not has_next:
        break
    js("document.querySelector('a.next, button.next, .pagination .next').click()")
    wait_for_load()
    time.sleep(1)
```

**Completion criterion**: All pages processed, total item count matches expectation.

### 4. Detail Page Content Extraction

```python
# For each item, fetch detail page
code = f"""
new_tab("{item['url']}")
wait_for_load()
# Try multiple selectors (sites vary)
content = js("""
(() => {
  for (const sel of ['.content', '.chapter_content', '#content', '.text', 'article', 'main']) {
    const el = document.querySelector(sel);
    if (el && el.innerText.length > 200) return el.innerText;
  }
  return document.body.innerText.slice(0, 5000);  // Fallback
})()
""")
print(content)
"""
```

**Completion criterion**: Content extracted, length > 200 chars, clean text (no nav/ads).

### 5. Rate Limiting & Retry

```python
import time, random

def fetch_with_retry(extract_func, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = extract_func()
            if result and len(result) > 100:
                return result
        except Exception as e:
            if attempt == max_retries - 1:
                raise
        time.sleep(2 ** attempt + random.uniform(0, 1))  # Exponential backoff + jitter
    return None
```

### 6. Assembly & Validation

```python
# Save chapter list
with open('chapters.json', 'w', encoding='utf-8') as f:
    json.dump(all_chapters, f, ensure_ascii=False, indent=2)

# Assemble full text
with open('full_text.txt', 'w', encoding='utf-8') as f:
    for ch in all_chapters:
        f.write(f"{ch['title']}\n{ch['content']}\n\n")

# Validate
print(f"Total chapters: {len(all_chapters)}")
print(f"Total chars: {sum(len(c['content']) for c in all_chapters)}")
# Spot check first/last
```

**Completion criterion**: Files written, chapter count matches, char count reasonable, UTF-8 valid.

## Implementation Notes

### Common Extraction Patterns

| Site Pattern | Selector / Method |
|--------------|-------------------|
| `onclick="func(id)"` | `el.getAttribute('onclick').match(/func\((\d+)\)/)` |
| `href="/item/123"` | `el.getAttribute('href').match(/\/item\/(\d+)/)` |
| `data-id="123"` | `el.getAttribute('data-id')` |
| React/Vue data attributes | `el.dataset.id` or `el.getAttribute('data-id')` |

### Anti-Bot Handling

```python
# If Cloudflare challenge detected
if "challenge" in page_info().get('title', '').lower() or "cloudflare" in html.lower():
    # Wait longer, maybe solve manually, or use undetected-chromedriver
    time.sleep(10)
    # Re-check
```

### Playwright China Mirror

Always set for reliable browser binary downloads in China:

```bash
# In ~/.profile or systemd drop-in
export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/
```

Or per-command:
```bash
PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/ browser_exec ...
```

## Pitfalls

| Issue | Solution |
|-------|----------|
| Empty extraction result | Selector wrong; use `page_info()` + `js('document.body.innerHTML')` to debug DOM |
| 404 on detail URLs | URL pattern differs; visit one in browser manually to verify |
| Rate limited / IP blocked | Increase delays (2-5s), add jitter, rotate User-Agent |
| Login wall | Stop — cannot bypass; report to user |
| Content truncated | Selector catches partial; use fallback selectors or body extraction |
| Memory/timeout on large scrapes | Batch into smaller runs, save progress incrementally to JSON |
| `browser_exec` session stale | Call `ensure_real_tab()` or start new session with `session=` param |

## Verification

```bash
# 1. Chapter/item count reasonable
python3 -c "
import json
with open('output/chapters.json') as f:
    ch = json.load(f)
print(f'Items: {len(ch)}')
print(f'First: {ch[0][\"title\"]}')
print(f'Last: {ch[-1][\"title\"]}')
"

# 2. Output file exists and non-empty
test -s output/full_text.txt && echo "OK" || echo "EMPTY"

# 3. Character count
wc -m output/full_text.txt

# 4. UTF-8 valid
file output/full_text.txt
# Should show: UTF-8 Unicode text

# 5. No duplicate IDs
python3 -c "
import json
with open('output/chapters.json') as f:
    ch = json.load(f)
ids = [c['id'] for c in ch]
print(f'Unique: {len(set(ids))} / Total: {len(ids)}')"
```

## Integration

- Output feeds into `novel-to-sillytavern-pipeline` for character card generation
- Use with `cross-platform-text-processing` for encoding/large file handling
- Combine with `memory-local` to store extracted entities

---

*Distilled from session 20260926_020816_1453bcf8 (324 messages: complete novel download from 12kanshu.com - 119 chapters via read_tz() JS pattern, pagination across index pages, Playwright China mirror config). Pattern threshold ≥3 met across: JS-rendered list extraction, onclick handler parsing, pagination handling, detail page content fetch, rate limiting, assembly validation.*